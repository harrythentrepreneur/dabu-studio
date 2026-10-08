"""
Virtual Display Manager for CapCut Web Automation
Handles virtual display setup for headless environments
"""

import os
import sys
import logging
import subprocess
from typing import Optional, Dict, Any
import platform

logger = logging.getLogger(__name__)


class VirtualDisplayManager:
    """
    Manages virtual display for browser automation.
    Supports both Linux (Xvfb) and fallback for other platforms.
    """
    
    def __init__(self, display_num: int = 99, width: int = 1920, height: int = 1080):
        """
        Initialize virtual display manager.
        
        Args:
            display_num: Display number (typically 99)
            width: Display width
            height: Display height
        """
        self.display_num = display_num
        self.width = width
        self.height = height
        self.display_process = None
        self.original_display = os.environ.get('DISPLAY')
        self.is_linux = platform.system().lower() == 'linux'
        self.virtual_display = None
        
    def start(self) -> bool:
        """
        Start virtual display based on platform.
        
        Returns:
            True if virtual display started successfully
        """
        if not self.is_linux:
            logger.info(f"Platform {platform.system()} doesn't require virtual display for testing")
            # On Mac/Windows, we'll run with visible browser for now
            return True
            
        try:
            # Check if Xvfb is installed
            result = subprocess.run(['which', 'Xvfb'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("Xvfb not installed. Installing...")
                self._install_xvfb()
            
            # Start Xvfb
            display_str = f":{self.display_num}"
            xvfb_cmd = [
                'Xvfb',
                display_str,
                '-screen', '0',
                f'{self.width}x{self.height}x24',
                '-ac',  # Disable access control
                '+extension', 'GLX',  # Enable GLX for WebGL
                '+extension', 'RANDR',  # Enable resize and rotate
                '-nolisten', 'tcp'  # Security: don't listen on TCP
            ]
            
            logger.info(f"Starting Xvfb on display {display_str}")
            self.display_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Set DISPLAY environment variable
            os.environ['DISPLAY'] = display_str
            
            # Wait a moment for Xvfb to start
            import time
            time.sleep(2)
            
            # Verify Xvfb is running
            if self.display_process.poll() is None:
                logger.info(f"Virtual display started successfully on {display_str}")
                return True
            else:
                logger.error("Xvfb process terminated unexpectedly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start virtual display: {e}")
            return False
    
    def _install_xvfb(self):
        """Install Xvfb based on the Linux distribution."""
        try:
            # Try apt-get (Debian/Ubuntu)
            result = subprocess.run(
                ['apt-get', 'update'],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                subprocess.run(
                    ['apt-get', 'install', '-y', 'xvfb'],
                    check=True
                )
                logger.info("Xvfb installed via apt-get")
                return
                
            # Try yum (RedHat/CentOS)
            result = subprocess.run(
                ['yum', '--version'],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                subprocess.run(
                    ['yum', 'install', '-y', 'xorg-x11-server-Xvfb'],
                    check=True
                )
                logger.info("Xvfb installed via yum")
                return
                
            # Try apk (Alpine)
            result = subprocess.run(
                ['apk', '--version'],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                subprocess.run(
                    ['apk', 'add', 'xvfb'],
                    check=True
                )
                logger.info("Xvfb installed via apk")
                return
                
        except Exception as e:
            logger.error(f"Failed to install Xvfb: {e}")
            raise
    
    def stop(self):
        """Stop virtual display and restore original environment."""
        if self.display_process:
            logger.info("Stopping virtual display")
            self.display_process.terminate()
            try:
                self.display_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.display_process.kill()
            self.display_process = None
        
        # Restore original DISPLAY variable
        if self.original_display:
            os.environ['DISPLAY'] = self.original_display
        elif 'DISPLAY' in os.environ:
            del os.environ['DISPLAY']
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


class PyVirtualDisplay:
    """
    Alternative using pyvirtualdisplay package (cross-platform).
    Fallback option if native Xvfb is not available.
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """Initialize PyVirtualDisplay wrapper."""
        self.width = width
        self.height = height
        self.display = None
        
    def start(self) -> bool:
        """Start virtual display using pyvirtualdisplay."""
        try:
            from pyvirtualdisplay import Display
            
            self.display = Display(
                visible=False,
                size=(self.width, self.height),
                backend='xvfb'
            )
            self.display.start()
            
            logger.info(f"PyVirtualDisplay started: {self.width}x{self.height}")
            return True
            
        except ImportError:
            logger.warning("pyvirtualdisplay not installed. Install with: pip install pyvirtualdisplay")
            return False
        except Exception as e:
            logger.error(f"Failed to start PyVirtualDisplay: {e}")
            return False
    
    def stop(self):
        """Stop PyVirtualDisplay."""
        if self.display:
            try:
                self.display.stop()
                logger.info("PyVirtualDisplay stopped")
            except Exception as e:
                logger.error(f"Error stopping PyVirtualDisplay: {e}")
            self.display = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def get_display_manager(prefer_native: bool = True) -> Optional[object]:
    """
    Get the appropriate display manager for the current platform.
    
    Args:
        prefer_native: Prefer native Xvfb over pyvirtualdisplay
        
    Returns:
        Display manager instance or None
    """
    system = platform.system().lower()
    
    if system == 'linux':
        if prefer_native:
            # Try native Xvfb first
            manager = VirtualDisplayManager()
            if manager.start():
                return manager
            manager.stop()
        
        # Try pyvirtualdisplay as fallback
        py_manager = PyVirtualDisplay()
        if py_manager.start():
            return py_manager
        py_manager.stop()
    
    elif system == 'darwin':  # macOS
        logger.info("macOS detected - will run browser in visible mode")
        return None
        
    elif system == 'windows':
        logger.info("Windows detected - will run browser in visible mode")
        return None
    
    logger.warning("No suitable virtual display manager found")
    return None


# Test function
def test_virtual_display():
    """Test virtual display functionality."""
    print("Testing Virtual Display Manager...")
    
    with VirtualDisplayManager() as display:
        print(f"DISPLAY environment: {os.environ.get('DISPLAY')}")
        
        # Test that we can use the display
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                page.goto("https://www.google.com")
                print("✅ Browser launched successfully with virtual display")
                page.screenshot(path="virtual_display_test.png")
                print("📸 Screenshot saved: virtual_display_test.png")
                browser.close()
                
        except Exception as e:
            print(f"❌ Browser test failed: {e}")
    
    print("Virtual display test complete")


if __name__ == "__main__":
    test_virtual_display()