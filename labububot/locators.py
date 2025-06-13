"""
CSS selectors and URLs for PopMart website elements
"""

class PopMartLocators:
    """CSS selectors for PopMart website elements"""
    
    # URLs
    LOGIN_PAGE = 'https://www.popmart.com/us/user/login?redirect=%2Faccount'
    BASE_URL = 'https://www.popmart.com'
    
    # Login elements
    AGREEMENT = '.policy_acceptBtn__ZNU71'
    LOGIN_FIELD = '.index_loginInput__HBgjq'
    LOGIN_BTN = '.index_loginButton__O6r8l'
    PASSWORD_FIELD = '#password'
    
    # Shopping elements  
    BUY_NOW = '.index_usBtn__2KlEx.index_red__kx6Ql.index_btnFull__F7k90'
    GO_TO_CART = '.ant-btn.ant-btn-primary.ant-btn-dangerous.index_noticeFooterBtn__XpFsc'
    CHECKOUT = '.ant-btn.ant-btn-primary.ant-btn-dangerous.index_checkout__V9YPC'
    CHECKBOX = '.index_checkbox__w_166'
    PAY = '#__next > div > div > div.layout_pcLayout__49ZwP > div.index_container__SNJGT > div.index_leftContainer__3Roux > div > button'
    ORDERING = '#buttons-container > div > div.paypal-button-row.paypal-button-number-0.paypal-button-layout-horizontal.paypal-button-number-multiple.paypal-button-env-production.paypal-button-color-black.paypal-button-text-color-white.paypal-logo-color-white.paypal-button-shape-rect'
    
    # Status indicators
    OUT_OF_STOCK_INDICATORS = [
        'out of stock',
        'sold out', 
        'not available',
        'unavailable',
        'coming soon'
    ]
    
    # Common Chrome installation paths (Windows)
    CHROME_PATHS_WINDOWS = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", 
        r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
        r"C:\Program Files\Google\Chrome Dev\Application\chrome.exe",
    ]
    
    @classmethod
    def get_chrome_paths_for_user(cls, username: str = None) -> list[str]:
        """Get Chrome paths with current username substituted"""
        import os
        current_user = username or os.getenv('USERNAME', 'User')
        
        paths = []
        for path in cls.CHROME_PATHS_WINDOWS:
            if '{username}' in path:
                paths.append(path.format(username=current_user))
            else:
                paths.append(path)
        
        return paths


class APIEndpoints:
    """API endpoints for PopMart (experimental)"""
    
    BASE_API = 'https://www.popmart.com/api'
    
    # Auth endpoints (hypothetical - would need to be discovered)
    LOGIN = f'{BASE_API}/auth/login'
    LOGOUT = f'{BASE_API}/auth/logout'
    REFRESH = f'{BASE_API}/auth/refresh'
    
    # Product endpoints
    PRODUCT_INFO = f'{BASE_API}/products/{{product_id}}'
    PRODUCT_AVAILABILITY = f'{BASE_API}/products/{{product_id}}/availability'
    
    # Cart endpoints  
    ADD_TO_CART = f'{BASE_API}/cart/add'
    GET_CART = f'{BASE_API}/cart'
    CHECKOUT = f'{BASE_API}/checkout'