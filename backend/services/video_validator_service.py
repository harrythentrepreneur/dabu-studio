"""
Video validation service for validating video files and parameters.
"""

from pathlib import Path
from typing import List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_service import BaseService
from .video_metadata_service import VideoMetadataService
from utils.exceptions import VideoSizeError, VideoFormatError, DurationMismatchError
from models.schemas import VideoFile
from config.constants import (
    VIDEO_SIZE_WARNING_MB,
    MIN_TARGET_DURATION,
    MAX_TARGET_DURATION,
    DURATION_MISMATCH_TOLERANCE
)


class VideoValidatorService(BaseService):
    """Service for validating video files and processing parameters."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        self.metadata_service = VideoMetadataService(temp_dir)
    
    def validate_video_files(
        self, 
        video_paths: List[Path],
        max_size_mb: float = VIDEO_SIZE_WARNING_MB,
        required_aspect_ratio: Optional[Tuple[int, int]] = (9, 16)
    ) -> List[VideoFile]:
        """
        Validate multiple video files.
        
        Args:
            video_paths: List of video file paths
            max_size_mb: Maximum file size in MB
            required_aspect_ratio: Required aspect ratio (width, height)
            
        Returns:
            List of validated VideoFile objects
            
        Raises:
            VideoSizeError: If any video exceeds size limit
            VideoFormatError: If aspect ratio doesn't match
        """
        def validate_single_video(video_path: Path) -> VideoFile:
            """Validate a single video file."""
            video_info = self.metadata_service.get_video_info(video_path)
            
            # Check file size
            if video_info.size_mb > max_size_mb:
                raise VideoSizeError(
                    f"Video {video_path.name} exceeds size limit: "
                    f"{video_info.size_mb:.1f}MB > {max_size_mb}MB"
                )
            
            # Check aspect ratio if required
            if required_aspect_ratio:
                width, height = video_info.resolution
                video_ratio = width / height
                required_ratio = required_aspect_ratio[0] / required_aspect_ratio[1]
                
                if abs(video_ratio - required_ratio) > 0.1:  # 10% tolerance
                    self.logger.warning(
                        f"Video {video_path.name} aspect ratio {width}:{height} "
                        f"doesn't match required {required_aspect_ratio}"
                    )
            
            self.logger.info(f"Validated video: {video_path.name}")
            return video_info
        
        # Validate all videos in parallel for faster processing
        validated_videos_dict = {}
        
        with ThreadPoolExecutor(max_workers=min(4, len(video_paths))) as executor:
            # Submit all validation tasks
            future_to_path = {
                executor.submit(validate_single_video, path): path 
                for path in video_paths
            }
            
            # Collect results
            for future in as_completed(future_to_path):
                video_path = future_to_path[future]
                try:
                    video_info = future.result()
                    validated_videos_dict[video_path] = video_info
                except Exception as e:
                    # Re-raise the exception to maintain error handling behavior
                    raise e
        
        # Return videos in original order
        validated_videos = [validated_videos_dict[path] for path in video_paths]
        return validated_videos
    
    def validate_target_duration(self, duration: float) -> bool:
        """
        Validate if target duration is within acceptable bounds.
        
        Args:
            duration: Target duration in seconds
            
        Returns:
            True if duration is valid
            
        Raises:
            ValueError: If duration is outside acceptable range
        """
        if not MIN_TARGET_DURATION <= duration <= MAX_TARGET_DURATION:
            raise ValueError(
                f"Target duration {duration}s is outside acceptable range: "
                f"{MIN_TARGET_DURATION}s - {MAX_TARGET_DURATION}s"
            )
        
        return True
    
    def validate_video_duration(
        self,
        video_path: Path,
        target_duration: float,
        tolerance: float = DURATION_MISMATCH_TOLERANCE
    ) -> bool:
        """
        Validate if video duration matches target within tolerance.
        
        Args:
            video_path: Path to video file
            target_duration: Target duration in seconds
            tolerance: Acceptable tolerance in seconds
            
        Returns:
            True if duration is within tolerance
            
        Raises:
            DurationMismatchError: If duration exceeds tolerance
        """
        actual_duration = self.metadata_service.get_video_duration(video_path)
        difference = abs(actual_duration - target_duration)
        
        if difference > tolerance:
            raise DurationMismatchError(
                f"Duration mismatch: {actual_duration:.1f}s vs target {target_duration}s",
                target_duration=target_duration,
                actual_duration=actual_duration,
                tolerance=tolerance
            )
        
        self.logger.info(
            f"Duration validated: {actual_duration:.1f}s "
            f"(target: {target_duration}s, diff: {difference:.1f}s)"
        )
        return True
    
    def validate_sufficient_video_content(
        self,
        video_paths: List[Path],
        target_duration: float,
        safety_margin: float = 2.0
    ) -> bool:
        """
        Validate that there's sufficient video content for target duration.
        
        Args:
            video_paths: List of video file paths
            target_duration: Target duration in seconds
            safety_margin: Extra margin in seconds
            
        Returns:
            True if sufficient content available
            
        Raises:
            VideoFormatError: If insufficient video content
        """
        total_duration = 0
        for video_path in video_paths:
            duration = self.metadata_service.get_video_duration(video_path)
            total_duration += duration
        
        required_duration = target_duration + safety_margin
        
        if total_duration < required_duration:
            raise VideoFormatError(
                f"Insufficient video content: {total_duration:.1f}s available, "
                f"{required_duration:.1f}s required (including {safety_margin}s margin)"
            )
        
        self.logger.info(
            f"Video content validated: {total_duration:.1f}s available "
            f"for {target_duration:.1f}s target"
        )
        return True