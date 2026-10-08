"""
Video extractor service for extracting segments from video files.
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Any

from .base_service import BaseService
from .video_metadata_service import VideoMetadataService
from utils.exceptions import VideoNotFoundError, FFmpegError, DurationMismatchError
from config.constants import (
    FFMPEG_COMMON_ARGS,
    SEGMENT_DURATION_TOLERANCE,
    VIDEO_TRIM_FILTER_FORMAT,
    AUDIO_TRIM_FILTER_FORMAT
)

try:
    from config.settings import VideoConfig
except ImportError:
    # Fallback configuration
    class VideoConfig:
        PRECISE_MODE_CRF = 18
        PRECISE_MODE_PRESET = "fast"
        LOG_FFMPEG_COMMANDS = False


class VideoExtractorService(BaseService):
    """Service for extracting video segments with precise timing control."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        self.metadata_service = VideoMetadataService(temp_dir)
    
    def extract_segment(
        self,
        input_video: Path,
        output_path: Path,
        start_timestamp: str,
        end_timestamp: str,
        use_copy_codec: bool = True,
        precise_mode: bool = False,
        voiceover_duration: Optional[float] = None,
        segment_number: Optional[int] = None,
        debug_collector: Optional[Any] = None
    ) -> Path:
        """
        Extract a segment from a video file with flexible precision modes.
        
        Args:
            input_video: Input video path
            output_path: Output segment path
            start_timestamp: Start time (HH:MM:SS.mmm)
            end_timestamp: End time (HH:MM:SS.mmm)
            use_copy_codec: Whether to copy codec (no re-encoding)
            precise_mode: Force precise cutting at exact timestamps
            voiceover_duration: Optional exact duration override for voiceover sync
            segment_number: Segment number for debug tracking
            debug_collector: Debug collector for tracking
            
        Returns:
            Path to extracted segment
            
        Raises:
            VideoNotFoundError: If input video doesn't exist
            FFmpegError: If extraction fails
        """
        self.ensure_file_exists(input_video, f"Input video not found: {input_video}")
        
        try:
            # Calculate duration for precise extraction
            start_seconds = self.metadata_service.timestamp_to_seconds(start_timestamp)
            
            # Use voiceover duration if provided, otherwise calculate from timestamps
            if voiceover_duration is not None:
                duration_seconds = voiceover_duration
                self.logger.info(f"Using exact voiceover duration: {duration_seconds:.2f}s")
            else:
                end_seconds = self.metadata_service.timestamp_to_seconds(end_timestamp)
                duration_seconds = end_seconds - start_seconds
            
            # Build FFmpeg command based on mode
            cmd = self._build_extraction_command(
                input_video=input_video,
                output_path=output_path,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                start_seconds=start_seconds,
                duration_seconds=duration_seconds,
                use_copy_codec=use_copy_codec,
                precise_mode=precise_mode,
                voiceover_duration=voiceover_duration
            )
            
            self.logger.debug(f"Extracting segment: {start_timestamp} to {end_timestamp} (duration: {duration_seconds:.3f}s)")
            
            if VideoConfig.LOG_FFMPEG_COMMANDS:
                self.logger.info(f"FFmpeg command: {' '.join(cmd)}")
            
            # Collect debug data - FFmpeg command BEFORE execution
            expected_duration = voiceover_duration if voiceover_duration is not None else duration_seconds
            if debug_collector and segment_number:
                debug_collector.collect_extraction_command(
                    segment_num=segment_number,
                    ffmpeg_command=cmd,
                    source_video=input_video,
                    output_path=output_path,
                    expected_duration=expected_duration,
                    actual_duration=None  # Will be updated after extraction
                )
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.ensure_file_exists(output_path, f"Failed to create segment: {output_path}")
            
            # Always get actual duration for validation and debugging
            actual_duration = self.metadata_service.get_video_duration(output_path)
            
            # Update debug collector with actual duration
            if debug_collector and segment_number:
                debug_collector.collect_extraction_command(
                    segment_num=segment_number,
                    ffmpeg_command=cmd,
                    source_video=input_video,
                    output_path=output_path,
                    expected_duration=expected_duration,
                    actual_duration=actual_duration
                )
            
            # Validate extracted duration if in precise mode
            if precise_mode:
                self._validate_extracted_duration(actual_duration, expected_duration)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg extraction failed: {e.stderr}")
            raise FFmpegError(
                f"Failed to extract segment: {e.stderr}",
                original_error=e
            )
    
    def _build_extraction_command(
        self,
        input_video: Path,
        output_path: Path,
        start_timestamp: str,
        end_timestamp: str,
        start_seconds: float,
        duration_seconds: float,
        use_copy_codec: bool,
        precise_mode: bool,
        voiceover_duration: Optional[float]
    ) -> List[str]:
        """Build FFmpeg command based on extraction mode."""
        
        if voiceover_duration is not None:
            # Force exact duration with re-encoding for frame accuracy (voiceover mode)
            end_time = start_seconds + duration_seconds
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_seconds),  # Fast seek to start position (input seeking)
                '-i', str(input_video),
                '-t', str(duration_seconds),  # Exact duration instead of trim filter
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Optimized for speed while maintaining sync accuracy
                '-crf', '18',
                '-c:a', 'aac',
            ] + FFMPEG_COMMON_ARGS + [str(output_path)]
            self.logger.info(f"Extracting with exact voiceover duration: {duration_seconds:.2f}s")
            
        elif precise_mode:
            # Precise mode: Use trim filter for EXACT frame-accurate cuts
            end_time = start_seconds + duration_seconds
            cmd = [
                'ffmpeg', '-y',
                '-i', str(input_video),
                '-vf', VIDEO_TRIM_FILTER_FORMAT.format(start=start_seconds, end=end_time),
                '-af', AUDIO_TRIM_FILTER_FORMAT.format(start=start_seconds, end=end_time),
                '-c:v', 'libx264',
                '-preset', VideoConfig.PRECISE_MODE_PRESET,
                '-crf', str(VideoConfig.PRECISE_MODE_CRF),
                '-c:a', 'aac',
                '-b:a', '192k',
            ] + FFMPEG_COMMON_ARGS + [str(output_path)]
            self.logger.info(f"Using PRECISE mode for segment extraction: {start_timestamp} to {end_timestamp}")
            
        elif use_copy_codec:
            # Fast mode: Copy codec but less accurate (cuts at keyframes)
            cmd = [
                'ffmpeg', '-y',
                '-i', str(input_video),
                '-ss', start_timestamp,
                '-to', end_timestamp,
                '-c', 'copy',
            ] + FFMPEG_COMMON_ARGS + [str(output_path)]
            self.logger.debug(f"Using COPY mode for segment extraction: {start_timestamp} to {end_timestamp}")
            
        else:
            # Standard re-encoding mode
            cmd = [
                'ffmpeg', '-y',
                '-i', str(input_video),
                '-ss', start_timestamp,
                '-to', end_timestamp,
            ] + FFMPEG_COMMON_ARGS + [str(output_path)]
            self.logger.debug(f"Using STANDARD mode for segment extraction: {start_timestamp} to {end_timestamp}")
        
        return cmd
    
    def _validate_extracted_duration(self, actual_duration: float, expected_duration: float) -> None:
        """Validate that extracted segment has expected duration."""
        tolerance = SEGMENT_DURATION_TOLERANCE
        
        if abs(actual_duration - expected_duration) > tolerance:
            self.logger.warning(
                f"Duration mismatch in extracted segment: "
                f"expected {expected_duration:.3f}s, got {actual_duration:.3f}s "
                f"(tolerance: ±{tolerance}s)"
            )
    
    def concatenate_segments(
        self,
        segment_files: List[Path],
        output_path: Path
    ) -> Path:
        """
        Concatenate video segments with hard cuts (no transitions).
        
        Args:
            segment_files: List of segment file paths
            output_path: Output video path
            
        Returns:
            Path to compiled video
            
        Raises:
            ValueError: If no segments provided
            FFmpegError: If concatenation fails
        """
        if not segment_files:
            raise ValueError("No segment files provided")
        
        # Import merger service to avoid circular dependency
        from .video_merger_service import VideoMergerService
        merger_service = VideoMergerService(self.temp_dir)
        
        return merger_service.concatenate_videos(
            segment_files,
            output_path,
            quality="original"
        )