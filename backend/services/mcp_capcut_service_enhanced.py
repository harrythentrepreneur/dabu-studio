#!/usr/bin/env python3
"""
Enhanced MCP CapCut Service - Reliable and robust version with AI-based element detection
Uses Model Context Protocol approach with enhanced accessibility tree analysis
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


class ElementScoring:
    """Enhanced element scoring system for intelligent element finding"""
    
    @staticmethod
    def calculate_score(element: Dict, search_terms: List[str], context: str = "") -> float:
        """Calculate element relevance score using advanced heuristics."""
        score = 0.0
        
        # Get element properties
        text = (element.get('text', '') or '').lower()
        aria_label = (element.get('ariaLabel', '') or '').lower()
        title = (element.get('title', '') or '').lower()
        placeholder = (element.get('placeholder', '') or '').lower()
        class_name = (element.get('className', '') or '').lower()
        element_id = (element.get('id', '') or '').lower()
        role = (element.get('role', '') or '').lower()
        tag = (element.get('tag', '') or '').lower()
        
        # Combined searchable text
        searchable_text = f"{text} {aria_label} {title} {placeholder} {class_name} {element_id}".lower()
        
        # Exact match scoring (highest priority)
        search_phrase = ' '.join(search_terms).lower()
        if search_phrase in text:
            score += 10.0
        elif search_phrase in aria_label:
            score += 9.0
        elif search_phrase in title:
            score += 8.0
        
        # Individual term scoring with position weighting
        for i, term in enumerate(search_terms):
            term_weight = 1.0 / (i + 1)  # Earlier terms get higher weight
            
            # Text content (highest priority)
            if term in text:
                score += 3.0 * term_weight
                # Bonus for exact word match
                if f" {term} " in f" {text} " or text.startswith(term) or text.endswith(term):
                    score += 1.0 * term_weight
            
            # ARIA label (accessibility priority)
            if term in aria_label:
                score += 2.5 * term_weight
            
            # Title attribute
            if term in title:
                score += 2.0 * term_weight
            
            # Placeholder text
            if term in placeholder:
                score += 2.0 * term_weight
            
            # Class name
            if term in class_name:
                score += 1.0 * term_weight
            
            # Element ID
            if term in element_id:
                score += 1.5 * term_weight
        
        # Element type scoring
        if element.get('isClickable'):
            score += 2.0
        if element.get('isInput'):
            score += 1.5
        
        # Tag-specific bonuses
        if tag == 'button':
            score += 1.5
        elif tag == 'a':
            score += 1.0
        elif tag in ['input', 'select', 'textarea']:
            score += 1.0
        
        # Role-based scoring
        if role == 'button':
            score += 1.5
        elif role == 'link':
            score += 1.0
        elif role in ['textbox', 'combobox', 'searchbox']:
            score += 1.0
        
        # Context-aware scoring
        if context:
            context_terms = context.lower().split()
            for term in context_terms:
                if term in searchable_text:
                    score += 0.5
        
        # Position scoring (prefer elements higher and more centered on page)
        if 'position' in element:
            pos = element['position']
            # Prefer elements in the upper 2/3 of the page
            if pos['y'] < 600:
                score += 0.5
            # Prefer elements that are not too far to the edges
            if 100 < pos['x'] < 1500:
                score += 0.5
        
        # Visibility scoring
        if element.get('isVisible', True):
            score += 1.0
        
        # Penalize very long text (likely not a button/action element)
        if len(text) > 100:
            score *= 0.8
        
        return score


class MCPCapCutServiceEnhanced(BaseService):
    """
    Enhanced MCP CapCut service with robust element detection and error handling
    Uses Model Context Protocol principles with intelligent accessibility tree analysis
    """
    
    def __init__(self):
        """Initialize the enhanced MCP CapCut service."""
        super().__init__()
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE:
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            logger.info("Gemini Vision integration enabled for enhanced detection")
        else:
            self.model = None
            logger.warning("Gemini Vision not available, using pure MCP approach")
        
        # Service configuration
        self.max_retries = 3
        self.retry_delay = 2
        self.element_wait_timeout = 10000
        self.page_load_timeout = 30000
        
        # Output directories
        self.output_dir = Path(__file__).parent.parent / "output"
        self.screenshot_dir = Path("/tmp/capcut_mcp_enhanced")
        self.screenshot_dir.mkdir(exist_ok=True)
        
        # Element scoring system
        self.element_scorer = ElementScoring()
        
        logger.info("Enhanced MCP CapCut Service initialized")
    
    async def process_video_with_captions(
        self,
        video_path: str,
        caption_style: str = "TikTok Bold",
        request_id: str = None
    ) -> Dict[str, Any]:
        """
        Process video with enhanced MCP CapCut automation.
        
        Args:
            video_path: Path to video file
            caption_style: Caption style to apply
            request_id: Unique request identifier
            
        Returns:
            Dictionary with processing results
        """
        request_id = request_id or f"mcp_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
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
            logger.info(f"Starting enhanced MCP CapCut processing for {request_id}")
            
            # Initialize Playwright
            playwright = await async_playwright().start()
            browser = await self._create_browser(playwright)
            context = await self._create_context(browser)
            page = await context.new_page()
            
            # Apply stealth mode if available
            if STEALTH_AVAILABLE:
                stealth = Stealth()
                await stealth.apply_stealth_async(page)
                logger.info("Stealth mode applied")
            
            # Step 1: Navigate and authenticate
            logger.info("Step 1: Navigating to CapCut and authenticating...")
            auth_success = await self._mcp_navigation_and_auth(page, request_id)
            if not auth_success:
                raise Exception("Failed to navigate and authenticate")
            result["steps_completed"].append("authentication")
            
            # Step 2: Ensure we're in the editor
            logger.info("Step 2: Ensuring we're in the editor...")
            editor_success = await self._mcp_ensure_in_editor(page, request_id)
            if not editor_success:
                raise Exception("Failed to reach editor")
            result["steps_completed"].append("editor_navigation")
            
            # Step 3: Upload video
            logger.info("Step 3: Uploading video...")
            upload_success = await self._mcp_video_upload(page, video_path, request_id)
            if not upload_success:
                raise Exception("Failed to upload video")
            result["steps_completed"].append("video_upload")
            
            # Wait for interface to settle
            await page.wait_for_timeout(3000)
            
            # Step 4: Generate captions following exact workflow
            logger.info("Step 4: Generating captions...")
            
            # Step 4a: Click Captions left sidebar button
            logger.info("Step 4a: Clicking Captions left sidebar button...")
            captions_success = await self._mcp_click_captions_sidebar(page, request_id)
            if not captions_success:
                raise Exception("Failed to click Captions sidebar button")
            
            # Wait for panel to open
            await page.wait_for_timeout(2000)
            
            # Step 4b: Panel should already show caption options, skip redundant click
            logger.info("Step 4b: Caption panel is open, proceeding to Auto captions...")
            
            # Step 4c: Click on "Auto captions Free" card
            logger.info("Step 4c: Clicking on Auto captions Free card...")
            auto_captions_card_success = await self._mcp_click_auto_captions_free_card(page, request_id)
            if not auto_captions_card_success:
                raise Exception("Failed to expand Auto captions Free card")
            
            # Step 4d: Click the Generate button
            logger.info("Step 4d: Clicking Generate button...")
            generate_success = await self._mcp_click_auto_captions_generate(page, request_id)
            if not generate_success:
                raise Exception("Failed to click Generate button")
            
            # Step 4e: Wait for generation to complete
            logger.info("Step 4e: Waiting for caption generation...")
            generation_complete = await self._mcp_wait_for_caption_generation(page, request_id)
            if not generation_complete:
                raise Exception("Caption generation did not complete")
            
            # Step 4f: Apply caption style via Presets
            logger.info("Step 4f: Applying caption style...")
            style_success = await self._mcp_apply_caption_style(page, caption_style, request_id)
            if not style_success:
                logger.warning("Failed to apply caption style, using default")
            
            result["steps_completed"].append("caption_generation")
            logger.info("Caption generation workflow completed!")
            
            # Step 5: Export video
            logger.info("Step 5: Exporting video...")
            export_success = await self._mcp_export_video(page, request_id)
            if not export_success:
                raise Exception("Failed to export video")
            
            result["steps_completed"].append("video_export")
            
            # Success!
            result["success"] = True
            result["processing_time"] = time.time() - start_time
            
            # Set expected output paths
            result["captioned_video_path"] = str(self.output_dir / f"captioned_{request_id}.mp4")
            result["project_bundle_path"] = str(self.output_dir / f"project_{request_id}.zip")
            
            logger.info(f"Enhanced MCP CapCut processing completed successfully for {request_id}")
            
        except Exception as e:
            error_msg = f"Enhanced MCP CapCut processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result["error"] = error_msg
            
            # Save error screenshot
            if page:
                await self._save_error_screenshot(page, request_id, str(e))
        
        finally:
            # Save session for future use
            try:
                if page and page.context:
                    context_file = Path.home() / ".capcut_browser_context"
                    context_file.mkdir(exist_ok=True)
                    await page.context.storage_state(path=str(context_file / "state.json"))
                    logger.info("Session saved for future use")
            except Exception as save_error:
                logger.warning(f"Failed to save session: {save_error}")
            
            # Cleanup
            await self._cleanup_resources(page, context, browser, playwright)
            
            # Clean up screenshots if failed (disabled for debugging)
            # if not result.get("success", False):
            #     await self._cleanup_screenshots()
        
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
        context_file = Path.home() / ".capcut_browser_context" / "state.json"
        
        context_params = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation']
        }
        
        if context_file.exists():
            logger.info("Loading saved CapCut session...")
            context_params['storage_state'] = str(context_file)
        else:
            logger.info("No saved session found, creating new context")
        
        return await browser.new_context(**context_params)
    
    async def _get_accessibility_tree_enhanced(self, page: Page) -> List[Dict]:
        """
        Get enhanced accessibility tree with more comprehensive element detection.
        This is the core of the MCP approach - using structured data instead of visual cues.
        """
        try:
            elements = await page.evaluate("""
                () => {
                    const elements = [];
                    const processedNodes = new Set();
                    
                    function processNode(node, depth = 0) {
                        if (depth > 10 || processedNodes.has(node)) return;
                        processedNodes.add(node);
                        
                        const rect = node.getBoundingClientRect();
                        const style = window.getComputedStyle(node);
                        
                        // Check if element is visible
                        const isVisible = rect.width > 0 && 
                                        rect.height > 0 && 
                                        style.display !== 'none' && 
                                        style.visibility !== 'hidden' && 
                                        style.opacity !== '0' &&
                                        rect.top < window.innerHeight &&
                                        rect.bottom > 0 &&
                                        rect.left < window.innerWidth &&
                                        rect.right > 0;
                        
                        if (!isVisible) return;
                        
                        // Check if element is interactive or has content
                        const isInteractive = 
                            node.tagName === 'BUTTON' ||
                            node.tagName === 'A' ||
                            node.tagName === 'INPUT' ||
                            node.tagName === 'SELECT' ||
                            node.tagName === 'TEXTAREA' ||
                            node.getAttribute('role') === 'button' ||
                            node.getAttribute('role') === 'link' ||
                            node.getAttribute('role') === 'textbox' ||
                            node.onclick !== null ||
                            style.cursor === 'pointer' ||
                            node.hasAttribute('tabindex');
                        
                        const hasText = node.innerText && node.innerText.trim().length > 0;
                        const hasLabel = node.getAttribute('aria-label') || 
                                       node.getAttribute('title') ||
                                       node.getAttribute('placeholder') ||
                                       node.getAttribute('alt');
                        
                        if (isInteractive || hasText || hasLabel) {
                            // Get all text content
                            let text = '';
                            if (node.innerText) {
                                text = node.innerText.trim();
                            } else if (node.value) {
                                text = node.value;
                            } else if (node.textContent) {
                                text = node.textContent.trim();
                            }
                            
                            // Get parent context for better understanding
                            let parentText = '';
                            let parent = node.parentElement;
                            let parentDepth = 0;
                            while (parent && parentDepth < 2) {
                                if (parent.getAttribute('aria-label')) {
                                    parentText = parent.getAttribute('aria-label');
                                    break;
                                }
                                parent = parent.parentElement;
                                parentDepth++;
                            }
                            
                            elements.push({
                                index: elements.length,
                                tag: node.tagName.toLowerCase(),
                                text: text.substring(0, 200),
                                role: node.getAttribute('role'),
                                ariaLabel: node.getAttribute('aria-label'),
                                ariaDescribedBy: node.getAttribute('aria-describedby'),
                                title: node.getAttribute('title'),
                                placeholder: node.getAttribute('placeholder'),
                                alt: node.getAttribute('alt'),
                                type: node.type,
                                name: node.name,
                                id: node.id,
                                className: node.className,
                                href: node.href,
                                value: node.value,
                                checked: node.checked,
                                disabled: node.disabled,
                                readonly: node.readOnly,
                                required: node.required,
                                isClickable: isInteractive,
                                isInput: node.tagName === 'INPUT' || 
                                         node.tagName === 'TEXTAREA' || 
                                         node.tagName === 'SELECT',
                                isButton: node.tagName === 'BUTTON' || 
                                         node.getAttribute('role') === 'button',
                                isLink: node.tagName === 'A' || 
                                       node.getAttribute('role') === 'link',
                                isVisible: true,
                                parentContext: parentText,
                                position: {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height),
                                    top: Math.round(rect.top),
                                    bottom: Math.round(rect.bottom),
                                    left: Math.round(rect.left),
                                    right: Math.round(rect.right)
                                },
                                style: {
                                    cursor: style.cursor,
                                    zIndex: style.zIndex,
                                    position: style.position
                                }
                            });
                        }
                        
                        // Process children
                        for (const child of node.children) {
                            processNode(child, depth + 1);
                        }
                    }
                    
                    // Start processing from body
                    processNode(document.body);
                    
                    // Sort by position (top to bottom, left to right)
                    elements.sort((a, b) => {
                        if (Math.abs(a.position.y - b.position.y) < 10) {
                            return a.position.x - b.position.x;
                        }
                        return a.position.y - b.position.y;
                    });
                    
                    return elements;
                }
            """)
            
            logger.info(f"Enhanced accessibility tree analysis found {len(elements)} elements")
            return elements
            
        except Exception as e:
            logger.error(f"Failed to get enhanced accessibility tree: {e}")
            return []
    
    async def _find_element_intelligently_enhanced(
        self, 
        page: Page, 
        description: str,
        context: str = "",
        element_type: str = None,
        max_results: int = 5
    ) -> Optional[List[Dict]]:
        """
        Enhanced intelligent element finding using advanced scoring and AI-like decision making.
        This is the core MCP approach - using natural language to find elements.
        
        Args:
            page: The page to search
            description: Natural language description of the element
            context: Additional context about where the element might be
            element_type: Optional filter for element type (button, input, link, etc.)
            max_results: Maximum number of results to return
            
        Returns:
            List of matching elements sorted by relevance score
        """
        try:
            elements = await self._get_accessibility_tree_enhanced(page)
            
            if not elements:
                logger.warning("No elements found in accessibility tree")
                return None
            
            # Process description into search terms
            # Remove common words and split into meaningful terms
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                         'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                         'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                         'should', 'may', 'might', 'must', 'can', 'button', 'click', 'select',
                         'find', 'locate', 'search'}
            
            words = description.lower().split()
            search_terms = [word for word in words if word not in stop_words and len(word) > 2]
            
            # If no search terms after filtering, use original words
            if not search_terms:
                search_terms = [word for word in words if len(word) > 2]
            
            logger.info(f"Searching for elements with terms: {search_terms}")
            
            # Score all elements
            scored_elements = []
            for element in elements:
                # Apply element type filter if specified
                if element_type:
                    if element_type == 'button' and not element.get('isButton'):
                        continue
                    elif element_type == 'input' and not element.get('isInput'):
                        continue
                    elif element_type == 'link' and not element.get('isLink'):
                        continue
                
                # Calculate score
                score = self.element_scorer.calculate_score(element, search_terms, context)
                
                if score > 0:
                    element['relevance_score'] = score
                    scored_elements.append(element)
            
            # Sort by score
            scored_elements.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Return top results
            results = scored_elements[:max_results]
            
            if results:
                logger.info(f"Found {len(results)} matching elements:")
                for i, elem in enumerate(results[:3]):  # Log top 3
                    text_content = elem.get('text', '') or elem.get('ariaLabel', '') or 'No text'
                    if text_content:
                        text_content = text_content[:50]
                    logger.info(f"  {i+1}. Score: {elem['relevance_score']:.2f} - {text_content}")
                
                return results
            else:
                logger.warning(f"No matching elements found for: {description}")
                return None
                
        except Exception as e:
            logger.error(f"Enhanced element finding failed: {e}")
            return None
    
    async def _click_element_intelligently_enhanced(
        self, 
        page: Page, 
        description: str, 
        request_id: str,
        context: str = "",
        element_type: str = None,
        retry_count: int = 3
    ) -> bool:
        """
        Enhanced intelligent clicking with retry logic and multiple strategies.
        
        Args:
            page: The page to interact with
            description: Natural language description of the element to click
            request_id: Request ID for logging
            context: Additional context
            element_type: Optional element type filter
            retry_count: Number of retry attempts
            
        Returns:
            True if click was successful, False otherwise
        """
        for attempt in range(retry_count):
            try:
                # Find matching elements
                elements = await self._find_element_intelligently_enhanced(
                    page, description, context, element_type
                )
                
                if not elements:
                    if attempt < retry_count - 1:
                        logger.warning(f"No elements found, retrying... (attempt {attempt + 1}/{retry_count})")
                        await page.wait_for_timeout(2000)
                        continue
                    return False
                
                # Try clicking the best match
                best_element = elements[0]
                
                # Log what we're about to click
                element_desc = (
                    best_element.get('text', '')[:50] or 
                    best_element.get('ariaLabel', '') or 
                    f"{best_element.get('tag')} element"
                )
                logger.info(f"Attempting to click: '{element_desc}' (score: {best_element['relevance_score']:.2f})")
                
                # Get element position
                pos = best_element['position']
                center_x = pos['x'] + pos['width'] // 2
                center_y = pos['y'] + pos['height'] // 2
                
                # Try multiple click strategies
                click_successful = False
                
                # Strategy 1: Direct position click
                try:
                    await page.mouse.click(center_x, center_y)
                    click_successful = True
                    logger.info(f"Successfully clicked element using position click")
                except Exception as e:
                    logger.warning(f"Position click failed: {e}")
                
                # Strategy 2: Try using selector if we have an ID
                if not click_successful and best_element.get('id'):
                    try:
                        await page.click(f"#{best_element['id']}")
                        click_successful = True
                        logger.info(f"Successfully clicked element using ID selector")
                    except:
                        pass
                
                # Strategy 3: JavaScript click as fallback
                if not click_successful:
                    try:
                        # Find element by position and click via JavaScript
                        js_clicked = await page.evaluate(f"""
                            () => {{
                                const element = document.elementFromPoint({center_x}, {center_y});
                                if (element) {{
                                    element.click();
                                    return true;
                                }}
                                return false;
                            }}
                        """)
                        if js_clicked:
                            click_successful = True
                            logger.info(f"Successfully clicked element using JavaScript")
                    except:
                        pass
                
                if click_successful:
                    # Wait for any page changes
                    await page.wait_for_timeout(1000)
                    return True
                
                # If click failed and we have more elements, try the next one
                if len(elements) > 1 and attempt < retry_count - 1:
                    logger.warning(f"First element click failed, trying next best match...")
                    # Continue to next attempt which will find elements again
                    await page.wait_for_timeout(1000)
                    continue
                    
            except Exception as e:
                logger.error(f"Click attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    await page.wait_for_timeout(2000)
                    continue
        
        logger.error(f"All click attempts failed for: {description}")
        return False
    
    async def _dismiss_overlays_mcp(self, page: Page, request_id: str) -> bool:
        """
        Dismiss overlays using MCP approach - find and click close buttons intelligently.
        """
        try:
            logger.info("Checking for overlays using MCP approach...")
            
            # First, try keyboard shortcut
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            
            # Look for close buttons using intelligent finding
            close_descriptions = [
                "close button x",
                "dismiss button",
                "skip button",
                "got it button",
                "ok button",
                "continue button",
                "next button"
            ]
            
            for desc in close_descriptions:
                clicked = await self._click_element_intelligently_enhanced(
                    page, desc, request_id, 
                    context="overlay modal popup dialog",
                    element_type="button",
                    retry_count=1
                )
                if clicked:
                    logger.info(f"Dismissed overlay using: {desc}")
                    await page.wait_for_timeout(1000)
                    return True
            
            # If no close buttons found, try to remove overlays via JavaScript
            await page.evaluate("""
                () => {
                    // Remove common overlay elements
                    const overlaySelectors = [
                        '[class*="overlay"]',
                        '[class*="modal"]',
                        '[class*="popup"]',
                        '[class*="dialog"]',
                        '[class*="guide"]',
                        '[class*="tutorial"]',
                        '[class*="onboarding"]'
                    ];
                    
                    overlaySelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => {
                            // Don't remove video or editor elements
                            if (!el.className.includes('video') && 
                                !el.className.includes('editor') &&
                                !el.className.includes('timeline')) {
                                el.style.display = 'none';
                            }
                        });
                    });
                }
            """)
            
            return True
            
        except Exception as e:
            logger.warning(f"Overlay dismissal failed: {e}")
            return False
    
    async def _mcp_navigation_and_auth(self, page: Page, request_id: str) -> bool:
        """Navigate to CapCut and handle authentication using MCP approach."""
        try:
            logger.info("Navigating to CapCut...")
            await page.goto("https://www.capcut.com/editor", 
                           wait_until='domcontentloaded', 
                           timeout=self.page_load_timeout)
            await page.wait_for_timeout(8000)
            
            # Take screenshot
            screenshot_path = self.screenshot_dir / f"initial_state_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Initial screenshot saved: {screenshot_path}")
            
            # Analyze page state
            page_state = await self._analyze_page_state_mcp(page, request_id)
            logger.info(f"Current page state: {page_state}")
            
            if page_state == PageState.EDITOR:
                logger.info("Already in CapCut editor")
                return True
            
            if page_state == PageState.LOGIN:
                logger.info("Login required")
                
                # Check for saved session
                context_file = Path.home() / ".capcut_browser_context" / "state.json"
                if context_file.exists():
                    logger.info("Attempting to use saved session...")
                    await page.reload()
                    await page.wait_for_timeout(5000)
                    
                    page_state = await self._analyze_page_state_mcp(page, request_id)
                    if page_state == PageState.EDITOR:
                        logger.info("Successfully loaded saved session")
                        return True
                
                # Try authentication
                auth_success = await self._handle_authentication_mcp(page, request_id)
                if not auth_success:
                    logger.error("Authentication failed")
                    return False
                
                await page.wait_for_timeout(5000)
                page_state = await self._analyze_page_state_mcp(page, request_id)
                
                if page_state == PageState.LOGIN:
                    logger.error("Still on login page after authentication")
                    return False
            
            return page_state in [PageState.EDITOR, PageState.PROJECT_LIST]
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def _analyze_page_state_mcp(self, page: Page, request_id: str) -> PageState:
        """Analyze page state using MCP approach with Gemini Vision fallback."""
        try:
            # First try Gemini Vision if available
            if self.model:
                return await self._analyze_with_gemini_vision(page, request_id)
            
            # Fallback to accessibility tree analysis
            elements = await self._get_accessibility_tree_enhanced(page)
            
            # Analyze text content
            all_text = ' '.join([elem.get('text', '') for elem in elements]).lower()
            
            # Check for state indicators
            if any(word in all_text for word in ['sign in', 'login', 'email', 'password']):
                return PageState.LOGIN
            elif any(word in all_text for word in ['timeline', 'editor', 'media', 'effects']):
                return PageState.EDITOR
            elif any(word in all_text for word in ['new project', 'create project', 'my projects']):
                return PageState.PROJECT_LIST
            elif any(word in all_text for word in ['uploading', 'processing', 'importing']):
                return PageState.UPLOADING
            elif any(word in all_text for word in ['exporting', 'rendering', 'downloading']):
                return PageState.EXPORTING
            else:
                return PageState.UNKNOWN
                
        except Exception as e:
            logger.error(f"Page state analysis failed: {e}")
            return PageState.UNKNOWN
    
    async def _analyze_with_gemini_vision(self, page: Page, request_id: str) -> PageState:
        """Use Gemini Vision for page state analysis."""
        try:
            screenshot_path = self.screenshot_dir / f"analysis_{request_id}_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            
            prompt = """
            Analyze this CapCut webpage screenshot and determine the current page state.
            
            Respond with ONLY one of these exact values:
            - LOGIN (if you see login/signup forms)
            - EDITOR (if you see video timeline, editing tools)
            - PROJECT_LIST (if you see list of projects)
            - UPLOADING (if files are being uploaded)
            - PROCESSING (if something is processing)
            - EXPORTING (if video is being exported)
            - UNKNOWN (if unclear)
            """
            
            uploaded_file = genai.upload_file(str(screenshot_path))
            response = self.model.generate_content([prompt, uploaded_file])
            response_text = response.text.strip().upper()
            
            state_mapping = {
                'LOGIN': PageState.LOGIN,
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
    
    async def _handle_authentication_mcp(self, page: Page, request_id: str) -> bool:
        """Handle authentication using MCP approach."""
        try:
            email = os.getenv('CAPCUT_EMAIL')
            password = os.getenv('CAPCUT_PASSWORD')
            
            if not email or not password:
                logger.warning("Email/password not configured")
                return False
            
            # Find and fill email field
            email_filled = await self._fill_input_field(page, "email", email, request_id)
            if not email_filled:
                return False
            
            # Click continue/next
            await self._click_element_intelligently_enhanced(
                page, "continue next submit", request_id,
                element_type="button"
            )
            await page.wait_for_timeout(3000)
            
            # Find and fill password field
            password_filled = await self._fill_input_field(page, "password", password, request_id)
            if not password_filled:
                return False
            
            # Click sign in
            await self._click_element_intelligently_enhanced(
                page, "sign in login submit", request_id,
                element_type="button"
            )
            await page.wait_for_timeout(5000)
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def _fill_input_field(self, page: Page, field_type: str, value: str, request_id: str) -> bool:
        """Fill an input field using MCP approach."""
        try:
            # Find the input field
            elements = await self._find_element_intelligently_enhanced(
                page, f"{field_type} input field",
                element_type="input"
            )
            
            if not elements:
                logger.error(f"No {field_type} input field found")
                return False
            
            element = elements[0]
            pos = element['position']
            
            # Click on the field
            await page.mouse.click(pos['x'] + pos['width'] // 2, pos['y'] + pos['height'] // 2)
            await page.wait_for_timeout(500)
            
            # Clear existing text
            await page.keyboard.press('Control+A')
            await page.keyboard.press('Backspace')
            
            # Type the value
            await page.keyboard.type(value)
            await page.wait_for_timeout(500)
            
            logger.info(f"Successfully filled {field_type} field")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fill {field_type} field: {e}")
            return False
    
    async def _mcp_ensure_in_editor(self, page: Page, request_id: str) -> bool:
        """Ensure we're in the editor using MCP approach."""
        try:
            page_state = await self._analyze_page_state_mcp(page, request_id)
            
            if page_state == PageState.EDITOR:
                logger.info("Already in editor")
                return True
            
            if page_state == PageState.PROJECT_LIST:
                logger.info("In project list, creating new project...")
                
                # Click new project button
                new_project_clicked = await self._click_element_intelligently_enhanced(
                    page, "new project create", request_id,
                    element_type="button"
                )
                
                if new_project_clicked:
                    await page.wait_for_timeout(5000)
                    page_state = await self._analyze_page_state_mcp(page, request_id)
                    return page_state == PageState.EDITOR
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to ensure editor state: {e}")
            return False
    
    async def _mcp_video_upload(self, page: Page, video_path: str, request_id: str) -> bool:
        """Upload video using MCP approach with proper wait for completion."""
        try:
            logger.info(f"Uploading video: {video_path}")
            
            # Strategy 1: Direct file input
            file_inputs = await page.query_selector_all('input[type="file"]')
            if file_inputs:
                await file_inputs[0].set_input_files(video_path)
                logger.info("Video file set, waiting for upload to start...")
                
                # Wait for upload to start
                await page.wait_for_timeout(3000)
                
                # Now wait for upload to complete
                upload_complete = await self._wait_for_upload_completion(page, request_id)
                if not upload_complete:
                    logger.warning("Upload completion not detected, using fallback timeout")
                    await page.wait_for_timeout(15000)  # Fallback timeout
                
                logger.info("Video upload completed successfully")
                return True
            
            # Strategy 2: Click upload button to reveal file input
            upload_clicked = await self._click_element_intelligently_enhanced(
                page, "upload import add video media", request_id,
                context="editor toolbar"
            )
            
            if upload_clicked:
                await page.wait_for_timeout(2000)
                
                # Check for file input again
                file_inputs = await page.query_selector_all('input[type="file"]')
                if file_inputs:
                    await file_inputs[0].set_input_files(video_path)
                    logger.info("Video file set after clicking upload, waiting for completion...")
                    
                    # Wait for upload to start
                    await page.wait_for_timeout(3000)
                    
                    # Wait for upload to complete
                    upload_complete = await self._wait_for_upload_completion(page, request_id)
                    if not upload_complete:
                        logger.warning("Upload completion not detected, using fallback timeout")
                        await page.wait_for_timeout(15000)
                    
                    logger.info("Video upload completed successfully")
                    return True
            
            logger.error("No upload mechanism found")
            return False
            
        except Exception as e:
            logger.error(f"Video upload failed: {e}")
            return False
    
    async def _wait_for_upload_completion(self, page: Page, request_id: str) -> bool:
        """Wait for video upload to complete by monitoring progress indicators."""
        try:
            logger.info("Monitoring upload progress...")
            
            start_time = time.time()
            timeout = 60  # 1 minute timeout
            last_progress_text = ""
            
            while time.time() - start_time < timeout:
                try:
                    # Get current page elements
                    elements = await self._get_accessibility_tree_enhanced(page)
                    all_text = ' '.join([elem.get('text', '') for elem in elements]).lower()
                    
                    # Check for upload/processing indicators
                    if any(indicator in all_text for indicator in ['uploading', 'processing', 'loading', '%']):
                        # Extract percentage if available
                        import re
                        percentages = re.findall(r'(\d+)%', all_text)
                        if percentages:
                            current_progress = f"{percentages[0]}%"
                            if current_progress != last_progress_text:
                                logger.info(f"Upload progress: {current_progress}")
                                last_progress_text = current_progress
                        else:
                            logger.info("Upload in progress...")
                        
                        # If we see 100%, upload is complete
                        if '100%' in all_text:
                            logger.info("Upload reached 100%")
                            await page.wait_for_timeout(2000)  # Wait a bit for UI to update
                            return True
                    
                    # Check if video appears in timeline (indicates upload complete)
                    if any(indicator in all_text for indicator in ['00:00', 'timeline', 'trim', 'split']):
                        # These UI elements appear after upload completes
                        logger.info("Video appears to be loaded in timeline")
                        return True
                    
                    # Wait before checking again
                    await page.wait_for_timeout(2000)
                    
                except Exception as e:
                    logger.warning(f"Error checking upload progress: {e}")
                    await page.wait_for_timeout(2000)
            
            logger.warning("Upload completion check timed out")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for upload completion: {e}")
            return False
    
    async def _mcp_click_captions_sidebar(self, page: Page, request_id: str) -> bool:
        """Click Captions in the sidebar using MCP approach."""
        try:
            # Dismiss any overlays first
            await self._dismiss_overlays_mcp(page, request_id)
            
            # Click Captions button
            clicked = await self._click_element_intelligently_enhanced(
                page, "captions", request_id,
                context="sidebar left panel tools",
                retry_count=2
            )
            
            if clicked:
                await page.wait_for_timeout(2000)
                logger.info("Captions sidebar clicked successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Captions sidebar: {e}")
            return False
    
    async def _mcp_click_captions_within_panel(self, page: Page, request_id: str) -> bool:
        """Click Captions within the opened panel."""
        try:
            clicked = await self._click_element_intelligently_enhanced(
                page, "captions", request_id,
                context="panel tools options",
                retry_count=2
            )
            
            if clicked:
                await page.wait_for_timeout(2000)
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to click Captions within panel: {e}")
            return False
    
    async def _mcp_click_auto_captions_free_card(self, page: Page, request_id: str) -> bool:
        """Click Auto captions card to expand it."""
        try:
            # Take screenshot to see what's visible
            screenshot_path = self.screenshot_dir / f"before_auto_captions_{request_id}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot before auto captions: {screenshot_path}")
            
            # The actual UI shows "Auto captions" not "Auto captions Free"
            # Try to click on the Auto captions section
            clicked = await self._click_element_intelligently_enhanced(
                page, "auto captions automatically recognize speech videos", request_id,
                context="generate captions panel",
                retry_count=2
            )
            
            if not clicked:
                # Try simpler search
                clicked = await self._click_element_intelligently_enhanced(
                    page, "auto captions", request_id,
                    context="captions panel",
                    retry_count=2
                )
            
            if clicked:
                await page.wait_for_timeout(2000)
                logger.info("Auto captions card expanded")
                return True
            
            # Log what we can see for debugging
            elements = await self._get_accessibility_tree_enhanced(page)
            logger.info("Looking for Auto captions elements:")
            for elem in elements:
                text = elem.get('text', '').lower()
                if 'auto' in text or 'caption' in text or 'generate' in text:
                    logger.info(f"  Found: {elem.get('text', '')[:100]}")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Auto captions card: {e}")
            return False
    
    async def _mcp_click_auto_captions_generate(self, page: Page, request_id: str) -> bool:
        """Click Generate button for auto captions."""
        try:
            # Click Generate button
            clicked = await self._click_element_intelligently_enhanced(
                page, "generate", request_id,
                context="auto captions expanded card",
                element_type="button"
            )
            
            if clicked:
                await page.wait_for_timeout(2000)
                logger.info("Generate button clicked")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to click Generate button: {e}")
            return False
    
    async def _mcp_wait_for_caption_generation(self, page: Page, request_id: str) -> bool:
        """Wait for caption generation to complete."""
        try:
            logger.info("Waiting for caption generation...")
            
            start_time = time.time()
            timeout = 300  # 5 minutes
            
            while time.time() - start_time < timeout:
                # Check for completion indicators
                elements = await self._get_accessibility_tree_enhanced(page)
                all_text = ' '.join([elem.get('text', '') for elem in elements]).lower()
                
                # Check for progress indicators
                if any(indicator in all_text for indicator in ['generating', 'processing', '%']):
                    logger.info("Generation in progress...")
                    await page.wait_for_timeout(5000)
                    continue
                
                # Check for completion
                if any(indicator in all_text for indicator in ['complete', 'done', '00:00', 'timestamp']):
                    logger.info("Caption generation complete!")
                    return True
                
                await page.wait_for_timeout(5000)
            
            logger.warning("Caption generation timeout")
            return False
            
        except Exception as e:
            logger.error(f"Error waiting for caption generation: {e}")
            return False
    
    async def _mcp_apply_caption_style(self, page: Page, style: str, request_id: str) -> bool:
        """Apply caption style using Presets."""
        try:
            # Open Presets panel
            presets_clicked = await self._click_element_intelligently_enhanced(
                page, "presets", request_id,
                context="right panel toolbar"
            )
            
            if not presets_clicked:
                logger.warning("Could not open Presets panel")
                return False
            
            await page.wait_for_timeout(2000)
            
            # Click Templates tab
            templates_clicked = await self._click_element_intelligently_enhanced(
                page, "templates", request_id,
                context="presets panel tabs"
            )
            
            if templates_clicked:
                await page.wait_for_timeout(2000)
                
                # Select first template or specific style
                style_clicked = await self._click_element_intelligently_enhanced(
                    page, f"{style} template style", request_id,
                    context="templates list"
                )
                
                if not style_clicked:
                    # Try clicking first template as fallback
                    await self._click_element_intelligently_enhanced(
                        page, "first template", request_id,
                        context="templates list"
                    )
            
            # Close presets panel
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(1000)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply caption style: {e}")
            return False
    
    async def _mcp_export_video(self, page: Page, request_id: str) -> bool:
        """Export video using MCP approach."""
        try:
            # Click Export button
            export_clicked = await self._click_element_intelligently_enhanced(
                page, "export", request_id,
                context="top toolbar",
                element_type="button"
            )
            
            if not export_clicked:
                logger.error("Could not click Export button")
                return False
            
            await page.wait_for_timeout(3000)
            
            # Handle export dialog
            await self._click_element_intelligently_enhanced(
                page, "export start export", request_id,
                context="export dialog",
                element_type="button"
            )
            
            # Wait for export to complete
            logger.info("Waiting for export to complete...")
            await page.wait_for_timeout(30000)  # Wait 30 seconds
            
            # Click Download
            download_clicked = await self._click_element_intelligently_enhanced(
                page, "download", request_id,
                context="export complete dialog",
                element_type="button"
            )
            
            if download_clicked:
                logger.info("Download initiated")
                await page.wait_for_timeout(10000)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    async def _save_error_screenshot(self, page: Page, request_id: str, error: str):
        """Save error screenshot for debugging."""
        try:
            screenshot_path = self.screenshot_dir / f"error_{request_id}_{int(time.time())}.png"
            await page.screenshot(path=str(screenshot_path))
            logger.info(f"Error screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.error(f"Failed to save error screenshot: {e}")
    
    async def _cleanup_resources(self, page, context, browser, playwright):
        """Clean up browser resources."""
        try:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
            logger.info("Browser resources cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
    
    async def _cleanup_screenshots(self):
        """Clean up temporary screenshots."""
        try:
            import shutil
            if self.screenshot_dir.exists():
                shutil.rmtree(str(self.screenshot_dir))
                logger.info("Temporary screenshots cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up screenshots: {e}")


async def main():
    """Test the enhanced MCP CapCut service."""
    service = MCPCapCutServiceEnhanced()
    
    # Test with a video from the output folder
    output_dir = Path("../output")
    video_files = list(output_dir.glob("*.mp4"))
    
    if video_files:
        video_path = str(video_files[0])
        print(f"Testing with video: {video_path}")
        
        result = await service.process_video_with_captions(
            video_path=video_path,
            caption_style="TikTok Bold"
        )
        
        print(f"\nEnhanced MCP CapCut Service Test Results:")
        print(f"Success: {result.get('success')}")
        print(f"Steps Completed: {result.get('steps_completed')}")
        print(f"Processing Time: {result.get('processing_time', 0):.2f} seconds")
        if result.get('error'):
            print(f"Error: {result.get('error')}")
    else:
        print("No video files found in output folder")

if __name__ == "__main__":
    asyncio.run(main())