"""
Utility functions and helpers for TikTok Video Ad Automation.

This package contains utility modules for common operations:
- logger: Logging configuration and utilities
- exceptions: Custom exception classes  
- error_handler: Centralized error handling
- audio: Audio processing utilities
- ffmpeg: FFmpeg operation helpers
- debug_collector: Debug data collection for troubleshooting
- files: File system operations

These utilities provide reusable functionality across the application
while keeping the core business logic clean and focused.
"""

from .logger import get_logger, LogContext
from .exceptions import (
    VideoProcessingError,
    GeminiAPIError,
    ScriptValidationError,
    InsufficientVideoDataError,
    VideoNotFoundError,
    DurationMismatchError,
    FFmpegError,
    VideoFormatError,
    JSONParseError,
    GeminiProcessingError
)
from .error_handler import ErrorHandler

__all__ = [
    'get_logger',
    'LogContext',
    'VideoProcessingError',
    'GeminiAPIError', 
    'ScriptValidationError',
    'InsufficientVideoDataError',
    'VideoNotFoundError',
    'DurationMismatchError',
    'FFmpegError',
    'VideoFormatError',
    'JSONParseError',
    'GeminiProcessingError',
    'ErrorHandler'
]