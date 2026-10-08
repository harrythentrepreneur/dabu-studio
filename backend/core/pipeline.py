"""
Main pipeline orchestrator for TikTok Video Ad Automation.

This module coordinates the complete video processing pipeline, handling:
- Video preparation and merging
- AI analysis with Gemini API
- Segment extraction and compilation
- Output generation and cleanup

The pipeline supports both standard mode (AI determines segments) and voiceover mode
(segments based on pre-recorded audio timing).
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from .video_processor import VideoProcessor
from .gemini_client import GeminiClient
from models.schemas import ProcessingRequest, ProcessingResponse, GeminiResponse
from config.constants import DEFAULT_TARGET_DURATION
from utils.exceptions import VideoProcessingError
from utils.logger import get_logger


class Pipeline:
    """
    Main pipeline orchestrator that coordinates video processing and AI analysis.
    
    This class implements the complete processing pipeline, coordinating between 
    video processing operations and Gemini AI analysis to create TikTok ads.
    """
    
    def __init__(self, temp_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize the pipeline with required components.
        
        Args:
            temp_dir: Directory for temporary files
            output_dir: Directory for output files
        """
        # Set up directories
        self.temp_dir = temp_dir or Path(__file__).parent.parent / 'temp'
        self.output_dir = output_dir or Path(__file__).parent.parent / 'output'
        
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.video_processor = VideoProcessor(self.temp_dir)
        self.gemini_client = GeminiClient()
        self.logger = get_logger(__name__)
        
        # Status tracking
        self._status_emitter = None
        self._total_steps = 10
        
        self.logger.info("Pipeline initialized")
    
    def set_status_emitter(self, emitter: Any) -> None:
        """Set status emitter for real-time progress updates."""
        self._status_emitter = emitter
    
    def execute(
        self,
        script: str,
        video_files: List[Path],
        voiceover_path: Optional[Path] = None,
        target_duration: float = DEFAULT_TARGET_DURATION,
        use_mock: bool = False,
        request_id: Optional[str] = None
    ) -> ProcessingResponse:
        """
        Execute the complete processing pipeline.
        
        Args:
            script: TikTok ad script
            video_files: List of video files to process
            voiceover_path: Optional voiceover audio file
            target_duration: Target duration in seconds
            use_mock: Use mock Gemini response for testing
            request_id: Unique request identifier for file naming
            
        Returns:
            ProcessingResponse with success status and output file paths
        """
        start_time = time.time()
        voiceover_segments = None
        voiceover_included = False
        
        # Initialize debug collector if debug mode is enabled
        debug_collector = None
        if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
            from utils.debug_collector import DebugCollector
            debug_collector = DebugCollector(request_id, self.output_dir)
            self.logger.info("Debug mode enabled - collecting detailed diagnostic data")
        
        try:
            # Step 0 (Optional): Analyze voiceover if provided
            if voiceover_path and voiceover_path.exists():
                voiceover_segments, voiceover_included = self._analyze_voiceover(
                    voiceover_path, script, debug_collector
                )
            
            # Step 1: Prepare videos for analysis
            self._emit_status("Merging videos", 15, "Preparing video files for analysis...")
            
            merged_full, merged_compressed, video_index = self._prepare_videos(
                video_files, request_id
            )
            
            # Step 2: Analyze with Gemini AI
            self._emit_status("AI Analysis", 40, "Analyzing video content with Gemini AI...")
            
            gemini_response = self._analyze_with_gemini(
                compressed_video_path=merged_compressed,
                script=script,
                target_duration=target_duration,
                voiceover_segments=voiceover_segments,
                use_mock=use_mock
            )
            
            # Step 3: Validate analysis results
            self._emit_status("Validating results", 55, "Validating AI analysis results...")
            self._validate_analysis_results(gemini_response, target_duration, voiceover_segments)
            
            # Collect debug data for Gemini response
            if debug_collector:
                self._collect_gemini_debug_data(gemini_response, voiceover_segments, debug_collector)
            
            # Step 4: Extract and compile segments
            self._emit_status("Extracting segments", 70, "Extracting video segments...")
            
            compiled_video = self._extract_and_compile_segments(
                merged_full,
                gemini_response,
                self.output_dir,
                request_id,
                voiceover_segments,
                debug_collector
            )
            
            # Step 5: Export outputs
            self._emit_status("Exporting outputs", 85, "Generating final outputs...")
            
            output_files = self._export_outputs(
                compiled_video,
                script,
                gemini_response,
                self.output_dir,
                request_id
            )
            
            # Step 6 (Optional): Add voiceover if provided
            if voiceover_included and voiceover_path:
                self._emit_status("Adding voiceover", 92, "Adding voiceover to final video...")
                
                final_video = self.video_processor.add_voiceover_to_video(
                    compiled_video, voiceover_path, compiled_video.with_name(f"{compiled_video.stem}_with_voiceover.mp4")
                )
                output_files['video'] = final_video
                compiled_video = final_video
                
                self._log_voiceover_sync_info(voiceover_segments, final_video)
            
            # Step 7: Cleanup
            self._emit_status("Cleanup", 98, "Cleaning up temporary files...")
            self.video_processor.cleanup_temp_files([merged_compressed])
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            self._log_completion_summary(output_files, processing_time)
            
            # Collect final debug data
            if debug_collector:
                self._collect_final_debug_data(
                    output_files, gemini_response, voiceover_segments, 
                    target_duration, debug_collector
                )
            
            # Emit completion status
            self._emit_completion(
                success=True,
                result_data={
                    'download_urls': self._generate_download_urls(output_files, request_id),
                    'metadata': self._generate_metadata(gemini_response, processing_time, len(video_files), voiceover_included)
                }
            )
            
            # Return success response
            return ProcessingResponse(
                success=True,
                output_video_path=output_files['video'],
                script_file_path=output_files['script'],
                timestamps_file_path=output_files['timestamps'],
                merged_full_path=merged_full,
                gemini_response=gemini_response,
                processing_time=processing_time,
                voiceover_included=voiceover_included
            )
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            
            # Keep merged_full.mp4 for manual processing if it exists
            if 'merged_full' in locals():
                self.logger.info(f"Keeping {merged_full} for manual processing")
            
            # Emit error completion
            self._emit_completion(
                success=False,
                error_message=str(e)
            )
            
            # Return error response
            return ProcessingResponse(
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _analyze_voiceover(self, voiceover_path: Path, script: str, debug_collector) -> tuple:
        """Analyze voiceover using Whisper API."""
        self.logger.info("="*60)
        self.logger.info("VOICEOVER MODE: Using Whisper for exact timing")
        self.logger.info("="*60)
        
        self._emit_status("Analyzing voiceover", 5, "Processing voiceover with Whisper API...")
        
        try:
            from services.voiceover_analyzer import VoiceoverAnalyzer
            analyzer = VoiceoverAnalyzer()
            voiceover_segments = analyzer.analyze_voiceover(voiceover_path, script)
            
            self.logger.info(f"✓ Voiceover analyzed: {len(voiceover_segments)} segments")
            for i, seg in enumerate(voiceover_segments, 1):
                self.logger.info(
                    f"  Segment {i}: {seg['start']:.2f}s → {seg['end']:.2f}s "
                    f"({seg['duration']:.2f}s)"
                )
            
            # Collect debug data
            if debug_collector:
                from utils.audio import AudioUtils
                audio_utils = AudioUtils()
                voiceover_duration = audio_utils.get_audio_duration(voiceover_path)
                debug_collector.collect_whisper_data(
                    voiceover_path=voiceover_path,
                    voiceover_duration=voiceover_duration,
                    raw_segments=voiceover_segments,
                    processed_segments=voiceover_segments
                )
            
            self._emit_status("Analyzing voiceover", 10, f"Voiceover analyzed: {len(voiceover_segments)} segments")
            return voiceover_segments, True
            
        except ImportError as e:
            self.logger.warning(f"Voiceover analyzer not available: {e}")
            self.logger.info("Falling back to STANDARD MODE")
        except Exception as e:
            self.logger.error(f"Voiceover analysis failed: {e}")
            self.logger.info("Falling back to STANDARD MODE")
        
        return None, False
    
    def _prepare_videos(self, video_files: List[Path], request_id: Optional[str]) -> tuple:
        """Prepare videos for analysis by merging and compressing."""
        # Generate timestamps for output files
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = request_id or f"{timestamp}_{os.getpid()}"
        
        # Create output paths
        merged_full = self.temp_dir / f"merged_full_{session_id}.mp4"
        merged_compressed = self.temp_dir / f"merged_compressed_{session_id}.mp4"
        
        # Merge videos at full quality
        self.logger.info("Creating full-quality merged video...")
        merged_full = self.video_processor.concatenate_videos(
            video_files, merged_full, quality="original"
        )
        
        # Create compressed version for Gemini
        from models.schemas import CompressionSettings
        compression_settings = CompressionSettings()
        
        self.logger.info("Creating compressed version for AI analysis...")
        merged_compressed = self.video_processor.concatenate_videos(
            video_files, merged_compressed, quality="compressed", 
            compression_settings=compression_settings
        )
        
        # Create video index
        video_index = self.video_processor.create_video_index(video_files)
        
        return merged_full, merged_compressed, video_index
    
    def _analyze_with_gemini(
        self, 
        compressed_video_path: Path, 
        script: str, 
        target_duration: float, 
        voiceover_segments: Optional[List[Dict]] = None,
        use_mock: bool = False
    ) -> GeminiResponse:
        """Analyze video with Gemini AI."""
        if use_mock:
            self.logger.info("Using mock Gemini response")
            return self._create_mock_response(script, target_duration, voiceover_segments)
        
        return self.gemini_client.analyze_video_segments(
            video_path=compressed_video_path,
            script=script,
            target_duration=target_duration,
            voiceover_segments=voiceover_segments
        )
    
    def _validate_analysis_results(
        self, 
        gemini_response: GeminiResponse, 
        target_duration: float, 
        voiceover_segments: Optional[List[Dict]]
    ) -> None:
        """Validate Gemini analysis results."""
        if not gemini_response.script_segments:
            raise VideoProcessingError("No segments found in Gemini response")
        
        # Validate segment count for voiceover mode
        if voiceover_segments:
            expected_count = len(voiceover_segments)
            actual_count = len(gemini_response.script_segments)
            if actual_count != expected_count:
                self.logger.warning(
                    f"Segment count mismatch: expected {expected_count}, got {actual_count}"
                )
        
        # Validate total duration
        total_duration = sum(seg.duration_seconds for seg in gemini_response.script_segments)
        if abs(total_duration - target_duration) > 3.0:
            self.logger.warning(
                f"Duration mismatch: target={target_duration}s, actual={total_duration}s"
            )
        
        self.logger.info(f"Analysis validated: {len(gemini_response.script_segments)} segments")
    
    def _extract_and_compile_segments(
        self,
        merged_full: Path,
        gemini_response: GeminiResponse,
        output_dir: Path,
        request_id: str,
        voiceover_segments: Optional[List[Dict]],
        debug_collector
    ) -> Path:
        """Extract segments from full-quality video and compile them."""
        segment_files = []
        
        for i, segment in enumerate(gemini_response.script_segments):
            segment_output = self.temp_dir / f"segment_{i+1:03d}_{request_id}.mp4"
            
            # Extract segment
            extracted_segment = self.video_processor.extract_segment(
                input_video=merged_full,
                output_path=segment_output,
                start_timestamp=segment.start_timestamp,
                end_timestamp=segment.end_timestamp,
                use_copy_codec=True,
                precise_mode=False,
                voiceover_duration=segment.duration_seconds if voiceover_segments else None,
                segment_number=segment.segment_number,
                debug_collector=debug_collector
            )
            
            segment_files.append(extracted_segment)
        
        # Compile segments into final video
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        compiled_output = output_dir / f"compiled_video_{request_id or timestamp}.mp4"
        
        compiled_video = self.video_processor.concatenate_with_hard_cuts(
            segment_files, compiled_output
        )
        
        # Clean up temporary segment files
        self.video_processor.cleanup_temp_files(segment_files)
        
        return compiled_video
    
    def _export_outputs(
        self,
        compiled_video: Path,
        script: str,
        gemini_response: GeminiResponse,
        output_dir: Path,
        request_id: str
    ) -> Dict[str, Path]:
        """Export final outputs (script file and timestamps JSON)."""
        from datetime import datetime
        import json
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = request_id or timestamp
        
        # Export script file
        script_file = output_dir / f"script_{base_name}.txt"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script)
        
        # Export timestamps JSON
        timestamps_file = output_dir / f"timestamps_{base_name}.json"
        timestamps_data = {
            'script_segments': [
                {
                    'segment_number': seg.segment_number,
                    'segment_text': seg.segment_text,
                    'start_timestamp': seg.start_timestamp,
                    'end_timestamp': seg.end_timestamp,
                    'duration_seconds': seg.duration_seconds,
                    'confidence': seg.confidence,
                    'visual_description': seg.visual_description
                }
                for seg in gemini_response.script_segments
            ],
            'total_duration': gemini_response.total_duration,
            'target_duration': gemini_response.target_duration,
            'generated_at': datetime.now().isoformat()
        }
        
        with open(timestamps_file, 'w', encoding='utf-8') as f:
            json.dump(timestamps_data, f, indent=2, ensure_ascii=False)
        
        return {
            'video': compiled_video,
            'script': script_file,
            'timestamps': timestamps_file
        }
    
    def _create_mock_response(
        self, 
        script: str, 
        target_duration: float, 
        voiceover_segments: Optional[List[Dict]]
    ) -> GeminiResponse:
        """Create mock Gemini response for testing."""
        from models.schemas import ScriptSegment
        
        if voiceover_segments:
            # Use voiceover segments
            segments = []
            for i, vseg in enumerate(voiceover_segments):
                segments.append(ScriptSegment(
                    segment_number=i + 1,
                    segment_text=vseg['text'],
                    start_timestamp="00:00:05.000",  # Mock timestamps
                    end_timestamp=f"00:00:{5 + vseg['duration']:06.3f}",
                    duration_seconds=vseg['duration'],
                    confidence=0.8,
                    visual_description=f"Mock visual for segment {i + 1}"
                ))
        else:
            # Create standard segments
            num_segments = max(3, min(8, int(target_duration / 5)))
            segment_duration = target_duration / num_segments
            
            segments = []
            for i in range(num_segments):
                start_sec = i * segment_duration
                end_sec = (i + 1) * segment_duration
                
                segments.append(ScriptSegment(
                    segment_number=i + 1,
                    segment_text=f"Mock segment {i + 1} text",
                    start_timestamp=f"00:00:{start_sec:06.3f}",
                    end_timestamp=f"00:00:{end_sec:06.3f}",
                    duration_seconds=segment_duration,
                    confidence=0.8,
                    visual_description=f"Mock visual for segment {i + 1}"
                ))
        
        return GeminiResponse(
            script_segments=segments,
            total_duration=target_duration,
            target_duration=target_duration
        )
    
    def _emit_status(self, step_name: str, progress: int, message: str):
        """Emit status update if status emitter is available."""
        if self._status_emitter:
            self._status_emitter.emit_status(step_name, progress, message)
    
    def _emit_completion(self, success: bool, result_data: Optional[Dict] = None, error_message: Optional[str] = None):
        """Emit completion status."""
        if self._status_emitter:
            self._status_emitter.emit_complete(success, result_data, error_message)
    
    def _collect_gemini_debug_data(self, gemini_response, voiceover_segments, debug_collector):
        """Collect Gemini response debug data."""
        try:
            gemini_dict = {
                'total_duration': gemini_response.total_duration,
                'target_duration': gemini_response.target_duration,
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
                    for i, seg in enumerate(gemini_response.script_segments)
                ]
            }
            debug_collector.collect_gemini_response(gemini_dict, voiceover_segments)
        except Exception as debug_error:
            self.logger.warning(f"Debug collection error (non-fatal): {debug_error}")
    
    def _log_voiceover_sync_info(self, voiceover_segments, final_video):
        """Log voiceover synchronization information."""
        if voiceover_segments:
            voiceover_total = sum(s['duration'] for s in voiceover_segments)
            video_duration = self.video_processor.get_video_duration(final_video)
            difference = abs(video_duration - voiceover_total)
            
            if difference > 5.0:
                self.logger.warning(
                    f"Duration difference: video={video_duration:.2f}s, "
                    f"voiceover={voiceover_total:.2f}s (difference: {difference:.2f}s)"
                )
            else:
                self.logger.info(
                    f"✓ Sync validated: video={video_duration:.2f}s, "
                    f"voiceover={voiceover_total:.2f}s (difference: {difference:.2f}s)"
                )
    
    def _log_completion_summary(self, output_files, processing_time):
        """Log completion summary with file locations."""
        self.logger.info("\n" + "="*60)
        self.logger.info(f"✅ PIPELINE COMPLETE in {processing_time:.1f} seconds!")
        self.logger.info("="*60)
        
        self.logger.info("\n📁 YOUR FILES ARE READY:")
        self.logger.info("-" * 40)
        self.logger.info(f"OUTPUT FOLDER: {self.output_dir.absolute()}")
        self.logger.info("")
        self.logger.info("  🎬 FINAL VIDEO:")
        self.logger.info(f"     → {output_files['video'].name}")
        self.logger.info(f"     Size: {output_files['video'].stat().st_size / (1024*1024):.1f}MB")
        self.logger.info("")
        self.logger.info("  📝 SCRIPT (for ElevenLabs):")
        self.logger.info(f"     → {output_files['script'].name}")
        self.logger.info("")
        self.logger.info("  ⏱️  TIMESTAMPS:")
        self.logger.info(f"     → {output_files['timestamps'].name}")
        self.logger.info("")
        self.logger.info("💡 Quick access: open %s", self.output_dir.absolute())
        self.logger.info("="*60)
    
    def _collect_final_debug_data(self, output_files, gemini_response, voiceover_segments, target_duration, debug_collector):
        """Collect final compilation debug data."""
        try:
            final_duration = self.video_processor.get_video_duration(output_files['video'])
            segment_order = [
                seg.segment_number if seg.segment_number is not None else i+1 
                for i, seg in enumerate(gemini_response.script_segments)
            ]
            
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
            self.logger.warning(f"Debug collection error (non-fatal): {debug_error}")
    
    def _generate_download_urls(self, output_files, request_id):
        """Generate download URLs for API response."""
        return {
            'video': f"/api/download/{request_id}/video",
            'script': f"/api/download/{request_id}/script", 
            'timestamps': f"/api/download/{request_id}/timestamps"
        }
    
    def _generate_metadata(self, gemini_response, processing_time, input_video_count, voiceover_included):
        """Generate metadata for API response."""
        from datetime import datetime, timezone
        
        return {
            'total_duration': gemini_response.total_duration if gemini_response else None,
            'segments_count': len(gemini_response.script_segments) if gemini_response else 0,
            'processing_time': processing_time,
            'input_videos_count': input_video_count,
            'voiceover_included': voiceover_included,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }