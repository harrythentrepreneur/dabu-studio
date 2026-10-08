"""
Configuration settings for TikTok Video Ad Automation.

This package contains all configuration and constant definitions:
- constants: Application-wide constants and magic values
- settings: Runtime configuration settings that can be environment-controlled

By centralizing configuration, we avoid hardcoded values throughout the 
codebase and make the application easier to configure and maintain.
"""

from .constants import *  # Import all constants for backward compatibility
from .settings import VideoConfig

__all__ = [
    # Re-export all constants from constants.py for easy access
    'ALLOWED_VIDEO_EXTENSIONS',
    'ALLOWED_AUDIO_EXTENSIONS', 
    'DEFAULT_TARGET_DURATION',
    'MAX_FILE_SIZE_BYTES',
    'GEMINI_MODEL',
    'PROCESSING_STEPS',
    'STATUS_MESSAGES',
    'ERROR_MESSAGES',
    # Settings
    'VideoConfig'
]