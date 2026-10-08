"""
Video metadata service for extracting and managing video file information.
"""

import cv2
import ffmpeg
from pathlib import Path
from typing import Tuple

from .base_service import BaseService
from utils.exceptions import VideoNotFoundError, VideoFormatError, FFmpegError
from utils.error_handler import handle_service_error, wrap_service_method
from models.schemas import VideoFile
from config.constants import ALLOWED_VIDEO_EXTENSIONS


class VideoMetadataService(BaseService):
    """Service for extracting and managing video metadata."""
    
    @wrap_service_method("VideoMetadataService", "get_video_duration")
    def get_video_duration(self, video_path: Path) -> float:
        """
        Get video duration in seconds using FFprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
            
        Raises:
            VideoNotFoundError: If video file doesn't exist
            FFmpegError: If FFprobe fails
        """
        self.ensure_file_exists(video_path, f"Video file not found: {video_path}")
        
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['streams'][0]['duration'])
            self.logger.debug(f"Video duration for {video_path.name}: {duration}s")
            return duration
        except ffmpeg.Error as e:
            self.logger.error(f"FFprobe error for {video_path}: {e.stderr.decode()}")
            raise FFmpegError(
                f"Failed to get duration for {video_path}",
                original_error=e
            )
        except (KeyError, IndexError):
            # Try alternative method with OpenCV
            return self._get_duration_opencv(video_path)
    
    def _get_duration_opencv(self, video_path: Path) -> float:
        """
        Fallback method to get video duration using OpenCV.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
            
        Raises:
            VideoFormatError: If duration cannot be determined
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            
            if fps > 0 and frame_count > 0:
                duration = frame_count / fps
                self.logger.debug(f"Video duration (OpenCV) for {video_path.name}: {duration}s")
                return duration
            else:
                raise VideoFormatError(f"Cannot determine duration for {video_path}")
        except Exception as e:
            raise VideoFormatError(
                f"Failed to get duration for {video_path}",
                original_error=e
            )
    
    def get_video_info(self, video_path: Path) -> VideoFile:
        """
        Get comprehensive video information.
        
        Args:
            video_path: Path to video file
            
        Returns:
            VideoFile object with video metadata
            
        Raises:
            VideoNotFoundError: If video file doesn't exist
            VideoFormatError: If video format is invalid
        """
        self.ensure_file_exists(video_path, f"Video file not found: {video_path}")
        
        try:
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            
            if not video_stream:
                raise VideoFormatError(f"No video stream found in {video_path}")
            
            duration = float(video_stream.get('duration', 0))
            if duration == 0:
                duration = self.get_video_duration(video_path)
            
            return VideoFile(
                filename=video_path.name,
                path=video_path,
                duration=duration,
                size_mb=self.get_file_size_mb(video_path),
                format=video_path.suffix.lstrip('.'),
                resolution=(
                    int(video_stream['width']),
                    int(video_stream['height'])
                ),
                fps=eval(video_stream.get('r_frame_rate', '30/1'))
            )
        except Exception as e:
            self.logger.error(f"Error getting video info for {video_path}: {e}")
            raise VideoFormatError(
                f"Failed to get video info for {video_path}",
                original_error=e
            )
    
    def is_valid_video_file(self, file_path: Path) -> bool:
        """
        Check if file is a valid video file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if valid video file
        """
        if not file_path.exists():
            return False
        
        # Check extension
        if file_path.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
            return False
        
        try:
            # Try to get basic video info
            self.get_video_info(file_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def seconds_to_timestamp(seconds: float) -> str:
        """
        Convert seconds to timestamp format HH:MM:SS.mmm.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    @staticmethod
    def timestamp_to_seconds(timestamp: str) -> float:
        """
        Convert timestamp format HH:MM:SS.mmm to seconds.
        
        Args:
            timestamp: Timestamp string
            
        Returns:
            Time in seconds
        """
        parts = timestamp.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds