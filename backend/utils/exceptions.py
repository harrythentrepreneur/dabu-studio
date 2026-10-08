"""
Custom exception classes for the TikTok Video Ad Automation tool.

This module defines all custom exceptions used throughout the application
for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class VideoProcessingError(Exception):
    """Base exception for video processing errors."""
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message}: {str(self.original_error)}"
        return self.message


class VideoNotFoundError(VideoProcessingError):
    """Raised when a video file cannot be found."""
    pass


class VideoFormatError(VideoProcessingError):
    """Raised when a video format is not supported or corrupted."""
    pass


class VideoSizeError(VideoProcessingError):
    """Raised when video size exceeds limits."""
    pass


class FFmpegError(VideoProcessingError):
    """Raised when FFmpeg operations fail."""
    pass


class GeminiAPIError(Exception):
    """Base exception for Gemini API related errors."""
    
    def __init__(
        self, 
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data


class GeminiUploadError(GeminiAPIError):
    """Raised when file upload to Gemini API fails."""
    pass


class GeminiProcessingError(GeminiAPIError):
    """Raised when Gemini processing fails."""
    pass


class JSONParseError(GeminiAPIError):
    """Raised when Gemini response JSON parsing fails."""
    pass


class ScriptValidationError(Exception):
    """Raised when script validation fails."""
    
    def __init__(self, message: str, max_length: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.max_length = max_length


class DurationMismatchError(VideoProcessingError):
    """Raised when output duration doesn't match target duration."""
    
    def __init__(
        self, 
        message: str,
        target_duration: float,
        actual_duration: float,
        tolerance: float = 3.0
    ):
        super().__init__(message)
        self.target_duration = target_duration
        self.actual_duration = actual_duration
        self.tolerance = tolerance


class InsufficientVideoDataError(VideoProcessingError):
    """Raised when there isn't enough video content for the target duration."""
    
    def __init__(
        self, 
        message: str, 
        required_duration: float = 0, 
        available_duration: float = 0
    ):
        super().__init__(message)
        self.required_duration = required_duration
        self.available_duration = available_duration


class VoiceoverAnalysisError(Exception):
    """Raised when voiceover analysis fails."""
    
    def __init__(
        self,
        message: str,
        audio_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.audio_path = audio_path
        self.details = details or {}


class WhisperAPIError(Exception):
    """Raised when Whisper API operations fail."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data