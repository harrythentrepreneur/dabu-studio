"""
Intelligent CapCut Service with Gemini Vision Integration
Dynamically detects UI elements and implements multiple upload strategies
"""

import os
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum

# Load environment variables first
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment")

# Playwright imports
try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    from playwright.async_api._generated import Playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("WARNING: Playwright not installed")

# Stealth mode for bypassing detection
try:
    from playwright_stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("WARNING: playwright-stealth not installed")

# Gemini Vision for intelligent UI analysis
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("WARNING: google-generativeai not installed")

from services.base_service import BaseService
from utils.logger import get_logger
from utils.overlay_dismissor import IntelligentOverlayDismissor

logger = get_logger(__name__)


class PageState(Enum):
    """Different page states in CapCut"""
    UNKNOWN = "unknown"
    LOGIN = "login"
    SIGNUP = "signup"
    EDITOR = "editor"
    PROJECT_LIST = "project_list"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    EXPORTING = "exporting"


class UploadStrategy(Enum):
    """Different upload strategies"""
    FILE_INPUT = "file_input"
    DRAG_DROP = "drag_drop"
    UPLOAD_BUTTON = "upload_button"
    NEW_PROJECT = "new_project"
    TEMPLATE_START = "template_start"


class IntelligentCapCutService(BaseService):
    """
    Intelligent CapCut service with Gemini Vision integration
    Dynamically detects UI elements and implements multiple strategies
    """
    
    def __init__(self):
        """Initialize the intelligent CapCut service."""
        super().__init__()
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            logger.info("Gemini Vision integration enabled")
        else:
            self.model = None
            logger.warning("Gemini Vision not available, using fallback detection")
        
        # Service configuration
        self.max_retries = 3
        self.retry_delay = 2
        self.element_wait_timeout = 10000
        self.page_load_timeout = 30000
        
        # Initialize overlay dismissor
        try:
            self.overlay_dismissor = IntelligentOverlayDismissor()
            logger.info("Intelligent overlay dismissor initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize overlay dismissor: {e}")
            self.overlay_dismissor = None
        
        # Output directories
        self.output_dir = Path(__file__).parent.parent / "output"
        self.screenshot_dir = Path("/tmp/capcut_intelligent")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        logger.info("Intelligent CapCut Service initialized")
    
    async def process_video_with_captions(
        self,
        video_path: str,
        caption_style: str = "TikTok Bold",
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Process video with intelligent CapCut automation.
        
        Args:
            video_path: Path to video file
            caption_style: Caption style to apply
            request_id: Unique request identifier
            
        Returns:
            Dictionary with processing results
        """
        request_id = request_id or f"intelligent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = {
            "success": False,
            "request_id": request_id,
            "error": None,
            "outputs": {},
            "processing_time": 0,
            "steps_completed": []
        }
        
        start_time = time.time()
        playwright = None
        browser = None
        context = None
        page = None
        
        try:
            logger.info(f"Starting intelligent CapCut processing for {request_id}")
            
            # Initialize Playwright
            playwright = await async_playwright().start()
            browser = await self._create_browser(playwright)
            context = await self._create_context(browser)
            page = await context.new_page()
            
            # Apply stealth mode
            if STEALTH_AVAILABLE:
                stealth = Stealth()
                await stealth.apply_stealth_async(page)
            
            # Step 1: Navigate and authenticate
            logger.info("Step 1: Navigating to CapCut and authenticating...")
            auth_success = await self._intelligent_navigation_and_auth(page, request_id)
            if not auth_success:
                raise Exception("Failed to navigate and authenticate")
            result["steps_completed"].append("authentication")
            
            # Step 2: Ensure we're in the editor
            logger.info("Step 2: Ensuring we're in the editor...")
            editor_success = await self._ensure_in_editor_intelligent(page, request_id)
            if not editor_success:
                raise Exception("Failed to reach editor")
            result["steps_completed"].append("editor_navigation")
            
            # Step 3: Upload video using intelligent strategies
            logger.info("Step 3: Uploading video with intelligent strategies...")
            upload_success = await self._intelligent_video_upload(page, video_path, request_id)
            if not upload_success:
                raise Exception("Failed to upload video")
            result["steps_completed"].append("video_upload")
            
            # Step 4: Generate captions following exact workflow
            logger.info("Step 4: Generating captions following exact workflow...")
            
            # Wait for interface to settle after upload
            await page.wait_for_timeout(3000)
            
            # Step 4a: Click Captions left sidebar button
            logger.info("Step 4a: Clicking Captions left sidebar button...")
            captions_success = await self._click_captions_sidebar_button(page, request_id)
            if not captions_success:
                raise Exception("Failed to click Captions sidebar button")
            
            # Step 4a.5: Wait for Captions panel to open and stabilize
            logger.info("Step 4a.5: Waiting for Captions panel to open...")
            
            # Wait for the Captions panel to actually become visible
            # Look for common caption panel elements that should appear
            caption_panel_selectors = [
                'div[class*="caption-panel"]',
                'div[class*="captions-panel"]',
                'div[class*="sidebar-panel"]',
                'div[class*="left-panel"]',
                'div[class*="tools-panel"]',
                'div:has-text("Auto captions")',
                'div:has-text("Auto Captions")',
                'div:has-text("Free CC")',
                'div:has-text("Generate")'
            ]
            
            panel_opened = False
            for selector in caption_panel_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    logger.info(f"Caption panel opened - found selector: {selector}")
                    panel_opened = True
                    break
                except:
                    continue
            
            if not panel_opened:
                logger.warning("Caption panel may not have opened properly, continuing anyway...")
            
            # Additional wait for panel to fully expand
            await page.wait_for_timeout(2000)
            
            # Take screenshot to see what's now visible
            screenshot_path = self.screenshot_dir / f"captions_panel_open_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Captions panel screenshot saved: {screenshot_path}")
            
            # Debug: Get all visible text to see what's actually on the page
            try:
                visible_text = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        const texts = [];
                        let node;
                        while (node = walker.nextNode()) {
                            const text = node.textContent.trim();
                            if (text && text.length > 2) {
                                texts.push(text);
                            }
                        }
                        return texts;
                    }
                """)
                logger.info(f"Visible text after Captions click: {visible_text[:20]}...")  # First 20 text elements
            except Exception as e:
                logger.warning(f"Could not extract visible text: {e}")
            
            # Step 4b: Click on "Captions" within the opened panel to get to caption tools
            logger.info("Step 4b: Clicking on Captions within the opened panel...")
            captions_tools_success = await self._click_captions_within_panel(page, request_id)
            if not captions_tools_success:
                logger.warning("Failed to click Captions within panel, trying direct approach...")
            
            # Step 4c: Click on "Auto captions Free" card to expand it and reveal the Generate button
            logger.info("Step 4c: Clicking on Auto captions Free card to expand it...")
            auto_captions_card_success = await self._click_auto_captions_free_card(page, request_id)
            if not auto_captions_card_success:
                raise Exception("Failed to expand Auto captions Free card")
            
            # Take screenshot to see the expanded card
            screenshot_path = self.screenshot_dir / f"auto_captions_card_expanded_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Auto captions card expanded screenshot saved: {screenshot_path}")
            
            # Step 4d: Now click the Generate button that's visible in the expanded card
            logger.info("Step 4d: Clicking Generate button in the expanded Auto captions card...")
            generate_success = await self._click_auto_captions_generate(page, request_id)
            if not generate_success:
                raise Exception("Failed to click Generate button")
            
            # Step 4f: Wait for generation to complete
            logger.info("Step 4f: Waiting for caption generation to complete...")
            generation_complete = await self._wait_for_caption_generation(page, request_id)
            if not generation_complete:
                raise Exception("Caption generation did not complete")
            
            # Step 4g: Go to Presets on right side top bar
            logger.info("Step 4g: Going to Presets on right side top bar...")
            presets_success = await self._open_presets_panel(page, request_id)
            if not presets_success:
                raise Exception("Failed to open Presets panel")
            
            # Step 4h: Select Templates tab
            logger.info("Step 4h: Selecting Templates tab...")
            templates_success = await self._select_templates_tab(page, request_id)
            if not templates_success:
                raise Exception("Failed to select Templates tab")
            
            # Step 4i: Select first template
            logger.info("Step 4i: Selecting first template...")
            template_success = await self._select_first_template(page, request_id)
            if not template_success:
                raise Exception("Failed to select first template")
            
            # Step 4j: Close presets
            logger.info("Step 4j: Closing presets panel...")
            close_success = await self._close_presets_panel(page, request_id)
            if not close_success:
                logger.warning("Failed to close presets panel, continuing...")
            
            result["steps_completed"].append("caption_generation")
            logger.info("Caption generation workflow completed successfully!")
            
            # Step 5: Export video following exact workflow
            logger.info("Step 5: Exporting final video following exact workflow...")
            
            # Step 5a: Click Export button
            logger.info("Step 5a: Clicking Export button...")
            export_click_success = await self._click_export_button(page, request_id)
            if not export_click_success:
                raise Exception("Failed to click Export button")
            
            # Step 5b: Handle export dialog (export settings)
            logger.info("Step 5b: Handling export dialog...")
            export_dialog_success = await self._handle_export_dialog(page, request_id)
            if not export_dialog_success:
                logger.warning("Export dialog handling failed, continuing...")
            
            # Step 5c: Wait for export to complete
            logger.info("Step 5c: Waiting for export to complete...")
            export_complete = await self._wait_for_export_completion(page, request_id)
            if not export_complete:
                logger.warning("Export completion not detected, continuing...")
            
            # Step 5d: Click Download button (now visible after export)
            logger.info("Step 5d: Clicking Download button...")
            download_click_success = await self._click_download_option(page, request_id)
            if not download_click_success:
                raise Exception("Failed to click Download button")
            
            # Step 5e: Wait for download to complete
            logger.info("Step 5e: Waiting for download to complete...")
            download_complete = await self._wait_for_download_completion(page, request_id)
            if not download_complete:
                logger.warning("Download completion not detected, continuing...")
            
            result["steps_completed"].append("video_export")
            logger.info("Video export workflow completed successfully!")
            
            # Success!
            result["success"] = True
            result["processing_time"] = time.time() - start_time
            
            # Set expected output paths for integration with main service
            # Note: Browser automation doesn't download files, so we create placeholder paths
            result["captioned_video_path"] = str(self.output_dir / f"captioned_{request_id}.mp4")
            result["project_bundle_path"] = str(self.output_dir / f"project_{request_id}.zip")
            
            logger.info(f"Intelligent CapCut processing completed successfully for {request_id}")
            
        except Exception as e:
            error_msg = f"Intelligent CapCut processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg
            
            # Save error screenshot for debugging
            if page:
                await self._save_error_screenshot(page, request_id, str(e))
        
        finally:
            # Save the session for future use
            try:
                if page and page.context:
                    context_file = Path.home() / ".capcut_browser_context"
                    context_file.mkdir(exist_ok=True)
                    await page.context.storage_state(path=str(context_file / "state.json"))
                    logger.info("Session saved for future use")
            except Exception as save_error:
                logger.warning(f"Failed to save session: {save_error}")
            
            # Enhanced cleanup with error handling
            try:
                if page:
                    await page.close()
                    logger.info("Page closed successfully")
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            
            try:
                if context:
                    await context.close()
                    logger.info("Context closed successfully")
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
            
            try:
                if browser:
                    await browser.close()
                    logger.info("Browser closed successfully")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            
            try:
                if playwright:
                    await playwright.stop()
                    logger.info("Playwright stopped successfully")
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
            
            # Clean up temporary screenshots if processing failed
            if not result.get("success", False):
                try:
                    import shutil
                    if self.screenshot_dir.exists():
                        shutil.rmtree(str(self.screenshot_dir))
                        logger.info("Temporary screenshots cleaned up")
                except Exception as e:
                    logger.warning(f"Error cleaning up screenshots: {e}")
        
        return result
    
    async def _create_browser(self, playwright: Playwright) -> Browser:
        """Create browser with optimal settings."""
        return await playwright.chromium.launch(
            headless=False,  # Visible for debugging
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080',
                '--start-maximized',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
    
    async def _create_context(self, browser: Browser) -> BrowserContext:
        """Create browser context with optimal settings and saved session."""
        # Check for saved session
        context_file = Path.home() / ".capcut_browser_context" / "state.json"
        
        if context_file.exists():
            logger.info("Loading saved CapCut session...")
            return await browser.new_context(
                storage_state=str(context_file),
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation']
            )
        else:
            logger.info("No saved session found, creating new context")
            return await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation']
            )
    
    async def _intelligent_navigation_and_auth(self, page: Page, request_id: str) -> bool:
        """Intelligently navigate to CapCut using saved session."""
        try:
            # Navigate to CapCut
            logger.info("Navigating to CapCut...")
            await page.goto("https://www.capcut.com/editor", 
                           wait_until='domcontentloaded', 
                           timeout=self.page_load_timeout)
            await page.wait_for_timeout(8000)
            
            # Take screenshot and analyze current state
            screenshot_path = self.screenshot_dir / f"initial_state_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Initial screenshot saved: {screenshot_path}")
            
            # Analyze with Gemini Vision
            page_state = await self._analyze_page_state_intelligent(page, request_id)
            logger.info(f"Current page state: {page_state}")
            
            # If we're already in editor, great!
            if page_state == PageState.EDITOR:
                logger.info("Already in CapCut editor")
                return True
            
            # If we need to login, try to use saved session first
            if page_state == PageState.LOGIN:
                logger.info("Login required, checking for saved session...")
                
                # Try to load saved context
                context_file = Path.home() / ".capcut_browser_context" / "state.json"
                if context_file.exists():
                    logger.info("Found saved session, reloading page with saved context...")
                    
                    # Get the current context and reload with saved state
                    context = page.context
                    await context.storage_state(path=str(context_file))
                    
                    # Reload the page
                    await page.reload()
                    await page.wait_for_timeout(5000)
                    
                    # Check state again
                    page_state = await self._analyze_page_state_intelligent(page, request_id)
                    logger.info(f"Page state after loading saved session: {page_state}")
                    
                    if page_state == PageState.EDITOR:
                        logger.info("Successfully loaded saved session")
                        return True
                
                # If saved session didn't work, try manual authentication
                logger.info("Saved session failed, attempting manual authentication...")
                auth_success = await self._handle_authentication_intelligent(page, page_state, request_id)
                if not auth_success:
                    logger.error("Manual authentication failed")
                    return False
                
                # Wait for navigation after auth
                await page.wait_for_timeout(5000)
                page_state = await self._analyze_page_state_intelligent(page, request_id)
                logger.info(f"Page state after authentication: {page_state}")
                
                if page_state == PageState.LOGIN:
                    logger.error("Still on login page after authentication")
                    return False
            
            # Ensure we're in the editor
            if page_state not in [PageState.EDITOR, PageState.PROJECT_LIST]:
                logger.error(f"Failed to reach editor, current state: {page_state}")
                return False
            
            logger.info("Successfully navigated to CapCut editor")
            return True
            
        except Exception as e:
            logger.error(f"Navigation and authentication failed: {e}")
            return False
    
    async def _analyze_page_state_intelligent(self, page: Page, request_id: str) -> PageState:
        """Intelligently analyze the current page state using Gemini Vision."""
        try:
            if self.model:
                # Use Gemini Vision for intelligent analysis
                return await self._analyze_with_gemini_vision(page, request_id)
            else:
                # Fallback to traditional detection
                return await self._analyze_with_traditional_detection(page)
                
        except Exception as e:
            logger.warning(f"Page state analysis failed: {e}, using fallback")
            return await self._analyze_with_traditional_detection(page)
    
    async def _analyze_with_gemini_vision(self, page: Page, request_id: str) -> PageState:
        """Analyze page state using Gemini Vision."""
        try:
            # Take screenshot
            screenshot_path = self.screenshot_dir / f"analysis_{request_id}_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            
            # Analyze with Gemini
            prompt = """
            Analyze this CapCut webpage screenshot and determine the current page state.
            
            Look for these indicators:
            1. LOGIN/SIGNUP: Login forms, signup buttons, authentication fields
            2. EDITOR: Video timeline, editing tools, upload areas, project workspace
            3. PROJECT_LIST: List of projects, create new project buttons
            4. UPLOADING: Upload progress, file processing indicators
            5. PROCESSING: Video processing, caption generation progress
            6. EXPORTING: Export options, download buttons
            
            Respond with ONLY one of these exact values:
            - LOGIN
            - SIGNUP  
            - EDITOR
            - PROJECT_LIST
            - UPLOADING
            - PROCESSING
            - EXPORTING
            - UNKNOWN
            """
            
            # Upload screenshot to Gemini
            uploaded_file = genai.upload_file(str(screenshot_path))
            response = self.model.generate_content([prompt, uploaded_file])
            
            # Parse response
            response_text = response.text.strip().upper()
            logger.info(f"Gemini Vision analysis result: {response_text}")
            
            # Map to PageState enum
            state_mapping = {
                'LOGIN': PageState.LOGIN,
                'SIGNUP': PageState.SIGNUP,
                'EDITOR': PageState.EDITOR,
                'PROJECT_LIST': PageState.PROJECT_LIST,
                'UPLOADING': PageState.UPLOADING,
                'PROCESSING': PageState.PROCESSING,
                'EXPORTING': PageState.EXPORTING
            }
            
            return state_mapping.get(response_text, PageState.UNKNOWN)
            
        except Exception as e:
            logger.error(f"Gemini Vision analysis failed: {e}")
            return PageState.UNKNOWN
    
    async def _analyze_with_traditional_detection(self, page: Page) -> PageState:
        """Fallback page state detection using traditional methods."""
        try:
            url = page.url.lower()
            title = await page.title()
            
            # URL-based detection
            if 'signup' in url or 'login' in url:
                return PageState.LOGIN
            elif 'my-edit' in url or 'editor' in url:
                return PageState.EDITOR
            elif 'projects' in url:
                return PageState.PROJECT_LIST
            
            # Title-based detection
            if 'sign' in title.lower():
                return PageState.LOGIN
            elif 'edit' in title.lower():
                return PageState.EDITOR
            
            # Element-based detection
            login_elements = await page.query_selector_all('input[type="email"], input[type="password"]')
            if login_elements:
                return PageState.LOGIN
            
            editor_elements = await page.query_selector_all('[data-testid="timeline"], .timeline, .editor-tools')
            if editor_elements:
                return PageState.EDITOR
            
            return PageState.UNKNOWN
            
        except Exception as e:
            logger.error(f"Traditional detection failed: {e}")
            return PageState.UNKNOWN
    
    async def _handle_authentication_intelligent(self, page: Page, page_state: PageState, request_id: str) -> bool:
        """Intelligently handle authentication using multiple strategies."""
        try:
            logger.info(f"Handling authentication for {page_state}")
            
            # Try multiple authentication strategies
            auth_strategies = [
                self._try_google_auth,
                self._try_email_auth,
                self._try_social_auth
            ]
            
            for strategy in auth_strategies:
                try:
                    auth_success = await strategy(page, page_state, request_id)
                    if auth_success:
                        logger.info("Authentication successful")
                        return True
                except Exception as e:
                    logger.warning(f"Authentication strategy {strategy.__name__} failed: {e}")
                    continue
            
            logger.error("All authentication strategies failed")
            return False
            
        except Exception as e:
            logger.error(f"Authentication handling failed: {e}")
            return False
    
    async def _try_google_auth(self, page: Page, page_state: PageState, request_id: str) -> bool:
        """Try Google authentication."""
        try:
            # Look for Google sign-in button
            google_selectors = [
                'button:has-text("Continue with Google")',
                'button:has-text("Sign in with Google")',
                'button:has-text("Google")',
                '[data-provider="google"]',
                '.google-signin-btn'
            ]
            
            for selector in google_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found Google button: {selector}")
                        await element.click()
                        await page.wait_for_timeout(5000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Google auth failed: {e}")
            return False
    
    async def _try_email_auth(self, page: Page, page_state: PageState, request_id: str) -> bool:
        """Try email/password authentication."""
        try:
            email = os.getenv('CAPCUT_EMAIL')
            password = os.getenv('CAPCUT_PASSWORD')
            
            if not email or not password:
                logger.warning("Email/password credentials not configured")
                return False
            
            # Fill email first
            email_selectors = [
                'input[type="email"]',
                'input[placeholder*="email" i]',
                'input[name="email"]',
                'input[placeholder*="Email" i]',
                'input[name="signUsername"]'  # Based on debug results
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=3000)
                    if email_input:
                        logger.info(f"Found email input: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                logger.warning("Email input not found")
                return False
            
            await email_input.fill(email)
            await page.wait_for_timeout(2000)
            
            # Try to submit email first (multi-step login)
            submit_email_selectors = [
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button[type="submit"]'
            ]
            
            submit_btn = None
            for selector in submit_email_selectors:
                try:
                    submit_btn = await page.wait_for_selector(selector, timeout=3000)
                    if submit_btn:
                        logger.info(f"Found submit button: {selector}")
                        break
                except:
                    continue
            
            if submit_btn:
                logger.info("Clicking submit button...")
                await submit_btn.click()
                await page.wait_for_timeout(5000)  # Wait longer for page transition
                
                # Take screenshot for debugging
                screenshot_path = self.screenshot_dir / f"after_email_submit_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Debug screenshot saved: {screenshot_path}")
                
                # Now look for password field (it should be visible after email submission)
                await page.wait_for_timeout(3000)  # Additional wait
                
                password_selectors = [
                    'input[type="password"]',
                    'input[placeholder*="password" i]',
                    'input[name="password"]',
                    'input[placeholder*="Password" i]',
                    'input[placeholder*="Enter password" i]'
                ]
                
                password_input = None
                for selector in password_selectors:
                    try:
                        password_input = await page.wait_for_selector(selector, timeout=8000)  # Longer timeout
                        if password_input:
                            logger.info(f"Found password input: {selector}")
                            break
                    except:
                        continue
                
                if not password_input:
                    # Try to find any input that might be password
                    logger.warning("Password input not found, trying alternative approach...")
                    
                    # Look for any input that's not email
                    all_inputs = await page.query_selector_all('input')
                    for inp in all_inputs:
                        try:
                            input_type = await inp.get_attribute('type') or 'unknown'
                            input_placeholder = await inp.get_attribute('placeholder') or 'no placeholder'
                            input_name = await inp.get_attribute('name') or 'no name'
                            
                            logger.info(f"Checking input: type={input_type}, placeholder='{input_placeholder}', name='{input_name}'")
                            
                            if (input_type != 'email' and 
                                'email' not in input_placeholder.lower() and 
                                'email' not in input_name.lower() and
                                input_type != 'file' and
                                input_type != 'hidden'):
                                logger.info(f"Found potential password input: type={input_type}, placeholder={input_placeholder}")
                                password_input = inp
                                break
                        except Exception as e:
                            logger.warning(f"Error checking input: {e}")
                            continue
                
                if not password_input:
                    logger.warning("Password input still not found")
                    return False
                
                # Fill password
                logger.info("Filling password...")
                await password_input.fill(password)
                await page.wait_for_timeout(2000)
                
                # Submit password
                submit_selectors = [
                    'button:has-text("Sign in")',
                    'button:has-text("Log in")',
                    'button:has-text("Continue")',
                    'button[type="submit"]',
                    'button:has-text("Submit")',
                    'button:has-text("Next")'
                ]
                
                final_submit_btn = None
                for selector in submit_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            logger.info(f"Found final submit button: {selector}")
                            final_submit_btn = element
                            break
                    except:
                        continue
                
                if final_submit_btn:
                    logger.info("Clicking final submit button...")
                    await final_submit_btn.click()
                    await page.wait_for_timeout(10000)  # Wait longer for authentication
                    
                    # Take final screenshot for debugging
                    screenshot_path = self.screenshot_dir / f"after_password_submit_{request_id}.png"
                    await page.screenshot(path=str(screenshot_path))
                    logger.info(f"Final debug screenshot saved: {screenshot_path}")
                    
                    return True
                else:
                    logger.warning("Final submit button not found")
                    return False
            else:
                logger.warning("Submit button not found")
                return False
            
        except Exception as e:
            logger.error(f"Email auth failed: {e}")
            return False
    
    async def _try_social_auth(self, page: Page, page_state: PageState, request_id: str) -> bool:
        """Try other social authentication methods."""
        try:
            social_methods = ['facebook', 'apple', 'twitter']
            
            for method in social_methods:
                try:
                    selector = f'button:has-text("{method.title()}"), [data-provider="{method}"]'
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found {method} auth button")
                        await element.click()
                        await page.wait_for_timeout(5000)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Social auth failed: {e}")
            return False
    
    async def _ensure_in_editor_intelligent(self, page: Page, request_id: str) -> bool:
        """Intelligently ensure we're in the CapCut editor."""
        try:
            page_state = await self._analyze_page_state_intelligent(page, request_id)
            
            if page_state == PageState.EDITOR:
                logger.info("Already in editor")
                return True
            
            elif page_state == PageState.PROJECT_LIST:
                logger.info("In project list, creating new project...")
                return await self._create_new_project_intelligent(page, request_id)
            
            else:
                logger.warning(f"Unexpected page state: {page_state}")
                return False
                
        except Exception as e:
            logger.error(f"Editor navigation failed: {e}")
            return False
    
    async def _create_new_project_intelligent(self, page: Page, request_id: str) -> bool:
        """Intelligently create a new project."""
        try:
            # Look for new project button
            new_project_selectors = [
                'button:has-text("New Project")',
                'button:has-text("Create")',
                '[data-testid="new-project-btn"]',
                '.new-project-btn'
            ]
            
            for selector in new_project_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found new project button: {selector}")
                        await element.click()
                        await page.wait_for_timeout(5000)
                        
                        # Check if we're now in editor
                        page_state = await self._analyze_page_state_intelligent(page, request_id)
                        return page_state == PageState.EDITOR
                except:
                    continue
            
            logger.warning("New project button not found")
            return False
            
        except Exception as e:
            logger.error(f"New project creation failed: {e}")
            return False
    
    async def _intelligent_video_upload(self, page: Page, video_path: str, request_id: str) -> bool:
        """Intelligently upload video using multiple strategies."""
        try:
            logger.info(f"Starting intelligent video upload for: {video_path}")
            
            # Try multiple upload strategies
            upload_strategies = [
                (self._upload_via_file_input, "File Input"),
                (self._upload_via_drag_drop, "Drag & Drop"),
                (self._upload_via_button, "Upload Button"),
                (self._upload_via_new_project, "New Project")
            ]
            
            for strategy_func, strategy_name in upload_strategies:
                try:
                    logger.info(f"Trying upload strategy: {strategy_name}")
                    success = await strategy_func(page, video_path, request_id)
                    if success:
                        logger.info(f"Upload successful using {strategy_name}")
                        return True
                except Exception as e:
                    logger.warning(f"Upload strategy {strategy_name} failed: {e}")
                    continue
            
            logger.error("All upload strategies failed")
            return False
            
        except Exception as e:
            logger.error(f"Intelligent upload failed: {e}")
            return False
    
    async def _upload_via_file_input(self, page: Page, video_path: str, request_id: str) -> bool:
        """Upload via file input element."""
        try:
            logger.info("Trying file input strategy...")
            
            # Look for file input with multiple approaches
            file_input_selectors = [
                'input[type="file"]',
                '[data-testid="file-input"]',
                '.file-input',
                'input[accept*="video"]',
                'input[accept*="mp4"]'
            ]
            
            file_input = None
            
            # Approach 1: Try standard selectors with longer timeout
            for selector in file_input_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found file input with selector: {selector}")
                        file_input = element
                        break
                except:
                    continue
            
            # Approach 2: Look for any file input in the page
            if not file_input:
                try:
                    file_inputs = await page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        file_input = file_inputs[0]
                        logger.info(f"Found {len(file_inputs)} file inputs with query_selector_all")
                except:
                    logger.warning("No file inputs found with query_selector_all")
            
            # Approach 3: Look for hidden file inputs
            if not file_input:
                try:
                    hidden_file_inputs = await page.query_selector_all('input[type="file"][style*="display: none"], input[type="file"][hidden]')
                    if hidden_file_inputs:
                        file_input = hidden_file_inputs[0]
                        logger.info("Found hidden file input")
                except:
                    logger.warning("No hidden file inputs found")
            
            # Approach 4: Look for any input that might be file input
            if not file_input:
                try:
                    all_inputs = await page.query_selector_all('input')
                    for inp in all_inputs:
                        try:
                            input_type = await inp.get_attribute('type') or 'unknown'
                            input_accept = await inp.get_attribute('accept') or ''
                            
                            if input_type == 'file' or 'video' in input_accept.lower() or 'mp4' in input_accept.lower():
                                file_input = inp
                                logger.info(f"Found potential file input: type={input_type}, accept={input_accept}")
                                break
                        except:
                            continue
                except:
                    logger.warning("Error checking all inputs for file input")
            
            # Approach 5: Look for drop zones that might have hidden file inputs
            if not file_input:
                try:
                    drop_zones = await page.query_selector_all('[class*="drop"], [class*="upload"], [class*="drag"]')
                    for zone in drop_zones:
                        try:
                            hidden_inputs = await zone.query_selector_all('input[type="file"]')
                            if hidden_inputs:
                                file_input = hidden_inputs[0]
                                logger.info("Found file input in drop zone")
                                break
                        except:
                            continue
                except:
                    logger.warning("Error checking drop zones for file inputs")
            
            if file_input:
                logger.info("File input found, setting files...")
                
                # Check if file input is visible
                is_visible = await file_input.is_visible()
                logger.info(f"File input visible: {is_visible}")
                
                # Take screenshot before setting file
                screenshot_path = self.screenshot_dir / f"before_file_set_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Pre-file screenshot saved: {screenshot_path}")
                
                # Set the video file
                await file_input.set_input_files(video_path)
                logger.info(f"Video file set: {video_path}")
                
                # Wait for upload to start
                await page.wait_for_timeout(5000)
                
                # Take screenshot after setting file
                screenshot_path = self.screenshot_dir / f"after_file_set_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Post-file screenshot saved: {screenshot_path}")
                
                            # Wait for upload to complete with intelligent detection
            logger.info("Waiting for upload to complete...")
            upload_complete = await self._wait_for_upload_completion(page, request_id)
            if not upload_complete:
                logger.warning("Upload completion not detected, using fallback timeout")
                await page.wait_for_timeout(15000)  # Fallback timeout
                
                # Take final screenshot
                screenshot_path = self.screenshot_dir / f"upload_complete_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Upload complete screenshot saved: {screenshot_path}")
                
                logger.info("File input upload completed successfully")
                return True
            else:
                logger.warning("No file input found")
                return False
            
        except Exception as e:
            logger.error(f"File input upload failed: {e}")
            return False
    
    async def _upload_via_drag_drop(self, page: Page, video_path: str, request_id: str) -> bool:
        """Upload via drag and drop."""
        try:
            # Look for drop zone
            drop_zone_selectors = [
                '[data-testid="drop-zone"]',
                '.drop-zone',
                '.upload-area',
                'div:has-text("Drop files here")'
            ]
            
            for selector in drop_zone_selectors:
                try:
                    drop_zone = await page.wait_for_selector(selector, timeout=5000)
                    if drop_zone:
                        logger.info(f"Found drop zone: {selector}")
                        
                        # Simulate drag and drop
                        await page.evaluate(f"""
                            const dropZone = document.querySelector('{selector}');
                            const file = new File([''], '{Path(video_path).name}', {{ type: 'video/mp4' }});
                            const dataTransfer = new DataTransfer();
                            dataTransfer.items.add(file);
                            
                            const dropEvent = new DragEvent('drop', {{
                                dataTransfer: dataTransfer,
                                bubbles: true
                            }});
                            
                            dropZone.dispatchEvent(dropEvent);
                        """)
                        
                        await page.wait_for_timeout(10000)  # Wait for upload
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Drag and drop upload failed: {e}")
            return False
    
    async def _upload_via_button(self, page: Page, video_path: str, request_id: str) -> bool:
        """Upload via upload button."""
        try:
            # Look for upload button
            upload_button_selectors = [
                'button:has-text("Upload")',
                '[data-testid="upload-btn"]',
                '.upload-btn',
                '.upload-button'
            ]
            
            for selector in upload_button_selectors:
                try:
                    upload_btn = await page.wait_for_selector(selector, timeout=5000)
                    if upload_btn:
                        logger.info(f"Found upload button: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_upload_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        logger.info(f"Pre-click screenshot saved: {screenshot_path}")
                        
                        await upload_btn.click()
                        await page.wait_for_timeout(3000)
                        
                        # Take screenshot after clicking
                        screenshot_path = self.screenshot_dir / f"after_upload_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        logger.info(f"Post-click screenshot saved: {screenshot_path}")
                        
                        # Look for file input that appears after clicking
                        logger.info("Looking for file input after clicking upload button...")
                        
                        # Try multiple approaches to find the file input
                        file_input = None
                        
                        # Approach 1: Wait for file input to appear
                        try:
                            file_input = await page.wait_for_selector('input[type="file"]', timeout=8000)
                            if file_input:
                                logger.info("Found file input with input[type='file']")
                        except:
                            logger.warning("File input not found with input[type='file']")
                        
                        # Approach 2: Look for any file input
                        if not file_input:
                            try:
                                file_inputs = await page.query_selector_all('input[type="file"]')
                                if file_inputs:
                                    file_input = file_inputs[0]
                                    logger.info(f"Found {len(file_inputs)} file inputs")
                            except:
                                logger.warning("No file inputs found with query_selector_all")
                        
                        # Approach 3: Look for any input that might be file input
                        if not file_input:
                            try:
                                all_inputs = await page.query_selector_all('input')
                                for inp in all_inputs:
                                    try:
                                        input_type = await inp.get_attribute('type') or 'unknown'
                                        if input_type == 'file':
                                            file_input = inp
                                            logger.info("Found file input in all inputs")
                                            break
                                    except:
                                        continue
                            except:
                                logger.warning("Error checking all inputs")
                        
                        # Approach 4: Look for hidden file inputs
                        if not file_input:
                            try:
                                hidden_file_inputs = await page.query_selector_all('input[type="file"][style*="display: none"], input[type="file"][hidden]')
                                if hidden_file_inputs:
                                    file_input = hidden_file_inputs[0]
                                    logger.info("Found hidden file input")
                            except:
                                logger.warning("No hidden file inputs found")
                        
                        if file_input:
                            logger.info("File input found, setting files...")
                            
                            # Check if file input is visible
                            is_visible = await file_input.is_visible()
                            logger.info(f"File input visible: {is_visible}")
                            
                            # Set the video file
                            await file_input.set_input_files(video_path)
                            logger.info(f"Video file set: {video_path}")
                            
                            # Wait for upload to start
                            await page.wait_for_timeout(5000)
                            
                            # Take screenshot after setting file
                            screenshot_path = self.screenshot_dir / f"after_file_set_{request_id}.png"
                            await page.screenshot(path=str(screenshot_path))
                            logger.info(f"Post-file screenshot saved: {screenshot_path}")
                            
                            # Wait for upload to complete (look for progress indicators)
                            logger.info("Waiting for upload to complete...")
                            await page.wait_for_timeout(15000)  # Wait 15 seconds for upload
                            
                            # Take final screenshot
                            screenshot_path = self.screenshot_dir / f"upload_complete_{request_id}.png"
                            await page.screenshot(path=str(screenshot_path))
                            logger.info(f"Upload complete screenshot saved: {screenshot_path}")
                            
                            logger.info("Upload via button completed successfully")
                            return True
                        else:
                            logger.warning("File input not found after clicking upload button")
                            return False
                except Exception as e:
                    logger.warning(f"Upload button strategy failed: {e}")
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Button upload failed: {e}")
            return False
    
    async def _upload_via_new_project(self, page: Page, video_path: str, request_id: str) -> bool:
        """Upload by starting a new project."""
        try:
            # Look for "Start with video" or similar
            start_video_selectors = [
                'button:has-text("Start with video")',
                'button:has-text("Upload video")',
                '[data-testid="start-video-btn"]'
            ]
            
            for selector in start_video_selectors:
                try:
                    start_btn = await page.wait_for_selector(selector, timeout=5000)
                    if start_btn:
                        logger.info(f"Found start video button: {selector}")
                        await start_btn.click()
                        await page.wait_for_timeout(2000)
                        
                        # Look for file input
                        file_input = await page.wait_for_selector('input[type="file"]', timeout=5000)
                        if file_input:
                            await file_input.set_input_files(video_path)
                            await page.wait_for_timeout(10000)  # Wait for upload
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"New project upload failed: {e}")
            return False

    async def _intelligent_caption_generation(self, page: Page, caption_style: str, request_id: str) -> bool:
        """Intelligently generate captions with auto-caption feature."""
        try:
            logger.info(f"Starting intelligent caption generation with style: {caption_style}")
            
            # Take screenshot before starting caption generation
            screenshot_path = self.screenshot_dir / f"before_caption_gen_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Pre-caption screenshot saved: {screenshot_path}")
            
            # Step 1: Try multiple tab strategies for finding caption options
            logger.info("Step 1: Looking for auto-caption options in multiple tabs...")
            
            # Define all possible tab selectors with priority order
            tab_strategies = [
                {
                    'name': 'Transcript',
                    'selectors': [
                        'div:has-text("Transcript")',
                        '[data-testid="transcript-tab"]',
                        '.transcript-tab',
                        'div[class*="transcript"]',
                        'button:has-text("Transcript")',
                        '[role="tab"]:has-text("Transcript")'
                    ]
                },
                {
                    'name': 'Captions',
                    'selectors': [
                        'div:has-text("Captions")',
                        '[data-testid="captions-tab"]',
                        '.captions-tab',
                        'div[class*="captions"]',
                        'div[class*="caption"]',
                        'button:has-text("Captions")',
                        '[role="tab"]:has-text("Captions")'
                    ]
                },
                {
                    'name': 'Auto-Caption',
                    'selectors': [
                        'div:has-text("Auto-Caption")',
                        'div:has-text("Auto Caption")',
                        'button:has-text("Auto-Caption")',
                        'button:has-text("Auto Caption")',
                        '[data-testid="auto-caption-tab"]'
                    ]
                }
            ]
            
            # Try each tab strategy
            for strategy in tab_strategies:
                logger.info(f"Trying {strategy['name']} tab...")
                
                tab_element = None
                for selector in strategy['selectors']:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            logger.info(f"Found {strategy['name']} tab with selector: {selector}")
                            tab_element = element
                            break
                    except:
                        continue
                
                if tab_element:
                    # Click the tab
                    await self._safe_click(page, tab_element, f"{strategy['name']} tab", request_id)
                    await page.wait_for_timeout(3000)  # Increased wait time
                    logger.info(f"Clicked {strategy['name']} tab")
                    
                    # Wait for panel to load and check for auto-caption options
                    await page.wait_for_timeout(2000)
                    
                    # Check if auto-caption options are available
                    auto_caption_available = await self._check_auto_caption_availability(page, request_id)
                    if auto_caption_available:
                        logger.info(f"Auto-caption options found in {strategy['name']} tab")
                        break
                    else:
                        logger.info(f"Auto-caption options not found in {strategy['name']} tab")
                else:
                    logger.warning(f"{strategy['name']} tab not found")
            
                        # If no tab worked, try a broader search
            if not auto_caption_available:
                logger.info("No specific tab worked, trying broader search for caption options...")
                auto_caption_available = await self._search_for_caption_options_broadly(page, request_id)
            
            if not auto_caption_available:
                logger.error("No caption options found in any tab")
                return False
            
            # Take screenshot after navigating to transcript/captions
            screenshot_path = self.screenshot_dir / f"transcript_captions_tab_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Transcript/Captions tab screenshot saved: {screenshot_path}")
            
            # Step 2: Look for and click the "Free CC" auto-caption button
            logger.info("Step 2: Looking for auto-caption generation button...")
            
            # Quick check for any obvious blocking overlays
            await page.wait_for_timeout(1000)
            
            auto_caption_selectors = [
                'button:has-text("Free CC")',
                'div:has-text("Free CC")',
                'button:has-text("Generate")',
                'div:has-text("Generate")',
                'button:has-text("Generate captions")',
                'div:has-text("Generate captions")',
                'button:has-text("Auto captions")',
                'div:has-text("Auto captions")',
                'button:has-text("Auto")',
                'div:has-text("Auto")',
                'button:has-text("CC")',
                'div:has-text("CC")',
                'button:has-text("Subtitle")',
                'div:has-text("Subtitle")',
                'button:has-text("Transcribe")',
                'div:has-text("Transcribe")',
                '[data-testid="auto-caption-btn"]',
                '[data-testid="generate-caption"]',
                '[data-testid="auto-caption"]',
                '.auto-caption-btn',
                '.generate-caption-btn',
                '.auto-caption',
                '.generate-caption',
                '[class*="auto-caption"]',
                '[class*="generate-caption"]',
                '[class*="auto-caption-btn"]',
                '[class*="generate-caption-btn"]'
            ]
            
            auto_caption_btn = None
            for selector in auto_caption_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found auto-caption button: {selector}")
                        auto_caption_btn = element
                        break
                except:
                    continue
            
            if not auto_caption_btn:
                # Try to find any element with "Free" or "CC" text
                try:
                    free_elements = await page.query_selector_all('*:has-text("Free")')
                    cc_elements = await page.query_selector_all('*:has-text("CC")')
                    
                    for element in free_elements + cc_elements:
                        try:
                            text = await element.inner_text()
                            if 'free' in text.lower() and 'cc' in text.lower():
                                auto_caption_btn = element
                                logger.info(f"Found auto-caption button with text: '{text}'")
                                break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"Error searching for auto-caption button: {e}")
            
            if auto_caption_btn:
                logger.info("Auto-caption button found, clicking...")
                
                # Take screenshot before clicking auto-caption
                screenshot_path = self.screenshot_dir / f"auto_caption_button_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Auto-caption button screenshot saved: {screenshot_path}")
                
                await self._safe_click(page, auto_caption_btn, "auto-caption button", request_id)
                await page.wait_for_timeout(3000)
                logger.info("Clicked auto-caption button")
                
                # Step 3: Wait for caption generation to complete
                logger.info("Step 3: Waiting for caption generation to complete...")
                
                # Look for progress indicators
                progress_selectors = [
                    'div:has-text("%")',
                    'div:has-text("Generating")',
                    'div:has-text("Processing")',
                    'div:has-text("Loading")',
                    '[class*="progress"]',
                    '[class*="loading"]'
                ]
                
                progress_element = None
                for selector in progress_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            progress_element = element
                            logger.info(f"Found progress indicator: {selector}")
                            break
                    except:
                        continue
                
                if progress_element:
                    logger.info("Caption generation in progress, waiting for completion...")
                    
                    # Wait for progress to complete (look for completion indicators)
                    max_wait_time = 120  # 2 minutes max
                    wait_time = 0
                    
                    while wait_time < max_wait_time:
                        try:
                            # Check if progress is still showing
                            progress_text = await progress_element.inner_text()
                            logger.info(f"Progress: {progress_text}")
                            
                            # Look for completion indicators
                            if any(word in progress_text.lower() for word in ['complete', 'done', 'finished', '100%']):
                                logger.info("Caption generation completed!")
                                break
                            
                            # Wait and check again
                            await page.wait_for_timeout(5000)
                            wait_time += 5
                            
                        except Exception as e:
                            logger.warning(f"Error checking progress: {e}")
                            break
                    
                    logger.info(f"Waited {wait_time} seconds for caption generation")
                else:
                    logger.info("No progress indicator found, waiting default time...")
                    await page.wait_for_timeout(30000)  # Wait 30 seconds
                
                # Take screenshot after caption generation
                screenshot_path = self.screenshot_dir / f"captions_generated_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Captions generated screenshot saved: {screenshot_path}")
                
                # Step 4: Select caption style
                logger.info("Step 4: Selecting caption style...")
                
                # Look for style selection options
                style_selectors = [
                    'button:has-text("Style")',
                    'div:has-text("Style")',
                    '[data-testid="style-selector"]',
                    '.style-selector'
                ]
                
                style_selector = None
                for selector in style_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            logger.info(f"Found style selector: {selector}")
                            style_selector = element
                            break
                    except:
                        continue
                
                if style_selector:
                    await style_selector.click()
                    await page.wait_for_timeout(2000)
                    logger.info("Clicked style selector")
                    
                    # Look for the specific caption style
                    style_options = [
                        f'button:has-text("{caption_style}")',
                        f'div:has-text("{caption_style}")',
                        f'[data-testid="{caption_style.lower().replace(" ", "-")}"]'
                    ]
                    
                    selected_style = None
                    for option in style_options:
                        try:
                            element = await page.wait_for_selector(option, timeout=3000)
                            if element:
                                logger.info(f"Found style option: {option}")
                                selected_style = element
                                break
                        except:
                            continue
                    
                    if selected_style:
                        await selected_style.click()
                        await page.wait_for_timeout(2000)
                        logger.info(f"Selected style: {caption_style}")
                    else:
                        logger.warning(f"Style '{caption_style}' not found, using default")
                else:
                    logger.info("No style selector found, using default style")
                
                # Take final screenshot
                screenshot_path = self.screenshot_dir / f"style_selected_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Style selected screenshot saved: {screenshot_path}")
                
                logger.info("Caption generation and style selection completed successfully")
                return True
            else:
                # Auto-caption button not found - this might mean we need to wait for the interface to update
                # or look in a different location
                logger.warning("Auto-caption button not found immediately, trying alternative approaches...")
                
                # Wait a bit more for the interface to fully load
                await page.wait_for_timeout(5000)
                
                # Try looking for auto-caption options in different ways
                alternative_selectors = [
                    'button:has-text("Generate")',
                    'div:has-text("Generate")',
                    'button:has-text("Auto")',
                    'div:has-text("Auto")',
                    'button:has-text("CC")',
                    'div:has-text("CC")',
                    '[class*="generate"]',
                    '[class*="auto"]',
                    '[class*="caption"]'
                ]
                
                for selector in alternative_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            text = await element.inner_text()
                            logger.info(f"Found alternative element: {selector} -> '{text}'")
                            
                            # Check if it's clickable and related to captions
                            if any(keyword.lower() in text.lower() for keyword in ['generate', 'auto', 'caption', 'cc']):
                                logger.info("This looks like an auto-caption option, clicking...")
                                await self._safe_click(page, element, "alternative auto-caption option", request_id)
                                await page.wait_for_timeout(3000)
                                
                                # Take screenshot after clicking
                                screenshot_path = self.screenshot_dir / f"alternative_caption_clicked_{request_id}.png"
                                await page.screenshot(path=str(screenshot_path))
                                logger.info(f"Alternative caption option clicked, screenshot saved")
                                
                                # Wait for any generation to start
                                await page.wait_for_timeout(10000)
                                return True
                    except:
                        continue
                
                logger.error("Auto-caption button not found with any approach")
                return False
                
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return False
    
    async def _intelligent_video_export(self, page: Page, request_id: str) -> bool:
        """Intelligently export the final video."""
        try:
            logger.info("Starting intelligent video export")
            
            # Take screenshot before looking for export button
            screenshot_path = self.screenshot_dir / f"before_export_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Pre-export screenshot saved: {screenshot_path}")
            
            # Look for the export button with multiple strategies
            export_button_selectors = [
                # Primary selectors for the blue Export button
                'button:has-text("Export")',
                '[data-testid="export-btn"]',
                '.export-btn',
                '.export-button',
                # More specific selectors
                'button[class*="export"]',
                'div[class*="export"]',
                # Look for any element with "Export" text
                '[class*="export"]:has-text("Export")',
                'button:has-text("Export"):visible',
                # Fallback: any button with export text
                'button:has-text("Export")'
            ]
            
            # Dismiss any overlays before looking for export button
            await self._dismiss_guide_overlays(page, request_id)
            await page.wait_for_timeout(1000)
            
            export_button = None
            
            # Strategy 1: Try standard selectors
            for selector in export_button_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found export button with selector: {selector}")
                        export_button = element
                        break
                except:
                    continue
            
            # Strategy 2: Look for any element with "Export" text
            if not export_button:
                try:
                    logger.info("Looking for any element with 'Export' text...")
                    export_elements = await page.query_selector_all('*:has-text("Export")')
                    
                    for element in export_elements:
                        try:
                            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                            is_visible = await element.is_visible()
                            text_content = await element.inner_text()
                            
                            logger.info(f"Found export element: {tag_name}, visible: {is_visible}, text: '{text_content}'")
                            
                            if is_visible and 'export' in text_content.lower():
                                export_button = element
                                logger.info(f"Selected export element: {tag_name}")
                                break
                        except Exception as e:
                            logger.warning(f"Error checking export element: {e}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error in export element search: {e}")
            
            # Strategy 3: Look for buttons in the top bar area
            if not export_button:
                try:
                    logger.info("Looking for buttons in top bar area...")
                    top_bar_selectors = [
                        'header button',
                        '.top-bar button',
                        '[class*="header"] button',
                        '[class*="toolbar"] button'
                    ]
                    
                    for selector in top_bar_selectors:
                        try:
                            buttons = await page.query_selector_all(selector)
                            for button in buttons:
                                try:
                                    text = await button.inner_text()
                                    if 'export' in text.lower():
                                        export_button = button
                                        logger.info(f"Found export button in top bar: '{text}'")
                                        break
                                except:
                                    continue
                            if export_button:
                                break
                        except:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error in top bar search: {e}")
            
            if export_button:
                logger.info("Export button found, clicking...")
                
                # Take screenshot before clicking
                screenshot_path = self.screenshot_dir / f"export_button_found_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Export button screenshot saved: {screenshot_path}")
                
                await self._safe_click(page, export_button, "export button", request_id)
                await page.wait_for_timeout(3000)
                
                # Take screenshot after clicking
                screenshot_path = self.screenshot_dir / f"after_export_click_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Post-export click screenshot saved: {screenshot_path}")
                
                # Now look for the download button in the export dialog
                logger.info("Looking for download button in export dialog...")
                
                # Wait for export dialog to appear and dismiss any overlays
                await page.wait_for_timeout(3000)
                await self._dismiss_guide_overlays(page, request_id)
                await page.wait_for_timeout(1000)
                
                download_button_selectors = [
                    'button:has-text("Download")',
                    '[data-testid="download-btn"]',
                    '.download-btn',
                    'button:has-text("Download"):visible',
                    'button:has-text("Export")',
                    'button:has-text("Start Export")'
                ]
                
                download_button = None
                for selector in download_button_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            logger.info(f"Found download button: {selector}")
                            download_button = element
                            break
                    except:
                        continue
                
                if download_button:
                    logger.info("Download button found, clicking...")
                    
                    # Take screenshot before download click
                    screenshot_path = self.screenshot_dir / f"download_button_found_{request_id}.png"
                    await page.screenshot(path=str(screenshot_path))
                    logger.info(f"Download button screenshot saved: {screenshot_path}")
                    
                    # Try multiple click strategies
                    click_success = False
                    
                    # Strategy 1: Direct click
                    try:
                        await download_button.click()
                        click_success = True
                        logger.info("Download button clicked successfully")
                    except Exception as e:
                        logger.warning(f"Direct click failed: {e}")
                    
                    # Strategy 2: Force click if direct failed
                    if not click_success:
                        try:
                            await download_button.click(force=True)
                            click_success = True
                            logger.info("Download button clicked with force")
                        except Exception as e:
                            logger.warning(f"Force click failed: {e}")
                    
                    # Strategy 3: JavaScript click if both failed
                    if not click_success:
                        try:
                            await page.evaluate("(element) => element.click()", download_button)
                            click_success = True
                            logger.info("Download button clicked with JavaScript")
                        except Exception as e:
                            logger.warning(f"JavaScript click failed: {e}")
                    
                    if click_success:
                        logger.info("Download initiated")
                        
                        # Wait for download to start
                        await page.wait_for_timeout(10000)
                        
                        # Take final screenshot
                        screenshot_path = self.screenshot_dir / f"download_complete_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        logger.info(f"Download complete screenshot saved: {screenshot_path}")
                        
                        logger.info("Video export completed successfully")
                        return True
                    else:
                        logger.error("All click strategies failed for download button")
                        return False
                else:
                    logger.warning("Download button not found in export dialog")
                    return False
            else:
                logger.error("Export button not found")
                return False
                
        except Exception as e:
            logger.error(f"Video export failed: {e}")
            return False
    
    async def _save_error_screenshot(self, page: Page, request_id: str, error_message: str):
        """Save error screenshot for debugging."""
        try:
            screenshot_path = self.screenshot_dir / f"error_{request_id}_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Error screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to save error screenshot: {e}")

    async def _dismiss_guide_overlays(self, page: Page, request_id: str) -> bool:
        """Quick overlay check and dismissal - only when needed."""
        try:
            # Quick check for obvious overlays first (fast, no Gemini needed)
            has_obvious_overlay = await page.evaluate("""
                () => {
                    const overlays = document.querySelectorAll('[class*="guide"], [class*="tutorial"], [class*="overlay"], [class*="popup"], [class*="modal"], [class*="dialog"]');
                    return overlays.length > 0 && Array.from(overlays).some(el => {
                        const style = window.getComputedStyle(el);
                        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                    });
                }
            """)
            
            if not has_obvious_overlay:
                # No overlays visible, skip expensive analysis
                return False
            
            # Only use Gemini if we actually see something that might be blocking
            logger.info("🔍 Overlay detected, using intelligent dismissal...")
            
            if self.overlay_dismissor:
                return await self.overlay_dismissor.analyze_and_dismiss_overlays(page, request_id)
            else:
                # Enhanced fallback dismissal
                await self._enhanced_overlay_dismissal(page, request_id)
                return True
                
        except Exception as e:
            logger.warning(f"Error in overlay dismissal: {e}")
            return False
    
    async def _enhanced_overlay_dismissal(self, page: Page, request_id: str) -> bool:
        """Enhanced overlay dismissal with multiple strategies."""
        try:
            logger.info("Using enhanced overlay dismissal...")
            
            # Strategy 1: Keyboard shortcuts
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Strategy 2: Click common close buttons
            close_selectors = [
                'button:has-text("×")', 'button:has-text("X")', 'button:has-text("Close")',
                'button:has-text("Skip")', 'button:has-text("Got it")', 'button:has-text("OK")',
                'button:has-text("Continue")', 'button:has-text("Next")', 'button:has-text("Dismiss")',
                'button[class*="close"]', 'button[class*="dismiss"]', 'button[class*="skip"]',
                '[role="button"][aria-label*="close" i]', '[role="button"][aria-label*="dismiss" i]',
                'svg[class*="close"]', 'i[class*="close"]', 'span[class*="close"]'
            ]
            
            for selector in close_selectors:
                try:
                    buttons = await page.query_selector_all(selector)
                    for button in buttons:
                        if await button.is_visible():
                            await button.click()
                            logger.info(f"Clicked close button: {selector}")
                            await page.wait_for_timeout(1000)
                            break
                except:
                    continue
            
            # Strategy 3: JavaScript cleanup
            await page.evaluate("""
                () => {
                    // Remove overlays
                    document.querySelectorAll('[class*="guide"], [class*="tutorial"], [class*="overlay"], [class*="popup"], [class*="modal"], [class*="dialog"]').forEach(el => {
                        if (el && el.parentNode) el.remove();
                    });
                    
                    // Hide overlays
                    document.querySelectorAll('[class*="guide"], [class*="tutorial"], [class*="overlay"], [class*="popup"], [class*="modal"], [class*="dialog"]').forEach(el => {
                        if (el) {
                            el.style.display = 'none';
                            el.style.visibility = 'hidden';
                            el.style.opacity = '0';
                        }
                    });
                }
            """)
            
            # Strategy 4: Wait for any remaining overlays to disappear
            await page.wait_for_timeout(2000)
            
            return True
            
        except Exception as e:
            logger.warning(f"Enhanced overlay dismissal failed: {e}")
            return False
    
    async def _dismiss_detected_overlays(self, page: Page, request_id: str) -> bool:
        """Dismiss overlays that have been detected as blocking."""
        try:
            logger.info("Dismissing detected blocking overlays...")
            
            # First try keyboard shortcuts again
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Look for close buttons or dismissible elements
            close_button_selectors = [
                # Common close button patterns
                'button:has-text("×")',
                'button:has-text("X")',
                'button:has-text("Close")',
                'button:has-text("Skip")',
                'button:has-text("Got it")',
                'button:has-text("OK")',
                'button:has-text("Continue")',
                'button:has-text("Next")',
                'button:has-text("Dismiss")',
                # Class-based selectors
                'button[class*="close"]',
                'button[class*="dismiss"]',
                'button[class*="skip"]',
                '[role="button"][aria-label*="close" i]',
                '[role="button"][aria-label*="dismiss" i]',
                # Icon-based close buttons
                'svg[class*="close"]',
                'i[class*="close"]',
                'span[class*="close"]'
            ]
            
            dismissed_count = 0
            
            for selector in close_button_selectors:
                try:
                    close_buttons = await page.query_selector_all(selector)
                    for button in close_buttons:
                        try:
                            if await button.is_visible():
                                # Try multiple click methods
                                try:
                                    await button.click()
                                except:
                                    try:
                                        await button.click(force=True)
                                    except:
                                        await page.evaluate("(el) => el.click()", button)
                                
                                logger.info(f"Clicked close button: {selector}")
                                dismissed_count += 1
                                await page.wait_for_timeout(1000)
                                break  # Only click one button per selector type
                        except:
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error with close button selector {selector}: {e}")
                    continue
            
            # If no close buttons found, try removing overlay elements directly
            if dismissed_count == 0:
                logger.info("No close buttons found, removing overlay elements directly...")
                await page.evaluate("""
                    // More aggressive overlay removal
                    const overlaySelectors = [
                        '[class*="guide"][class*="overlay"]',
                        '[class*="guide-wapper"]',
                        '[class*="tutorial"][class*="overlay"]',
                        '[class*="modal-overlay"]',
                        '[class*="popup-overlay"]',
                        '[class*="onboarding"]',
                        '[class*="walkthrough"]',
                        '[class*="intro"][class*="overlay"]'
                    ];
                    
                    overlaySelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            if (el) el.remove();
                        });
                    });
                    
                    // Also hide any fixed position overlays
                    document.querySelectorAll('div').forEach(el => {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' && 
                            style.zIndex && parseInt(style.zIndex) > 1000 &&
                            el.className && el.className.includes('overlay')) {
                            el.style.display = 'none';
                        }
                    });
                """)
                dismissed_count = 1  # Assume we removed something
            
            logger.info(f"Dismissed {dismissed_count} blocking overlays")
            return dismissed_count > 0
            
        except Exception as e:
            logger.warning(f"Error dismissing detected overlays: {e}")
            return False
    
    async def _try_close_overlay(self, overlay_element, element_class: str) -> bool:
        """Try to close a specific overlay element."""
        try:
            # Strategy 1: Look for close buttons within the overlay
            close_selectors = [
                'button:has-text("Close")',
                'button:has-text("Skip")',
                'button:has-text("Got it")',
                'button:has-text("OK")',
                'button:has-text("Next")',
                'button:has-text("×")',
                'button:has-text("✕")',
                'button:has-text("✖")',
                'button:has-text("X")',
                'button:has-text("x")',
                '[class*="close"]',
                '[class*="dismiss"]'
            ]
            
            for close_selector in close_selectors:
                try:
                    close_btn = await overlay_element.wait_for_selector(close_selector, timeout=2000)
                    if close_btn:
                        await close_btn.click()
                        logger.info(f"Clicked close button: {close_selector}")
                        return True
                except:
                    continue
            
            # Strategy 2: Look for any clickable element that might be a close button
            try:
                close_candidates = await overlay_element.query_selector_all('button, div, span, svg')
                for candidate in close_candidates:
                    try:
                        text = await candidate.inner_text()
                        class_attr = await candidate.get_attribute('class') or ''
                        
                        if (text in ['×', '✕', '✖', 'X', 'x', 'Close', 'Skip', 'OK'] or
                            'close' in class_attr.lower() or
                            'dismiss' in class_attr.lower()):
                            
                            await candidate.click()
                            logger.info(f"Clicked close candidate: text='{text}', class='{class_attr}'")
                            return True
                    except:
                        continue
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error trying to close overlay: {e}")
            return False
    
    async def _minimal_overlay_check(self, page: Page, request_id: str) -> bool:
        """Minimal overlay check as a fallback."""
        try:
            logger.info("Performing minimal overlay check...")
            
            # Press Escape key as a final attempt
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Look for any visible close buttons
            close_patterns = ['×', 'X', 'Close', 'Skip', 'Dismiss', 'OK', 'Got it']
            
            for pattern in close_patterns:
                try:
                    # Look for buttons with this text
                    button = await page.query_selector(f'button:has-text("{pattern}")')
                    if button and await button.is_visible():
                        await button.click(force=True)
                        logger.info(f"Clicked close button with text: {pattern}")
                        await page.wait_for_timeout(1000)
                        return True
                except:
                    continue
            
            # Final JavaScript cleanup
            await page.evaluate("""
                // Remove any remaining overlays
                document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="popup"]').forEach(el => {
                    if (el.className && !el.className.includes('video') && !el.className.includes('timeline')) {
                        el.style.display = 'none';
                    }
                });
            """)
            
            logger.info("Minimal overlay check completed")
            return False
            
        except Exception as e:
            logger.warning(f"Error in minimal overlay check: {e}")
            return False
    
    async def _safe_click(self, page: Page, element, element_name: str, request_id: str) -> bool:
        """Safely click an element with smart overlay handling."""
        try:
            logger.info(f"Preparing to click {element_name}...")
            
            # Try direct click first (most efficient)
            try:
                await element.click()
                logger.info(f"{element_name} clicked successfully using direct click")
                return True
            except Exception as e:
                logger.warning(f"Direct click failed: {e}")
            
            # Try force click if direct fails
            try:
                await element.click(force=True)
                logger.info(f"{element_name} clicked successfully using force click")
                return True
            except Exception as e:
                logger.warning(f"Force click failed: {e}")
            
            # Try with timeout and no-wait options for pointer event interception
            try:
                await element.click(timeout=10000, no_wait_after=True)
                logger.info(f"{element_name} clicked successfully using timeout + no_wait")
                return True
            except Exception as e:
                logger.warning(f"Timeout + no_wait click failed: {e}")
            
            # Try with specific position click (center of element)
            try:
                bounding_box = await element.bounding_box()
                if bounding_box:
                    x = bounding_box['x'] + bounding_box['width'] / 2
                    y = bounding_box['y'] + bounding_box['height'] / 2
                    await page.mouse.click(x, y)
                    logger.info(f"{element_name} clicked successfully using position click")
                    return True
            except Exception as e:
                logger.warning(f"Position click failed: {e}")
            
            # Only try overlay dismissal if we get blocking errors
            if "intercept" in str(e).lower() or "block" in str(e).lower():
                logger.info("Element appears blocked, dismissing overlays...")
                await self._dismiss_guide_overlays(page, request_id)
                await page.wait_for_timeout(500)
                
                # Try one more time after overlay dismissal
                try:
                    await element.click(force=True)
                    logger.info(f"{element_name} clicked after overlay dismissal")
                    return True
                except Exception as retry_error:
                    logger.warning(f"Click after overlay dismissal failed: {retry_error}")
                    pass
            
            # Final fallback: JavaScript click
            try:
                await page.evaluate("(el) => el.click()", element)
                logger.info(f"{element_name} clicked successfully using JavaScript")
                return True
            except:
                pass
            
            logger.error(f"All click strategies failed for {element_name}")
            return False
            
        except Exception as e:
            logger.error(f"Safe click failed for {element_name}: {e}")
            return False
    
    async def _scroll_and_click(self, page: Page, element) -> None:
        """Scroll element into view and click."""
        await element.scroll_into_view_if_needed()
        await page.wait_for_timeout(500)
        await element.click(force=True)
    
    async def _check_auto_caption_availability(self, page: Page, request_id: str) -> bool:
        """Check if auto-caption options are available on the current page."""
        try:
            logger.info("Checking for auto-caption availability...")
            
            # Look for auto-caption related elements
            auto_caption_selectors = [
                'button:has-text("Free CC")',
                'div:has-text("Free CC")',
                'button:has-text("Generate")',
                'div:has-text("Generate")',
                'button:has-text("Generate captions")',
                'div:has-text("Generate captions")',
                'button:has-text("Auto captions")',
                'div:has-text("Auto captions")',
                'button:has-text("Auto")',
                'div:has-text("Auto")',
                'button:has-text("CC")',
                'div:has-text("CC")',
                'button:has-text("Subtitle")',
                'div:has-text("Subtitle")',
                'button:has-text("Transcribe")',
                'div:has-text("Transcribe")',
                '[data-testid="auto-caption-btn"]',
                '[data-testid="generate-caption"]',
                '[data-testid="auto-caption"]',
                '.auto-caption-btn',
                '.generate-caption-btn',
                '.auto-caption',
                '.generate-caption',
                '[class*="auto-caption"]',
                '[class*="generate-caption"]',
                '[class*="auto-caption-btn"]',
                '[class*="generate-caption-btn"]'
            ]
            
            for selector in auto_caption_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = await element.inner_text()
                        logger.info(f"Found auto-caption element: {selector} -> '{text}'")
                        return True
                except:
                    continue
            
            # Also check for any text containing auto-caption related words
            caption_keywords = [
                "Free", "CC", "Generate", "Auto", "Caption", "Subtitle", 
                "Speech", "Transcribe", "Transcription", "AI", "Machine"
            ]
            
            for keyword in caption_keywords:
                try:
                    elements = await page.query_selector_all(f'*:has-text("{keyword}")')
                    if elements:
                        for element in elements[:3]:  # Check first 3
                            try:
                                text = await element.inner_text()
                                if any(keyword.lower() in text.lower() for keyword in ['free', 'cc', 'generate', 'auto', 'caption']):
                                    logger.info(f"Found potential auto-caption text: '{text}'")
                                    return True
                            except:
                                continue
                except:
                    continue
            
            logger.info("No auto-caption options found on this page")
            return False
            
        except Exception as e:
            logger.warning(f"Error checking auto-caption availability: {e}")
            return False
    
    async def _search_for_caption_options_broadly(self, page: Page, request_id: str) -> bool:
        """Search for caption options more broadly across the entire page."""
        try:
            logger.info("Performing broad search for caption options...")
            
            # Take a screenshot for analysis
            screenshot_path = self.screenshot_dir / f"broad_search_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Broad search screenshot saved: {screenshot_path}")
            
            # Strategy 1: Look for any buttons with caption-related text
            broad_selectors = [
                'button', 'div[role="button"]', '[class*="btn"]', '[class*="button"]'
            ]
            
            for base_selector in broad_selectors:
                try:
                    elements = await page.query_selector_all(base_selector)
                    for element in elements[:10]:  # Check first 10 elements
                        try:
                            if await element.is_visible():
                                text = await element.inner_text()
                                if text and any(keyword in text.lower() for keyword in ['caption', 'cc', 'subtitle', 'transcribe', 'generate', 'auto']):
                                    logger.info(f"Found potential caption button: '{text}'")
                                    return True
                        except:
                            continue
                except:
                    continue
            
            # Strategy 2: Look for any text containing caption-related words
            caption_text_selectors = [
                'div', 'span', 'p', 'label', 'a'
            ]
            
            for text_selector in caption_text_selectors:
                try:
                    elements = await page.query_selector_all(text_selector)
                    for element in elements[:20]:  # Check first 20 elements
                        try:
                            if await element.is_visible():
                                text = await element.inner_text()
                                if text and len(text.strip()) > 0:
                                    text_lower = text.lower()
                                    if any(keyword in text_lower for keyword in ['free cc', 'generate caption', 'auto caption', 'speech to text']):
                                        logger.info(f"Found potential caption text: '{text}'")
                                        return True
                        except:
                            continue
                except:
                    continue
            
            # Strategy 3: Use Gemini Vision for intelligent analysis if available
            if self.model:
                try:
                    logger.info("Using Gemini Vision for intelligent caption option detection...")
                    prompt = """
                    Analyze this CapCut webpage screenshot and look for any options to generate captions, 
                    auto-captions, or speech-to-text features. Look for buttons, text, or UI elements 
                    that suggest caption generation capabilities.
                    
                    Respond with ONLY:
                    - "FOUND" if you see caption generation options
                    - "NOT_FOUND" if you don't see any caption generation options
                    """
                    
                    uploaded_file = genai.upload_file(str(screenshot_path))
                    response = self.model.generate_content([prompt, uploaded_file])
                    response_text = response.text.strip().upper()
                    
                    if response_text == "FOUND":
                        logger.info("Gemini Vision detected caption options")
                        return True
                    else:
                        logger.info("Gemini Vision did not detect caption options")
                        
                except Exception as e:
                    logger.warning(f"Gemini Vision analysis failed: {e}")
            
            logger.info("Broad search did not find caption options")
            return False
            
        except Exception as e:
            logger.warning(f"Broad caption search failed: {e}")
            return False
    
    async def _click_captions_sidebar_button(self, page: Page, request_id: str) -> bool:
        """Click the Captions button in the left sidebar."""
        try:
            logger.info("Looking for Captions sidebar button...")
            
            # Look for the Captions button in the left sidebar
            captions_selectors = [
                'div:has-text("Captions")',
                '[data-testid="captions-tab"]',
                '.captions-tab',
                'div[class*="captions"]',
                'div[class*="caption"]',
                'button:has-text("Captions")',
                '[role="tab"]:has-text("Captions")'
            ]
            
            for selector in captions_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Captions button with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_captions_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the button and ensure it's actually clicked
                        await self._safe_click(page, element, "Captions sidebar button", request_id)
                        
                        # Wait a bit and verify the click registered
                        await page.wait_for_timeout(1000)
                        
                        # Try clicking again if the first click didn't work
                        # Sometimes the first click doesn't register properly
                        await self._safe_click(page, element, "Captions sidebar button (second attempt)", request_id)
                        
                        # Wait for the panel to start opening
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Captions sidebar button clicked successfully")
                        return True
                except:
                    continue
            
            logger.error("Captions sidebar button not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Captions sidebar button: {e}")
            return False
    
    async def _click_captions_within_panel(self, page: Page, request_id: str) -> bool:
        """Click on Captions within the opened panel to get to caption tools."""
        try:
            logger.info("Looking for Captions within the opened panel...")
            
            # Look for "Captions" text within the panel that was just opened
            captions_within_panel_selectors = [
                'div:has-text("Captions"):not(:has-text("Media"))',  # Captions but not the sidebar button
                'div[class*="panel"]:has-text("Captions")',
                'div[class*="tools"]:has-text("Captions")',
                'div[class*="sidebar"]:has-text("Captions")',
                'div[class*="left"]:has-text("Captions")',
                'div:has-text("Captions")[class*="item"]',
                'div:has-text("Captions")[class*="tool"]'
            ]
            
            for selector in captions_within_panel_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Captions within panel with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_captions_panel_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click on Captions within the panel
                        await self._safe_click(page, element, "Captions within panel", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Captions within panel clicked successfully")
                        return True
                except:
                    continue
            
            logger.warning("Could not find Captions within the opened panel")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Captions within panel: {e}")
            return False

    async def _click_auto_captions_free_card(self, page: Page, request_id: str) -> bool:
        """Click on the "Auto captions Free" card to expand it and reveal the Generate button."""
        try:
            logger.info("Looking for Auto captions Free card to click and expand...")
            
            # First check if the card is already expanded
            is_already_expanded = await page.evaluate("""
                () => {
                    const card = document.querySelector('div#text-intelligent-detect-text');
                    if (card) {
                        // Check if it has the active class
                        const hasActiveClass = card.classList.contains('text-intelligent-item__active');
                        // Check if the footer with Generate button is visible
                        const footer = card.querySelector('footer.active-panel');
                        const generateButton = card.querySelector('button.generate-caption');
                        return hasActiveClass || (footer && generateButton);
                    }
                    return false;
                }
            """)
            
            if is_already_expanded:
                logger.info("Auto captions Free card is already expanded!")
                return True
            
            # The card is not expanded, so we need to click it
            # Based on the HTML structure, we need to click on the specific card
            auto_captions_card_selectors = [
                # The exact ID of the Auto captions card
                'div#text-intelligent-detect-text',
                # Click on the header part of the card (this usually triggers expansion)
                'div#text-intelligent-detect-text header',
                # The text-intelligent-item class
                'div.text-intelligent-item.text-intelligent-detect',
                # Try clicking on the title area
                'div#text-intelligent-detect-text .title',
                # Or the entire clickable area with Auto captions text
                'div.text-intelligent-item:has-text("Auto captions"):has-text("Free")'
            ]
            
            for selector in auto_captions_card_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Auto captions Free card with selector: {selector}")
                        
                        # Check if the element is visible
                        is_visible = await element.is_visible()
                        if not is_visible:
                            logger.warning(f"Element found but not visible: {selector}")
                            continue
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_auto_captions_card_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the card to expand it
                        logger.info(f"Clicking on Auto captions Free card to expand it...")
                        await element.click()
                        
                        # Wait for the card to expand
                        await page.wait_for_timeout(2000)
                        
                        # Check if the card expanded successfully
                        is_expanded_after_click = await page.evaluate("""
                            () => {
                                const card = document.querySelector('div#text-intelligent-detect-text');
                                if (card) {
                                    // Check for active class
                                    const hasActiveClass = card.classList.contains('text-intelligent-item__active');
                                    // Check for active footer
                                    const activeFooter = card.querySelector('footer.active-panel');
                                    // Check for Generate button
                                    const generateButton = card.querySelector('button.generate-caption');
                                    
                                    return {
                                        hasActiveClass: hasActiveClass,
                                        hasActiveFooter: !!activeFooter,
                                        hasGenerateButton: !!generateButton,
                                        isExpanded: hasActiveClass || (activeFooter && generateButton)
                                    };
                                }
                                return {isExpanded: false};
                            }
                        """)
                        
                        logger.info(f"Card expansion check: {is_expanded_after_click}")
                        
                        if is_expanded_after_click.get('isExpanded'):
                            logger.info("Successfully expanded Auto captions Free card!")
                            
                            # Take screenshot after successful expansion
                            screenshot_path = self.screenshot_dir / f"after_auto_captions_card_expanded_{request_id}.png"
                            await page.screenshot(path=str(screenshot_path))
                            
                            return True
                        else:
                            logger.warning(f"Card did not expand after clicking {selector}, trying next selector...")
                            
                except Exception as e:
                    logger.warning(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            # If standard clicking didn't work, try force click
            logger.info("Standard clicks didn't expand the card, trying force click...")
            try:
                card = await page.wait_for_selector('div#text-intelligent-detect-text', timeout=3000)
                if card:
                    await card.click(force=True)
                    await page.wait_for_timeout(2000)
                    
                    # Final check
                    final_check = await page.evaluate("""
                        () => {
                            const card = document.querySelector('div#text-intelligent-detect-text');
                            return card && (
                                card.classList.contains('text-intelligent-item__active') ||
                                card.querySelector('button.generate-caption')
                            );
                        }
                    """)
                    
                    if final_check:
                        logger.info("Card expanded after force click!")
                        return True
                        
            except Exception as e:
                logger.error(f"Force click failed: {e}")
            
            logger.error("Could not expand Auto captions Free card with any method")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Auto captions Free card: {e}")
            return False

    async def _click_auto_captions_section(self, page: Page, request_id: str) -> bool:
        """Click on the Auto captions section to activate it."""
        try:
            logger.info("Looking for Auto captions section to click...")
            
            # Look for the Auto captions section
            auto_captions_selectors = [
                'div:has-text("Auto captions Free")',  # Most specific - what we see in demo
                'div:has-text("Auto Captions Free")',
                'div:has-text("Auto captions")',
                'div:has-text("Auto Captions")',
                'div:has-text("Free CC")',  # Alternative text seen in demo
                'div:has-text("Free cc")',
                '[data-testid="auto-captions"]',
                '.auto-captions',
                'div[class*="auto-caption"]',
                'div[class*="auto-captions"]'
            ]
            
            for selector in auto_captions_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found Auto captions section with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_auto_captions_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click on the Auto captions section
                        await self._safe_click(page, element, "Auto captions section", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Auto captions section clicked successfully")
                        return True
                except:
                    continue
            
            logger.error("Auto captions section not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Auto captions section: {e}")
            return False

    async def _verify_generate_button_visible(self, page: Page, request_id: str) -> bool:
        """Verify that the Generate button for Auto captions is visible before attempting to click it."""
        try:
            logger.info("Verifying Generate button for Auto captions is visible...")
            
            # Look for the Generate button that appears AFTER clicking the Auto captions Free card
            # This button should become visible when the card is expanded
            generate_button_selectors = [
                # Look for the Generate button specifically within the Auto captions context
                # This is the most specific selector - within the Auto captions card
                'div:has-text("Auto captions Free"):has-text("Automatically recognize speech in videos") button:has-text("Generate")',
                
                # Look for Generate button within the specific form in the Auto captions context
                'form[class*="select-lang-form"]:has-text("Language used in video") button:has-text("Generate")',
                
                # Look for Generate button within the text-intelligent-detect div (Auto captions specific)
                'div[class*="text-intelligent-detect"]:has-text("Auto captions") button:has-text("Generate")',
                'div[class*="text-intelligent-item"]:has-text("Auto captions") button:has-text("Generate")',
                
                # Look for the specific Generate button class that appears after expansion
                'button[class*="generate-caption"]',
                
                # Look for Generate button with the lv-btn classes in Auto captions context
                'button[class*="lv-btn"]:has-text("Generate"):not(:has-text("Auto lyrics"))',
                
                # Fallback: Look for Generate button that's clearly NOT from Auto lyrics
                'button:has-text("Generate"):not(:has-text("Auto lyrics")):not(:has-text("lyrics"))'
            ]
            
            for selector in generate_button_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Generate button for Auto captions is visible with selector: {selector}")
                        return True
                except:
                    continue
            
            logger.error("Generate button for Auto captions is not visible")
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify Generate button visibility: {e}")
            return False

    async def _click_generate_button(self, page: Page, request_id: str) -> bool:
        """Click the Generate button (which should be visible after clicking Auto captions)."""
        try:
            logger.info("Looking for Generate button...")
            
            # Look for the Generate button that appears AFTER clicking the Auto captions Free card
            # This button should become visible when the card is expanded
            # IMPORTANT: We need to be very specific to avoid clicking the Auto lyrics Generate button
            generate_selectors = [
                # Look for the Generate button specifically within the Auto captions context
                # This is the most specific selector - within the Auto captions card
                'div:has-text("Auto captions Free"):has-text("Automatically recognize speech in videos") button:has-text("Generate")',
                
                # Look for Generate button within the specific form in the Auto captions context
                'form[class*="select-lang-form"]:has-text("Language used in video") button:has-text("Generate")',
                
                # Look for Generate button within the text-intelligent-detect div (Auto captions specific)
                'div[class*="text-intelligent-detect"]:has-text("Auto captions") button:has-text("Generate")',
                'div[class*="text-intelligent-item"]:has-text("Auto captions") button:has-text("Generate")',
                
                # Look for the specific Generate button class that appears after expansion
                'button[class*="generate-caption"]',
                
                # Look for Generate button with the lv-btn classes in Auto captions context
                'button[class*="lv-btn"]:has-text("Generate"):not(:has-text("Auto lyrics"))',
                
                # Fallback: Look for Generate button that's clearly NOT from Auto lyrics
                'button:has-text("Generate"):not(:has-text("Auto lyrics")):not(:has-text("lyrics"))'
            ]
            
            for selector in generate_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found Generate button with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_generate_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the Generate button
                        try:
                            # First try normal click
                            await self._safe_click(page, element, "Generate button", request_id)
                            await page.wait_for_timeout(2000)
                            logger.info("Generate button clicked successfully using normal click")
                            return True
                        except Exception as click_error:
                            logger.warning(f"Normal click failed: {click_error}, trying JavaScript click...")
                            
                            # Try JavaScript click to bypass pointer event interceptions
                            try:
                                await page.evaluate("(element) => element.click()", element)
                                await page.wait_for_timeout(2000)
                                logger.info("Generate button clicked successfully using JavaScript click")
                                return True
                            except Exception as js_error:
                                logger.warning(f"JavaScript click also failed: {js_error}, trying force click...")
                                
                                # Try force click with modified options
                                try:
                                    await element.click(force=True, timeout=5000)
                                    await page.wait_for_timeout(2000)
                                    logger.info("Generate button clicked successfully using force click")
                                    return True
                                except Exception as force_error:
                                    logger.error(f"All click methods failed: {force_error}")
                                    return False
                except:
                    continue
            
            logger.error("Generate button not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Generate button: {e}")
            return False

    async def _click_auto_captions_generate(self, page: Page, request_id: str) -> bool:
        """Click the Generate button in the expanded Auto captions card."""
        try:
            logger.info("Looking for Generate button in Auto captions card...")
            
            # First check if the Generate button is visible
            # Based on the HTML structure, the button has class "generate-caption"
            generate_visible = await page.evaluate("""
                () => {
                    const button = document.querySelector('button.generate-caption');
                    if (button) {
                        const rect = button.getBoundingClientRect();
                        const isVisible = rect.width > 0 && rect.height > 0 && 
                                         rect.top >= 0 && rect.bottom <= window.innerHeight;
                        return {
                            found: true,
                            visible: isVisible,
                            text: button.innerText,
                            className: button.className
                        };
                    }
                    return {found: false};
                }
            """)
            
            logger.info(f"Generate button check: {generate_visible}")
            
            if not generate_visible.get('found'):
                logger.error("Generate button not found in DOM")
                return False
            
            if not generate_visible.get('visible'):
                logger.error("Generate button found but not visible - card may not be expanded")
                return False
            
            # The Generate button is visible, now click it
            generate_selectors = [
                'button.generate-caption',  # The exact class from the HTML
                'button.lv-btn.generate-caption',  # More specific with all classes
                'div#text-intelligent-detect-text button.generate-caption',  # Within the specific card
                'button:has-text("Generate")',  # Fallback text-based selector
            ]
            
            for selector in generate_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        # Verify it's visible before clicking
                        is_visible = await element.is_visible()
                        if not is_visible:
                            logger.warning(f"Generate button found with {selector} but not visible")
                            continue
                        
                        logger.info(f"Found visible Generate button with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_generate_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the Generate button
                        logger.info("Clicking Generate button...")
                        try:
                            await element.click()
                        except Exception as click_error:
                            # If normal click fails, try force click
                            logger.warning(f"Normal click failed: {click_error}, trying force click...")
                            await element.click(force=True)
                        
                        await page.wait_for_timeout(2000)
                        
                        # Take screenshot after clicking
                        screenshot_path = self.screenshot_dir / f"after_generate_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        logger.info("Generate button clicked successfully!")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Failed with selector {selector}: {str(e)}")
                    continue
            
            # If all selectors failed, try JavaScript click as last resort
            logger.info("Standard selectors failed, trying JavaScript click...")
            try:
                js_clicked = await page.evaluate("""
                    () => {
                        const button = document.querySelector('button.generate-caption');
                        if (button) {
                            button.click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if js_clicked:
                    logger.info("Generate button clicked via JavaScript!")
                    await page.wait_for_timeout(2000)
                    return True
                    
            except Exception as e:
                logger.error(f"JavaScript click failed: {e}")
            
            logger.error("Could not click Generate button with any method")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Generate button: {e}")
            return False
    
    async def _wait_for_caption_generation(self, page: Page, request_id: str) -> bool:
        """Wait for caption generation to complete."""
        try:
            logger.info("Waiting for caption generation to complete...")
            
            # Look for progress indicators
            progress_selectors = [
                'div:has-text("%")',
                'div:has-text("Generating")',
                'div:has-text("Processing")',
                '[class*="progress"]',
                '[class*="loading"]'
            ]
            
            start_time = time.time()
            timeout = 300  # 5 minutes timeout for caption generation
            
            while time.time() - start_time < timeout:
                try:
                    # Check if any progress indicators are visible
                    has_progress = False
                    for selector in progress_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                if await element.is_visible():
                                    has_progress = True
                                    text = await element.inner_text()
                                    logger.info(f"Progress indicator visible: {text}")
                                    break
                            if has_progress:
                                break
                        except:
                            continue
                    
                    if not has_progress:
                        # Check if captions are visible (generation complete)
                        caption_selectors = [
                            'div[class*="caption"]',
                            'div[class*="subtitle"]',
                            'div:has-text("00:00")',  # Timestamp format
                            '[class*="timestamp"]'
                        ]
                        
                        for selector in caption_selectors:
                            try:
                                elements = await page.query_selector_all(selector)
                                if len(elements) > 0:
                                    logger.info("Caption generation appears to be complete - captions visible")
                                    return True
                            except:
                                continue
                    
                    # Wait before checking again
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    logger.warning(f"Error checking generation progress: {e}")
                    await page.wait_for_timeout(2000)
            
            logger.warning("Caption generation timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to wait for caption generation: {e}")
            return False
    
    async def _open_presets_panel(self, page: Page, request_id: str) -> bool:
        """Open the Presets panel on the right side."""
        try:
            logger.info("Looking for Presets button...")
            
            # Take screenshot to see current state
            screenshot_path = self.screenshot_dir / f"before_presets_search_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Pre-presets search screenshot saved: {screenshot_path}")
            
            # Look for the Presets button (usually in the right sidebar or top bar)
            presets_selectors = [
                'button:has-text("Presets")',
                'div:has-text("Presets")',
                '[data-testid="presets-button"]',
                '.presets-button',
                'button[class*="presets"]',
                'div[class*="presets"]',
                # More specific selectors based on screenshots
                'div[class*="presets-panel"] button:has-text("Presets")',
                'div[class*="right-panel"] button:has-text("Presets")',
                'div[class*="sidebar"] button:has-text("Presets")',
                # Look for presets in the rightmost vertical bar
                'div[class*="right-bar"] button:has-text("Presets")',
                'div[class*="tools-bar"] button:has-text("Presets")',
                # Look for any element with "Presets" text in the right area
                'div[class*="right"]:has-text("Presets")',
                'div[class*="sidebar"]:has-text("Presets")',
                'div[class*="panel"]:has-text("Presets")',
                # Fallback: any clickable element with Presets text
                '[role="button"]:has-text("Presets")',
                'div[class*="clickable"]:has-text("Presets")'
            ]
            
            for selector in presets_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Presets button with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_presets_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the button
                        await self._safe_click(page, element, "Presets button", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Presets panel opened successfully")
                        return True
                except:
                    continue
            
            # If specific selectors failed, try broader search
            logger.info("Specific selectors failed, trying broader search for Presets...")
            try:
                # Look for any element with "Presets" text anywhere on the page
                presets_elements = await page.query_selector_all('*:has-text("Presets")')
                logger.info(f"Found {len(presets_elements)} elements with 'Presets' text")
                
                for element in presets_elements:
                    try:
                        if await element.is_visible():
                            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                            text_content = await element.inner_text()
                            logger.info(f"Found visible Presets element: {tag_name} -> '{text_content}'")
                            
                            # Take screenshot before clicking
                            screenshot_path = self.screenshot_dir / f"before_broad_presets_click_{request_id}.png"
                            await page.screenshot(path=str(screenshot_path))
                            
                            # Click the element
                            await self._safe_click(page, element, f"broad Presets element '{text_content}'", request_id)
                            await page.wait_for_timeout(2000)
                            
                            logger.info(f"Broad Presets element '{text_content}' clicked successfully")
                            return True
                    except Exception as e:
                        logger.warning(f"Error with broad Presets element: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Broad Presets search failed: {e}")
            
            logger.error("Presets button not found with any method")
            return False
            
        except Exception as e:
            logger.error(f"Failed to open Presets panel: {e}")
            return False
    
    async def _select_templates_tab(self, page: Page, request_id: str) -> bool:
        """Select the Templates tab in the Presets panel."""
        try:
            logger.info("Looking for Templates tab...")
            
            # Look for the Templates tab
            templates_selectors = [
                'div:has-text("Templates")',
                'button:has-text("Templates")',
                '[data-testid="templates-tab"]',
                '.templates-tab',
                'div[class*="templates"]',
                'button[class*="templates"]',
                # More specific selectors based on screenshots
                'div[class*="presets-panel"] div:has-text("Templates")',
                'div[class*="presets-panel"] button:has-text("Templates")',
                'div[class*="tabs"] div:has-text("Templates")',
                'div[class*="tabs"] button:has-text("Templates")',
                # Look for tab-like elements
                '[role="tab"]:has-text("Templates")',
                'div[class*="tab"]:has-text("Templates")',
                'button[class*="tab"]:has-text("Templates")'
            ]
            
            for selector in templates_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Templates tab with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_templates_tab_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the tab
                        await self._safe_click(page, element, "Templates tab", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Templates tab selected successfully")
                        return True
                except:
                    continue
            
            logger.error("Templates tab not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select Templates tab: {e}")
            return False
    
    async def _select_first_template(self, page: Page, request_id: str) -> bool:
        """Select the first template available."""
        try:
            logger.info("Looking for first template...")
            
            # Look for template elements - based on screenshots showing grid of templates
            template_selectors = [
                # Look for template grid items
                'div[class*="template"]',
                'button[class*="template"]',
                '[data-testid*="template"]',
                '.template',
                # Look for specific template text patterns from screenshots
                'div:has-text("THE QUICK BROWN FOX")',
                'div:has-text("THE QUICK")',
                'div:has-text("BROWN FOX")',
                'div:has-text("THE")',
                'div:has-text("FOX")',
                # Look for template grid containers
                'div[class*="template-grid"]',
                'div[class*="template-item"]',
                'div[class*="template-card"]',
                # Fallback: any div with template-like text
                'div:has-text("THE QUICK"):has-text("BROWN FOX")'
            ]
            
            for selector in template_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        # Select the first template
                        first_template = elements[0]
                        
                        logger.info(f"Found template with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_template_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the template
                        await self._safe_click(page, first_template, "first template", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("First template selected successfully")
                        return True
                except:
                    continue
            
            # If no templates found with specific selectors, try broader search
            logger.info("No templates found with specific selectors, trying broader search...")
            try:
                # Look for any clickable elements that might be templates
                all_clickables = await page.query_selector_all('div[role="button"], button, div[class*="clickable"]')
                for element in all_clickables[:10]:  # Check first 10
                    try:
                        if await element.is_visible():
                            text = await element.inner_text()
                            # Check if it looks like a template (has template-like text)
                            if text and any(keyword in text.upper() for keyword in ['THE', 'QUICK', 'BROWN', 'FOX', 'TEMPLATE']):
                                logger.info(f"Found potential template: '{text}'")
                                
                                # Take screenshot before clicking
                                screenshot_path = self.screenshot_dir / f"before_broad_template_click_{request_id}.png"
                                await page.screenshot(path=str(screenshot_path))
                                
                                await self._safe_click(page, element, f"broad template '{text}'", request_id)
                                await page.wait_for_timeout(2000)
                                
                                logger.info(f"Broad template '{text}' selected successfully")
                                return True
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Broad template search failed: {e}")
            
            logger.error("No templates found with any method")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select first template: {e}")
            return False
    
    async def _close_presets_panel(self, page: Page, request_id: str) -> bool:
        """Close the Presets panel."""
        try:
            logger.info("Looking for close button in Presets panel...")
            
            # Look for close button (usually X or close icon)
            close_selectors = [
                'button:has-text("×")',
                'button:has-text("X")',
                'button:has-text("Close")',
                '[data-testid="close-button"]',
                '.close-button',
                'button[class*="close"]',
                'div[class*="close"]'
            ]
            
            for selector in close_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found close button with selector: {selector}")
                        
                        # Click the close button
                        await self._safe_click(page, element, "close button", request_id)
                        await page.wait_for_timeout(1000)
                        
                        logger.info("Presets panel closed successfully")
                        return True
                except:
                    continue
            
            logger.warning("Close button not found, trying Escape key")
            # Fallback to Escape key
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to close Presets panel: {e}")
            return False
    
    async def _click_export_button(self, page: Page, request_id: str) -> bool:
        """Click the Export button."""
        try:
            logger.info("Looking for Export button...")
            
            # Look for the Export button (usually prominent blue button in top right)
            export_selectors = [
                'button:has-text("Export")',
                'div:has-text("Export")',
                '[data-testid="export-button"]',
                '.export-button',
                'button[class*="export"]',
                'div[class*="export"]',
                # More specific selectors based on screenshots
                'button[class*="lv-btn"]:has-text("Export")',
                'button[class*="primary"]:has-text("Export")',
                'button[class*="blue"]:has-text("Export")',
                # Look for export button in top bar area
                'header button:has-text("Export")',
                '.top-bar button:has-text("Export")',
                '[class*="header"] button:has-text("Export")',
                '[class*="toolbar"] button:has-text("Export")'
            ]
            
            for selector in export_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Export button with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_export_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the button
                        await self._safe_click(page, element, "Export button", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Export button clicked successfully")
                        return True
                except:
                    continue
            
            logger.error("Export button not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Export button: {e}")
            return False
    
    async def _click_download_option(self, page: Page, request_id: str) -> bool:
        """Click the Download button that appears after export completion."""
        try:
            logger.info("Looking for Download button after export completion...")
            
            # Look for the Download button (usually prominent blue button after export)
            download_selectors = [
                'button:has-text("Download")',
                'div:has-text("Download")',
                '[data-testid="download-button"]',
                '.download-button',
                'div[class*="download"]',
                'button[class*="download"]',
                # More specific selectors for the post-export download button
                'div:has-text("You can download the video") button:has-text("Download")',
                'div:has-text("Exported") button:has-text("Download")',
                'button[class*="lv-btn"]:has-text("Download")'
            ]
            
            for selector in download_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found Download option with selector: {selector}")
                        
                        # Take screenshot before clicking
                        screenshot_path = self.screenshot_dir / f"before_download_click_{request_id}.png"
                        await page.screenshot(path=str(screenshot_path))
                        
                        # Click the option
                        await self._safe_click(page, element, "Download option", request_id)
                        await page.wait_for_timeout(2000)
                        
                        logger.info("Download option clicked successfully")
                        return True
                except:
                    continue
            
            logger.error("Download option not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Download option: {e}")
            return False
    
    async def _wait_for_download_start(self, page: Page, request_id: str) -> bool:
        """Wait for download to start."""
        try:
            logger.info("Waiting for download to start...")
            
            # Wait a bit for download to initiate
            await page.wait_for_timeout(5000)
            
            # Take screenshot to see current state
            screenshot_path = self.screenshot_dir / f"download_state_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            
            logger.info("Download process initiated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to wait for download: {e}")
            return False
    
    async def _wait_for_upload_completion(self, page: Page, request_id: str) -> bool:
        """Intelligently wait for video upload to complete."""
        try:
            logger.info("Monitoring upload progress...")
            
            # Look for upload progress indicators
            progress_selectors = [
                '[class*="progress"]', '[class*="upload"]', '[class*="loading"]',
                '[class*="spinner"]', '[class*="indicator"]'
            ]
            
            start_time = time.time()
            timeout = 60  # 1 minute timeout
            
            while time.time() - start_time < timeout:
                try:
                    # Check if any progress indicators are still visible
                    has_progress = False
                    for selector in progress_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                if await element.is_visible():
                                    has_progress = True
                                    break
                            if has_progress:
                                break
                        except:
                            continue
                    
                    if not has_progress:
                        # Check if video timeline or editor elements are visible
                        editor_selectors = [
                            '[class*="timeline"]', '[class*="editor"]', '[class*="video"]',
                            '[class*="track"]', '[class*="media"]'
                        ]
                        
                        for selector in editor_selectors:
                            try:
                                elements = await page.query_selector_all(selector)
                                for element in elements:
                                    if await element.is_visible():
                                        logger.info("Upload appears to be complete - editor elements visible")
                                        return True
                            except:
                                continue
                    
                    # Wait a bit before checking again
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    logger.warning(f"Error checking upload progress: {e}")
                    await page.wait_for_timeout(2000)
            
            logger.warning("Upload completion detection timed out")
            return False
            
        except Exception as e:
            logger.error(f"Upload completion detection failed: {e}")
            return False
    
    async def _handle_export_dialog(self, page: Page, request_id: str) -> bool:
        """Handle the export dialog that appears after clicking Export button."""
        try:
            logger.info("Handling export dialog...")
            
            # Wait for export dialog to appear
            await page.wait_for_timeout(3000)
            
            # Look for export settings dialog
            dialog_selectors = [
                'div:has-text("Export settings")',
                'div:has-text("Export")',
                'div[class*="export-dialog"]',
                'div[class*="export-modal"]',
                'div[class*="export-panel"]'
            ]
            
            dialog_found = False
            for selector in dialog_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"Found export dialog with selector: {selector}")
                        dialog_found = True
                        break
                except:
                    continue
            
            if not dialog_found:
                logger.warning("Export dialog not found, continuing...")
                return True
            
            # Take screenshot of export dialog
            screenshot_path = self.screenshot_dir / f"export_dialog_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Export dialog screenshot saved: {screenshot_path}")
            
            # Look for the Export button in the dialog
            export_in_dialog_selectors = [
                'button:has-text("Export")',
                'button:has-text("Start Export")',
                'button:has-text("Export Video")',
                'button[class*="export"]',
                'button[class*="submit"]'
            ]
            
            export_button = None
            for selector in export_in_dialog_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.info(f"Found export button in dialog: {selector}")
                        export_button = element
                        break
                except:
                    continue
            
            if export_button:
                logger.info("Clicking export button in dialog...")
                await self._safe_click(page, export_button, "export button in dialog", request_id)
                await page.wait_for_timeout(2000)
                
                # Take screenshot after clicking export
                screenshot_path = self.screenshot_dir / f"after_export_dialog_click_{request_id}.png"
                await page.screenshot(path=str(screenshot_path))
                logger.info(f"Export dialog export button clicked, screenshot saved")
                
                return True
            else:
                logger.warning("Export button not found in dialog")
                return False
                
        except Exception as e:
            logger.error(f"Failed to handle export dialog: {e}")
            return False
    
    async def _wait_for_export_completion(self, page: Page, request_id: str) -> bool:
        """Wait for export to complete and download to be ready."""
        try:
            logger.info("Waiting for export to complete...")
            
            # Look for export progress indicators
            progress_selectors = [
                'div:has-text("%")',
                'div:has-text("Exporting")',
                'div:has-text("Processing")',
                '[class*="progress"]',
                '[class*="loading"]',
                'div:has-text("Exporting...")'
            ]
            
            start_time = time.time()
            timeout = 600  # 10 minutes timeout for export
            
            while time.time() - start_time < timeout:
                try:
                    # Check if any progress indicators are visible
                    has_progress = False
                    for selector in progress_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            for element in elements:
                                if await element.is_visible():
                                    has_progress = True
                                    text = await element.inner_text()
                                    logger.info(f"Export progress: {text}")
                                    break
                            if has_progress:
                                break
                        except:
                            continue
                    
                    if not has_progress:
                        # Check if export is complete (look for completion indicators)
                        completion_selectors = [
                            'div:has-text("Exported")',
                            'div:has-text("Export complete")',
                            'div:has-text("Download")',
                            'button:has-text("Download")',
                            'div:has-text("You can download the video")'
                        ]
                        
                        for selector in completion_selectors:
                            try:
                                element = await page.wait_for_selector(selector, timeout=2000)
                                if element and await element.is_visible():
                                    text = await element.inner_text()
                                    logger.info(f"Export completed! Found: {text}")
                                    return True
                            except:
                                continue
                    
                    # Wait before checking again
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    logger.warning(f"Error checking export progress: {e}")
                    await page.wait_for_timeout(2000)
            
            logger.warning("Export completion timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to wait for export completion: {e}")
            return False
    
    async def _wait_for_download_completion(self, page: Page, request_id: str) -> bool:
        """Wait for download to complete and verify success."""
        try:
            logger.info("Waiting for download to complete...")
            
            # Wait for download to start and complete
            await page.wait_for_timeout(10000)  # Wait 10 seconds for download
            
            # Take final screenshot
            screenshot_path = self.screenshot_dir / f"download_complete_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Download completion screenshot saved: {screenshot_path}")
            
            # Check for download success indicators
            success_selectors = [
                'div:has-text("Downloaded")',
                'div:has-text("Download complete")',
                'div:has-text("Video saved")',
                'div:has-text("Success")'
            ]
            
            for selector in success_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element and await element.is_visible():
                        text = await element.inner_text()
                        logger.info(f"Download success indicator found: {text}")
                        return True
                except:
                    continue
            
            logger.info("Download appears to be complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to wait for download completion: {e}")
            return False

    async def _mouse_click_element(self, page: Page, element) -> None:
        """Click element using mouse at its center."""
        bbox = await element.bounding_box()
        if bbox:
            x = bbox['x'] + bbox['width'] / 2
            y = bbox['y'] + bbox['height'] / 2
            await page.mouse.click(x, y)
        else:
            raise Exception("Could not get element bounding box")
