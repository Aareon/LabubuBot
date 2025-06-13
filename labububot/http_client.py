"""
HTTP client management using httpx for LabubuBot
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

import httpx

from .locators import PopMartLocators, APIEndpoints
from .utils import safe_log


class HTTPClientManager:
    """Manages HTTP operations using httpx"""
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
    
    async def setup_client(self) -> httpx.AsyncClient:
        """Setup async HTTP client with proper headers and settings"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            http2=True
        )
        
        return self.client
    
    async def close_client(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
            safe_log('info', "🔒 HTTP client closed")
            self.client = None
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating if necessary"""
        if not self.client:
            await self.setup_client()
        return self.client
    
    async def check_product_availability(self, product_url: str) -> Dict[str, Any]:
        """
        Check product availability using HTTP requests
        This is faster than Selenium for simple status checks
        """
        client = await self.get_client()
        safe_log('info', f"🔍 Checking product availability: {product_url}")
        
        try:
            response = await client.get(product_url)
            response.raise_for_status()
            
            # Basic availability check based on response
            content = response.text.lower()
            
            availability_status = {
                'url': product_url,
                'status_code': response.status_code,
                'available': True,
                'in_stock': False,
                'price': None,
                'title': None,
                'check_time': datetime.now().isoformat()
            }
            
            # Check for common out-of-stock indicators
            for indicator in PopMartLocators.OUT_OF_STOCK_INDICATORS:
                if indicator in content:
                    availability_status['in_stock'] = False
                    availability_status['stock_status'] = indicator
                    break
            else:
                # If no out-of-stock indicators found, assume in stock
                availability_status['in_stock'] = True
                availability_status['stock_status'] = 'in stock'
            
            # Try to extract title (basic regex/string matching)
            if 'popmart.com' in product_url:
                # PopMart specific title extraction
                title_start = content.find('<title>')
                title_end = content.find('</title>')
                if title_start != -1 and title_end != -1:
                    title = content[title_start + 7:title_end].strip()
                    availability_status['title'] = title
            
            safe_log('info', f"✅ Product check complete: {availability_status['stock_status']}")
            return availability_status
            
        except httpx.HTTPError as e:
            safe_log('error', f"❌ HTTP error checking product: {e}")
            return {
                'url': product_url,
                'available': False,
                'error': str(e),
                'check_time': datetime.now().isoformat()
            }
    
    async def monitor_product(self, product_url: str, check_interval: int = 30, max_checks: int = 100):
        """
        Monitor product availability using HTTP requests
        Useful for monitoring restocks without keeping browser open
        """
        safe_log('info', f"🔄 Starting product monitoring (checking every {check_interval}s)")
        
        client = await self.get_client()
        checks_performed = 0
        last_status = None
        
        try:
            while checks_performed < max_checks:
                current_status = await self.check_product_availability(product_url)
                checks_performed += 1
                
                # Log status changes
                if last_status is None:
                    safe_log('info', f"📊 Initial status: {current_status.get('stock_status', 'unknown')}")
                elif last_status.get('in_stock') != current_status.get('in_stock'):
                    if current_status.get('in_stock'):
                        safe_log('info', "🎉 PRODUCT NOW IN STOCK! Ready for purchase automation...")
                        return current_status
                    else:
                        safe_log('info', "❌ Product went out of stock")
                
                last_status = current_status
                
                # Wait before next check
                if checks_performed < max_checks:
                    safe_log('info', f"⏰ Waiting {check_interval}s... (Check {checks_performed}/{max_checks})")
                    await asyncio.sleep(check_interval)
            
            safe_log('info', f"✅ Monitoring complete after {checks_performed} checks")
            return last_status
            
        except KeyboardInterrupt:
            safe_log('info', "🛑 Monitoring stopped by user")
            return last_status
        except Exception as e:
            safe_log('error', f"❌ Monitoring error: {e}")
            raise
    
    async def attempt_api_login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Attempt API-based login using HTTP requests
        This is experimental and may not work with all sites
        """
        client = await self.get_client()
        safe_log('info', "🔐 Attempting API-based login...")
        
        # This is a placeholder - actual API endpoints would need to be discovered
        # through browser network analysis
        login_data = {
            'email': username,
            'password': password,
            'remember': True
        }
        
        try:
            # First, get the login page to extract CSRF tokens if needed
            login_page_response = await client.get(PopMartLocators.LOGIN_PAGE)
            
            # Extract CSRF token or other required fields
            # This would need to be customized based on the actual login form
            
            # Attempt login POST request
            login_response = await client.post(
                APIEndpoints.LOGIN,  # Hypothetical endpoint
                json=login_data
            )
            
            if login_response.status_code == 200:
                safe_log('info', "✅ API login successful")
                return {
                    'success': True,
                    'cookies': dict(login_response.cookies),
                    'response': login_response.json() if login_response.headers.get('content-type', '').startswith('application/json') else None
                }
            else:
                safe_log('warning', f"❌ API login failed: {login_response.status_code}")
                return {
                    'success': False,
                    'status_code': login_response.status_code,
                    'response': login_response.text
                }
                
        except Exception as e:
            safe_log('error', f"❌ API login error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_product_info(self, product_id: str) -> Dict[str, Any]:
        """Get product information via API (experimental)"""
        client = await self.get_client()
        
        try:
            url = APIEndpoints.PRODUCT_INFO.format(product_id=product_id)
            response = await client.get(url)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': 'Product not found or API unavailable'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def is_client_active(self) -> bool:
        """Check if HTTP client is active"""
        return self.client is not None and not self.client.is_closed