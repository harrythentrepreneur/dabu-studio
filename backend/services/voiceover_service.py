"""
Voiceover service for adding voiceover audio to video files.
"""

import subprocess
from pathlib import Path
from typing import List

from .base_service import BaseService
from .video_metadata_service import VideoMetadataService
from utils.exceptions import VideoNotFoundError, VideoProcessingError
from config.constants import PREFERRED_AUDIO_CODECS, AUDIO_VIDEO_SYNC_TOLERANCE


class VoiceoverService(BaseService):
    """Service for adding voiceover audio to video files."""
    
    def __init__(self, temp_dir: Path = None):
        super().__init__(temp_dir)
        self.metadata_service = VideoMetadataService(temp_dir)
    
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
            VideoNotFoundError: If video or voiceover file not found
            VideoProcessingError: If muxing fails
        """
        self.ensure_file_exists(video_path, f"Video file not found: {video_path}")
        self.ensure_file_exists(voiceover_path, f"Voiceover file not found: {voiceover_path}")
        
        # Import AudioUtils here to avoid circular import
        from utils.audio import AudioUtils
        audio_utils = AudioUtils()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Get durations for validation
            video_duration = self.metadata_service.get_video_duration(video_path)
            voiceover_duration = audio_utils.get_audio_duration(voiceover_path)
            
            self.logger.info(f"Video duration: {video_duration:.2f}s")
            self.logger.info(f"Voiceover duration: {voiceover_duration:.2f}s")
            
            # Warn if there's a significant mismatch
            duration_diff = abs(video_duration - voiceover_duration)
            if duration_diff > AUDIO_VIDEO_SYNC_TOLERANCE:
                self.logger.warning(
                    f"Duration mismatch detected: Video is {video_duration:.2f}s, "
                    f"Voiceover is {voiceover_duration:.2f}s (diff: {duration_diff:.2f}s)"
                )
            
            # Handle existing audio track
            video_no_audio, temp_no_audio = self._prepare_video_for_voiceover(
                video_path, audio_utils
            )
            
            # Add voiceover with codec fallback
            self._add_voiceover_with_fallback(
                video_no_audio, voiceover_path, output_path
            )
            
            # Clean up temp file if created
            if temp_no_audio and temp_no_audio.exists():
                temp_no_audio.unlink()
                self.logger.debug(f"Cleaned up temp file: {temp_no_audio}")
            
            self.ensure_file_exists(output_path, "Output video was not created")
            
            # Verify final duration
            self._verify_output_duration(output_path, voiceover_duration, audio_utils)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg error adding voiceover: {e.stderr}")
            raise VideoProcessingError(f"Failed to add voiceover: {e.stderr}")
        except Exception as e:
            self.logger.error(f"Error adding voiceover: {e}")
            raise VideoProcessingError(f"Failed to add voiceover: {str(e)}")
    
    def _prepare_video_for_voiceover(self, video_path: Path, audio_utils) -> tuple:
        """Prepare video file for voiceover by handling existing audio."""
        from utils.audio import AudioUtils
        
        if audio_utils.has_audio_track(video_path):
            # Strip existing audio first
            self.logger.info("Stripping existing audio track before adding voiceover")
            temp_no_audio = video_path.parent / f"temp_no_audio_{video_path.stem}.mp4"
            video_no_audio = audio_utils.strip_audio(video_path, temp_no_audio)
            return video_no_audio, temp_no_audio
        else:
            return video_path, None
    
    def _add_voiceover_with_fallback(
        self, 
        video_path: Path, 
        voiceover_path: Path, 
        output_path: Path
    ) -> None:
        """Add voiceover with codec fallback support."""
        
        for i, codec in enumerate(PREFERRED_AUDIO_CODECS):
            try:
                cmd = self._build_voiceover_command(
                    video_path, voiceover_path, output_path, codec
                )
                
                codec_name = "AAC" if codec == "aac" else "MP3"
                self.logger.info(f"Adding voiceover to video with {codec_name} codec: {voiceover_path.name}")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if i > 0:  # Used fallback codec
                    self.logger.info(f"Successfully used {codec_name} codec fallback")
                
                break  # Success, exit loop
                
            except subprocess.CalledProcessError as e:
                if i == len(PREFERRED_AUDIO_CODECS) - 1:  # Last codec failed
                    self.logger.error("All audio codecs failed")
                    raise VideoProcessingError(
                        f"Failed to add voiceover with all codecs: {e.stderr}"
                    )
                else:
                    codec_name = "AAC" if codec == "aac" else "MP3"
                    self.logger.warning(f"{codec_name} codec failed: {e.stderr}, trying next codec")
    
    def _build_voiceover_command(
        self, 
        video_path: Path, 
        voiceover_path: Path, 
        output_path: Path, 
        codec: str
    ) -> List[str]:
        """Build FFmpeg command for adding voiceover."""
        return [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', str(voiceover_path),
            '-map', '0:v',  # Video from first input
            '-map', '1:a',  # Audio from second input
            '-c:v', 'copy',  # Copy video codec
            '-c:a', codec,  # Audio codec
            '-b:a', '192k',  # Good audio quality
            # Note: Removed '-shortest' to allow full voiceover to play
            str(output_path)
        ]
    
    def _verify_output_duration(
        self, 
        output_path: Path, 
        voiceover_duration: float, 
        audio_utils
    ) -> None:
        """Verify that output duration matches voiceover duration."""
        output_duration = self.metadata_service.get_video_duration(output_path)
        
        if abs(output_duration - voiceover_duration) > 0.5:
            self.logger.warning(
                f"Duration mismatch after muxing: "
                f"video={output_duration:.2f}s, voiceover={voiceover_duration:.2f}s"
            )
        else:
            self.logger.info(f"Voiceover added successfully: {output_path.name}")