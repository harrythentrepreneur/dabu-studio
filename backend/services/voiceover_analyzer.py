"""
Voiceover analyzer using OpenAI Whisper API.

This module handles voiceover transcription and segmentation using the
Whisper API, creating exact timing segments for video synchronization.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from utils.audio import AudioUtils
from utils.logger import get_logger
from utils.exceptions import VoiceoverAnalysisError, WhisperAPIError

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

logger = get_logger(__name__)


class VoiceoverSegment:
    """Represents a segment of the voiceover with timing information."""
    
    def __init__(self, text: str, start: float, end: float):
        self.text = text
        self.start = start
        self.end = end
        self.duration = end - start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'duration': self.duration
        }
    
    def __repr__(self) -> str:
        return f"VoiceoverSegment(text='{self.text[:30]}...', start={self.start:.2f}, duration={self.duration:.2f})"


class VoiceoverAnalyzer:
    """Analyzes voiceover audio files using Whisper API for segmentation."""
    
    def __init__(self):
        """Initialize the VoiceoverAnalyzer."""
        self.audio_utils = AudioUtils()
        
        # Get API key from environment
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key or self.api_key == 'sk-xxx':
            logger.warning(
                "OpenAI API key not configured. Voiceover analysis will not be available. "
                "Please set OPENAI_API_KEY in your .env file."
            )
            self.api_available = False
        else:
            self.api_available = True
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except ImportError:
                logger.error("OpenAI package not installed. Run: pip install openai")
                self.api_available = False
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.api_available = False
        
        # Get configuration from environment
        self.max_segment_duration = float(os.getenv('WHISPER_MAX_SEGMENT_DURATION', '7.0'))
        self.min_segment_duration = float(os.getenv('WHISPER_MIN_SEGMENT_DURATION', '2.5'))
        
        logger.info(
            f"VoiceoverAnalyzer initialized. "
            f"Segment duration range: {self.min_segment_duration}-{self.max_segment_duration}s"
        )
    
    def analyze_voiceover(
        self, 
        voiceover_path: Path, 
        script: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze voiceover audio and return segments with exact timing.
        
        Args:
            voiceover_path: Path to voiceover audio file
            script: Original script text (for reference/validation)
            
        Returns:
            List of segment dictionaries with timing information
            
        Raises:
            VoiceoverAnalysisError: If analysis fails
        """
        logger.info(f"Starting voiceover analysis for: {voiceover_path.name}")
        
        # Validate audio file
        if not self.audio_utils.validate_audio_file(voiceover_path):
            raise VoiceoverAnalysisError(
                f"Invalid audio file: {voiceover_path}",
                audio_path=str(voiceover_path)
            )
        
        # Get total duration for validation
        total_duration = self.audio_utils.get_audio_duration(voiceover_path)
        logger.info(f"Total voiceover duration: {total_duration:.2f} seconds")
        
        # Check if API is available
        if not self.api_available:
            logger.warning("Whisper API not available, using fallback segmentation")
            return self._create_fallback_segments(script, total_duration)
        
        try:
            # Transcribe with Whisper API
            segments = self._transcribe_with_whisper(voiceover_path)
            
            # Process and optimize segments
            processed_segments = self._process_segments(segments, total_duration)
            
            # Validate against script
            self._validate_against_script(processed_segments, script)
            
            # Final validation: ensure segments cover full duration
            segments_dict = [seg.to_dict() for seg in processed_segments]
            segments_total = sum(seg['duration'] for seg in segments_dict)
            
            # If segments don't cover full duration, extend the last one
            if segments_total < total_duration:
                gap = total_duration - segments_total
                logger.warning(
                    f"Final segments total {segments_total:.2f}s < audio {total_duration:.2f}s. "
                    f"Extending last segment by {gap:.2f}s"
                )
                if segments_dict:
                    segments_dict[-1]['duration'] += gap
                    segments_dict[-1]['end'] = segments_dict[-1]['start'] + segments_dict[-1]['duration']
                    
                    # Recalculate total
                    segments_total = sum(seg['duration'] for seg in segments_dict)
                    logger.info(f"Adjusted total: {segments_total:.2f}s")
            
            logger.info(f"Analysis complete: {len(segments_dict)} segments, total {segments_total:.2f}s")
            return segments_dict
            
        except Exception as e:
            logger.error(f"Voiceover analysis failed: {e}")
            raise VoiceoverAnalysisError(
                f"Failed to analyze voiceover: {str(e)}",
                audio_path=str(voiceover_path),
                details={'error': str(e)}
            )
    
    def _transcribe_with_whisper(self, audio_path: Path) -> List[Dict[str, Any]]:
        """
        Transcribe audio using Whisper API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of raw segments from Whisper
            
        Raises:
            WhisperAPIError: If API call fails
        """
        logger.info("Calling Whisper API for transcription...")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                # Call Whisper API with verbose_json for timing
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"]
                )
            
            # Extract segments from response
            if hasattr(response, 'segments'):
                segments = response.segments
            elif isinstance(response, dict) and 'segments' in response:
                segments = response['segments']
            else:
                raise WhisperAPIError(
                    "Unexpected response format from Whisper API",
                    response_data=response if isinstance(response, dict) else None
                )
            
            logger.info(f"Whisper returned {len(segments)} raw segments")
            
            # Convert to our format
            raw_segments = []
            for seg in segments:
                raw_segments.append({
                    'text': seg.get('text', '').strip(),
                    'start': float(seg.get('start', 0)),
                    'end': float(seg.get('end', 0))
                })
            
            return raw_segments
            
        except Exception as e:
            if 'api' in str(e).lower() or 'key' in str(e).lower():
                raise WhisperAPIError(f"Whisper API error: {str(e)}")
            raise
    
    def _process_segments(
        self, 
        raw_segments: List[Dict[str, Any]], 
        total_duration: float
    ) -> List[VoiceoverSegment]:
        """
        Process raw segments from Whisper, handling splits and merges.
        
        Args:
            raw_segments: Raw segments from Whisper
            total_duration: Total audio duration
            
        Returns:
            List of processed VoiceoverSegment objects
        """
        logger.info("Processing segments for optimal duration...")
        
        processed = []
        current_segment = None
        
        for raw_seg in raw_segments:
            if not raw_seg['text']:  # Skip empty segments
                continue
            
            segment_duration = raw_seg['end'] - raw_seg['start']
            
            # If segment is too long, split it
            if segment_duration > self.max_segment_duration:
                split_segments = self._split_long_segment(raw_seg)
                processed.extend(split_segments)
            
            # If segment is too short, consider merging
            elif segment_duration < self.min_segment_duration:
                if current_segment is None:
                    current_segment = VoiceoverSegment(
                        raw_seg['text'],
                        raw_seg['start'],
                        raw_seg['end']
                    )
                else:
                    # Merge with previous segment if combined duration is reasonable
                    combined_duration = raw_seg['end'] - current_segment.start
                    if combined_duration <= self.max_segment_duration:
                        current_segment.text += " " + raw_seg['text']
                        current_segment.end = raw_seg['end']
                        current_segment.duration = combined_duration
                    else:
                        # Save current and start new
                        processed.append(current_segment)
                        current_segment = VoiceoverSegment(
                            raw_seg['text'],
                            raw_seg['start'],
                            raw_seg['end']
                        )
            
            # Segment is in acceptable range
            else:
                if current_segment:
                    processed.append(current_segment)
                    current_segment = None
                
                processed.append(VoiceoverSegment(
                    raw_seg['text'],
                    raw_seg['start'],
                    raw_seg['end']
                ))
        
        # Don't forget the last segment if we were building one
        if current_segment:
            processed.append(current_segment)
        
        # Ensure segments cover the full duration
        if processed:
            segments_total = processed[-1].end
            
            # If there's a gap at the end (e.g., silence), extend the last segment
            if segments_total < total_duration:
                gap = total_duration - segments_total
                logger.info(
                    f"Extending last segment by {gap:.2f}s to match total duration "
                    f"({segments_total:.2f}s -> {total_duration:.2f}s)"
                )
                processed[-1].end = total_duration
                processed[-1].duration = processed[-1].end - processed[-1].start
            
            # Recalculate total after adjustment
            segments_total = sum(seg.duration for seg in processed)
            logger.info(f"Total segments duration: {segments_total:.2f}s (audio: {total_duration:.2f}s)")
            
            if abs(segments_total - total_duration) > 0.5:
                logger.warning(
                    f"Segments duration mismatch after adjustment: {segments_total:.2f}s vs {total_duration:.2f}s"
                )
        
        logger.info(
            f"Processed {len(processed)} segments. "
            f"Duration range: {min(s.duration for s in processed):.1f}-"
            f"{max(s.duration for s in processed):.1f}s"
        )
        
        return processed
    
    def _split_long_segment(self, segment: Dict[str, Any]) -> List[VoiceoverSegment]:
        """
        Split a long segment into smaller chunks.
        
        Args:
            segment: Segment to split
            
        Returns:
            List of split segments
        """
        text = segment['text']
        start = segment['start']
        end = segment['end']
        duration = end - start
        
        # Calculate number of splits needed
        num_splits = int(duration / self.max_segment_duration) + 1
        split_duration = duration / num_splits
        
        # Try to split at sentence boundaries if possible
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        splits = []
        
        if len(sentences) >= num_splits:
            # Split by sentences
            sentences_per_split = len(sentences) // num_splits
            for i in range(num_splits):
                start_idx = i * sentences_per_split
                if i == num_splits - 1:
                    # Last split gets remaining sentences
                    split_text = '. '.join(sentences[start_idx:]) + '.'
                else:
                    end_idx = start_idx + sentences_per_split
                    split_text = '. '.join(sentences[start_idx:end_idx]) + '.'
                
                split_start = start + (i * split_duration)
                split_end = start + ((i + 1) * split_duration) if i < num_splits - 1 else end
                
                splits.append(VoiceoverSegment(split_text, split_start, split_end))
        else:
            # Split by words if not enough sentences
            words = text.split()
            words_per_split = len(words) // num_splits
            
            for i in range(num_splits):
                start_idx = i * words_per_split
                if i == num_splits - 1:
                    split_text = ' '.join(words[start_idx:])
                else:
                    end_idx = start_idx + words_per_split
                    split_text = ' '.join(words[start_idx:end_idx])
                
                split_start = start + (i * split_duration)
                split_end = start + ((i + 1) * split_duration) if i < num_splits - 1 else end
                
                splits.append(VoiceoverSegment(split_text, split_start, split_end))
        
        logger.info(f"Split long segment ({duration:.1f}s) into {len(splits)} parts")
        return splits
    
    def _validate_against_script(
        self, 
        segments: List[VoiceoverSegment], 
        script: str
    ) -> None:
        """
        Validate transcribed segments against original script.
        
        Args:
            segments: Processed segments
            script: Original script text
            
        Note: This is a soft validation - warns but doesn't fail
        """
        # Combine all segment text
        transcribed_text = ' '.join(seg.text for seg in segments)
        
        # Basic similarity check (word count)
        script_words = len(script.split())
        transcribed_words = len(transcribed_text.split())
        
        word_diff_ratio = abs(script_words - transcribed_words) / script_words
        
        if word_diff_ratio > 0.2:  # More than 20% difference
            logger.warning(
                f"Significant difference between script and transcription: "
                f"Script={script_words} words, Transcribed={transcribed_words} words"
            )
        else:
            logger.info(f"Script validation passed: {transcribed_words} words transcribed")
    
    def _create_fallback_segments(
        self, 
        script: str, 
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Create fallback segments when Whisper API is not available.
        
        Args:
            script: Script text
            total_duration: Total audio duration
            
        Returns:
            List of segment dictionaries
        """
        logger.info("Creating fallback segments based on script and duration")
        
        # Split script into sentences
        sentences = script.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            # If no sentences, split by word count
            words = script.split()
            target_words_per_segment = 15  # Roughly 5 seconds of speech
            sentences = []
            for i in range(0, len(words), target_words_per_segment):
                sentences.append(' '.join(words[i:i+target_words_per_segment]))
        
        # Calculate duration per sentence
        duration_per_sentence = total_duration / len(sentences)
        
        # Create segments
        segments = []
        current_time = 0.0
        
        for sentence in sentences:
            # Adjust duration based on sentence length
            word_count = len(sentence.split())
            # Assume 150 words per minute speaking rate
            estimated_duration = (word_count / 150) * 60
            
            # Blend estimated with average
            actual_duration = (estimated_duration + duration_per_sentence) / 2
            
            # Enforce min/max limits
            actual_duration = max(self.min_segment_duration, 
                                 min(self.max_segment_duration, actual_duration))
            
            # Don't exceed total duration
            if current_time + actual_duration > total_duration:
                actual_duration = total_duration - current_time
            
            segments.append({
                'text': sentence,
                'start': current_time,
                'end': current_time + actual_duration,
                'duration': actual_duration
            })
            
            current_time += actual_duration
            
            if current_time >= total_duration:
                break
        
        # Adjust last segment to match total duration
        if segments and current_time < total_duration:
            segments[-1]['end'] = total_duration
            segments[-1]['duration'] = total_duration - segments[-1]['start']
        
        logger.info(f"Created {len(segments)} fallback segments")
        return segments
    
    def get_segment_summary(self, segments: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of the segments for logging/debugging.
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Summary string
        """
        if not segments:
            return "No segments"
        
        total_duration = segments[-1]['end'] if segments else 0
        durations = [s['duration'] for s in segments]
        
        summary = (
            f"Segments: {len(segments)}, "
            f"Total duration: {total_duration:.2f}s, "
            f"Avg duration: {sum(durations)/len(durations):.2f}s, "
            f"Range: {min(durations):.2f}-{max(durations):.2f}s"
        )
        
        return summary