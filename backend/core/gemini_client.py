"""
Clean implementation of Gemini client with proper error handling.
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import google.generativeai as genai
from google.generativeai import types

from utils.logger import get_logger
from utils.exceptions import GeminiAPIError, GeminiProcessingError, JSONParseError
from models.schemas import GeminiResponse

logger = get_logger(__name__)


class GeminiClient:
    """Enhanced Gemini client with robust structured output and error handling."""
    
    # Gemini 2.5 Pro supports up to 65,536 output tokens (64K)
    MAX_OUTPUT_TOKENS = 65536
    DEFAULT_OUTPUT_TOKENS = 16384  # Conservative default for most use cases
    MIN_OUTPUT_TOKENS = 8192  # Minimum for basic responses
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client with optimal configuration."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        logger.info("GeminiClient initialized with Gemini 2.5 Pro")
        logger.info(f"Max output tokens available: {self.MAX_OUTPUT_TOKENS}")
    
    def create_voiceover_prompt(self, voiceover_segments: List[Dict], video_duration: str, script: str) -> str:
        """Create prompt for voiceover mode with exact durations."""
        segments_text = ""
        total_duration = 0
        
        for i, seg in enumerate(voiceover_segments, 1):
            segments_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEGMENT {i} - MANDATORY DURATION: {seg['duration']:.2f} seconds
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Voiceover text: "{seg['text']}"

YOUR RESPONSE FOR THIS SEGMENT MUST HAVE:
• segment_number: {i}
• segment_text: "{seg['text']}"
• duration_seconds: {seg['duration']:.2f}  ← THIS EXACT VALUE, NOT CALCULATED
• start_timestamp: [your chosen location in video]
• end_timestamp: [start + {seg['duration']:.2f} seconds]

FIND: The best {seg['duration']:.2f}-second continuous section for this voiceover
"""
            total_duration += seg['duration']
        
        # Create a duration reference table
        duration_table = "DURATION REFERENCE TABLE (USE THESE EXACT VALUES):\n"
        duration_table += "Segment | Text Preview | EXACT duration_seconds to use\n"
        duration_table += "─" * 60 + "\n"
        for i, seg in enumerate(voiceover_segments, 1):
            text_preview = seg['text'][:30] + "..." if len(seg['text']) > 30 else seg['text']
            duration_table += f"{i:7} | {text_preview:30} | {seg['duration']:.2f}\n"
        
        return f"""
YOUR TASK: Find the BEST video sections for a voiceover that is ALREADY RECORDED.

⚠️ THE VOICEOVER DURATIONS ARE FIXED - YOU CANNOT CHANGE THEM ⚠️

{duration_table}

VIDEO: Duration {video_duration}
TOTAL SEGMENTS: {len(voiceover_segments)}
TOTAL DURATION: {total_duration:.2f} seconds (this adds up the durations above)

FOR EACH SEGMENT BELOW, FIND THE BEST MATCHING SECTION:{segments_text}

HOW TO EVALUATE EACH SECTION:

1. WATCH THE ENTIRE DURATION (Most Important):
   - Does the WHOLE section support the voiceover, not just the beginning?
   - Are there any jarring cuts or unrelated content within the duration?
   - Does the visual story flow naturally for the entire segment length?
   - Would trimming at exactly X seconds create a complete, coherent visual?

2. VISUAL RELEVANCE THROUGHOUT:
   - Beginning: Strong opening that matches the voiceover start
   - Middle: Continues to support the message (no random unrelated shots)
   - End: Natural conclusion or transition point at the exact duration mark
   - Example: For "massive anxiety spike" (6.92s), find 6.92 seconds of continuous anxiety/stress visuals

2. QUALITY INDICATORS:
   - Sharp, in-focus footage (avoid blurry segments)
   - Good lighting and visibility
   - Stable camera work (unless motion adds to the story)
   - Professional-looking content

3. ENGAGEMENT FACTORS:
   - Hook moments (surprising reveals, transformations)
   - Visual progression that tells a story
   - High-energy or visually striking content
   - Faces/reactions when discussing emotions or results
   - Before/after visuals for transformation claims

4. AVOID:
   - Repetitive or static shots
   - Irrelevant b-roll that doesn't match the narrative
   - Low-quality, dark, or unclear footage
   - Segments where nothing meaningful happens

SEARCH STRATEGY:
1. For each voiceover segment, scan the ENTIRE video
2. Identify ALL possible sections of that exact duration
3. Evaluate each section for its COMPLETE duration:
   - Does second 1 to second X tell a coherent visual story?
   - Is there consistent relevance throughout?
   - Any distracting or off-topic moments within the duration?
4. Choose the section where the ENTIRE duration best supports the voiceover
5. Remember: You're extracting a continuous chunk - make sure it works from start to finish

⚠️ CRITICAL - YOUR RESPONSE MUST FOLLOW THIS EXACT FORMAT:

For EVERY segment, you MUST return these EXACT duration_seconds values:
{chr(10).join(f'• Segment {i+1}: duration_seconds = {seg["duration"]:.2f}' for i, seg in enumerate(voiceover_segments))}

DO NOT:
- Calculate duration from timestamps (I will do that)
- Round or modify these durations
- Use your own duration calculations

DO:
- Copy the exact duration_seconds values listed above
- Find the best visual match for that exact duration
- Set end_timestamp = start_timestamp + duration_seconds

EXAMPLE - If I say segment 3 must be 4.38 seconds:
✅ CORRECT: "duration_seconds": 4.38
❌ WRONG: "duration_seconds": 4.0
❌ WRONG: "duration_seconds": 5.2

REMEMBER: The voiceover audio is already recorded. These durations are FIXED and CANNOT change. If you return different durations, the video will be out of sync with the audio.

CRITICAL WARNING: If you return different durations than what I specified, the video will be out of sync with the voiceover. The durations are FIXED by the voiceover audio and CANNOT be changed.

EXAMPLE OF CORRECT RESPONSE:
If I say Segment 1 must be 4.04 seconds, you MUST return:
{{
  "segment_number": 1,
  "duration_seconds": 4.04,  // EXACTLY what I specified
  "start_timestamp": "00:03:24.500",  // Your chosen visual match location
  "end_timestamp": "00:03:28.540",  // start + 4.04 seconds
  ...
}}

REMEMBER: Find the BEST visual match location, but ALWAYS use my exact duration.
"""
    
    def create_standard_prompt(self, script: str, video_duration: str, target_duration: float) -> str:
        """Create prompt for standard mode."""
        # Estimate optimal segment count
        avg_segment_duration = 6.0  # Average between 5-8 seconds
        estimated_segments = int(target_duration / avg_segment_duration)
        estimated_segments = max(4, min(estimated_segments, 12))  # Reasonable bounds
        
        return f"""
Analyze this video to find the ABSOLUTE BEST visual segments that bring this TikTok ad script to life.

VIDEO: Duration {video_duration}
TARGET: {target_duration} seconds total

SCRIPT TO SEGMENT:
{script}

YOUR MISSION: Create a visually compelling TikTok ad by finding the BEST possible video segments.

SEGMENTATION STRATEGY:
1. Break the script into {estimated_segments} logical narrative chunks (5-8 seconds each)
2. Each chunk should represent a complete thought or selling point
3. Consider natural pauses and emphasis points in the script

FOR EACH SEGMENT, FIND VISUALS THAT:

1. DIRECTLY ILLUSTRATE THE MESSAGE:
   - Literal representation ("app" → show the app interface)
   - Metaphorical match ("breakthrough" → dramatic reveal/transformation)
   - Emotional resonance ("frustrated" → show frustration visually)

2. MAXIMIZE VISUAL IMPACT:
   - Opening hook: Find the most attention-grabbing visual for the first 3 seconds
   - Problem visualization: Show relatable pain points clearly
   - Solution demonstration: Crystal-clear product/service shots
   - Results/benefits: Visual proof, transformations, happy reactions
   - Call-to-action: Compelling final visual that motivates action

3. QUALITY CRITERIA:
   - Sharp, well-lit, professional footage
   - Dynamic movement or visual interest
   - Clear subject focus (no cluttered frames)
   - Smooth transitions between segments

4. ENGAGEMENT OPTIMIZATION:
   - Prioritize "scroll-stopping" moments
   - Include faces/emotions for human connection
   - Show transformations or before/after when relevant
   - Use variety - mix close-ups, wide shots, action shots
   - Avoid repetitive or boring visuals

5. SEARCH THE ENTIRE VIDEO:
   - Don't settle for the first match - scan everything
   - Compare multiple options for each segment
   - Consider how segments flow together as a story
   - Think about pacing - mix high and low energy appropriately

AVOID:
- Generic b-roll that doesn't advance the story
- Poor quality, dark, or shaky footage
- Segments with no clear focal point
- Visuals that contradict or distract from the message

REQUIREMENTS:
1. Create exactly {estimated_segments} segments (5-8 seconds each)
2. Total duration should equal {target_duration} seconds (±3 seconds)
3. Confidence score (0.0-1.0) should reflect visual-script alignment quality
4. Use specific, concise descriptions (max 150 chars)
5. Format timestamps as HH:MM:SS.mmm
6. Each segment must have ALL required fields

REMEMBER: This is for TikTok - every frame must earn attention. Choose visuals that make people stop scrolling and watch.
"""
    
    def upload_to_gemini(self, video_path: Path) -> types.File:
        """Upload video to Gemini."""
        logger.info(f"Uploading video: {video_path.name}")
        
        video_file = genai.upload_file(
            path=str(video_path),
            mime_type='video/mp4',
            display_name=video_path.name
        )
        
        # Wait for processing
        while video_file.state.name == "PROCESSING":
            logger.info("Processing video...")
            time.sleep(5)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise GeminiAPIError(f"Video processing failed: {video_file.state}")
        
        logger.info(f"Video ready: {video_file.uri}")
        return video_file
    
    def get_gemini_response_with_json(
        self,
        video_file: types.File,
        script: str,
        target_duration: float = 35.0,
        voiceover_segments: Optional[List[Dict]] = None,
        max_retries: int = 3
    ) -> GeminiResponse:
        """Get Gemini response with structured output."""
        
        # Create prompt based on mode
        if voiceover_segments:
            prompt = self.create_voiceover_prompt(voiceover_segments, "00:20:00", script)
            logger.info(f"Using voiceover mode with {len(voiceover_segments)} segments")
        else:
            prompt = self.create_standard_prompt(script, "00:20:00", target_duration)
            logger.info("Using standard mode")
        
        # Simplified schema for Gemini API compatibility
        # Gemini has limited JSON Schema support - avoiding unsupported fields
        response_schema = {
            "type": "object",
            "properties": {
                "segments": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "num": {"type": "integer"},
                            "text": {"type": "string"},
                            "start": {"type": "string"},  # Removed pattern validation
                            "end": {"type": "string"},    # Removed pattern validation
                            "duration": {"type": "number"},
                            "confidence": {"type": "number"},
                            "description": {"type": "string"}
                        },
                        "required": ["num", "text", "start", "end", "duration", "confidence", "description"]
                    }
                },
                "total_dur": {"type": "number"},
                "target_dur": {"type": "number"}
            },
            "required": ["segments", "total_dur", "target_dur"]
        }
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries}")
                
                # Calculate optimal token limit based on expected segments
                expected_segments = len(voiceover_segments) if voiceover_segments else 8
                # More accurate estimation: ~800-1000 tokens per segment for detailed responses
                # Each segment needs: text, timestamps, description, confidence, etc.
                tokens_per_segment = 1000
                overhead_tokens = 2000  # For structure, metadata, etc.
                
                # Calculate required tokens with safety margin
                required_tokens = (expected_segments * tokens_per_segment) + overhead_tokens
                
                # Use progressive token allocation based on needs
                if required_tokens <= self.MIN_OUTPUT_TOKENS:
                    output_tokens = self.MIN_OUTPUT_TOKENS
                elif required_tokens <= self.DEFAULT_OUTPUT_TOKENS:
                    output_tokens = self.DEFAULT_OUTPUT_TOKENS
                else:
                    # For large requests, use up to max but with reasonable bounds
                    output_tokens = min(required_tokens * 1.5, self.MAX_OUTPUT_TOKENS)
                
                logger.info(f"Token allocation: {output_tokens} tokens for {expected_segments} segments")
                logger.info(f"(Required: {required_tokens}, Max available: {self.MAX_OUTPUT_TOKENS})")
                
                # Generate content with structured output and optimal configuration
                # Following best practices from https://ai.google.dev/gemini-api/docs/structured-output
                generation_config = {
                    "temperature": 0.2,  # Lower for more deterministic JSON structure
                    "top_p": 0.8,  # Reduce randomness
                    "top_k": 40,  # Focus on likely tokens
                    "max_output_tokens": output_tokens,
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                    "candidate_count": 1  # Single response for consistency
                }
                
                logger.debug(f"Generation config: temp={generation_config['temperature']}, tokens={output_tokens}")
                
                response = self.model.generate_content(
                    [video_file, prompt],
                    generation_config=generation_config,
                    safety_settings={
                        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
                        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
                        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE"
                    }
                )
                
                response_text = response.text.strip()
                logger.info(f"Response: {len(response_text)} chars, tokens: ~{len(response_text)//4}")
                
                # Comprehensive response validation
                if not response_text:
                    raise GeminiAPIError("Empty response from Gemini API")
                
                if len(response_text) < 50:  # Suspiciously short
                    raise GeminiAPIError(f"Response too short ({len(response_text)} chars): {response_text[:100]}")
                
                # Check for truncation indicators
                is_truncated = self._detect_truncation(response_text)
                if is_truncated:
                    logger.warning(f"Detected truncated response. Attempting recovery...")
                    response_text = self._complete_json_advanced(response_text)
                
                # Parse and validate JSON
                try:
                    response_data = json.loads(response_text)
                    
                    # Transform to expected format if needed
                    transformed_data = self._transform_response_format(response_data, target_duration)
                    
                    # Validate with Pydantic model
                    gemini_response = GeminiResponse(**transformed_data)
                    
                    # Validate segment count
                    segment_count = len(gemini_response.script_segments)
                    logger.info(f"Successfully parsed {segment_count} segments")
                    
                    if voiceover_segments and segment_count != len(voiceover_segments):
                        logger.warning(f"Segment count mismatch: expected {len(voiceover_segments)}, got {segment_count}")
                    
                    return gemini_response
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error on attempt {attempt + 1}: {e}")
                    logger.error(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                    logger.error(f"Response text (first 500 chars): {response_text[:500]}...")
                    logger.error(f"Response text (last 100 chars): ...{response_text[-100:]}")
                    
                    # Show context around error position
                    if hasattr(e, 'pos'):
                        error_pos = e.pos
                        context_start = max(0, error_pos - 100)
                        context_end = min(len(response_text), error_pos + 100)
                        logger.error(f"Context around error: ...{response_text[context_start:context_end]}...")
                    
                    # Try aggressive JSON recovery before last attempt
                    if attempt < max_retries - 1:
                        logger.info("Attempting aggressive JSON recovery...")
                        try:
                            # Try to complete the JSON structure
                            completed_json = self._complete_json_advanced(response_text)
                            response_data = json.loads(completed_json)
                            transformed_data = self._transform_response_format(response_data, target_duration)
                            logger.info("JSON recovery successful!")
                            return GeminiResponse(**transformed_data)
                        except Exception as recovery_error:
                            logger.warning(f"JSON recovery failed: {recovery_error}")
                    
                    # On last attempt, try advanced fallback recovery
                    if attempt == max_retries - 1:
                        logger.warning("Final attempt failed, trying fallback recovery")
                        segments = self._extract_segments_fallback(response_text)
                        if segments:
                            response_data = {
                                'script_segments': segments,
                                'total_duration': sum(s['duration_seconds'] for s in segments),
                                'target_duration': target_duration
                            }
                            logger.info(f"Fallback recovery successful: {len(segments)} segments")
                            return GeminiResponse(**response_data)
                        else:
                            logger.error("Fallback recovery failed - no segments extracted")
                    
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"Attempt {attempt + 1} failed ({error_type}): {e}")
                
                # Log additional context for debugging
                if hasattr(e, 'response'):
                    logger.error(f"API response status: {getattr(e.response, 'status_code', 'unknown')}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying attempt {attempt + 2}/{max_retries} in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {error_type}: {e}")
        
        # If we get here, all attempts failed
        error_msg = f"Failed to get valid response after {max_retries} attempts"
        logger.error(error_msg)
        raise GeminiProcessingError(error_msg)
    
    def _detect_truncation(self, text: str) -> bool:
        """Detect if response appears to be truncated using multiple indicators."""
        indicators = [
            not text.rstrip().endswith('}'),  # Missing closing brace
            text.count('{') > text.count('}'),  # Unbalanced braces
            text.count('[') > text.count(']'),  # Unbalanced brackets
            '"segments"' in text and '"total_dur"' not in text,  # Missing required fields
            text.endswith(',') or text.endswith('"'),  # Ends mid-structure
            len(text) < 100 and '"segments"' not in text,  # Too short for valid response
        ]
        
        truncated = any(indicators)
        if truncated:
            logger.warning(f"Truncation indicators: {sum(indicators)}/6 detected")
        
        return truncated
    
    def _complete_json_advanced(self, text: str) -> str:
        """Advanced JSON completion with better structure detection."""
        import re
        
        logger.info(f"Attempting to complete truncated JSON ({len(text)} chars)")
        
        # First, handle unterminated strings - the most common truncation issue
        # Find the last string field that might be unterminated
        string_pattern = r'"([^"]*?)"\s*:\s*"([^"]*?)$'
        match = re.search(string_pattern, text)
        if match:
            # Found potential unterminated string
            logger.debug(f"Found potential unterminated string at position {match.start()}")
            # Close the string and remove any partial content after it
            text = text[:match.end()] + '"'
            logger.info("Closed unterminated string")
        
        # Remove any trailing incomplete content
        text = re.sub(r'[,\s]*$', '', text)
        
        # Count structural elements
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # Handle incomplete strings (secondary check)
        quote_matches = list(re.finditer(r'(?<!\\)"', text))
        if len(quote_matches) % 2 == 1:  # Odd number of quotes = unclosed string
            text += '"'
            logger.debug("Added closing quote")
        
        # Try to detect if we're in the middle of an object
        # Look for the last complete segment
        segment_pattern = r'\{[^}]*?"num"\s*:\s*\d+[^}]*?\}'
        segments = list(re.finditer(segment_pattern, text))
        if segments:
            last_complete_segment = segments[-1]
            # Check if there's incomplete content after the last segment
            remaining = text[last_complete_segment.end():].strip()
            if remaining and not remaining.startswith(']') and not remaining.startswith(','):
                # There's incomplete segment data, remove it
                text = text[:last_complete_segment.end()]
                logger.info("Removed incomplete segment data")
        
        # Ensure required fields are present
        if '"segments"' in text:
            # Close segments array if needed
            if open_brackets > 0:
                text += ']' * open_brackets
                logger.debug(f"Added {open_brackets} closing brackets")
            
            # Add missing summary fields with sensible defaults
            required_fields = [('total_dur', '35.0'), ('target_dur', '35.0')]
            for field, default_value in required_fields:
                if f'"{field}"' not in text:
                    # Add comma if needed
                    if not text.rstrip().endswith(',') and not text.rstrip().endswith('{'):
                        text += ','
                    text += f'"{field}":{default_value}'
                    logger.debug(f"Added missing field: {field}")
        
        # Close remaining objects
        if open_braces > 0:
            text += '}' * open_braces
            logger.debug(f"Added {open_braces} closing braces")
        
        logger.info(f"Completed JSON structure ({len(text)} chars)")
        return text
    
    def _transform_response_format(self, data: Dict, target_duration: float) -> Dict:
        """Transform response to match expected GeminiResponse format."""
        # Handle both old and new schema formats
        if 'segments' in data:
            # New optimized format - transform to old format
            transformed_segments = []
            for i, seg in enumerate(data['segments']):
                transformed_seg = {
                    'segment_number': seg.get('num', i + 1),
                    'segment_text': seg['text'],
                    'start_timestamp': seg['start'],
                    'end_timestamp': seg['end'],
                    'duration_seconds': seg['duration'],
                    'confidence': seg['confidence'],
                    'visual_description': seg['description']
                }
                transformed_segments.append(transformed_seg)
            
            return {
                'script_segments': transformed_segments,
                'total_duration': data.get('total_dur', target_duration),
                'target_duration': data.get('target_dur', target_duration)
            }
        else:
            # Already in expected format
            return data
    
    def _extract_segments_fallback(self, text: str) -> List[Dict]:
        """Advanced fallback to extract segments from malformed JSON."""
        import re
        segments = []
        logger.info("Attempting fallback segment extraction...")
        
        # Try multiple patterns for different schema formats
        patterns = [
            # New optimized format
            r'"num"\s*:\s*(\d+).*?"duration"\s*:\s*([\d.]+)',
            # Old format
            r'"segment_number"\s*:\s*(\d+).*?"duration_seconds"\s*:\s*([\d.]+)',
            # Partial format
            r'"\d+".*?"duration"\s*:\s*([\d.]+)',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.DOTALL))
            if matches:
                logger.info(f"Found {len(matches)} matches with pattern: {pattern[:50]}...")
                break
        else:
            logger.warning("No segment patterns found in response")
            return segments
        
        for i, match in enumerate(matches):
            try:
                # Extract basic info
                if len(match.groups()) >= 2:
                    seg_num = int(match.group(1))
                    duration = float(match.group(2))
                else:
                    seg_num = i + 1
                    duration = float(match.group(1)) if match.groups() else 5.0
                
                # Extract surrounding context for more fields
                start_pos = max(0, match.start() - 1000)
                end_pos = min(len(text), match.end() + 1000)
                chunk = text[start_pos:end_pos]
                
                # Build segment with defaults
                segment = {
                    'segment_number': seg_num,
                    'duration_seconds': duration,
                    'segment_text': f"Recovered segment {seg_num}",
                    'start_timestamp': "00:00:00.000",
                    'end_timestamp': f"00:00:{duration:06.3f}",
                    'confidence': 0.7,  # Lower confidence for recovered data
                    'visual_description': "Content recovered from partial response"
                }
                
                # Try to extract more specific fields
                field_patterns = {
                    'segment_text': r'"(?:text|segment_text)"\s*:\s*"([^"]{1,200})"',
                    'visual_description': r'"(?:description|visual_description)"\s*:\s*"([^"]{1,200})"',
                    'start_timestamp': r'"(?:start|start_timestamp)"\s*:\s*"([\d:.]*)"',
                    'end_timestamp': r'"(?:end|end_timestamp)"\s*:\s*"([\d:.]*)"',
                    'confidence': r'"confidence"\s*:\s*([\d.]+)',
                }
                
                for field, field_pattern in field_patterns.items():
                    match_field = re.search(field_pattern, chunk)
                    if match_field:
                        value = match_field.group(1)
                        if field == 'confidence':
                            segment[field] = min(1.0, max(0.0, float(value)))
                        else:
                            segment[field] = value
                
                segments.append(segment)
                logger.debug(f"Recovered segment {seg_num}: {duration}s - {segment['segment_text'][:50]}...")
                
            except (ValueError, AttributeError, IndexError) as e:
                logger.warning(f"Failed to parse segment {i + 1}: {e}")
                continue
        
        logger.info(f"Fallback extraction completed: {len(segments)} segments recovered")
        return segments
    
    def analyze_video_segments(self, video_path: Path, script: str, 
                              target_duration: float = 35.0, 
                              voiceover_segments: Optional[List[Dict]] = None) -> GeminiResponse:
        """Main entry point for video segment analysis with comprehensive error handling."""
        logger.info(f"Starting video analysis: {video_path.name}")
        logger.info(f"Script length: {len(script)} chars")
        logger.info(f"Target duration: {target_duration}s")
        logger.info(f"Mode: {'voiceover' if voiceover_segments else 'standard'}")
        
        try:
            # Upload video
            video_file = self.upload_to_gemini(video_path)
            
            # Process with retries
            result = self.get_gemini_response_with_json(
                video_file=video_file,
                script=script,
                target_duration=target_duration,
                voiceover_segments=voiceover_segments,
                max_retries=3
            )
            
            logger.info(f"Analysis completed successfully: {len(result.script_segments)} segments")
            return result
            
        except Exception as e:
            logger.error(f"Video analysis failed: {type(e).__name__}: {e}")
            raise GeminiProcessingError(f"Failed to analyze video segments: {e}") from e