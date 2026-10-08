"""
Additional video utility functions for the TikTok Video Ad Automation tool.

This module provides supplementary video processing utilities and
the main pipeline orchestration for the dual-file strategy.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.video_processor import VideoProcessor
from .logger import get_logger
from .exceptions import VideoProcessingError, DurationMismatchError
from models.schemas import (
    VideoFile,
    VideoIndexCollection,
    CompressionSettings,
    VideoMetadata,
    GeminiResponse,
    ScriptSegment
)
from config.settings import VideoConfig

logger = get_logger(__name__)


class VideoPipeline:
    """Orchestrates the complete video processing pipeline."""
    
    def __init__(self, video_processor: Optional[VideoProcessor] = None):
        """
        Initialize VideoPipeline.
        
        Args:
            video_processor: VideoProcessor instance (creates new if None)
        """
        self.processor = video_processor or VideoProcessor()
        self.temp_dir = self.processor.temp_dir
        
    def prepare_videos_for_pipeline(
        self,
        video_files: List[Path],
        output_dir: Optional[Path] = None,
        request_id: Optional[str] = None
    ) -> Tuple[Path, Path, VideoIndexCollection]:
        """
        Prepare videos with dual-file strategy (full quality + compressed).
        
        This is the critical function from the PRD that creates both
        merged_full.mp4 and merged_compressed.mp4.
        
        Args:
            video_files: List of input video file paths
            output_dir: Output directory (defaults to backend/temp)
            
        Returns:
            Tuple of (merged_full_path, merged_compressed_path, video_index)
        """
        if not output_dir:
            output_dir = self.temp_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate all video files first
        logger.info(f"Validating {len(video_files)} video files...")
        validated_videos = self.processor.validate_video_files(
            video_files,
            max_size_mb=500,
            required_aspect_ratio=(9, 16)
        )
        
        # Create video index for tracking boundaries
        logger.info("Creating video index...")
        video_index = self.processor.create_video_index(video_files)
        
        # Generate unique filenames with request_id or timestamp
        if request_id:
            file_suffix = request_id
        else:
            file_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_full_path = output_dir / f"merged_full_{file_suffix}.mp4"
        merged_compressed_path = output_dir / f"merged_compressed_{file_suffix}.mp4"
        
        # Step 1: Create full quality merged video
        logger.info("Creating full quality merged video...")
        start_time = time.time()
        
        self.processor.concatenate_videos(
            video_files,
            merged_full_path,
            quality="original"
        )
        
        full_size = self.processor.get_file_size(merged_full_path)
        merge_time = time.time() - start_time
        logger.info(
            f"Full quality merge complete: {full_size:.1f}MB in {merge_time:.1f}s"
        )
        
        # Step 2: Create compressed version for Gemini
        logger.info("Creating compressed version for Gemini API...")
        start_time = time.time()
        
        compression_settings = CompressionSettings(
            resolution="270x480",  # 9:16 aspect ratio at low res
            bitrate="1M",
            fps=15,
            codec="h264",
            preset="faster",
            audio_bitrate="64k"
        )
        
        self.processor.concatenate_videos(
            video_files,
            merged_compressed_path,
            quality="compressed",
            compression_settings=compression_settings
        )
        
        compressed_size = self.processor.get_file_size(merged_compressed_path)
        compress_time = time.time() - start_time
        compression_ratio = full_size / compressed_size
        
        logger.info(
            f"Compression complete: {compressed_size:.1f}MB in {compress_time:.1f}s "
            f"(ratio: {compression_ratio:.1f}:1)"
        )
        
        # Verify compressed size is under 100MB
        if compressed_size > 100:
            logger.warning(
                f"Compressed file size {compressed_size:.1f}MB exceeds 100MB target. "
                "May need Digital Ocean Spaces fallback."
            )
        
        # Update video index with merged file path
        video_index.merged_file_path = merged_full_path
        
        return merged_full_path, merged_compressed_path, video_index
    
    def extract_and_compile_segments(
        self,
        merged_full_video: Path,
        timestamps: GeminiResponse,
        output_dir: Optional[Path] = None,
        request_id: Optional[str] = None,
        use_precise_cuts: Optional[bool] = None,
        voiceover_segments: Optional[list] = None,  # NEW parameter
        debug_collector: Optional[Any] = None  # Debug collector instance
    ) -> Path:
        """
        Extract segments from full-quality merged video and compile them.
        
        This function implements the PRD requirement to ALWAYS extract
        from merged_full.mp4, never from the compressed version.
        
        Args:
            merged_full_video: Path to full quality merged video
            timestamps: Gemini response with segment timestamps
            output_dir: Output directory for final video
            request_id: Unique request identifier for file naming
            use_precise_cuts: Use precise frame-accurate cuts (slower but more accurate)
            voiceover_segments: Optional list of voiceover segments with exact durations
            
        Returns:
            Path to compiled video
        """
        if not output_dir:
            output_dir = Path(__file__).parent.parent / 'output'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use config default if not specified
        if use_precise_cuts is None:
            use_precise_cuts = VideoConfig.USE_PRECISE_CUTS
        
        segments = []
        temp_segments = []
        
        logger.info(f"Extracting {len(timestamps.script_segments)} segments...")
        logger.info(f"Extraction mode: {'PRECISE (frame-accurate)' if use_precise_cuts else 'FAST (keyframe-based)'}")
        if use_precise_cuts:
            logger.info("Note: Using precise mode ensures Gemini's timestamps are followed exactly")
        
        # Validate segment count match if voiceover is provided
        if voiceover_segments:
            if len(voiceover_segments) != len(timestamps.script_segments):
                logger.error(
                    f"Segment count mismatch: voiceover has {len(voiceover_segments)} segments, "
                    f"but script has {len(timestamps.script_segments)} segments"
                )
                raise VideoProcessingError(
                    f"Voiceover segment count ({len(voiceover_segments)}) doesn't match "
                    f"script segment count ({len(timestamps.script_segments)})"
                )
        
        # Get video duration to validate timestamps
        video_duration = self.processor.get_video_duration(merged_full_video)
        logger.info(f"Source video duration: {video_duration:.2f}s")
        
        # Validate and fix timestamps before extraction
        for idx, segment in enumerate(timestamps.script_segments):
            start_seconds = self.processor.timestamp_to_seconds(segment.start_timestamp)
            end_seconds = self.processor.timestamp_to_seconds(segment.end_timestamp)
            
            # Check for hour formatting error (e.g., 59:58 instead of 9:58)
            if start_seconds > 3540 and video_duration < 1800:  # > 59 minutes but video < 30 minutes
                logger.warning(
                    f"Segment {segment.segment_number} has invalid timestamp "
                    f"{segment.start_timestamp} ({start_seconds:.2f}s) - likely hour formatting error. "
                    f"Video duration is only {video_duration:.2f}s"
                )
                
                # Try to fix by removing one hour (3600 seconds)
                if 3540 <= start_seconds < 3660:  # Between 59:00 and 61:00
                    fixed_start = start_seconds - 3600
                    fixed_end = end_seconds - 3600 if end_seconds > 3600 else end_seconds
                    
                    # Update the segment timestamps
                    segment.start_timestamp = self.processor.seconds_to_timestamp(fixed_start)
                    segment.end_timestamp = self.processor.seconds_to_timestamp(fixed_end)
                    
                    logger.info(
                        f"Fixed segment {segment.segment_number} timestamps: "
                        f"{segment.start_timestamp} to {segment.end_timestamp}"
                    )
                else:
                    # Try a different fix: assume it's meant to be around 9-10 minutes
                    # Extract the minutes and seconds part only
                    parts = segment.start_timestamp.split(':')
                    if len(parts) == 3:
                        # Take last two parts as MM:SS
                        minutes = int(parts[1])
                        seconds = float(parts[2])
                        fixed_start = minutes * 60 + seconds
                        
                        # Do the same for end timestamp
                        end_parts = segment.end_timestamp.split(':')
                        if len(end_parts) == 3:
                            end_minutes = int(end_parts[1])
                            end_seconds = float(end_parts[2])
                            fixed_end = end_minutes * 60 + end_seconds
                            
                            segment.start_timestamp = self.processor.seconds_to_timestamp(fixed_start)
                            segment.end_timestamp = self.processor.seconds_to_timestamp(fixed_end)
                            
                            logger.info(
                                f"Fixed segment {segment.segment_number} by removing hour component: "
                                f"{segment.start_timestamp} to {segment.end_timestamp}"
                            )
            
            # Final validation - skip if still beyond video duration
            start_seconds = self.processor.timestamp_to_seconds(segment.start_timestamp)
            if start_seconds >= video_duration:
                logger.error(
                    f"Segment {segment.segment_number} start time {segment.start_timestamp} "
                    f"({start_seconds:.2f}s) still exceeds video duration ({video_duration:.2f}s) after fixes. "
                    f"Skipping this segment."
                )
                # Remove this segment from the list
                timestamps.script_segments.remove(segment)
                continue
        
        # CRITICAL: Sort segments by segment_number to ensure correct playback order
        # Gemini returns segments in JSON order, but segment_number defines playback order
        sorted_segments = sorted(timestamps.script_segments, key=lambda s: s.segment_number)
        logger.info("Sorted segments by segment_number for correct playback order")
        
        try:
            # Function to extract a single segment
            def extract_single_segment(idx, segment):
                # Check if we have voiceover duration for this segment
                # idx is 0-based, display number is 1-based
                display_num = idx + 1
                voiceover_duration = None
                
                # Match by segment_number if available (voiceover mode)
                if voiceover_segments and hasattr(segment, 'segment_number') and segment.segment_number:
                    # Find matching voiceover segment by number (1-based)
                    segment_idx = segment.segment_number - 1  # Convert to 0-based
                    if segment_idx < len(voiceover_segments):
                        base_duration = voiceover_segments[segment_idx]['duration']
                        voiceover_text = voiceover_segments[segment_idx].get('text', 'NO TEXT')
                        
                        # Calculate extended duration to include gap until next segment
                        # This fills the silence with video content
                        if segment_idx < len(voiceover_segments) - 1:
                            # Not the last segment - extend to start of next voiceover segment
                            current_end = voiceover_segments[segment_idx]['end']
                            next_start = voiceover_segments[segment_idx + 1]['start']
                            gap_duration = next_start - current_end
                            
                            if gap_duration > 0:
                                # Extend this segment to cover the gap
                                voiceover_duration = base_duration + gap_duration
                                logger.info(
                                    f"Segment {segment.segment_number}: Extending duration by {gap_duration:.3f}s "
                                    f"to fill gap (from {base_duration:.3f}s to {voiceover_duration:.3f}s)"
                                )
                            else:
                                voiceover_duration = base_duration
                        else:
                            # Last segment - might need to extend to match total voiceover duration
                            voiceover_duration = base_duration
                        
                        # LOG MISMATCH WARNING if texts don't match
                        if segment.segment_text and voiceover_text:
                            if segment.segment_text.strip() != voiceover_text.strip():
                                logger.warning(
                                    f"TEXT MISMATCH at segment {segment.segment_number}:\n"
                                    f"  Gemini text: '{segment.segment_text[:50]}...'\n"
                                    f"  Voiceover text: '{voiceover_text[:50]}...'\n"
                                    f"  This will cause sync issues!"
                                )
                        
                        logger.info(
                            f"Extracting segment {segment.segment_number}/{len(sorted_segments)}: "
                            f"{segment.start_timestamp} with duration {voiceover_duration:.2f}s "
                            f"(VOICEOVER mode - includes gap fill)"
                        )
                else:
                    logger.info(
                        f"Extracting segment {display_num}/{len(sorted_segments)}: "
                        f"{segment.start_timestamp} to {segment.end_timestamp} "
                        f"(mode: {'PRECISE' if use_precise_cuts else 'FAST'})"
                    )
                
                # Use segment_number for filename to ensure correct ordering
                # segment_number is 1-based, so subtract 1 for 0-based file naming
                file_idx = (segment.segment_number - 1) if hasattr(segment, 'segment_number') and segment.segment_number else idx
                segment_file = self.temp_dir / f"temp_segment_{file_idx:03d}.mp4"
                
                # Extract segment with optional voiceover duration
                self.processor.extract_segment(
                    merged_full_video,
                    segment_file,
                    segment.start_timestamp,
                    segment.end_timestamp,
                    use_copy_codec=not use_precise_cuts and voiceover_duration is None,
                    precise_mode=use_precise_cuts and voiceover_duration is None,
                    voiceover_duration=voiceover_duration,  # Pass voiceover duration if available
                    segment_number=segment.segment_number if hasattr(segment, 'segment_number') else display_num,
                    debug_collector=debug_collector  # Pass debug collector
                )
                
                return idx, segment_file
            
            # Extract segments in parallel for speed
            max_workers = min(4, len(sorted_segments))  # Limit to 4 parallel extractions
            logger.info(f"Extracting segments in parallel with {max_workers} workers...")
            
            segment_results = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(extract_single_segment, idx, segment): idx 
                    for idx, segment in enumerate(sorted_segments)
                }
                
                for future in as_completed(futures):
                    try:
                        idx, segment_file = future.result()
                        segment_results[idx] = segment_file
                    except Exception as e:
                        logger.error(f"Failed to extract segment: {e}")
                        raise
            
            # Sort segments by index to maintain order
            for i in sorted(segment_results.keys()):
                segments.append(segment_results[i])
                temp_segments.append(segment_results[i])
            
            # Compile segments with hard cuts
            if request_id:
                output_path = output_dir / f"compiled_video_{request_id}.mp4"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"compiled_video_{timestamp}.mp4"
            
            logger.info(f"Compiling {len(segments)} segments into final video...")
            
            # Always use standard concatenation - segments are extracted with proper durations
            final_video = self.processor.concatenate_with_hard_cuts(
                segments,
                output_path
            )
            
            # Validate duration - allow anything under 2.5 minutes (150 seconds)
            final_duration = self.processor.get_video_duration(final_video)
            if final_duration > 150.0:
                # Only raise an error if it's over 2.5 minutes
                raise DurationMismatchError(
                    f"Video duration {final_duration:.1f}s exceeds 2.5 minute limit",
                    actual_duration=final_duration,
                    target_duration=timestamps.target_duration,
                    tolerance=150.0
                )
            logger.info(f"Duration {final_duration:.1f}s is acceptable (under 2.5 minutes)")
            
            final_size = self.processor.get_file_size(final_video)
            logger.info(
                f"Final video created: {final_video.name} "
                f"({final_size:.1f}MB, {timestamps.total_duration:.1f}s)"
            )
            
            return final_video
            
        finally:
            # Clean up temporary segment files
            self.processor.cleanup_temp_files(temp_segments)
    
    def validate_sync(
        self, 
        voiceover_segments: list, 
        extracted_segments: List[Path]
    ) -> bool:
        """
        Validate that video segments match voiceover duration.
        
        Args:
            voiceover_segments: List of voiceover segments with durations
            extracted_segments: List of extracted video segment paths
            
        Returns:
            True if sync is valid
            
        Raises:
            DurationMismatchError: If durations don't match
        """
        voiceover_total = sum(s['duration'] for s in voiceover_segments)
        video_total = sum(
            self.processor.get_video_duration(s) for s in extracted_segments
        )
        
        if abs(voiceover_total - video_total) > 0.1:
            logger.error(
                f"Duration mismatch: voiceover={voiceover_total:.2f}s, "
                f"video={video_total:.2f}s"
            )
            raise DurationMismatchError(
                f"Video duration {video_total:.2f}s doesn't match "
                f"voiceover {voiceover_total:.2f}s",
                target_duration=voiceover_total,
                actual_duration=video_total
            )
        
        logger.info(f"Sync validation passed: duration={voiceover_total:.2f}s")
        return True
    
    def export_outputs(
        self,
        compiled_video: Path,
        script_text: str,
        timestamps: GeminiResponse,
        output_dir: Optional[Path] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export all three required outputs as per PRD.
        
        Args:
            compiled_video: Path to compiled video
            script_text: Original script text
            timestamps: Gemini response data
            output_dir: Output directory
            
        Returns:
            Dictionary with paths to all output files
        """
        if not output_dir:
            output_dir = compiled_video.parent
        
        # Use request_id if provided, otherwise generate timestamp
        if request_id:
            file_suffix = request_id
        else:
            file_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Video is already in place
        video_path = compiled_video
        
        # 2. Export raw script text (for ElevenLabs)
        script_path = output_dir / f"script_raw_{file_suffix}.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_text)
        logger.info(f"Exported script to: {script_path}")
        
        # 3. Export timestamps JSON
        timestamps_path = output_dir / f"timestamps_{file_suffix}.json"
        
        # Convert Pydantic model to dict and ensure JSON serializable
        timestamps_dict = json.loads(timestamps.model_dump_json(indent=2))
        
        with open(timestamps_path, 'w', encoding='utf-8') as f:
            json.dump(timestamps_dict, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported timestamps to: {timestamps_path}")
        
        return {
            'video': video_path,
            'script': script_path,
            'timestamps': timestamps_path
        }
    
    def create_extreme_compression(
        self,
        video_path: Path,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Create an extremely compressed version as fallback.
        
        Used when standard compression still exceeds 100MB.
        
        Args:
            video_path: Input video path
            output_path: Output path (auto-generated if None)
            
        Returns:
            Path to ultra-compressed video
        """
        if not output_path:
            output_path = self.temp_dir / f"ultra_compressed_{os.getpid()}.mp4"
        
        # Ultra compression settings
        ultra_settings = CompressionSettings(
            resolution="180x320",  # Even lower resolution
            bitrate="500k",        # Half the bitrate
            fps=10,                # Lower framerate
            codec="h264",
            preset="veryfast",     # Faster encoding
            audio_bitrate="32k"    # Minimal audio
        )
        
        logger.warning("Applying extreme compression settings...")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_path)
        ] + ultra_settings.to_ffmpeg_args() + [
            '-movflags', '+faststart',
            str(output_path)
        ]
        
        try:
            import subprocess
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            compressed_size = self.processor.get_file_size(output_path)
            logger.info(f"Ultra-compressed to {compressed_size:.1f}MB")
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            raise VideoProcessingError(
                f"Extreme compression failed: {e.stderr}",
                original_error=e
            )
    
    def generate_video_metadata(
        self,
        video_files: List[Path],
        merged_full: Path,
        merged_compressed: Path,
        video_index: VideoIndexCollection,
        compression_settings: CompressionSettings
    ) -> VideoMetadata:
        """
        Generate complete metadata for the processing pipeline.
        
        Args:
            video_files: Original video files
            merged_full: Full quality merged video
            merged_compressed: Compressed merged video
            video_index: Video boundary tracking
            compression_settings: Settings used for compression
            
        Returns:
            Complete VideoMetadata object
        """
        # Get info for all original videos
        original_videos = [
            self.processor.get_video_info(vf) for vf in video_files
        ]
        
        total_original_size = sum(v.size_mb for v in original_videos)
        compressed_size = self.processor.get_file_size(merged_compressed)
        
        return VideoMetadata(
            original_videos=original_videos,
            merged_full_path=merged_full,
            merged_compressed_path=merged_compressed,
            video_index=video_index,
            compression_settings=compression_settings,
            total_size_original_mb=total_original_size,
            size_compressed_mb=compressed_size,
            compression_ratio=total_original_size / compressed_size
        )