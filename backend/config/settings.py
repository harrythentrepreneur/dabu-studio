"""
Configuration settings for TikTok Video Ad Automation.

This module provides configuration options for controlling the video processing pipeline.
"""

import os
from pathlib import Path
from typing import Optional

class VideoConfig:
    """Configuration for video processing."""
    
    # Extraction Settings
    USE_PRECISE_CUTS = os.getenv("USE_PRECISE_CUTS", "true").lower() == "true"
    """
    Enable precise frame-accurate cutting for segment extraction.
    
    When True: Uses re-encoding for frame-accurate cuts that follow Gemini's timestamps exactly.
               Slower but ensures the output matches what Gemini analyzed.
    
    When False: Uses copy codec for faster extraction but may cut at keyframe boundaries,
                causing segments to be slightly off from Gemini's specified timestamps.
    
    Default: True (prioritize accuracy over speed)
    """
    
    # Quality Settings for Precise Mode
    PRECISE_MODE_CRF = int(os.getenv("PRECISE_MODE_CRF", "23"))
    """
    CRF (Constant Rate Factor) for video quality in precise mode.
    Lower values = better quality. 23 is default H.264, good quality/speed balance.
    Range: 0-51 (0 = lossless, 23 = default, 51 = worst)
    """
    
    PRECISE_MODE_PRESET = os.getenv("PRECISE_MODE_PRESET", "veryfast")
    """
    FFmpeg preset for encoding speed vs compression efficiency.
    Options: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    Default: veryfast for good speed/quality balance
    """
    
    # Keyframe Settings for Merged Videos
    KEYFRAME_INTERVAL = int(os.getenv("KEYFRAME_INTERVAL", "30"))
    """
    Keyframe interval in frames for merged videos.
    Lower values = more keyframes = better seeking precision but larger file size.
    Default: 30 (1 keyframe per second at 30fps)
    """
    
    # Duration Validation
    SEGMENT_DURATION_TOLERANCE = float(os.getenv("SEGMENT_DURATION_TOLERANCE", "0.5"))
    """
    Maximum allowed deviation in seconds between expected and actual segment duration.
    Used to validate that extracted segments match Gemini's specifications.
    """
    
    # Logging
    LOG_FFMPEG_COMMANDS = os.getenv("LOG_FFMPEG_COMMANDS", "false").lower() == "true"
    """
    Log full FFmpeg commands for debugging.
    """
    
    @classmethod
    def get_status(cls) -> dict:
        """Get current configuration status."""
        return {
            "use_precise_cuts": cls.USE_PRECISE_CUTS,
            "precise_mode_crf": cls.PRECISE_MODE_CRF,
            "precise_mode_preset": cls.PRECISE_MODE_PRESET,
            "keyframe_interval": cls.KEYFRAME_INTERVAL,
            "segment_duration_tolerance": cls.SEGMENT_DURATION_TOLERANCE,
            "log_ffmpeg_commands": cls.LOG_FFMPEG_COMMANDS,
        }
    
    @classmethod
    def log_config(cls, logger):
        """Log current configuration settings."""
        logger.info("Video Processing Configuration:")
        logger.info(f"  - Precise Cuts: {'ENABLED' if cls.USE_PRECISE_CUTS else 'DISABLED'}")
        if cls.USE_PRECISE_CUTS:
            logger.info(f"  - Quality (CRF): {cls.PRECISE_MODE_CRF}")
            logger.info(f"  - Encoding Preset: {cls.PRECISE_MODE_PRESET}")
        logger.info(f"  - Keyframe Interval: {cls.KEYFRAME_INTERVAL} frames")
        logger.info(f"  - Duration Tolerance: ±{cls.SEGMENT_DURATION_TOLERANCE}s")