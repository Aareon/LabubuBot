"""
Selenium WebDriver management for LabubuBot
"""

import os
import sys
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from .locators import PopMartLocators
from .utils import safe_log


class SeleniumDriverManager:
    """Manages Selenium WebDriver setup and configuration"""
    
    def __init__(self, headless: bool = False, timeout: int = 10):
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
    
    def setup_chrome_options(self) -> Options:
        """Setup Chrome options for automation"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            
        # Essential Chrome options for automation
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Window size
        chrome_options.add_argument('--window-size=1080,1024')
        
        # Additional options for Windows compatibility
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        return chrome_options
    
    def find_chrome_binary(self) -> Optional[str]:
        """Find Chrome binary installation on Windows"""
        if sys.platform != "win32":
            return None
            
        chrome_paths = PopMartLocators.get_chrome_paths_for_user()
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                safe_log('info', f"Found Chrome at: {chrome_path}")
                return chrome_path
        
        safe_log('warning', "Could not find Chrome installation")
        return None
    
    def setup_chrome_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with fallbacks"""
        chrome_options = self.setup_chrome_options()
        service = None
        
        # Method 1: Try webdriver_manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            safe_log('info', "Using ChromeDriverManager for driver setup")
        except ImportError:
            safe_log('warning', "webdriver_manager not found, trying alternative methods")
        except Exception as e:
            safe_log('warning', f"ChromeDriverManager failed: {e}, trying alternative methods")
        
        # Method 2: Try to find Chrome binary on Windows
        if sys.platform == "win32":
            chrome_binary = self.find_chrome_binary()
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
        
        # Default service if none set
        if not service:
            service = Service()
            
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        safe_log('info', "Chrome WebDriver setup successful")
        return driver
    
    def setup_edge_driver(self) -> webdriver.Edge:
        """Setup Edge WebDriver as fallback"""
        try:
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from selenium.webdriver.edge.service import Service as EdgeService
            from selenium.webdriver.edge.options import Options as EdgeOptions
            
            edge_options = EdgeOptions()
            
            # Copy Chrome options to Edge (most are compatible)
            chrome_options = self.setup_chrome_options()
            for arg in chrome_options.arguments:
                edge_options.add_argument(arg)
            
            edge_service = EdgeService(EdgeChromiumDriverManager().install())
            
            from selenium import webdriver as edge_webdriver
            driver = edge_webdriver.Edge(service=edge_service, options=edge_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            safe_log('info', "Using Microsoft Edge as Chrome alternative")
            return driver
            
        except Exception as e:
            safe_log('error', f"Edge fallback failed: {e}")
            raise
    
    def create_driver(self) -> webdriver.Chrome:
        """Create WebDriver with fallback options"""
        try:
            # Try Chrome first
            self.driver = self.setup_chrome_driver()
            self.wait = WebDriverWait(self.driver, self.timeout)
            return self.driver
            
        except Exception as chrome_error:
            safe_log('warning', f"Chrome driver failed: {chrome_error}")
            
            # Try Edge as fallback on Windows
            if sys.platform == "win32":
                try:
                    self.driver = self.setup_edge_driver()
                    self.wait = WebDriverWait(self.driver, self.timeout)
                    return self.driver
                except Exception as edge_error:
                    safe_log('error', f"Edge fallback also failed: {edge_error}")
            
            # If all fails, provide helpful error message
            self._raise_setup_error(chrome_error)
    
    def _raise_setup_error(self, original_error: Exception):
        """Raise informative error with setup instructions"""
        error_msg = "WebDriver setup failed. Please try one of the following solutions:\n"
        error_msg += "1. Install Google Chrome browser\n"
        error_msg += "2. Install webdriver-manager: pip install webdriver-manager\n"
        error_msg += "3. Download ChromeDriver manually and add to PATH\n"
        error_msg += "4. Use Edge browser as alternative (will be attempted automatically)\n"
        
        if sys.platform == "win32":
            error_msg += "5. Install Chrome from: https://www.google.com/chrome/\n"
        
        error_msg += f"\nOriginal error: {original_error}"
        
        safe_log('error', error_msg)
        raise RuntimeError(error_msg)
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            safe_log('info', "🔒 WebDriver closed")
            self.driver = None
            self.wait = None
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get the current driver instance"""
        return self.driver
    
    def get_wait(self) -> Optional[WebDriverWait]:
        """Get the current WebDriverWait instance"""
        return self.wait
    
    def is_driver_active(self) -> bool:
        """Check if driver is active and responsive"""
        if not self.driver:
            return False
        
        try:
            # Try to get current URL to test if driver is responsive
            _ = self.driver.current_url
            return True
        except:
            return False