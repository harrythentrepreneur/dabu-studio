"""
TikTok Video Ad Automation Backend Package.

This package provides video processing and AI-powered script matching
capabilities for creating TikTok ad videos.
"""

__version__ = "0.1.0"
__author__ = "TikTok Video Ad Automation Team"

# Optional imports - won't fail if modules don't exist
try:
    from .core.video_processor import VideoProcessor
except ImportError:
    pass

try:
    from .utils.video_utils import VideoPipeline
except ImportError:
    pass

try:
    from .utils.logger import get_logger, setup_logger
except ImportError:
    pass

__all__ = []