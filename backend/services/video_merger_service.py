"""
Video merger service for concatenating multiple video files.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_service import BaseService
from .video_metadata_service import VideoMetadataService
from utils.exceptions import VideoNotFoundError, FFmpegError
from models.schemas import VideoIndex, VideoIndexCollection, CompressionSettings
from config.constants import FFMPEG_COMMON_ARGS


class VideoMergerService(BaseService):
    """Service for merging multiple video files into a single file."""
    
    def __init__(self, temp_dir: Optional[Path] = None):
        super().__init__(temp_dir)
        self.metadata_service = VideoMetadataService(temp_dir)
    
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
            
        Raises:
            ValueError: If no video files provided
            VideoNotFoundError: If any video file not found
            FFmpegError: If concatenation fails
        """
        if not video_files:
            raise ValueError("No video files provided")
        
        # Create temporary file list for FFmpeg concat
        list_file = self.temp_dir / f"concat_{os.getpid()}.txt"
        
        try:
            # Write file list for concat (optimized without redundant checks)
            with open(list_file, 'w', buffering=8192) as f:  # Larger buffer for faster writes
                for video_path in video_files:
                    # Skip file existence check - already validated upstream
                    # Use absolute path and escape special characters
                    escaped_path = str(video_path.absolute()).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            self.logger.info(f"Concatenating {len(video_files)} videos to {output_path}")
            
            if quality == "original":
                # Fast concatenation using copy codec with optimizations
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-protocol_whitelist', 'file,pipe,concat',  # Allow efficient protocols
                    '-i', str(list_file),
                    '-c', 'copy',  # Just copy, don't re-encode (FAST!)
                    '-threads', '0',  # Use all available CPU threads
                    '-max_muxing_queue_size', '9999',  # Increase muxing queue for better throughput
                ] + FFMPEG_COMMON_ARGS + [str(output_path)]
                self.logger.info("Fast concatenation using copy codec (no re-encoding)")
            else:
                # Concatenate with compression
                if not compression_settings:
                    compression_settings = CompressionSettings()
                
                # Optimized compression with threading
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat',
                    '-safe', '0',
                    '-protocol_whitelist', 'file,pipe,concat',
                    '-i', str(list_file),
                    '-threads', '0',  # Use all available CPU threads
                    '-max_muxing_queue_size', '9999',
                ] + compression_settings.to_ffmpeg_args() + [
                    '-avoid_negative_ts', 'make_zero',  # Keep this for timestamp consistency
                    str(output_path)
                ]
            
            # Run FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.ensure_file_exists(output_path, f"Failed to create output file: {output_path}")
            
            output_size = self.get_file_size_mb(output_path)
            self.logger.info(
                f"Successfully concatenated videos. "
                f"Output: {output_path.name} ({output_size:.1f}MB)"
            )
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg concatenation failed: {e.stderr}")
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
        # Get all durations in parallel for faster processing
        video_durations = {}
        
        with ThreadPoolExecutor(max_workers=min(4, len(video_files))) as executor:
            # Submit all duration extraction tasks
            future_to_path = {
                executor.submit(self.metadata_service.get_video_duration, path): path 
                for path in video_files
            }
            
            # Collect results
            for future in as_completed(future_to_path):
                video_path = future_to_path[future]
                try:
                    duration = future.result()
                    video_durations[video_path] = duration
                except Exception as e:
                    self.logger.error(f"Failed to get duration for {video_path}: {e}")
                    raise
        
        # Now build the index with the durations we collected
        indices = []
        current_time = 0.0
        total_duration = 0.0
        
        for video_path in video_files:  # Maintain original order
            duration = video_durations[video_path]
            
            index = VideoIndex(
                filename=video_path.name,
                start_in_merged=self.metadata_service.seconds_to_timestamp(current_time),
                end_in_merged=self.metadata_service.seconds_to_timestamp(current_time + duration),
                duration=duration
            )
            
            indices.append(index)
            current_time += duration
            total_duration += duration
        
        self.logger.info(f"Created video index for {len(video_files)} files, total duration: {total_duration:.1f}s")
        
        return VideoIndexCollection(
            videos=indices,
            total_duration=total_duration,
            merged_file_path=Path("merged.mp4")  # Will be updated later
        )
    
    def compress_video(
        self,
        input_path: Path,
        output_path: Path,
        compression_settings: Optional[CompressionSettings] = None
    ) -> Path:
        """
        Compress a single video file with optimized settings.
        
        Args:
            input_path: Input video file path
            output_path: Output compressed file path
            compression_settings: Compression settings
            
        Returns:
            Path to compressed video file
            
        Raises:
            VideoNotFoundError: If input video not found
            FFmpegError: If compression fails
        """
        self.ensure_file_exists(input_path, f"Input video not found: {input_path}")
        
        if not compression_settings:
            compression_settings = CompressionSettings()
        
        try:
            self.logger.info(f"Compressing video: {input_path} -> {output_path}")
            
            # Build optimized compression command with hardware acceleration if available
            import platform
            
            # Base command
            cmd = ['ffmpeg', '-y']
            
            # Try to use hardware acceleration on macOS
            if platform.system() == 'Darwin':
                # Use VideoToolbox hardware encoder on macOS (if available)
                cmd.extend([
                    '-hwaccel', 'auto',  # Auto-detect hardware acceleration
                ])
            
            # Add input and threading options
            cmd.extend([
                '-i', str(input_path),
                '-threads', '0',  # Use all CPU threads
                '-max_muxing_queue_size', '9999',
            ])
            
            # Add compression settings and output
            cmd.extend(compression_settings.to_ffmpeg_args())
            cmd.extend([
                '-movflags', '+faststart',  # Optimize for streaming
                str(output_path)
            ])
            
            # Run compression
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.ensure_file_exists(output_path, f"Failed to create compressed file: {output_path}")
            
            input_size = self.get_file_size_mb(input_path)
            output_size = self.get_file_size_mb(output_path)
            compression_ratio = input_size / output_size if output_size > 0 else 0
            
            self.logger.info(
                f"Successfully compressed video. "
                f"Size: {input_size:.1f}MB -> {output_size:.1f}MB "
                f"(compression ratio: {compression_ratio:.1f}x)"
            )
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg compression failed: {e.stderr}")
            raise FFmpegError(
                f"Failed to compress video: {e.stderr}",
                original_error=e
            )