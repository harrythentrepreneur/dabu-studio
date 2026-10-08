"""
Gemini Vision Service - Uses Gemini's vision capabilities to detect UI elements
Analyzes screenshots to find buttons, inputs, and other UI elements dynamically
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import google.generativeai as genai
from PIL import Image
import io

logger = logging.getLogger(__name__)


class GeminiVisionService:
    """
    Service that uses Gemini's vision capabilities to analyze UI screenshots
    and provide guidance for browser automation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini Vision Service
        
        Args:
            api_key: Gemini API key (uses env var if not provided)
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Use Gemini Pro Vision model
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        logger.info("Gemini Vision Service initialized")
    
    async def analyze_screenshot(self, screenshot_path: str, task: str) -> Dict[str, Any]:
        """
        Analyze a screenshot to find UI elements for a specific task
        
        Args:
            screenshot_path: Path to the screenshot image
            task: Description of what we're trying to do (e.g., "find upload button")
        
        Returns:
            Dictionary with element locations and guidance
        """
        try:
            # Load the image
            image = Image.open(screenshot_path)
            
            # Create a detailed prompt for Gemini
            prompt = f"""
            Analyze this screenshot of a web application (CapCut online editor).
            
            Task: {task}
            
            Please identify:
            1. The exact location (coordinates or description) of relevant UI elements
            2. Text content of buttons, links, or labels
            3. Whether the page is loaded properly
            4. Any error messages or popups
            5. Suggested next action
            
            Respond in JSON format with:
            {{
                "page_state": "login|signup|editor|loading|error",
                "elements_found": [
                    {{
                        "type": "button|input|link|icon",
                        "text": "visible text",
                        "location": "top-left|top-right|center|bottom|specific description",
                        "action": "click|fill|wait",
                        "selector_hint": "suggested CSS selector or text to search"
                    }}
                ],
                "next_action": "specific action to take",
                "confidence": 0.0-1.0,
                "notes": "any additional observations"
            }}
            """
            
            # Send to Gemini
            response = self.model.generate_content([prompt, image])
            
            # Parse the response
            result = self._parse_gemini_response(response.text)
            
            logger.info(f"Vision analysis complete for task: {task}")
            logger.info(f"Page state: {result.get('page_state')}, Confidence: {result.get('confidence')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot: {e}")
            return {
                "error": str(e),
                "page_state": "unknown",
                "elements_found": [],
                "next_action": "retry",
                "confidence": 0.0
            }
    
    async def guide_interaction(self, screenshot_path: str, current_step: str) -> Dict[str, Any]:
        """
        Provide specific guidance for the current step in the workflow
        
        Args:
            screenshot_path: Path to current screenshot
            current_step: Current step in the workflow (login, upload, caption, export)
        
        Returns:
            Detailed guidance for the next action
        """
        step_tasks = {
            "login": "Find and click the login button or email input field",
            "upload": "Find the upload button or file input to add a video",
            "caption": "Find the captions or subtitles button to add auto-captions",
            "style": "Find and select the TikTok Bold caption style",
            "export": "Find the export or download button to save the video"
        }
        
        task = step_tasks.get(current_step, "Identify the current page state")
        
        result = await self.analyze_screenshot(screenshot_path, task)
        
        # Add specific guidance based on the step
        if current_step == "login" and result.get("page_state") == "login":
            result["specific_guidance"] = {
                "action": "fill_credentials",
                "email_selector": self._find_element_by_type(result, "input", "email"),
                "password_selector": self._find_element_by_type(result, "input", "password"),
                "submit_selector": self._find_element_by_type(result, "button", "submit|login|sign")
            }
        elif current_step == "upload" and result.get("page_state") == "editor":
            result["specific_guidance"] = {
                "action": "upload_video",
                "upload_selector": self._find_element_by_type(result, "button", "upload|import|add"),
                "file_input_hint": "Look for input[type='file'] after clicking upload"
            }
        elif current_step == "caption":
            result["specific_guidance"] = {
                "action": "add_captions",
                "caption_selector": self._find_element_by_type(result, "button", "caption|subtitle|text"),
                "auto_caption_selector": self._find_element_by_type(result, "button", "auto|generate|transcribe")
            }
        
        return result
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini's response, handling both JSON and text formats
        """
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: parse text response
        result = {
            "page_state": "unknown",
            "elements_found": [],
            "next_action": "unknown",
            "confidence": 0.5,
            "notes": response_text
        }
        
        # Try to extract key information from text
        lower_text = response_text.lower()
        if "login" in lower_text or "sign in" in lower_text:
            result["page_state"] = "login"
        elif "editor" in lower_text or "workspace" in lower_text:
            result["page_state"] = "editor"
        elif "loading" in lower_text:
            result["page_state"] = "loading"
        
        return result
    
    def _find_element_by_type(self, result: Dict, element_type: str, text_pattern: str) -> Optional[str]:
        """
        Find an element in the result by type and text pattern
        """
        elements = result.get("elements_found", [])
        for element in elements:
            if element.get("type") == element_type:
                element_text = element.get("text", "").lower()
                if any(pattern in element_text for pattern in text_pattern.split("|")):
                    return element.get("selector_hint", element.get("text"))
        return None
    
    async def find_clickable_coordinates(self, screenshot_path: str, button_text: str) -> Optional[Tuple[int, int]]:
        """
        Find approximate coordinates for a button with specific text
        
        Args:
            screenshot_path: Path to screenshot
            button_text: Text of the button to find
        
        Returns:
            Tuple of (x, y) coordinates or None
        """
        try:
            image = Image.open(screenshot_path)
            width, height = image.size
            
            prompt = f"""
            Find the button or clickable element with text "{button_text}" in this screenshot.
            
            Provide the approximate position as a percentage of the image dimensions.
            For example: if the button is in the center, return x=50, y=50
            If it's in the top-right, return x=90, y=10
            
            Respond with just the coordinates in format:
            x=XX, y=YY
            
            If the button is not found, respond with:
            not found
            """
            
            response = self.model.generate_content([prompt, image])
            text = response.text.strip().lower()
            
            if "not found" in text:
                return None
            
            # Parse coordinates
            import re
            match = re.search(r'x=(\d+),?\s*y=(\d+)', text)
            if match:
                x_percent = int(match.group(1))
                y_percent = int(match.group(2))
                
                # Convert to actual coordinates
                x = int(width * x_percent / 100)
                y = int(height * y_percent / 100)
                
                logger.info(f"Found '{button_text}' at coordinates ({x}, {y})")
                return (x, y)
            
        except Exception as e:
            logger.error(f"Error finding coordinates: {e}")
        
        return None