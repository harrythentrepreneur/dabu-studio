#!/usr/bin/env python3
"""
Main processing pipeline for TikTok Video Ad Automation.

This module implements the complete processing flow from PRD section 5,
orchestrating video processing, Gemini analysis, and output generation.
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.video_processor import VideoProcessor
from core.gemini_client import GeminiClient
from utils.video_utils import VideoPipeline
from utils.logger import get_logger, LogContext
from utils.exceptions import (
    VideoProcessingError,
    GeminiAPIError,
    DurationMismatchError
)
from models.schemas import (
    ProcessingRequest,
    ProcessingResponse,
    GeminiResponse
)
from config.settings import VideoConfig

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

logger = get_logger(__name__)


class MainPipeline:
    """Main processing pipeline orchestrator."""
    
    def __init__(self):
        """Initialize the main pipeline with all components."""
        self.video_processor = VideoProcessor()
        self.video_pipeline = VideoPipeline(self.video_processor)
        self.gemini_client = GeminiClient()
        
        # Set up directories
        self.input_dir = Path(__file__).parent.parent / 'input_videos'
        self.output_dir = Path(__file__).parent.parent / 'output'
        self.temp_dir = Path(__file__).parent / 'temp'
        
        for directory in [self.input_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("MainPipeline initialized")
        
        # Log video processing configuration
        VideoConfig.log_config(logger)
    
    def load_script(self, script_path: Optional[Path] = None) -> str:
        """
        Load script from file.
        
        Args:
            script_path: Path to script file (defaults to input_videos/script.txt)
            
        Returns:
            Script text
        """
        if not script_path:
            script_path = self.input_dir / 'script.txt'
        
        if not script_path.exists():
            raise FileNotFoundError(f"Script file not found: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read().strip()
        
        logger.info(f"Loaded script: {len(script)} characters")
        return script
    
    def get_video_files(self, video_dir: Optional[Path] = None) -> List[Path]:
        """
        Get list of video files from directory.
        
        Args:
            video_dir: Directory containing videos (defaults to input_videos/)
            
        Returns:
            List of video file paths
        """
        if not video_dir:
            video_dir = self.input_dir
        
        # Find all video files
        video_extensions = ['.mp4', '.MP4', '.mov', '.MOV', '.avi', '.AVI']
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(video_dir.glob(f'*{ext}'))
        
        # Filter out script.txt and other non-video files
        video_files = [
            vf for vf in video_files 
            if not vf.name.startswith('.') and vf.name != 'script.txt'
        ]
        
        # Sort by name for consistency
        video_files.sort()
        
        if not video_files:
            raise FileNotFoundError(f"No video files found in {video_dir}")
        
        logger.info(f"Found {len(video_files)} video files")
        return video_files
    
    def process(
        self,
        script: Optional[str] = None,
        video_files: Optional[List[Path]] = None,
        voiceover_path: Optional[Path] = None,  # NEW parameter
        target_duration: float = 35.0,
        use_mock: bool = False,
        request_id: Optional[str] = None,
        status_emitter = None
    ) -> ProcessingResponse:
        """
        Main processing pipeline implementation from PRD section 5.
        
        Args:
            script: TikTok ad script (loads from file if None)
            video_files: List of video files (auto-detects if None)
            voiceover_path: Optional path to voiceover audio file
            target_duration: Target duration in seconds
            use_mock: Use mock Gemini response for testing
            request_id: Unique request identifier for consistent file naming
            status_emitter: SSE status emitter for real-time updates
            
        Returns:
            ProcessingResponse with all outputs
        """
        start_time = time.time()
        voiceover_segments = None  # Will be populated if voiceover provided
        voiceover_included = False
        
        # Initialize debug collector if debug mode is enabled
        debug_collector = None
        if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
            from utils.debug_collector import DebugCollector
            debug_collector = DebugCollector(request_id, self.output_dir)
            logger.info("Debug mode enabled - collecting detailed diagnostic data")
        
        try:
            # Step 0 (Optional): Analyze voiceover if provided
            if voiceover_path and voiceover_path.exists():
                logger.info("="*60)
                logger.info("VOICEOVER MODE: Using Whisper for exact timing")
                logger.info("="*60)
                
                if status_emitter:
                    status_emitter.emit_status(1, "Analyzing voiceover", 5, "Processing voiceover with Whisper API...")
                
                try:
                    # Import here to avoid dependency if not using voiceover
                    from services.voiceover_analyzer import VoiceoverAnalyzer
                    analyzer = VoiceoverAnalyzer()
                    voiceover_segments = analyzer.analyze_voiceover(voiceover_path, script or self.load_script())
                    voiceover_included = True
                    
                    logger.info(f"✓ Voiceover analyzed: {len(voiceover_segments)} segments")
                    for i, seg in enumerate(voiceover_segments, 1):
                        logger.info(
                            f"  Segment {i}: {seg['start']:.2f}s → {seg['end']:.2f}s "
                            f"({seg['duration']:.2f}s)"
                        )
                    
                    # Collect debug data for Whisper analysis
                    if debug_collector:
                        from utils.audio_utils import AudioUtils
                        audio_utils = AudioUtils()
                        voiceover_duration = audio_utils.get_audio_duration(voiceover_path)
                        debug_collector.collect_whisper_data(
                            voiceover_path=voiceover_path,
                            voiceover_duration=voiceover_duration,
                            raw_segments=voiceover_segments,  # In this case, same as processed
                            processed_segments=voiceover_segments
                        )
                    
                    if status_emitter:
                        status_emitter.emit_status(1, "Analyzing voiceover", 10, f"Voiceover analyzed: {len(voiceover_segments)} segments")
                        
                except ImportError as e:
                    logger.warning(f"Voiceover analyzer not available: {e}")
                    logger.info("Falling back to STANDARD MODE")
                except Exception as e:
                    logger.error(f"Voiceover analysis failed: {e}")
                    logger.info("Falling back to STANDARD MODE")
            else:
                logger.info("="*60)
                logger.info("STANDARD MODE: Using Gemini auto-segmentation")
                logger.info("="*60)
            
            # Step 1 (or 2 with voiceover): Load inputs
            step_offset = 1 if voiceover_included else 0
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {1 + step_offset}: Loading inputs...")
            
            if status_emitter:
                # Adjust progress based on whether voiceover was analyzed
                progress = 15 if voiceover_included else 10
                status_emitter.emit_status(1 + step_offset, "Loading inputs", progress, "Preparing script and video files...")
            
            if not script:
                script = self.load_script()
            
            if not video_files:
                video_files = self.get_video_files()
            
            logger.info(f"Target duration: {target_duration} seconds")
            
            if status_emitter:
                progress = 20 if voiceover_included else 20
                status_emitter.emit_status(1 + step_offset, "Loading inputs", progress, f"Loaded script and {len(video_files)} video files")
            
            # Step 2 (or 3 with voiceover): Prepare videos (both versions + index)
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {2 + step_offset}: Preparing videos...")
            
            if status_emitter:
                status_emitter.emit_status(2 + step_offset, "Merging videos", 25, "Merging video files into full and compressed versions...")
            
            merged_full, merged_compressed, video_index = \
                self.video_pipeline.prepare_videos_for_pipeline(
                    video_files,
                    output_dir=self.temp_dir,
                    request_id=request_id
                )
            
            full_size = self.video_processor.get_file_size(merged_full)
            compressed_size = self.video_processor.get_file_size(merged_compressed)
            
            logger.info(f"✓ Full quality: {merged_full.name} ({full_size:.1f}MB)")
            logger.info(f"  Location: {merged_full.absolute()}")
            logger.info(f"✓ Compressed: {merged_compressed.name} ({compressed_size:.1f}MB)")
            logger.info(f"  Location: {merged_compressed.absolute()}")
            
            if status_emitter:
                status_emitter.emit_status(2 + step_offset, "Merging videos", 40, f"Videos merged successfully: {full_size:.1f}MB full, {compressed_size:.1f}MB compressed")
            
            # Step 3: Upload compressed to Gemini (always compressed)
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {3 + step_offset}: Uploading to Gemini API...")
            
            if status_emitter:
                status_emitter.emit_status(3 + step_offset, "Uploading to AI", 45, "Uploading compressed video to Gemini API...")
            
            if use_mock:
                logger.warning("Using MOCK mode - skipping actual Gemini upload")
                gemini_input = "mock_video"
            else:
                gemini_input = self.gemini_client.upload_to_gemini(merged_compressed)
                logger.info("✓ Upload complete")
            
            if status_emitter:
                status_emitter.emit_status(3 + step_offset, "Uploading to AI", 55, "Video uploaded successfully to Gemini API")
            
            # Step 4: Get Gemini analysis with auto-segmentation
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {4 + step_offset}: Analyzing with Gemini...")
            
            if status_emitter:
                status_emitter.emit_status(4 + step_offset, "AI Analysis", 60, "Analyzing video content and matching with script...")
            
            if use_mock:
                # Use fallback/mock response for testing
                video_duration = self.video_processor.get_video_duration(merged_full)
                timestamps = self.gemini_client.create_fallback_response(
                    script, target_duration, video_duration
                )
                logger.warning("Using MOCK Gemini response")
            else:
                timestamps = self.gemini_client.get_gemini_response_with_json(
                    gemini_input,
                    script,
                    target_duration,
                    voiceover_segments=voiceover_segments  # Pass voiceover segments if available
                )
            
            logger.info(f"✓ Received {len(timestamps.script_segments)} segments")
            for i, seg in enumerate(timestamps.script_segments, 1):
                logger.info(
                    f"  Segment {i}: {seg.start_timestamp} → {seg.end_timestamp} "
                    f"({seg.duration_seconds:.1f}s, confidence: {seg.confidence:.0%})"
                )
            
            # Collect debug data for Gemini response
            if debug_collector:
                try:
                    # Convert GeminiResponse to dict for debugging
                    gemini_dict = {
                        'total_duration': timestamps.total_duration,
                        'target_duration': timestamps.target_duration,
                        'script_segments': [
                            {
                                'segment_number': seg.segment_number if seg.segment_number is not None else i+1,
                                'segment_text': seg.segment_text or '',
                                'start_timestamp': seg.start_timestamp or '00:00:00.000',
                                'end_timestamp': seg.end_timestamp or '00:00:00.000',
                                'duration_seconds': seg.duration_seconds or 0,
                                'confidence': seg.confidence if seg.confidence is not None else 0,
                                'visual_description': seg.visual_description or ''
                            }
                            for i, seg in enumerate(timestamps.script_segments)
                        ]
                    }
                    debug_collector.collect_gemini_response(gemini_dict, voiceover_segments)
                except Exception as debug_error:
                    logger.warning(f"Debug collection error (non-fatal): {debug_error}")
            
            if status_emitter:
                status_emitter.emit_status(4 + step_offset, "AI Analysis", 75, f"Analysis complete: {len(timestamps.script_segments)} segments identified")
            
            # Step 5: Validate and adjust duration if needed
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {5 + step_offset}: Validating duration...")
            
            if status_emitter:
                status_emitter.emit_status(5 + step_offset, "Validating duration", 78, "Checking segment durations and quality...")
            
            total_duration = timestamps.total_duration
            difference = abs(total_duration - target_duration)
            
            if difference > 15.0:
                logger.warning(
                    f"Duration outside tolerance: {total_duration:.1f}s "
                    f"(target: {target_duration}s, diff: {difference:.1f}s)"
                )
                # Could implement duration adjustment logic here
            else:
                logger.info(f"✓ Duration validated: {total_duration:.1f}s (within ±15s tolerance)")
            
            if status_emitter:
                status_emitter.emit_status(5 + step_offset, "Validating duration", 80, f"Duration validated: {total_duration:.1f}s")
            
            # Step 6: Extract segments from full-quality merged video
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {6 + step_offset}: Extracting and compiling segments...")
            
            if status_emitter:
                status_emitter.emit_status(6 + step_offset, "Extracting segments", 82, "Extracting video segments from full-quality source...")
            
            compiled_video = self.video_pipeline.extract_and_compile_segments(
                merged_full,
                timestamps,
                output_dir=self.output_dir,
                request_id=request_id,
                voiceover_segments=voiceover_segments,  # Pass voiceover segments for exact durations
                debug_collector=debug_collector  # Pass debug collector for tracking
            )
            
            logger.info(f"✓ Compiled video: {compiled_video.name}")
            
            if status_emitter:
                status_emitter.emit_status(6 + step_offset, "Extracting segments", 90, "Video segments extracted and compiled successfully")
            
            # Step 7: Export everything
            logger.info("\n" + "-"*40)
            logger.info(f"STEP {7 + step_offset}: Exporting outputs...")
            
            if status_emitter:
                status_emitter.emit_status(7 + step_offset, "Exporting outputs", 92, "Preparing final outputs (video, script, timestamps)...")
            
            output_files = self.video_pipeline.export_outputs(
                compiled_video,
                script,
                timestamps,
                output_dir=self.output_dir,
                request_id=request_id
            )
            
            logger.info(f"✓ Exported video: {output_files['video'].name}")
            logger.info(f"✓ Exported script: {output_files['script'].name}")
            logger.info(f"✓ Exported timestamps: {output_files['timestamps'].name}")
            
            if status_emitter:
                status_emitter.emit_status(7 + step_offset, "Exporting outputs", 95, "All outputs exported successfully")
            
            # Step 8 (Optional): Add voiceover to video if provided
            if voiceover_included and voiceover_path:
                logger.info("\n" + "-"*40)
                logger.info("STEP 9: Adding voiceover audio...")
                
                if status_emitter:
                    status_emitter.emit_status(9, "Adding voiceover", 96, "Muxing voiceover audio to video...")
                
                final_video = self.video_processor.add_voiceover_to_video(
                    compiled_video,
                    voiceover_path,
                    compiled_video.parent / f"{compiled_video.stem}_with_voiceover.mp4"
                )
                
                # Log sync info but don't fail - the video is done!
                if voiceover_segments:
                    voiceover_total = sum(s['duration'] for s in voiceover_segments)
                    video_duration = self.video_processor.get_video_duration(final_video)
                    difference = abs(video_duration - voiceover_total)
                    
                    if difference > 5.0:  # Only warn for large differences
                        logger.warning(
                            f"Duration difference: video={video_duration:.2f}s, "
                            f"voiceover={voiceover_total:.2f}s (difference: {difference:.2f}s)"
                        )
                    else:
                        logger.info(
                            f"✓ Sync validated: video={video_duration:.2f}s, "
                            f"voiceover={voiceover_total:.2f}s (difference: {difference:.2f}s)"
                        )
                
                # Update the compiled_video reference and output files
                compiled_video = final_video
                output_files['video'] = final_video
                
                logger.info(f"✓ Voiceover added: {final_video.name}")
                
                if status_emitter:
                    status_emitter.emit_status(9, "Adding voiceover", 97, "Voiceover successfully added to video")
            
            # Step 9 or 10: Cleanup
            logger.info("\n" + "-"*40)
            step_num = 10 if voiceover_included else 8
            logger.info(f"STEP {step_num}: Cleanup...")
            
            if status_emitter:
                status_emitter.emit_status(step_num, "Cleanup", 98, "Cleaning up temporary files...")
            
            self.video_processor.cleanup_temp_files([merged_compressed])
            logger.info("✓ Temporary files cleaned")
            
            if status_emitter:
                step_num = 10 if voiceover_included else 8
                status_emitter.emit_status(step_num, "Cleanup", 100, "Processing completed successfully!")
            
            # Calculate total processing time
            processing_time = time.time() - start_time
            
            logger.info("\n" + "="*60)
            logger.info(f"✅ PIPELINE COMPLETE in {processing_time:.1f} seconds!")
            logger.info("="*60)
            
            # Show clear output locations
            logger.info("\n📁 YOUR FILES ARE READY:")
            logger.info("-" * 40)
            logger.info(f"OUTPUT FOLDER: {self.output_dir.absolute()}")
            logger.info("")
            logger.info("  🎬 FINAL VIDEO:")
            logger.info(f"     → {output_files['video'].name}")
            logger.info(f"     Size: {output_files['video'].stat().st_size / (1024*1024):.1f}MB")
            logger.info("")
            logger.info("  📝 SCRIPT (for ElevenLabs):")
            logger.info(f"     → {output_files['script'].name}")
            logger.info("")
            logger.info("  ⏱️  TIMESTAMPS:")
            logger.info(f"     → {output_files['timestamps'].name}")
            logger.info("")
            logger.info("💡 Quick access: open %s", self.output_dir.absolute())
            logger.info("="*60)
            
            # Collect final compilation data for debug
            if debug_collector:
                try:
                    # Get actual final duration
                    final_duration = self.video_processor.get_video_duration(output_files['video'])
                    segment_order = [
                        seg.segment_number if seg.segment_number is not None else i+1 
                        for i, seg in enumerate(timestamps.script_segments)
                    ]
                    
                    # In voiceover mode, expected duration is sum of voiceover segments
                    # Otherwise, use the target duration
                    if voiceover_segments:
                        expected_final_duration = sum(seg['duration'] for seg in voiceover_segments)
                    else:
                        expected_final_duration = target_duration
                    
                    debug_collector.collect_final_compilation(
                        final_video=output_files['video'],
                        expected_duration=expected_final_duration,
                        actual_duration=final_duration,
                        segment_order=segment_order
                    )
                except Exception as debug_error:
                    logger.warning(f"Debug collection error (non-fatal): {debug_error}")
            
            # Return success response
            return ProcessingResponse(
                success=True,
                output_video_path=output_files['video'],
                script_file_path=output_files['script'],
                timestamps_file_path=output_files['timestamps'],
                merged_full_path=merged_full if 'merged_full' in locals() else None,
                gemini_response=timestamps,
                processing_time=processing_time,
                voiceover_included=voiceover_included  # Include voiceover flag
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            
            # Keep merged_full.mp4 for manual processing
            if 'merged_full' in locals():
                logger.info(f"Keeping {merged_full} for manual processing")
            
            # Return error response
            return ProcessingResponse(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def robust_processing(
        self,
        script: str,
        video_files: List[Path],
        target_duration: float = 35.0
    ) -> ProcessingResponse:
        """
        Robust processing with error handling and retries.
        
        Args:
            script: TikTok ad script
            video_files: List of video files
            target_duration: Target duration
            
        Returns:
            ProcessingResponse
        """
        try:
            # First attempt with normal processing
            return self.process(script, video_files, target_duration)
            
        except GeminiAPIError as e:
            logger.warning(f"Gemini API error, trying with extreme compression: {e}")
            
            # Try extreme compression if file too large
            try:
                # Get the compressed file
                merged_compressed = list(self.temp_dir.glob("merged_compressed_*.mp4"))[0]
                
                # Create ultra-compressed version
                ultra_compressed = self.video_pipeline.create_extreme_compression(
                    merged_compressed
                )
                
                # Retry with ultra-compressed
                gemini_input = self.gemini_client.upload_to_gemini(ultra_compressed)
                
                # Continue processing...
                logger.info("Retrying with ultra-compressed video")
                return self.process(script, video_files, target_duration)
                
            except Exception as retry_error:
                logger.error(f"Retry with extreme compression failed: {retry_error}")
                raise
                
        except Exception as e:
            logger.error(f"Robust processing failed: {e}")
            raise


def main():
    """Command-line interface for the pipeline."""
    parser = argparse.ArgumentParser(
        description="TikTok Video Ad Automation Pipeline"
    )
    parser.add_argument(
        '--script',
        type=str,
        help='Path to script file (defaults to input_videos/script.txt)'
    )
    parser.add_argument(
        '--videos',
        type=str,
        help='Directory containing video files (defaults to input_videos/)'
    )
    parser.add_argument(
        '--duration',
        type=float,
        default=35.0,
        help='Target duration in seconds (default: 35)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock Gemini response for testing'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize pipeline
    pipeline = MainPipeline()
    
    # Prepare parameters
    script = None
    if args.script:
        script_path = Path(args.script)
        script = pipeline.load_script(script_path)
    
    video_files = None
    if args.videos:
        video_dir = Path(args.videos)
        video_files = pipeline.get_video_files(video_dir)
    
    # Run pipeline
    try:
        response = pipeline.process(
            script=script,
            video_files=video_files,
            target_duration=args.duration,
            use_mock=args.mock
        )
        
        if response.success:
            print(f"\n✅ Success! Your files are ready:")
            print(f"\n📁 OUTPUT FOLDER: {response.output_video_path.parent}")
            print(f"  🎬 Video: {response.output_video_path.name}")
            print(f"  📝 Script: {response.script_file_path.name}")
            print(f"  ⏱️  Timestamps: {response.timestamps_file_path.name}")
            print(f"\n📊 Stats:")
            print(f"  • Duration: {response.final_duration:.1f}s")
            print(f"  • Processing time: {response.processing_time:.1f}s")
            print(f"\n💡 Tip: Open the output folder with: open {response.output_video_path.parent}")
        else:
            print(f"\n❌ Failed: {response.error_message}")
            
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()