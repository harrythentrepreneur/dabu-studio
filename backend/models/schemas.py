"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field


class ScriptSegment(BaseModel):
    """Individual script segment with timing"""
    segment_number: Optional[int] = Field(None, description="Segment number")
    segment_text: Optional[str] = Field(None, description="Text of the segment")
    start_timestamp: Optional[str] = Field(None, description="Start time (HH:MM:SS.mmm)")
    end_timestamp: Optional[str] = Field(None, description="End time (HH:MM:SS.mmm)")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    visual_description: Optional[str] = Field(None, description="Description of matching visuals")


class GeminiResponse(BaseModel):
    """Response from Gemini API"""
    total_duration: float = Field(..., description="Total duration in seconds")
    target_duration: float = Field(..., description="Target duration in seconds")
    script_segments: List[ScriptSegment] = Field(..., description="List of script segments")


class VideoFile(BaseModel):
    """Video file information"""
    path: str
    filename: str
    duration: Optional[float] = None
    size_mb: Optional[float] = None


class VideoIndex(BaseModel):
    """Video index information"""
    filename: str
    start_time: float
    end_time: float
    duration: float


class VideoIndexCollection(BaseModel):
    """Collection of video indices"""
    videos: List[VideoIndex]
    total_duration: float


class ProcessingRequest(BaseModel):
    """Request for video processing"""
    script: str = Field(..., description="Script text")
    video_files: Optional[List[str]] = Field(None, description="List of video file paths")
    target_duration: float = Field(35.0, description="Target duration in seconds")
    voiceover_path: Optional[str] = Field(None, description="Path to voiceover file")
    use_mock: bool = Field(False, description="Use mock Gemini response")
    request_id: Optional[str] = Field(None, description="Unique request ID")


class ProcessingResponse(BaseModel):
    """Response from video processing"""
    success: bool
    output_video_path: Optional[Path] = None
    script_file_path: Optional[Path] = None
    timestamps_file_path: Optional[Path] = None
    merged_full_path: Optional[Path] = None
    gemini_response: Optional[GeminiResponse] = None
    processing_time: float
    voiceover_included: bool = False
    error_message: Optional[str] = None
    final_duration: Optional[float] = None

    class Config:
        # Allow Path objects
        arbitrary_types_allowed = True


class CompressionSettings(BaseModel):
    """Video compression configuration settings."""
    resolution: str = Field("270x480", description="Video resolution e.g. 270x480")
    bitrate: str = Field("1M", description="Target video bitrate e.g. 1M")
    fps: int = Field(15, description="Frames per second")
    codec: str = Field("h264", description="Video codec")
    preset: str = Field("faster", description="FFmpeg encoding preset")
    audio_bitrate: str = Field("64k", description="Audio bitrate")

    def to_ffmpeg_args(self) -> list[str]:
        """Convert settings to ffmpeg CLI argument list."""
        return [
            '-vf', f'scale={self.resolution}',
            '-r', str(self.fps),
            '-c:v', self.codec,
            '-preset', self.preset,
            '-b:v', self.bitrate,
            '-c:a', 'aac',
            '-b:a', self.audio_bitrate
        ]

class VideoMetadata(BaseModel):
    """Metadata about processed videos."""
    original_videos: List[VideoFile]
    merged_full_path: Path
    merged_compressed_path: Path
    video_index: VideoIndexCollection
    compression_settings: CompressionSettings
    total_size_original_mb: float
    size_compressed_mb: float
    processing_time: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True