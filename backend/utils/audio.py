"""
Audio utilities for voiceover processing and synchronization.

This module provides essential audio operations needed for the voiceover
integration feature, including duration detection, audio track management,
and format validation.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
import re

from .logger import get_logger
from .exceptions import VideoProcessingError

logger = get_logger(__name__)


class AudioUtils:
    """Utility class for audio operations."""
    
    # Supported audio formats
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac'}
    
    def __init__(self):
        """Initialize AudioUtils."""
        self.ffprobe_path = 'ffprobe'
        self.ffmpeg_path = 'ffmpeg'
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Duration in seconds as float
            
        Raises:
            VideoProcessingError: If duration cannot be determined
        """
        if not audio_path.exists():
            raise VideoProcessingError(f"Audio file not found: {audio_path}")
        
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(audio_path)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            
            logger.info(f"Audio duration for {audio_path.name}: {duration:.2f} seconds")
            return duration
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr}")
            raise VideoProcessingError(f"Failed to get audio duration: {e.stderr}")
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse FFprobe output: {e}")
            raise VideoProcessingError(f"Failed to parse audio metadata: {e}")
    
    def has_audio_track(self, video_path: Path) -> bool:
        """
        Check if video has existing audio track.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if video has audio track, False otherwise
        """
        if not video_path.exists():
            logger.warning(f"Video file not found: {video_path}")
            return False
        
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a',  # Select audio streams only
                str(video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            has_audio = len(data.get('streams', [])) > 0
            
            logger.info(f"Video {video_path.name} has audio track: {has_audio}")
            return has_audio
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFprobe error checking audio track: {e.stderr}")
            return False
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse FFprobe output: {e}")
            return False
    
    def strip_audio(self, video_path: Path, output_path: Path) -> Path:
        """
        Remove audio track from video.
        
        Args:
            video_path: Path to input video
            output_path: Path for output video without audio
            
        Returns:
            Path to output video
            
        Raises:
            VideoProcessingError: If audio stripping fails
        """
        if not video_path.exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-y',  # Overwrite output
                '-i', str(video_path),
                '-c:v', 'copy',  # Copy video stream
                '-an',  # Remove audio
                str(output_path)
            ]
            
            logger.info(f"Stripping audio from {video_path.name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path.exists():
                raise VideoProcessingError("Output file was not created")
            
            logger.info(f"Audio stripped successfully: {output_path.name}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error stripping audio: {e.stderr}")
            raise VideoProcessingError(f"Failed to strip audio: {e.stderr}")
    
    def validate_audio_file(self, audio_path: Path) -> bool:
        """
        Validate audio file format and integrity.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if valid, False otherwise
        """
        # Check if file exists
        if not audio_path.exists():
            logger.warning(f"Audio file does not exist: {audio_path}")
            return False
        
        # Check file extension
        if audio_path.suffix.lower() not in self.SUPPORTED_AUDIO_FORMATS:
            logger.warning(
                f"Unsupported audio format: {audio_path.suffix}. "
                f"Supported: {self.SUPPORTED_AUDIO_FORMATS}"
            )
            return False
        
        # Check file size (min 1KB, max 100MB)
        file_size = audio_path.stat().st_size
        if file_size < 1024:  # 1KB
            logger.warning(f"Audio file too small: {file_size} bytes")
            return False
        if file_size > 100 * 1024 * 1024:  # 100MB
            logger.warning(f"Audio file too large: {file_size / (1024*1024):.2f} MB")
            return False
        
        # Try to get duration to verify file integrity
        try:
            duration = self.get_audio_duration(audio_path)
            if duration <= 0:
                logger.warning(f"Invalid audio duration: {duration}")
                return False
            
            # Check reasonable duration (1 second to 5 minutes)
            if duration < 1 or duration > 300:
                logger.warning(
                    f"Audio duration outside reasonable range: {duration:.2f} seconds"
                )
                return False
            
            logger.info(f"Audio file validated successfully: {audio_path.name}")
            return True
            
        except VideoProcessingError as e:
            logger.warning(f"Failed to validate audio file: {e}")
            return False
    
    def get_audio_info(self, audio_path: Path) -> Dict[str, Any]:
        """
        Get detailed audio file information.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        if not audio_path.exists():
            raise VideoProcessingError(f"Audio file not found: {audio_path}")
        
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-select_streams', 'a:0',  # First audio stream
                str(audio_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            data = json.loads(result.stdout)
            
            # Extract relevant information
            format_info = data.get('format', {})
            stream_info = data.get('streams', [{}])[0] if data.get('streams') else {}
            
            audio_info = {
                'duration': float(format_info.get('duration', 0)),
                'size_bytes': int(format_info.get('size', 0)),
                'bit_rate': int(format_info.get('bit_rate', 0)),
                'format_name': format_info.get('format_name', 'unknown'),
                'codec_name': stream_info.get('codec_name', 'unknown'),
                'channels': stream_info.get('channels', 0),
                'sample_rate': stream_info.get('sample_rate', '0'),
                'file_path': str(audio_path),
                'file_name': audio_path.name
            }
            
            logger.info(
                f"Audio info for {audio_path.name}: "
                f"duration={audio_info['duration']:.2f}s, "
                f"codec={audio_info['codec_name']}, "
                f"bitrate={audio_info['bit_rate']//1000}kbps"
            )
            
            return audio_info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error getting audio info: {e.stderr}")
            raise VideoProcessingError(f"Failed to get audio info: {e.stderr}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse audio metadata: {e}")
            raise VideoProcessingError(f"Failed to parse audio metadata: {e}")
    
    def extract_audio_from_video(self, video_path: Path, output_path: Path) -> Path:
        """
        Extract audio track from video file.
        
        Args:
            video_path: Path to input video
            output_path: Path for extracted audio
            
        Returns:
            Path to extracted audio file
            
        Raises:
            VideoProcessingError: If extraction fails
        """
        if not video_path.exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        if not self.has_audio_track(video_path):
            raise VideoProcessingError(f"Video has no audio track: {video_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Determine output codec based on file extension
            output_ext = output_path.suffix.lower()
            if output_ext == '.mp3':
                codec_args = ['-c:a', 'libmp3lame', '-b:a', '192k']
            elif output_ext == '.aac':
                codec_args = ['-c:a', 'aac', '-b:a', '192k']
            elif output_ext == '.wav':
                codec_args = ['-c:a', 'pcm_s16le']
            else:
                # Default to copying codec
                codec_args = ['-c:a', 'copy']
            
            cmd = [
                self.ffmpeg_path,
                '-y',  # Overwrite output
                '-i', str(video_path),
                '-vn',  # No video
                *codec_args,
                str(output_path)
            ]
            
            logger.info(f"Extracting audio from {video_path.name} to {output_path.name}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path.exists():
                raise VideoProcessingError("Output audio file was not created")
            
            logger.info(f"Audio extracted successfully: {output_path.name}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error extracting audio: {e.stderr}")
            raise VideoProcessingError(f"Failed to extract audio: {e.stderr}")