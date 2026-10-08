"""
Main pipeline orchestrator that coordinates all business workflows.
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base_workflow import BaseWorkflow
from .video_processing_workflow import VideoProcessingWorkflow
from .gemini_analysis_workflow import GeminiAnalysisWorkflow
from models.schemas import ProcessingRequest, ProcessingResponse, GeminiResponse
from config.constants import DEFAULT_TARGET_DURATION
from utils.exceptions import VideoProcessingError
from utils.logger import get_logger


class PipelineOrchestrator(BaseWorkflow):
    """
    Main orchestrator that coordinates video processing and AI analysis workflows.
    
    This class implements the complete processing pipeline from PRD section 5,
    coordinating between video processing and Gemini analysis workflows.
    """
    
    def __init__(self, temp_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        
        # Initialize output directory
        self.output_dir = output_dir or Path(__file__).parent.parent / 'output'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize workflows
        self.video_workflow = VideoProcessingWorkflow(self.temp_dir)
        self.gemini_workflow = GeminiAnalysisWorkflow(self.temp_dir)
        
        self._total_steps = 10  # Complete pipeline steps
        
        self.logger.info("PipelineOrchestrator initialized")
    
    def set_status_emitter(self, emitter: Any) -> None:
        """Set status emitter for all workflows."""
        super().set_status_emitter(emitter)
        self.video_workflow.set_status_emitter(emitter)
        self.gemini_workflow.set_status_emitter(emitter)
    
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
            video_files: List of video files
            voiceover_path: Optional voiceover audio file
            target_duration: Target duration in seconds
            use_mock: Use mock Gemini response for testing
            request_id: Unique request identifier
            
        Returns:
            ProcessingResponse with all outputs
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
            merged_full, merged_compressed, video_index = self.video_workflow.prepare_videos_for_analysis(
                video_files, request_id
            )
            
            # Step 2: Analyze with Gemini AI
            gemini_response = self.gemini_workflow.analyze_video_segments(
                compressed_video_path=merged_compressed,
                script=script,
                target_duration=target_duration,
                voiceover_segments=voiceover_segments,
                use_mock=use_mock
            )
            
            # Step 3: Validate analysis results
            self.gemini_workflow.validate_analysis_results(
                gemini_response, target_duration, voiceover_segments
            )
            
            # Collect debug data for Gemini response
            if debug_collector:
                self._collect_gemini_debug_data(gemini_response, voiceover_segments, debug_collector)
            
            # Step 4: Extract and compile segments
            compiled_video = self.video_workflow.extract_and_compile_segments(
                merged_full,
                gemini_response,
                self.output_dir,
                request_id,
                voiceover_segments,
                debug_collector
            )
            
            # Step 5: Export outputs
            output_files = self.video_workflow.export_outputs(
                compiled_video,
                script,
                gemini_response,
                self.output_dir,
                request_id
            )
            
            # Step 6 (Optional): Add voiceover if provided
            if voiceover_included and voiceover_path:
                final_video = self.video_workflow.add_voiceover_to_compiled_video(
                    compiled_video, voiceover_path
                )
                output_files['video'] = final_video
                compiled_video = final_video
                
                self._log_voiceover_sync_info(voiceover_segments, final_video)
            
            # Step 7: Cleanup
            self.video_workflow.cleanup_temporary_files([merged_compressed])
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            self._log_completion_summary(output_files, processing_time)
            
            # Collect final debug data
            if debug_collector:
                self._collect_final_debug_data(
                    output_files, gemini_response, voiceover_segments, 
                    target_duration, debug_collector
                )
            
            # Don't emit completion here - let the caller handle it
            # This allows CapCut processing to continue without disconnecting SSE
            # self.emit_completion(
            #     success=True,
            #     result_data={
            #         'download_urls': self._generate_download_urls(output_files, request_id),
            #         'metadata': self._generate_metadata(gemini_response, processing_time, len(video_files), voiceover_included)
            #     }
            # )
            
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
            
            # Don't emit completion here - let the caller handle it
            # self.emit_completion(
            #     success=False,
            #     error_message=str(e)
            # )
            
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
        
        self.emit_status("Analyzing voiceover", 5, "Processing voiceover with Whisper API...")
        
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
            
            self.emit_status("Analyzing voiceover", 10, f"Voiceover analyzed: {len(voiceover_segments)} segments")
            return voiceover_segments, True
            
        except ImportError as e:
            self.logger.warning(f"Voiceover analyzer not available: {e}")
            self.logger.info("Falling back to STANDARD MODE")
        except Exception as e:
            self.logger.error(f"Voiceover analysis failed: {e}")
            self.logger.info("Falling back to STANDARD MODE")
        
        return None, False
    
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
            from services import VideoMetadataService
            metadata_service = VideoMetadataService(self.temp_dir)
            
            voiceover_total = sum(s['duration'] for s in voiceover_segments)
            video_duration = metadata_service.get_video_duration(final_video)
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
            from services import VideoMetadataService
            metadata_service = VideoMetadataService(self.temp_dir)
            
            final_duration = metadata_service.get_video_duration(output_files['video'])
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
        # This would be filled by the API layer
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

    async def process_async(
        self,
        script: str,
        video_paths: List[str],
        voiceover_path: Optional[str] = None,
        target_duration: float = DEFAULT_TARGET_DURATION,
        request_id: Optional[str] = None,
        processing_mode: str = 'express_builder'
    ) -> Dict[str, Any]:
        """
        Async wrapper for the execute method, adapted for RunPod interface.
        
        Args:
            script: TikTok ad script
            video_paths: List of video file paths (strings)
            voiceover_path: Optional voiceover file path
            target_duration: Target duration in seconds
            request_id: Unique request identifier
            processing_mode: Processing mode (express_builder, quick_create)
            
        Returns:
            Dictionary with processing results compatible with RunPod handler
        """
        try:
            # Convert string paths to Path objects
            video_files = [Path(vp) for vp in video_paths]
            voiceover_file = Path(voiceover_path) if voiceover_path else None
            
            # Execute the pipeline using existing synchronous method
            result = self.execute(
                script=script,
                video_files=video_files,
                voiceover_path=voiceover_file,
                target_duration=target_duration,
                request_id=request_id
            )
            
            if result.success:
                # Convert ProcessingResponse to RunPod-compatible format
                return {
                    'success': True,
                    'video_path': str(result.output_video_path) if result.output_video_path else None,
                    'script_path': str(result.script_file_path) if result.script_file_path else None,
                    'timestamps_path': str(result.timestamps_file_path) if result.timestamps_file_path else None,
                    'segments': result.gemini_response.script_segments if result.gemini_response else [],
                    'capcut_success': True,  # Assuming success if we got here
                    'processing_time': result.processing_time,
                    'processing_mode': processing_mode
                }
            else:
                return {
                    'success': False,
                    'error': result.error_message or 'Processing failed',
                    'processing_time': result.processing_time
                }
                
        except Exception as e:
            self.logger.error(f"Error in process_async: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }