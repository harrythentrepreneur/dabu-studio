"""
Gemini API integration for RunPod worker
Handles video analysis and script matching
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime

logger = logging.getLogger(__name__)

class GeminiProcessor:
    """Handles Gemini API interactions for video analysis"""
    
    def __init__(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def analyze_video_with_script(
        self,
        video_path: str,
        script: str,
        target_duration: int
    ) -> Dict[str, Any]:
        """
        Analyze video and match script segments to timestamps
        
        Args:
            video_path: Path to video file
            script: Script text to match
            target_duration: Target duration in seconds
            
        Returns:
            Analysis results with timestamps
        """
        try:
            # Upload video to Gemini
            logger.info(f"Uploading video to Gemini: {video_path}")
            video_file = genai.upload_file(video_path)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(script, target_duration)
            
            # Generate response with structured output
            response = self.model.generate_content(
                [video_file, prompt],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    max_output_tokens=65536,
                    temperature=0.3
                )
            )
            
            # Parse response
            result = json.loads(response.text)
            
            # Validate timestamps
            if self._validate_timestamps(result, target_duration):
                return {
                    "status": "success",
                    "segments": result.get("segments", []),
                    "total_duration": result.get("total_duration", 0),
                    "analysis_metadata": {
                        "model": "gemini-2.0-flash-exp",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": "Invalid timestamps in Gemini response"
                }
                
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _create_analysis_prompt(self, script: str, target_duration: int) -> str:
        """Create prompt for Gemini analysis"""
        return f"""
        Analyze this video and match the following script to appropriate timestamps.
        
        SCRIPT (Target duration: {target_duration} seconds):
        {script}
        
        REQUIREMENTS:
        1. Find the BEST matching video segments for each script line
        2. Each segment should be 2-10 seconds long
        3. Total duration should be within ±15 seconds of {target_duration}
        4. Segments must not overlap
        5. Return timestamps in seconds (not frames)
        
        OUTPUT FORMAT:
        {{
            "segments": [
                {{
                    "text": "script line text",
                    "start": 0.0,
                    "end": 3.5,
                    "confidence": 0.95,
                    "visual_description": "what's happening in this segment"
                }}
            ],
            "total_duration": 35.0,
            "video_duration": 180.0
        }}
        
        IMPORTANT:
        - Match based on visual relevance, not just timing
        - Prioritize engaging, dynamic segments
        - Ensure smooth transitions between segments
        """
    
    def _validate_timestamps(self, result: Dict[str, Any], target_duration: int) -> bool:
        """Validate that timestamps are valid and within tolerance"""
        try:
            segments = result.get("segments", [])
            if not segments:
                return False
            
            # Check for overlaps and validity
            for i, segment in enumerate(segments):
                if segment["start"] < 0 or segment["end"] <= segment["start"]:
                    return False
                
                # Check for overlap with next segment
                if i < len(segments) - 1:
                    if segment["end"] > segments[i + 1]["start"]:
                        return False
            
            # Check total duration tolerance
            total = result.get("total_duration", 0)
            if abs(total - target_duration) > 15:
                logger.warning(f"Duration {total}s outside tolerance for target {target_duration}s")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def analyze_for_gifs(self, script: str) -> List[Dict[str, Any]]:
        """
        Analyze script to identify moments suitable for GIF creation
        
        Args:
            script: Script text to analyze
            
        Returns:
            List of GIF-worthy moments
        """
        try:
            prompt = f"""
            Analyze this script and identify 3-5 moments that would make great GIFs.
            
            SCRIPT:
            {script}
            
            For each moment, provide:
            1. The exact text/phrase
            2. Why it would make a good GIF
            3. Suggested duration (2-5 seconds)
            4. Visual style suggestions
            
            OUTPUT FORMAT:
            {{
                "gif_moments": [
                    {{
                        "text": "specific phrase",
                        "reason": "why this works as a GIF",
                        "duration": 3,
                        "style": "energetic/dramatic/funny/etc",
                        "loop_type": "bounce/repeat/reverse"
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            
            result = json.loads(response.text)
            return result.get("gif_moments", [])
            
        except Exception as e:
            logger.error(f"GIF analysis error: {e}")
            return []