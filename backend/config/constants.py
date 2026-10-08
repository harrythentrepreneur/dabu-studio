"""
Constants and configuration values for TikTok Video Ad Automation.

This module centralizes all magic values and configuration constants to improve
maintainability and avoid hardcoded values throughout the codebase.
"""

from pathlib import Path
from typing import Set, Dict, Any

# ==================== File System Constants ====================

# File Extensions
ALLOWED_VIDEO_EXTENSIONS: Set[str] = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {'.mp3', '.wav', '.m4a', '.aac', '.ogg'}

# Directory Names
DEFAULT_TEMP_DIR_NAME = 'temp'
DEFAULT_OUTPUT_DIR_NAME = 'output'
DEFAULT_INPUT_DIR_NAME = 'input_videos'

# File Patterns
TEMP_FILE_PATTERNS = ['merged_*.mp4', 'temp_segment_*.mp4', 'concat_*.txt', 'ultra_compressed_*.mp4']
SCRIPT_FILENAME = 'script.txt'

# ==================== Video Processing Constants ====================

# Quality Settings
DEFAULT_CRF = 23
HIGH_QUALITY_CRF = 18
PRECISE_MODE_CRF = 18
COMPRESSED_CRF = 28

# Encoding Presets
FAST_PRESET = 'veryfast'
BALANCED_PRESET = 'fast'
PRECISE_PRESET = 'veryfast'  # Optimized for speed while maintaining accuracy

# Compression Settings
COMPRESSED_WIDTH = 270
COMPRESSED_HEIGHT = 480
COMPRESSED_BITRATE = '1M'
COMPRESSED_FPS = 15
COMPRESSED_AUDIO_BITRATE = '64k'

# Duration Settings
DEFAULT_TARGET_DURATION = 35.0
MIN_TARGET_DURATION = 15.0
MAX_TARGET_DURATION = 60.0
SEGMENT_DURATION_TOLERANCE = 0.5
DURATION_MISMATCH_TOLERANCE = 15.0

# Segment Settings
MIN_SEGMENT_DURATION = 3.0
MAX_SEGMENT_DURATION = 12.0
DEFAULT_SEGMENT_DURATION = 6.0
MIN_SEGMENTS = 3
MAX_SEGMENTS = 15

# ==================== API Constants ====================

# File Size Limits
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB
MAX_COMPRESSED_SIZE_MB = 100
TARGET_COMPRESSED_SIZE_MB = 50

# Timeouts
DEFAULT_PROCESSING_TIMEOUT = 600  # 10 minutes
SSE_KEEPALIVE_INTERVAL = 30  # seconds
FILE_UPLOAD_TIMEOUT = 300  # 5 minutes

# Retry Settings
DEFAULT_MAX_RETRIES = 3
GEMINI_MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2

# CORS Origins
ALLOWED_CORS_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001', 
    'http://localhost:3002',
    'http://localhost:3003',
    'http://localhost:3004',
    'http://localhost:3005',
    'http://localhost:3006'
]

# ==================== Gemini API Constants ====================

# Token Limits
GEMINI_MAX_OUTPUT_TOKENS = 65536  # Gemini 2.5 Pro limit (64K)
GEMINI_DEFAULT_OUTPUT_TOKENS = 16384  # Conservative default
GEMINI_MIN_OUTPUT_TOKENS = 8192  # Minimum for basic responses
TOKENS_PER_SEGMENT = 1000  # Estimated tokens per detailed segment
OVERHEAD_TOKENS = 2000  # For structure, metadata, etc.

# Model Settings
GEMINI_MODEL = 'gemini-2.5-pro'
GEMINI_TEMPERATURE = 0.2  # Lower for more deterministic JSON
GEMINI_TOP_P = 0.8  # Reduce randomness
GEMINI_TOP_K = 40  # Focus on likely tokens

# Response Settings
MIN_RESPONSE_LENGTH = 50
TRUNCATION_CHECK_INDICATORS = 6

# ==================== Audio Processing Constants ====================

# Audio Settings
DEFAULT_AUDIO_BITRATE = '192k'
HIGH_QUALITY_AUDIO_BITRATE = '256k'
COMPRESSED_AUDIO_BITRATE_VALUE = '64k'

# Audio Codecs (in order of preference)
PREFERRED_AUDIO_CODECS = ['aac', 'libmp3lame']

# Sync Tolerance
AUDIO_VIDEO_SYNC_TOLERANCE = 1.0  # seconds
VOICEOVER_SYNC_WARNING_THRESHOLD = 5.0  # seconds

# ==================== Logging Constants ====================

# Log Levels
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 3

# Log File Names
MAIN_LOG_FILE = 'main.log'
ERROR_LOG_FILE = 'main_errors.log'

# ==================== Pipeline Constants ====================

# Processing Steps (for status tracking)
PROCESSING_STEPS = {
    'LOADING_INPUTS': 1,
    'MERGING_VIDEOS': 2,
    'UPLOADING_TO_AI': 3,
    'AI_ANALYSIS': 4,
    'VALIDATING_DURATION': 5,
    'EXTRACTING_SEGMENTS': 6,
    'EXPORTING_OUTPUTS': 7,
    'CLEANUP': 8,
    'ADDING_VOICEOVER': 9  # Optional step
}

# Status Messages
STATUS_MESSAGES = {
    'LOADING_INPUTS': 'Loading script and video files...',
    'MERGING_VIDEOS': 'Merging video files into full and compressed versions...',
    'UPLOADING_TO_AI': 'Uploading compressed video to Gemini API...',
    'AI_ANALYSIS': 'Analyzing video content and matching with script...',
    'VALIDATING_DURATION': 'Checking segment durations and quality...',
    'EXTRACTING_SEGMENTS': 'Extracting video segments from full-quality source...',
    'EXPORTING_OUTPUTS': 'Preparing final outputs (video, script, timestamps)...',
    'CLEANUP': 'Cleaning up temporary files...',
    'ADDING_VOICEOVER': 'Adding voiceover audio to video...'
}

# ==================== Error Messages ====================

ERROR_MESSAGES = {
    'SCRIPT_REQUIRED': 'Script text is required',
    'NO_VIDEOS_PROVIDED': 'At least one video file is required',
    'INVALID_FILE_TYPE': 'File type not supported',
    'FILE_TOO_LARGE': 'File exceeds maximum size limit',
    'VIDEO_NOT_FOUND': 'Video file not found',
    'GEMINI_API_ERROR': 'Failed to communicate with Gemini API',
    'PROCESSING_FAILED': 'Video processing failed',
    'DURATION_MISMATCH': 'Video duration outside acceptable tolerance',
    'INSUFFICIENT_VIDEO_DATA': 'Not enough video content for target duration'
}

# ==================== Validation Constants ====================

# Script Validation
MIN_SCRIPT_LENGTH = 20  # characters
MAX_SCRIPT_LENGTH = 5000  # characters
SCRIPT_WARNING_LENGTH = 50  # warn if too short

# Video Validation
MAX_VIDEO_COUNT = 20
MIN_VIDEO_COUNT = 1
VIDEO_SIZE_WARNING_MB = 500

# Quality Thresholds
MIN_CONFIDENCE_SCORE = 0.3
GOOD_CONFIDENCE_SCORE = 0.7
HIGH_CONFIDENCE_SCORE = 0.9

# ==================== Cleanup Constants ====================

# File Age Limits
TEMP_FILE_MAX_AGE_HOURS = 2
LOG_FILE_MAX_AGE_DAYS = 7
CACHE_MAX_AGE_HOURS = 24

# Cleanup Patterns
CLEANUP_EXTENSIONS = ['.mp4', '.txt', '.json', '.log']
CLEANUP_SIZE_THRESHOLD_MB = 1000  # Clean up if temp dir > 1GB

# ==================== FFmpeg Constants ====================

# Common FFmpeg Options
FFMPEG_COMMON_ARGS = ['-avoid_negative_ts', 'make_zero', '-movflags', '+faststart']
FFMPEG_KEYFRAME_ARGS = ['-g', '30']  # Keyframe every 30 frames
FFMPEG_QUALITY_ARGS = ['-crf', '23', '-preset', 'fast']

# Video Filters
VIDEO_SCALE_FILTER = 'scale=270:480'
VIDEO_TRIM_FILTER_FORMAT = 'trim=start={start}:end={end},setpts=PTS-STARTPTS'
AUDIO_TRIM_FILTER_FORMAT = 'atrim=start={start}:end={end},asetpts=PTS-STARTPTS'

# ==================== Development Constants ====================

# Debug Settings
DEBUG_MODE_ENV_VAR = 'DEBUG_MODE'
DEFAULT_DEBUG_MODE = False

# Test Settings
MOCK_MODE_ENV_VAR = 'USE_MOCK_GEMINI'
DEFAULT_MOCK_MODE = False

# Performance Settings
PROCESSING_THREAD_COUNT = 4
MAX_CONCURRENT_UPLOADS = 2

# ==================== Helper Functions ====================

def get_file_extensions_display(extensions: Set[str]) -> str:
    """Convert file extensions set to display string."""
    return ', '.join(sorted(extensions))

def get_step_progress(step_name: str, total_steps: int = 8) -> int:
    """Calculate progress percentage for a processing step."""
    step_num = PROCESSING_STEPS.get(step_name, 1)
    return int((step_num / total_steps) * 100)

def validate_target_duration(duration: float) -> bool:
    """Validate if target duration is within acceptable bounds."""
    return MIN_TARGET_DURATION <= duration <= MAX_TARGET_DURATION

def get_optimal_segments_count(target_duration: float) -> int:
    """Calculate optimal number of segments for target duration."""
    segments = int(target_duration / DEFAULT_SEGMENT_DURATION)
    return max(MIN_SEGMENTS, min(segments, MAX_SEGMENTS))

# ==================== Configuration Classes ====================

class VideoConfig:
    """Video processing configuration."""
    USE_PRECISE_CUTS = False  # Use fast keyframe-based cuts by default
    MAX_VIDEO_SIZE_MB = 500
    DEFAULT_ASPECT_RATIO = (9, 16)
    PARALLEL_EXTRACTION_WORKERS = 4
    PRECISE_MODE_CRF = 18
    PRECISE_MODE_PRESET = "veryfast"  # Optimized for speed
    LOG_FFMPEG_COMMANDS = False