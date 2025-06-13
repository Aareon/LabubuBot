"""
Main LabubuBot class - orchestrates all bot operations
"""

import json
import time
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    WebDriverException,
    ElementClickInterceptedException
)

from .config import Config
from .locators import PopMartLocators
from .selenium_driver import SeleniumDriverManager
from .http_client import HTTPClientManager
from .utils import safe_log, format_time, extract_product_id


class LabubuBot:
    """Main LabubuBot class for PopMart automation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.data_dir = Path("_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize managers
        self.selenium_manager = SeleniumDriverManager(
            headless=config.headless, 
            timeout=config.timeout
        )
        self.http_manager = HTTPClientManager()
        
    @classmethod
    def from_config_file(cls, config_path: str = "_data/config.yml") -> 'LabubuBot':
        """Create LabubuBot instance from config file"""
        config = Config.from_file(config_path)
        return cls(config)
    
    # Session Management
    def start_selenium_session(self, headless: bool = None):
        """Start Selenium browser session"""
        safe_log('info', "🚀 Starting LabubuBot Selenium session...")
        
        if headless is not None:
            self.selenium_manager.headless = headless
            
        self.selenium_manager.create_driver()
        safe_log('info', "✅ Selenium session started successfully")
    
    async def start_http_session(self):
        """Start HTTP client session"""
        safe_log('info', "🌐 Starting HTTP client session...")
        await self.http_manager.setup_client()
        safe_log('info', "✅ HTTP session started successfully")
    
    def close_sessions(self):
        """Close all active sessions"""
        self.selenium_manager.close_driver()
        asyncio.run(self.http_manager.close_client())
    
    # Authentication & Session Management
    def wait_for_login_success(self, timeout: int = 300) -> Dict[str, Any]:
        """
        Wait for successful login redirect and save session data
        Monitors for redirect to https://popmart.com/{ca|us}/account
        """
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("Selenium session not started. Call start_selenium_session() first.")
            
        driver = self.selenium_manager.get_driver()
        end_time = time.time() + timeout
        
        safe_log('info', "⏳ Waiting for successful login redirect...")
        safe_log('info', "💡 Looking for redirect to account page (ca/us)")
        
        while time.time() < end_time:
            current_url = driver.current_url
            
            # Check if redirected to account page (ca or us)
            if re.match(r'https://popmart\.com/(ca|us)/account', current_url):
                safe_log('info', f"✅ Login successful! Detected redirect to: {current_url}")
                
                # Save session data immediately
                session_data = self.export_session_data()
                safe_log('info', "💾 Session data saved successfully")
                
                # Close the browser window
                safe_log('info', "🔒 Closing browser window...")
                driver.quit()
                
                return session_data
                
            time.sleep(1)  # Check every second
        
        raise TimeoutError(f"Login timeout ({timeout}s) - did not detect successful redirect to account page")
    
    def interactive_login_and_export_cookies(self) -> Dict[str, Any]:
        """
        Open browser for interactive login when credentials are not provided
        Returns: Dictionary containing cookies and local storage data
        """
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("Selenium session not started. Call start_selenium_session() first.")
            
        driver = self.selenium_manager.get_driver()
        wait = self.selenium_manager.get_wait()
        
        safe_log('info', "🔐 Starting interactive login process...")
        safe_log('info', "👤 Please log in manually in the browser window that opens")
        
        try:
            # Navigate to login page
            driver.get(PopMartLocators.LOGIN_PAGE)
            safe_log('info', "📄 Navigated to login page")
            
            # Accept agreement if present
            try:
                agreement_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.AGREEMENT))
                )
                agreement_btn.click()
                safe_log('info', "✅ Agreement accepted")
            except TimeoutException:
                safe_log('info', "ℹ️  No agreement dialog found")
            
            # Wait for user to complete login manually using URL-based detection
            safe_log('info', "⏳ Waiting for you to complete login in the browser...")
            safe_log('info', "💡 The browser window should be open - please log in manually")
            safe_log('info', "🎯 The bot will automatically detect when you're redirected to the account page")
            
            # Use URL-based detection to avoid stale element references
            login_successful = False
            max_wait_time = 300  # 5 minutes timeout
            start_time = time.time()
            
            while not login_successful and (time.time() - start_time) < max_wait_time:
                try:
                    current_url = driver.current_url
                    safe_log('debug', f"Current URL: {current_url}")
                    
                    # Check if redirected to account page (ca or us) - the specific pattern we're looking for
                    if re.match(r'https://popmart\.com/(ca|us)/account', current_url):
                        safe_log('info', f"✅ Login successful! Detected redirect to: {current_url}")
                        login_successful = True
                        break
                    
                    # Also check for other account-related URLs as backup
                    current_url_lower = current_url.lower()
                    if ("account" in current_url_lower and "login" not in current_url_lower):
                        safe_log('info', f"✅ Login successful! Detected account page: {current_url}")
                        login_successful = True
                        break
                        
                except Exception as e:
                    # If there's any issue getting the URL, just continue
                    safe_log('debug', f"URL check error (continuing): {e}")
                    pass
                
                # Wait before checking again
                time.sleep(1)
            
            if not login_successful:
                raise TimeoutError("Login timeout - did not detect successful redirect to account page")
            
            # Export cookies and local storage immediately
            safe_log('info', "📤 Login successful! Exporting session data...")
            session_data = self.export_session_data()
            
            # Close the browser window
            safe_log('info', "🔒 Closing browser window...")
            driver.quit()
            
            return session_data
                
        except TimeoutError:
            safe_log('error', "⏰ Login timeout - please try again")
            raise Exception("Interactive login timed out")
        except Exception as e:
            safe_log('error', f"❌ Interactive login failed: {e}")
            raise
    
    def login_and_export_cookies(self) -> Dict[str, Any]:
        """
        Login to PopMart using Selenium and export cookies for future automation
        Uses interactive login if credentials are not provided
        Returns: Dictionary containing cookies and local storage data
        """
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("Selenium session not started. Call start_selenium_session() first.")
            
        # Check if we have credentials for automated login
        if not self.config.username or not self.config.password:
            safe_log('info', "🔐 No credentials provided - using interactive login")
            return self.interactive_login_and_export_cookies()
        
        # Use automated login if credentials are available
        driver = self.selenium_manager.get_driver()
        wait = self.selenium_manager.get_wait()
        
        safe_log('info', "🔐 Starting automated login process...")
        
        try:
            # Navigate to login page
            driver.get(PopMartLocators.LOGIN_PAGE)
            safe_log('info', "📄 Navigated to login page")
            
            # Accept agreement if present
            try:
                agreement_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.AGREEMENT))
                )
                agreement_btn.click()
                safe_log('info', "✅ Agreement accepted")
            except TimeoutException:
                safe_log('info', "ℹ️  No agreement dialog found")
            
            # Enter username
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PopMartLocators.LOGIN_FIELD))
            )
            username_field.clear()
            username_field.send_keys(self.config.username)
            safe_log('info', "✅ Username entered")
            
            # Enter password
            password_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PopMartLocators.PASSWORD_FIELD))
            )
            password_field.clear()
            password_field.send_keys(self.config.password)
            safe_log('info', "✅ Password entered")
            
            # Click login button
            login_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.LOGIN_BTN))
            )
            login_btn.click()
            safe_log('info', "🔑 Login button clicked")
            
            # Wait for login redirect using the new method
            safe_log('info', "⏳ Waiting for login redirect to account page...")
            return self.wait_for_login_success(timeout=60)
            
        except TimeoutError:
            safe_log('warning', "⚠️  Automated login timeout, falling back to interactive login")
            return self.interactive_login_and_export_cookies()
        except Exception as e:
            safe_log('warning', f"⚠️  Automated login failed: {e}")
            safe_log('info', "🔄 Falling back to interactive login...")
            return self.interactive_login_and_export_cookies()
    
    def export_session_data(self) -> Dict[str, Any]:
        """Export cookies and local storage data from current Selenium session"""
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("No active Selenium session to export from")
            
        driver = self.selenium_manager.get_driver()
        safe_log('info', "📤 Exporting session data...")
        
        # Get cookies
        cookies = driver.get_cookies()
        
        # Get local storage
        local_storage = driver.execute_script(
            "return Object.keys(localStorage).reduce((obj, key) => { "
            "try { obj[key] = JSON.parse(localStorage.getItem(key)); } "
            "catch(e) { obj[key] = localStorage.getItem(key); } "
            "return obj; }, {});"
        )
        
        # Save to files
        cookie_path = self.data_dir / self.config.cookie_file
        storage_path = self.data_dir / self.config.storage_file
        
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
            
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(local_storage, f, indent=2, ensure_ascii=False)
            
        safe_log('info', f"💾 Cookies saved to: {cookie_path}")
        safe_log('info', f"💾 Local storage saved to: {storage_path}")
        
        return {
            'cookies': cookies,
            'local_storage': local_storage,
            'export_time': datetime.now().isoformat()
        }
    
    def load_session_data(self) -> tuple[List[Dict], Dict]:
        """Load previously exported cookies and local storage"""
        cookie_path = self.data_dir / self.config.cookie_file
        storage_path = self.data_dir / self.config.storage_file
        
        if not cookie_path.exists() or not storage_path.exists():
            raise FileNotFoundError("Session data files not found. Please login first.")
            
        # Load cookies
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
            
        # Load local storage
        with open(storage_path, 'r', encoding='utf-8') as f:
            local_storage = json.load(f)
            
        return cookies, local_storage
    
    def apply_session_data(self, cookies: List[Dict], local_storage: Dict):
        """Apply cookies and local storage to current Selenium session"""
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("No active Selenium session")
            
        driver = self.selenium_manager.get_driver()
        safe_log('info', "🔄 Applying session data...")
        
        # Navigate to target domain first
        driver.get(PopMartLocators.BASE_URL)
        
        # Accept agreement if present
        try:
            wait = self.selenium_manager.get_wait()
            agreement_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.AGREEMENT))
            )
            agreement_btn.click()
            safe_log('info', "✅ Agreement accepted")
        except TimeoutException:
            pass
        
        # Set cookies
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                safe_log('warning', f"Failed to set cookie {cookie.get('name', 'unknown')}: {e}")
                
        # Set local storage
        for key, value in local_storage.items():
            try:
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                    
                driver.execute_script(
                    f"localStorage.setItem(arguments[0], arguments[1]);", 
                    key, value_str
                )
            except Exception as e:
                safe_log('warning', f"Failed to set localStorage item {key}: {e}")
                
        safe_log('info', "✅ Session data applied successfully")
    
    # Automation Methods
    def automated_purchase(self) -> Dict[str, Any]:
        """Perform automated purchase using loaded session data"""
        if not self.selenium_manager.is_driver_active():
            raise RuntimeError("Selenium session not started. Call start_selenium_session() first.")
            
        driver = self.selenium_manager.get_driver()
        wait = self.selenium_manager.get_wait()
        
        start_time = time.time()
        safe_log('info', "🛒 Starting automated purchase process...")
        
        try:
            # Load and apply session data
            cookies, local_storage = self.load_session_data()
            self.apply_session_data(cookies, local_storage)
            
            # Navigate to target product
            driver.get(self.config.target_product)
            safe_log('info', f"📄 Navigated to product: {self.config.target_product}")
            
            # Refresh page to ensure session is active
            driver.refresh()
            time.sleep(2)
            
            # Wait for and click "Buy Now" button
            safe_log('info', "🔍 Looking for Buy Now button...")
            self._click_buy_now_button(driver, wait)
            
            # Handle "Go to Cart" button
            self._handle_go_to_cart(driver, wait)
            
            # Handle cart and checkout
            self._handle_checkout_process(driver, wait)
            
            # Handle payment
            self._handle_payment_process(driver, wait)
            
            processing_time = time.time() - start_time
            formatted_time = format_time(processing_time)
            
            safe_log('info', "🎉 ALL THINGS DONE! LET'S PAY!")
            safe_log('info', f"🔗 Payment URL: {driver.current_url}")
            safe_log('info', f"⏱️  Total processing time: {formatted_time}")
            
            return {
                'success': True,
                'payment_url': driver.current_url,
                'processing_time': processing_time,
                'formatted_time': formatted_time
            }
            
        except Exception as e:
            safe_log('error', f"❌ Automated purchase failed: {e}")
            raise
    
    def _click_buy_now_button(self, driver, wait):
        """Handle clicking the Buy Now button with retries"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                buy_now_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.BUY_NOW))
                )
                buy_now_btn.click()
                safe_log('info', "✅ Buy Now button clicked!")
                return
            except TimeoutException:
                safe_log('warning', f"❌ Buy Now button not found, attempt {attempt + 1}/{max_attempts}")
                time.sleep(1)
        
        raise Exception("Buy Now button not found after multiple attempts")
    
    def _handle_go_to_cart(self, driver, wait):
        """Handle the Go to Cart button"""
        try:
            # Make button visible and clickable
            driver.execute_script("""
                const btn = document.querySelector('%s');
                if (btn) {
                    btn.style.position = 'fixed';
                    btn.style.zIndex = '9999';
                    btn.style.opacity = '1';
                    btn.style.display = 'block';
                }
            """ % PopMartLocators.GO_TO_CART)
            
            go_to_cart_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.GO_TO_CART))
            )
            
            # Force click using JavaScript
            driver.execute_script("arguments[0].click();", go_to_cart_btn)
            safe_log('info', "✅ Go to Cart button clicked!")
            
        except TimeoutException:
            safe_log('warning', "❌ Go to Cart button not found, continuing...")
    
    def _handle_checkout_process(self, driver, wait):
        """Handle the checkout process"""
        # Wait for navigation to cart
        wait.until(
            lambda driver: "cart" in driver.current_url.lower() or "checkout" in driver.current_url.lower()
        )
        
        # Select checkbox
        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.CHECKBOX))
        )
        checkbox.click()
        safe_log('info', "✅ Checkbox selected!")
        
        # Click checkout button
        checkout_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.CHECKOUT))
        )
        checkout_btn.click()
        safe_log('info', "✅ Proceeding to checkout!")
        
        # Wait for checkout page to load
        wait.until(
            lambda driver: "checkout" in driver.current_url.lower() or "payment" in driver.current_url.lower()
        )
        time.sleep(5)
    
    def _handle_payment_process(self, driver, wait):
        """Handle the payment process"""
        # Click pay button
        try:
            pay_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, PopMartLocators.PAY))
            )
            
            # Force click using JavaScript
            driver.execute_script("arguments[0].click();", pay_btn)
            safe_log('info', "✅ Pay button clicked!")
        except TimeoutException:
            safe_log('warning', "❌ Pay button not clicked")
        
        # Hover over ordering element (PayPal button)
        try:
            ordering_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PopMartLocators.ORDERING))
            )
            
            ActionChains(driver).move_to_element(ordering_element).perform()
            safe_log('info', "🎯 BUY!! Hovered over PayPal button")
            
        except TimeoutException:
            safe_log('warning', "❌ Ordering element not found")
        
        # Wait for final navigation
        wait.until(
            lambda driver: len(driver.current_url) > 50  # Wait for URL change
        )
    
    # HTTP-based methods
    async def check_product_availability(self, product_url: str = None) -> Dict[str, Any]:
        """Check product availability using HTTP requests"""
        url = product_url or self.config.target_product
        return await self.http_manager.check_product_availability(url)
    
    async def monitor_product_for_restock(self, check_interval: int = 30, max_checks: int = 100) -> Dict[str, Any]:
        """Monitor product for restock and return when available"""
        return await self.http_manager.monitor_product(
            self.config.target_product, 
            check_interval, 
            max_checks
        )
    
    async def monitor_and_purchase(self, check_interval: int = 30, max_checks: int = 100) -> Dict[str, Any]:
        """Monitor product and automatically trigger purchase when available"""
        safe_log('info', "🔄 Starting monitoring with auto-purchase...")
        
        # Monitor for availability
        result = await self.monitor_product_for_restock(check_interval, max_checks)
        
        # If product becomes available, trigger purchase
        if result and result.get('in_stock'):
            safe_log('info', "🚀 Product available! Starting purchase automation...")
            
            # Start Selenium session if not already started
            if not self.selenium_manager.is_driver_active():
                self.start_selenium_session()
            
            # Run automated purchase
            purchase_result = self.automated_purchase()
            
            return {
                'monitoring_result': result,
                'purchase_result': purchase_result,
                'success': purchase_result.get('success', False)
            }
        else:
            return {
                'monitoring_result': result,
                'purchase_result': None,
                'success': False,
                'message': 'Product did not become available during monitoring period'
            }
    
    async def api_login_test(self) -> Dict[str, Any]:
        """Test API-based login (experimental)"""
        return await self.http_manager.attempt_api_login(
            self.config.username, 
            self.config.password
        )
    
    # Utility methods
    def get_product_id(self) -> str:
        """Extract product ID from configured target URL"""
        return extract_product_id(self.config.target_product)
    
    def is_selenium_active(self) -> bool:
        """Check if Selenium session is active"""
        return self.selenium_manager.is_driver_active()
    
    def is_http_active(self) -> bool:
        """Check if HTTP client is active"""
        return self.http_manager.is_client_active()