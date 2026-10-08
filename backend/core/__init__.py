"""
Core business logic for TikTok Video Ad Automation.

This package contains the main processing pipeline and core components:
- Pipeline: Main orchestrator for the complete processing workflow
- VideoProcessor: Handles all video processing operations
- GeminiClient: Interface to Google Gemini AI API

These modules work together to process video files and create TikTok ads
by matching video segments with script content using AI analysis.
"""

from .pipeline import Pipeline
from .video_processor import VideoProcessor
from .gemini_client import GeminiClient

__all__ = [
    'Pipeline',
    'VideoProcessor', 
    'GeminiClient'
]