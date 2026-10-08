"""
Video processing workflow for handling video preparation and compilation.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_workflow import BaseWorkflow
from services import (
    VideoMetadataService,
    VideoValidatorService,
    VideoMergerService,
    VideoExtractorService,
    VoiceoverService,
    FileCleanupService
)
from models.schemas import GeminiResponse, VideoFile, VideoIndexCollection
from config.constants import DEFAULT_TARGET_DURATION, STATUS_MESSAGES, PROCESSING_STEPS
from config.constants import VideoConfig
from utils.exceptions import VideoProcessingError


class VideoProcessingWorkflow(BaseWorkflow):
    """Workflow for video processing operations."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        
        # Initialize services
        self.metadata_service = VideoMetadataService(self.temp_dir)
        self.validator_service = VideoValidatorService(self.temp_dir)
        self.merger_service = VideoMergerService(self.temp_dir)
        self.extractor_service = VideoExtractorService(self.temp_dir)
        self.voiceover_service = VoiceoverService(self.temp_dir)
        self.cleanup_service = FileCleanupService(self.temp_dir)
        
        self._total_steps = 8  # Standard workflow steps
    
    def prepare_videos_for_analysis(
        self,
        video_files: List[Path],
        request_id: Optional[str] = None
    ) -> Tuple[Path, Path, VideoIndexCollection]:
        """
        Prepare videos for Gemini analysis by creating full and compressed versions.
        
        Args:
            video_files: List of video file paths
            request_id: Unique request identifier for file naming
            
        Returns:
            Tuple of (merged_full_path, merged_compressed_path, video_index)
        """
        self._current_step = PROCESSING_STEPS['MERGING_VIDEOS']
        self.emit_status(
            "Merging videos",
            25,
            STATUS_MESSAGES['MERGING_VIDEOS']
        )
        
        try:
            # Validate video files first
            validated_videos = self.validator_service.validate_video_files(video_files)
            self.logger.info(f"Validated {len(validated_videos)} video files")
            
            # Create video index for tracking
            video_index = self.merger_service.create_video_index(video_files)
            
            # Generate unique file names
            timestamp_suffix = request_id or "merged"
            merged_full_name = f"merged_full_{timestamp_suffix}.mp4"
            merged_compressed_name = f"merged_compressed_{timestamp_suffix}.mp4"
            
            merged_full_path = self.temp_dir / merged_full_name
            merged_compressed_path = self.temp_dir / merged_compressed_name
            
            # OPTIMIZED: First merge at full quality (fast copy), then compress from that
            self.logger.info("Creating merged video with optimized two-stage process...")
            
            # Stage 1: Fast merge at full quality (uses -c copy, no re-encoding)
            self.logger.info("Stage 1: Fast concatenation at full quality...")
            merged_full = self.merger_service.concatenate_videos(
                video_files,
                merged_full_path,
                quality="original"
            )
            
            self.emit_status(
                "Merging videos",
                30,
                "Full quality merge complete, compressing for AI analysis..."
            )
            
            # Stage 2: Compress from the merged full video (single source = much faster)
            self.logger.info("Stage 2: Compressing merged video for AI analysis...")
            from models.schemas import CompressionSettings
            compression_settings = CompressionSettings()
            
            # Use the full merged video as source for compression
            merged_compressed = self.merger_service.compress_video(
                merged_full_path,
                merged_compressed_path,
                compression_settings
            )
            
            # IMPORTANT: Clean up old temp files to prevent disk space issues
            self._cleanup_old_temp_files()
            
            # Update video index with actual merged file paths
            video_index.merged_file_path = merged_full_path
            
            self.emit_status(
                "Merging videos",
                40,
                f"Videos merged successfully: {self.metadata_service.get_file_size_mb(merged_full):.1f}MB full, {self.metadata_service.get_file_size_mb(merged_compressed):.1f}MB compressed"
            )
            
            return merged_full, merged_compressed, video_index
            
        except Exception as e:
            self.logger.error(f"Failed to prepare videos: {e}")
            raise VideoProcessingError(f"Video preparation failed: {e}")
    
    def extract_and_compile_segments(
        self,
        merged_video_path: Path,
        gemini_response: GeminiResponse,
        output_dir: Path,
        request_id: Optional[str] = None,
        voiceover_segments: Optional[List[Dict]] = None,
        debug_collector: Optional[Any] = None
    ) -> Path:
        """
        Extract segments from merged video and compile final output.
        
        Args:
            merged_video_path: Path to merged full-quality video
            gemini_response: Gemini analysis results with timestamps
            output_dir: Directory for output files
            request_id: Unique request identifier
            voiceover_segments: Optional voiceover timing data
            debug_collector: Optional debug data collector
            
        Returns:
            Path to compiled final video
        """
        self._current_step = PROCESSING_STEPS['EXTRACTING_SEGMENTS']
        self.emit_status(
            "Extracting segments",
            82,
            STATUS_MESSAGES['EXTRACTING_SEGMENTS']
        )
        
        try:
            segment_files = []
            temp_segments = []
            
            # Prepare extraction tasks
            extraction_tasks = []
            for i, segment in enumerate(gemini_response.script_segments, 1):
                segment_name = f"segment_{i:03d}.mp4"
                segment_path = self.temp_dir / segment_name
                temp_segments.append(segment_path)
                
                # Determine if we need voiceover-precise duration
                voiceover_duration = None
                if voiceover_segments and i <= len(voiceover_segments):
                    voiceover_duration = voiceover_segments[i-1]['duration']
                
                # Prepare extraction task
                task = {
                    'index': i,
                    'segment': segment,
                    'segment_path': segment_path,
                    'voiceover_duration': voiceover_duration
                }
                extraction_tasks.append(task)
            
            # Extract segments in parallel
            # Use fewer workers to avoid system overload during re-encoding
            import os
            max_workers = min(VideoConfig.PARALLEL_EXTRACTION_WORKERS, os.cpu_count() or 4, len(extraction_tasks))
            self.logger.info(f"Extracting {len(extraction_tasks)} segments in parallel (using {max_workers} workers)...")
            
            def extract_single_segment(task):
                """Helper function to extract a single segment."""
                i = task['index']
                segment = task['segment']
                segment_path = task['segment_path']
                voiceover_duration = task['voiceover_duration']
                
                extracted_segment = self.extractor_service.extract_segment(
                    input_video=merged_video_path,
                    output_path=segment_path,
                    start_timestamp=segment.start_timestamp,
                    end_timestamp=segment.end_timestamp,
                    use_copy_codec=False if voiceover_duration else True,
                    precise_mode=True if voiceover_duration else False,
                    voiceover_duration=voiceover_duration,
                    segment_number=i,
                    debug_collector=debug_collector
                )
                
                self.logger.debug(f"Extracted segment {i}: {segment_path.name}")
                return i, extracted_segment
            
            # Use ThreadPoolExecutor for parallel extraction
            extracted_segments_dict = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all extraction tasks
                future_to_task = {
                    executor.submit(extract_single_segment, task): task 
                    for task in extraction_tasks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        index, extracted_path = future.result()
                        extracted_segments_dict[index] = extracted_path
                        
                        # Update progress
                        progress = 82 + int((len(extracted_segments_dict) / len(extraction_tasks)) * 8)
                        self.emit_status(
                            "Extracting segments",
                            progress,
                            f"Extracted {len(extracted_segments_dict)}/{len(extraction_tasks)} segments"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to extract segment {task['index']}: {e}")
                        raise VideoProcessingError(f"Segment {task['index']} extraction failed: {e}")
            
            # Sort segments by index to maintain order
            for i in sorted(extracted_segments_dict.keys()):
                segment_files.append(extracted_segments_dict[i])
            
            # Compile segments into final video
            timestamp_suffix = request_id or "compiled"
            compiled_name = f"compiled_video_{timestamp_suffix}.mp4"
            compiled_path = output_dir / compiled_name
            
            self.logger.info("Compiling final video from segments...")
            final_video = self.extractor_service.concatenate_segments(
                segment_files,
                compiled_path
            )
            
            # Clean up temporary segment files
            self.cleanup_service.cleanup_temp_files(temp_segments)
            
            # NOTE: Keep merged_full video for frontend download option
            # The cleanup method will remove old ones after 1 hour
            
            self.emit_status(
                "Extracting segments",
                90,
                "Video segments extracted and compiled successfully"
            )
            
            return final_video
            
        except Exception as e:
            self.logger.error(f"Failed to extract and compile segments: {e}")
            raise VideoProcessingError(f"Segment extraction failed: {e}")
    
    def _cleanup_old_temp_files(self):
        """Clean up old temp files to prevent disk space issues."""
        try:
            import time
            from pathlib import Path
            
            # Get current time
            current_time = time.time()
            
            # Clean up merged files older than 1 hour
            for pattern in ['merged_full_*.mp4', 'merged_compressed_*.mp4']:
                for file_path in self.temp_dir.glob(pattern):
                    try:
                        # Check file age
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > 3600:  # 1 hour in seconds
                            file_path.unlink()
                            self.logger.debug(f"Cleaned up old temp file: {file_path.name}")
                    except Exception as e:
                        self.logger.warning(f"Could not clean up {file_path}: {e}")
            
            # Also clean up segment files
            for pattern in ['segment_*.mp4', 'temp_segment_*.mp4']:
                for file_path in self.temp_dir.glob(pattern):
                    try:
                        file_path.unlink()
                        self.logger.debug(f"Cleaned up segment file: {file_path.name}")
                    except Exception:
                        pass
                        
        except Exception as e:
            self.logger.warning(f"Cleanup failed (non-critical): {e}")
    
    def add_voiceover_to_compiled_video(
        self,
        compiled_video_path: Path,
        voiceover_path: Path
    ) -> Path:
        """
        Add voiceover audio to compiled video.
        
        Args:
            compiled_video_path: Path to compiled video
            voiceover_path: Path to voiceover audio
            
        Returns:
            Path to video with voiceover
        """
        self._current_step = PROCESSING_STEPS['ADDING_VOICEOVER']
        self.emit_status(
            "Adding voiceover",
            96,
            STATUS_MESSAGES['ADDING_VOICEOVER']
        )
        
        try:
            output_path = compiled_video_path.parent / f"{compiled_video_path.stem}_with_voiceover.mp4"
            
            final_video = self.voiceover_service.add_voiceover_to_video(
                compiled_video_path,
                voiceover_path,
                output_path
            )
            
            self.emit_status(
                "Adding voiceover",
                97,
                "Voiceover successfully added to video"
            )
            
            return final_video
            
        except Exception as e:
            self.logger.error(f"Failed to add voiceover: {e}")
            raise VideoProcessingError(f"Voiceover addition failed: {e}")
    
    def export_outputs(
        self,
        compiled_video: Path,
        script: str,
        gemini_response: GeminiResponse,
        output_dir: Path,
        request_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export all final outputs (video, script, timestamps).
        
        Args:
            compiled_video: Path to compiled video
            script: Original script text
            gemini_response: Gemini analysis results
            output_dir: Output directory
            request_id: Unique request identifier
            
        Returns:
            Dictionary mapping output types to file paths
        """
        self._current_step = PROCESSING_STEPS['EXPORTING_OUTPUTS']
        self.emit_status(
            "Exporting outputs",
            92,
            STATUS_MESSAGES['EXPORTING_OUTPUTS']
        )
        
        try:
            timestamp_suffix = request_id or "output"
            
            # Video is already in the right location
            video_path = compiled_video
            
            # Export script file
            script_path = output_dir / f"script_raw_{timestamp_suffix}.txt"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script)
            
            # Export timestamps JSON
            timestamps_path = output_dir / f"timestamps_{timestamp_suffix}.json"
            import json
            with open(timestamps_path, 'w', encoding='utf-8') as f:
                # Use model_dump() for Pydantic v2, fallback to dict() for v1
                if hasattr(gemini_response, 'model_dump'):
                    json.dump(gemini_response.model_dump(), f, indent=2, default=str)
                else:
                    json.dump(gemini_response.dict(), f, indent=2, default=str)
            
            outputs = {
                'video': video_path,
                'script': script_path,
                'timestamps': timestamps_path
            }
            
            self.emit_status(
                "Exporting outputs",
                95,
                "All outputs exported successfully"
            )
            
            return outputs
            
        except Exception as e:
            self.logger.error(f"Failed to export outputs: {e}")
            raise VideoProcessingError(f"Output export failed: {e}")
    
    def cleanup_temporary_files(self, files_to_clean: List[Path]) -> None:
        """Clean up temporary files."""
        self._current_step = PROCESSING_STEPS['CLEANUP']
        self.emit_status(
            "Cleanup",
            98,
            STATUS_MESSAGES['CLEANUP']
        )
        
        self.cleanup_service.cleanup_temp_files(files_to_clean)
        
        self.emit_status(
            "Cleanup",
            100,
            "Processing completed successfully!"
        )
    
    def execute(self, *args, **kwargs):
        """Execute workflow - implemented by specific workflow methods."""
        raise NotImplementedError("Use specific workflow methods like prepare_videos_for_analysis")