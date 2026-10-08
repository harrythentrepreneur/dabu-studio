"""
Video processing module for TikTok Video Ad Automation.

This module handles all video operations including merging, compression,
extraction, and compilation using FFmpeg.
"""

import os
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import ffmpeg
import cv2
import numpy as np
from tqdm import tqdm

from utils.logger import get_logger, LogContext
from utils.exceptions import (
    VideoProcessingError,
    VideoNotFoundError,
    VideoFormatError,
    VideoSizeError,
    FFmpegError,
    DurationMismatchError
)
from models.schemas import (
    VideoFile,
    VideoIndex,
    VideoIndexCollection,
    CompressionSettings,
    VideoMetadata
)

# Only import config if available, otherwise use defaults
try:
    from config.settings import VideoConfig
except ImportError:
    class VideoConfig:
        PRECISE_MODE_CRF = 18
        PRECISE_MODE_PRESET = "fast"
        KEYFRAME_INTERVAL = 30
        SEGMENT_DURATION_TOLERANCE = 0.5
        LOG_FFMPEG_COMMANDS = False

logger = get_logger(__name__)


class VideoProcessor:
    """Main class for video processing operations."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        """
        Initialize VideoProcessor.
        
        Args:
            temp_dir: Directory for temporary files (defaults to backend/temp)
        """
        self.temp_dir = temp_dir or Path(__file__).parent / 'temp'
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean up old temporary files on initialization
        try:
            self._cleanup_old_temp_files()
        except Exception as e:
            logger.warning(f"Failed to clean old temp files: {e}")
        
        logger.info(f"VideoProcessor initialized with temp_dir: {self.temp_dir}")
    
    # ==================== Helper Functions ====================
    
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
    
    @staticmethod
    def get_file_size(file_path: Path) -> float:
        """
        Get file size in MB.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in megabytes
        """
        if not file_path.exists():
            raise VideoNotFoundError(f"File not found: {file_path}")
        return file_path.stat().st_size / (1024 * 1024)
    
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
        if not video_path.exists():
            raise VideoNotFoundError(f"Video file not found: {video_path}")
        
        try:
            probe = ffmpeg.probe(str(video_path))
            duration = float(probe['streams'][0]['duration'])
            logger.debug(f"Video duration for {video_path.name}: {duration}s")
            return duration
        except ffmpeg.Error as e:
            logger.error(f"FFprobe error for {video_path}: {e.stderr.decode()}")
            raise FFmpegError(
                f"Failed to get duration for {video_path}",
                original_error=e
            )
        except (KeyError, IndexError) as e:
            # Try alternative method with OpenCV
            return self._get_duration_opencv(video_path)
    
    def _get_duration_opencv(self, video_path: Path) -> float:
        """
        Fallback method to get video duration using OpenCV.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        try:
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()
            
            if fps > 0 and frame_count > 0:
                duration = frame_count / fps
                logger.debug(f"Video duration (OpenCV) for {video_path.name}: {duration}s")
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
        """
        if not video_path.exists():
            raise VideoNotFoundError(f"Video file not found: {video_path}")
        
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
                size_mb=self.get_file_size(video_path),
                format=video_path.suffix.lstrip('.'),
                resolution=(
                    int(video_stream['width']),
                    int(video_stream['height'])
                ),
                fps=eval(video_stream.get('r_frame_rate', '30/1'))
            )
        except Exception as e:
            logger.error(f"Error getting video info for {video_path}: {e}")
            raise VideoProcessingError(
                f"Failed to get video info for {video_path}",
                original_error=e
            )
    
    def validate_video_files(
        self, 
        video_paths: List[Path],
        max_size_mb: float = 500,
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
        validated_videos = []
        
        for video_path in video_paths:
            with LogContext(logger, video=str(video_path)):
                video_info = self.get_video_info(video_path)
                
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
                        logger.warning(
                            f"Video {video_path.name} aspect ratio {width}:{height} "
                            f"doesn't match required {required_aspect_ratio}"
                        )
                
                validated_videos.append(video_info)
                logger.info(f"Validated video: {video_path.name}")
        
        return validated_videos
    
    # ==================== Video Merging ====================
    
    def concatenate_videos(
        self,
        video_files: List[Path],
        output_path: Path,
        quality: str = "original",
        compression_settings: Optional[CompressionSettings] = None
    ) -> Path:
        """
        Concatenate multiple video files into one.
        
        Args:
            video_files: List of video file paths
            output_path: Output file path
            quality: "original" or "compressed"
            compression_settings: Compression settings if quality is "compressed"
            
        Returns:
            Path to output video file
        """
        if not video_files:
            raise ValueError("No video files provided")
        
        # Create temporary file list for FFmpeg concat
        list_file = self.temp_dir / f"concat_{os.getpid()}.txt"
        
        try:
            # Write file list for concat
            with open(list_file, 'w') as f:
                for video_path in video_files:
                    if not video_path.exists():
                        raise VideoNotFoundError(f"Video not found: {video_path}")
                    # Use absolute path and escape special characters
                    escaped_path = str(video_path.absolute()).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            logger.info(f"Concatenating {len(video_files)} videos to {output_path}")
            
            if quality == "original":
                # Concatenate WITHOUT re-encoding for SPEED
                # We'll handle precision during segment extraction instead
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(list_file),
                    '-c', 'copy',  # Just copy, don't re-encode (FAST!)
                    '-movflags', '+faststart',
                    str(output_path)
                ]
                logger.info("Fast concatenation using copy codec (no re-encoding)")
            else:
                # Concatenate with compression
                if not compression_settings:
                    compression_settings = CompressionSettings()
                
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', str(list_file)
                ] + compression_settings.to_ffmpeg_args() + [
                    '-movflags', '+faststart',
                    str(output_path)
                ]
            
            # Run FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path.exists():
                raise FFmpegError(f"Failed to create output file: {output_path}")
            
            output_size = self.get_file_size(output_path)
            logger.info(
                f"Successfully concatenated videos. "
                f"Output: {output_path.name} ({output_size:.1f}MB)"
            )
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg concatenation failed: {e.stderr}")
            raise FFmpegError(
                f"Failed to concatenate videos: {e.stderr}",
                original_error=e
            )
        finally:
            # Clean up temporary file
            if list_file.exists():
                list_file.unlink()
    
    def create_video_index(self, video_files: List[Path]) -> VideoIndexCollection:
        """
        Create an index tracking video boundaries in merged file.
        
        Args:
            video_files: List of video file paths
            
        Returns:
            VideoIndexCollection with boundary information
        """
        indices = []
        current_time = 0.0
        total_duration = 0.0
        
        for video_path in video_files:
            duration = self.get_video_duration(video_path)
            
            index = VideoIndex(
                filename=video_path.name,
                start_in_merged=self.seconds_to_timestamp(current_time),
                end_in_merged=self.seconds_to_timestamp(current_time + duration),
                duration=duration
            )
            
            indices.append(index)
            current_time += duration
            total_duration += duration
        
        logger.info(f"Created video index for {len(video_files)} files, total duration: {total_duration:.1f}s")
        
        return VideoIndexCollection(
            videos=indices,
            total_duration=total_duration,
            merged_file_path=Path("merged.mp4")  # Will be updated later
        )
    
    # ==================== Video Extraction ====================
    
    def extract_segment(
        self,
        input_video: Path,
        output_path: Path,
        start_timestamp: str,
        end_timestamp: str,
        use_copy_codec: bool = True,
        precise_mode: bool = False,
        voiceover_duration: Optional[float] = None,  # NEW parameter
        segment_number: Optional[int] = None,  # For debug tracking
        debug_collector: Optional[Any] = None  # Debug collector
    ) -> Path:
        """
        Extract a segment from a video file.
        
        Args:
            input_video: Input video path
            output_path: Output segment path
            start_timestamp: Start time (HH:MM:SS.mmm)
            end_timestamp: End time (HH:MM:SS.mmm)
            use_copy_codec: Whether to copy codec (no re-encoding)
            precise_mode: Force precise cutting at exact timestamps (overrides use_copy_codec)
            voiceover_duration: Optional exact duration override for voiceover sync
            
        Returns:
            Path to extracted segment
        """
        if not input_video.exists():
            raise VideoNotFoundError(f"Input video not found: {input_video}")
        
        try:
            # Calculate duration for precise extraction
            start_seconds = self.timestamp_to_seconds(start_timestamp)
            
            # Use voiceover duration if provided, otherwise calculate from timestamps
            if voiceover_duration is not None:
                # Force exact duration from voiceover
                duration_seconds = voiceover_duration
                logger.info(f"Using exact voiceover duration: {duration_seconds:.2f}s")
            else:
                end_seconds = self.timestamp_to_seconds(end_timestamp)
                duration_seconds = end_seconds - start_seconds
            
            # Build FFmpeg command based on mode
            if voiceover_duration is not None:
                # Force exact duration with re-encoding for frame accuracy (voiceover mode)
                # Using trim filter for EXACT frame-accurate duration control
                end_time = start_seconds + duration_seconds
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(input_video),  # Input file
                    '-vf', f'trim=start={start_seconds}:end={end_time},setpts=PTS-STARTPTS',  # Exact trim
                    '-af', f'atrim=start={start_seconds}:end={end_time},asetpts=PTS-STARTPTS',  # Audio trim
                    '-c:v', 'libx264',  # Re-encode for frame accuracy
                    '-preset', 'faster',  # Fast encoding
                    '-crf', '18',  # High quality
                    '-c:a', 'aac',  # Standard audio codec
                    '-avoid_negative_ts', 'make_zero',
                    str(output_path)
                ]
                logger.info(f"Extracting with exact voiceover duration: {duration_seconds:.2f}s")
            elif precise_mode:
                # Precise mode: Use trim filter for EXACT frame-accurate cuts
                # This guarantees exact duration output
                end_time = start_seconds + duration_seconds
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(input_video),  # Input file
                    '-vf', f'trim=start={start_seconds}:end={end_time},setpts=PTS-STARTPTS',  # Exact trim
                    '-af', f'atrim=start={start_seconds}:end={end_time},asetpts=PTS-STARTPTS',  # Audio trim
                    '-c:v', 'libx264',  # Re-encode video for precise cutting
                    '-preset', VideoConfig.PRECISE_MODE_PRESET,  # Use config value
                    '-crf', str(VideoConfig.PRECISE_MODE_CRF),  # Use config value
                    '-c:a', 'aac',  # Re-encode audio
                    '-b:a', '192k',  # Good audio quality
                    '-avoid_negative_ts', 'make_zero',
                    '-movflags', '+faststart',
                    str(output_path)
                ]
                logger.info(f"Using PRECISE mode for segment extraction: {start_timestamp} to {end_timestamp}")
            elif use_copy_codec:
                # Fast mode: Copy codec but less accurate (cuts at keyframes)
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(input_video),
                    '-ss', start_timestamp,
                    '-to', end_timestamp,
                    '-c', 'copy',
                    '-avoid_negative_ts', 'make_zero',
                    '-movflags', '+faststart',
                    str(output_path)
                ]
                logger.debug(f"Using COPY mode for segment extraction: {start_timestamp} to {end_timestamp}")
            else:
                # Standard re-encoding mode
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(input_video),
                    '-ss', start_timestamp,
                    '-to', end_timestamp,
                    '-avoid_negative_ts', 'make_zero',
                    '-movflags', '+faststart',
                    str(output_path)
                ]
                logger.debug(f"Using STANDARD mode for segment extraction: {start_timestamp} to {end_timestamp}")
            
            logger.debug(f"Extracting segment: {start_timestamp} to {end_timestamp} (duration: {duration_seconds:.3f}s)")
            
            if VideoConfig.LOG_FFMPEG_COMMANDS:
                logger.info(f"FFmpeg command: {' '.join(cmd)}")
            
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
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path.exists():
                raise FFmpegError(f"Failed to create segment: {output_path}")
            
            # Always get actual duration for validation and debugging
            actual_duration = self.get_video_duration(output_path)
            
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
                tolerance = VideoConfig.SEGMENT_DURATION_TOLERANCE
                
                if abs(actual_duration - expected_duration) > tolerance:
                    logger.warning(
                        f"Duration mismatch in extracted segment: "
                        f"expected {expected_duration:.3f}s, got {actual_duration:.3f}s "
                        f"(tolerance: ±{tolerance}s)"
                    )
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg extraction failed: {e.stderr}")
            raise FFmpegError(
                f"Failed to extract segment: {e.stderr}",
                original_error=e
            )
    
    def concatenate_with_hard_cuts(
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
        """
        return self.concatenate_videos(
            segment_files,
            output_path,
            quality="original"
        )
    
    
    def validate_and_adjust_duration(
        self,
        video_path: Path,
        target_duration: float,
        tolerance: float = 15.0
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
        actual_duration = self.get_video_duration(video_path)
        difference = abs(actual_duration - target_duration)
        
        if difference > tolerance:
            raise DurationMismatchError(
                f"Duration mismatch: {actual_duration:.1f}s vs target {target_duration}s",
                target_duration=target_duration,
                actual_duration=actual_duration,
                tolerance=tolerance
            )
        
        logger.info(
            f"Duration validated: {actual_duration:.1f}s "
            f"(target: {target_duration}s, diff: {difference:.1f}s)"
        )
        return True
    
    def add_voiceover_to_video(
        self,
        video_path: Path,
        voiceover_path: Path,
        output_path: Path
    ) -> Path:
        """
        Mux voiceover audio onto compiled video.
        
        Args:
            video_path: Path to video file
            voiceover_path: Path to voiceover audio file
            output_path: Path for output video with voiceover
            
        Returns:
            Path to output video with voiceover
            
        Raises:
            VideoProcessingError: If muxing fails
        """
        if not video_path.exists():
            raise VideoNotFoundError(f"Video file not found: {video_path}")
        if not voiceover_path.exists():
            raise VideoProcessingError(f"Voiceover file not found: {voiceover_path}")
        
        # Import AudioUtils here to avoid circular import
        from utils.audio_utils import AudioUtils
        audio_utils = AudioUtils()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get durations for validation
            video_duration = self.get_video_duration(video_path)
            voiceover_duration = audio_utils.get_audio_duration(voiceover_path)
            
            logger.info(f"Video duration: {video_duration:.2f}s")
            logger.info(f"Voiceover duration: {voiceover_duration:.2f}s")
            
            # Warn if there's a significant mismatch
            duration_diff = abs(video_duration - voiceover_duration)
            if duration_diff > 1.0:  # More than 1 second difference
                logger.warning(
                    f"Duration mismatch detected: Video is {video_duration:.2f}s, "
                    f"Voiceover is {voiceover_duration:.2f}s (diff: {duration_diff:.2f}s)"
                )
                logger.warning(
                    "The video segments may not have been extracted with exact voiceover durations. "
                    "This could cause sync issues."
                )
            
            # Check and handle existing audio track
            if audio_utils.has_audio_track(video_path):
                # Strip existing audio first
                logger.info("Stripping existing audio track before adding voiceover")
                temp_no_audio = video_path.parent / f"temp_no_audio_{video_path.stem}.mp4"
                video_no_audio = audio_utils.strip_audio(video_path, temp_no_audio)
            else:
                video_no_audio = video_path
                temp_no_audio = None
            
            # Add voiceover with fallback codec support
            aac_error = None
            mp3_error = None
            
            # Try AAC first
            try:
                cmd = [
                    'ffmpeg', '-y',
                    '-i', str(video_no_audio),
                    '-i', str(voiceover_path),
                    '-map', '0:v',  # Video from first input
                    '-map', '1:a',  # Audio from second input
                    '-c:v', 'copy',  # Copy video codec
                    '-c:a', 'aac',  # Try AAC first
                    '-b:a', '192k',  # Good audio quality
                    # Removed '-shortest' to allow full voiceover to play
                    # In voiceover mode, video should match voiceover duration exactly
                    str(output_path)
                ]
                
                logger.info(f"Adding voiceover to video with AAC codec: {voiceover_path.name}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
            except subprocess.CalledProcessError as e:
                aac_error = e
                logger.warning(f"AAC codec failed: {e.stderr}, trying MP3 fallback")
                
                # Fallback to MP3
                try:
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', str(video_no_audio),
                        '-i', str(voiceover_path),
                        '-map', '0:v',  # Video from first input
                        '-map', '1:a',  # Audio from second input
                        '-c:v', 'copy',  # Copy video codec
                        '-c:a', 'libmp3lame',  # Use MP3 codec
                        '-b:a', '192k',  # Good audio quality
                        # Removed '-shortest' to allow full voiceover to play
                        str(output_path)
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("Successfully used MP3 codec fallback")
                    
                except subprocess.CalledProcessError as e:
                    mp3_error = e
                    logger.error(f"Both AAC and MP3 codecs failed")
                    raise VideoProcessingError(
                        f"Failed to add voiceover with both codecs. "
                        f"AAC error: {aac_error.stderr if aac_error else 'N/A'}, "
                        f"MP3 error: {mp3_error.stderr if mp3_error else 'N/A'}"
                    )
            
            # Clean up temp file if created
            if temp_no_audio and temp_no_audio.exists():
                temp_no_audio.unlink()
                logger.debug(f"Cleaned up temp file: {temp_no_audio}")
            
            if not output_path.exists():
                raise VideoProcessingError("Output video was not created")
            
            # Verify duration matches
            output_duration = self.get_video_duration(output_path)
            voiceover_duration = audio_utils.get_audio_duration(voiceover_path)
            
            if abs(output_duration - voiceover_duration) > 0.5:
                logger.warning(
                    f"Duration mismatch after muxing: "
                    f"video={output_duration:.2f}s, voiceover={voiceover_duration:.2f}s"
                )
            else:
                logger.info(f"Voiceover added successfully: {output_path.name}")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error adding voiceover: {e.stderr}")
            raise VideoProcessingError(f"Failed to add voiceover: {e.stderr}")
        except Exception as e:
            logger.error(f"Error adding voiceover: {e}")
            raise VideoProcessingError(f"Failed to add voiceover: {str(e)}")
    
    def cleanup_temp_files(self, files_to_clean: List[Path]) -> None:
        """
        Clean up temporary files.
        
        Args:
            files_to_clean: List of file paths to delete
        """
        for file_path in files_to_clean:
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.debug(f"Deleted temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
    
    def _cleanup_old_temp_files(self, max_age_hours: int = 2) -> None:
        """
        Clean up old temporary files to prevent disk space issues.
        
        Args:
            max_age_hours: Delete files older than this many hours
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        patterns = ['merged_*.mp4', 'temp_segment_*.mp4', 'concat_*.txt', 'ultra_compressed_*.mp4']
        cleaned_count = 0
        cleaned_size = 0
        
        for pattern in patterns:
            for file_path in self.temp_dir.glob(pattern):
                try:
                    # Check file age
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_count += 1
                        cleaned_size += file_size
                        logger.debug(f"Cleaned old temp file: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Failed to clean {file_path}: {e}")
        
        if cleaned_count > 0:
            cleaned_mb = cleaned_size / (1024 * 1024)
            logger.info(f"Cleaned {cleaned_count} old temp files ({cleaned_mb:.1f}MB freed)")