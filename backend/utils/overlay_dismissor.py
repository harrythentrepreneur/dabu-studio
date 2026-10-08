"""
Intelligent Overlay Dismissor using Gemini Vision.
Detects and dismisses blocking overlays in web interfaces.
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Literal
import google.generativeai as genai
from playwright.async_api import Page, ElementHandle
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not available

logger = logging.getLogger(__name__)

class IntelligentOverlayDismissor:
    """Uses Gemini Vision to intelligently detect and dismiss blocking overlays."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        logger.info("IntelligentOverlayDismissor initialized with Gemini 2.5 Flash Lite")
    
    async def analyze_and_dismiss_overlays(self, page: Page, request_id: str) -> bool:
        """
        Analyze page for blocking overlays and dismiss them intelligently.
        
        Returns:
            True if overlays were found and dismissed, False if no blocking overlays
        """
        try:
            logger.info("🔍 Analyzing page for blocking overlays...")
            
            # Take screenshot for Gemini analysis
            screenshot_path = Path(f"temp_overlay_analysis_{request_id}.png")
            await page.screenshot(path=str(screenshot_path))
            
            # Analyze with Gemini Vision (with timeout)
            try:
                overlay_info = await asyncio.wait_for(
                    self._analyze_overlays_with_gemini(screenshot_path), 
                    timeout=10.0  # 10 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning("Gemini analysis timed out, using fallback detection")
                overlay_info = {
                    "has_blocking_overlay": True,
                    "overlay_type": "UNKNOWN",
                    "description": "Analysis timed out",
                    "has_close_button": True,
                    "button_texts": ["OK", "Got it", "Skip", "Next"]
                }
            
            if overlay_info['has_blocking_overlay']:
                logger.info(f"🚫 Blocking overlay detected: {overlay_info['overlay_type']}")
                success = await self._dismiss_detected_overlays(page, overlay_info)
                
                # Clean up temp file
                if screenshot_path.exists():
                    screenshot_path.unlink()
                
                return success
            else:
                logger.info("✅ No blocking overlays detected")
                if screenshot_path.exists():
                    screenshot_path.unlink()
                return False
                
        except Exception as e:
            logger.error(f"Error in overlay analysis: {e}")
            return False
    
    async def _analyze_overlays_with_gemini(self, screenshot_path: Path) -> Dict:
        """Use Gemini Vision to analyze screenshot for blocking overlays."""
        try:
            prompt = """
            Analyze this CapCut web interface screenshot and determine if there are blocking overlays.
            
            Look for:
            1. Guide overlays (yellow/blue coach marks with "Got it", "Next", "Skip" buttons)
            2. Tutorial popups (blocking the main interface)
            3. Modal dialogs (covering content)
            4. Welcome screens (first-time user experience)
            
            Respond with ONLY this JSON format:
            {
                "has_blocking_overlay": true/false,
                "overlay_type": "GUIDE" | "TUTORIAL" | "MODAL" | "WELCOME" | "NONE",
                "description": "Brief description of what's visible",
                "has_close_button": true/false,
                "button_texts": ["text1", "text2"] // visible button texts
            }
            """
            
            uploaded_file = genai.upload_file(str(screenshot_path))
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.text)
                logger.info(f"Gemini analysis result: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning("Failed to parse Gemini JSON response, using fallback")
                return {
                    "has_blocking_overlay": True,  # Assume blocking if we can't parse
                    "overlay_type": "UNKNOWN",
                    "description": "Fallback detection",
                    "has_close_button": True,
                    "button_texts": ["OK", "Got it", "Skip", "Next"]
                }
                
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
            return {
                "has_blocking_overlay": True,
                "overlay_type": "UNKNOWN",
                "description": "Analysis failed",
                "has_close_button": True,
                "button_texts": ["OK", "Got it", "Skip", "Next"]
            }
    
    async def _dismiss_detected_overlays(self, page: Page, overlay_info: Dict) -> bool:
        """Dismiss detected overlays using multiple strategies."""
        try:
            logger.info(f"🎯 Attempting to dismiss {overlay_info['overlay_type']} overlay...")
            
            # Strategy 1: Look for close buttons with specific text
            if overlay_info.get('button_texts'):
                for button_text in overlay_info['button_texts']:
                    try:
                        # Try multiple selectors for buttons
                        selectors = [
                            f'button:has-text("{button_text}")',
                            f'[role="button"]:has-text("{button_text}")',
                            f'div:has-text("{button_text}")',
                            f'span:has-text("{button_text}")'
                        ]
                        
                        for selector in selectors:
                            try:
                                button = await page.wait_for_selector(selector, timeout=2000)
                                if button:
                                    logger.info(f"Found button: {button_text}")
                                    await button.click()
                                    await page.wait_for_timeout(1000)
                                    
                                    # Check if overlay is gone
                                    if not await self._has_blocking_overlay(page):
                                        logger.info("✅ Overlay dismissed successfully")
                                        return True
                                    break
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"Failed to click button {button_text}: {e}")
                        continue
            
            # Strategy 2: Try common close button selectors
            close_selectors = [
                '[aria-label="Close"]',
                '[title="Close"]',
                '.close-button',
                '.close-btn',
                '.modal-close',
                '.overlay-close',
                'button[class*="close"]',
                'div[class*="close"]'
            ]
            
            for selector in close_selectors:
                try:
                    close_btn = await page.query_selector(selector)
                    if close_btn:
                        await close_btn.click()
                        await page.wait_for_timeout(1000)
                        if not await self._has_blocking_overlay(page):
                            logger.info("✅ Overlay dismissed via close button")
                            return True
                except:
                    continue
            
            # Strategy 3: JavaScript removal of common overlay classes
            await page.evaluate("""
                // Remove guide overlays
                document.querySelectorAll('[class*="guide"], [class*="tutorial"], [class*="overlay"]').forEach(el => {
                    if (el && el.parentNode) {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' || style.zIndex > 100) {
                            el.remove();
                        }
                    }
                });
                
                // Remove modal dialogs
                document.querySelectorAll('[role="dialog"], .modal, .popup').forEach(el => {
                    if (el && el.parentNode) {
                        el.remove();
                    }
                });
            """)
            
            await page.wait_for_timeout(1000)
            
            # Strategy 4: Final check and aggressive cleanup
            if await self._has_blocking_overlay(page):
                logger.warning("Overlay still present, attempting aggressive cleanup...")
                await page.evaluate("""
                    // Remove all fixed/absolute positioned elements with high z-index
                    document.querySelectorAll('*').forEach(el => {
                        const style = window.getComputedStyle(el);
                        if ((style.position === 'fixed' || style.position === 'absolute') && 
                            style.zIndex && parseInt(style.zIndex) > 100) {
                            el.remove();
                        }
                    });
                """)
                await page.wait_for_timeout(500)
            
            # Final verification
            final_check = await self._has_blocking_overlay(page)
            if not final_check:
                logger.info("✅ Overlay dismissed via aggressive cleanup")
                return True
            else:
                logger.error("❌ Failed to dismiss overlay after all strategies")
                return False
                
        except Exception as e:
            logger.error(f"Error dismissing overlays: {e}")
            return False
    
    async def _has_blocking_overlay(self, page: Page) -> bool:
        """Quick check if blocking overlays are still present."""
        try:
            # Check for common overlay indicators
            overlay_indicators = [
                '[class*="guide"]',
                '[class*="tutorial"]',
                '[class*="overlay"]',
                '[role="dialog"]',
                '.modal',
                '.popup'
            ]
            
            for selector in overlay_indicators:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # Check if it's actually blocking (high z-index, fixed position)
                        is_blocking = await page.evaluate("""
                            (el) => {
                                const style = window.getComputedStyle(el);
                                return (style.position === 'fixed' || style.position === 'absolute') && 
                                       style.zIndex && parseInt(style.zIndex) > 100;
                            }
                        """, element)
                        
                        if is_blocking:
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for overlays: {e}")
            return False
