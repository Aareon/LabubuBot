"""
Utility functions for LabubuBot
"""

import sys
import io
import logging
from pathlib import Path


def setup_logging():
    """Setup logging with proper encoding for Windows console"""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Fix Windows console encoding issues
    if sys.platform == "win32":
        # Set console to UTF-8 if possible
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except:
            pass

    # Create handlers with proper encoding
    file_handler = logging.FileHandler(log_dir / 'labubot.log', encoding='utf-8')
    console_handler = logging.StreamHandler()

    # Set encoding for console handler on Windows
    if sys.platform == "win32":
        try:
            console_handler.stream = io.TextIOWrapper(
                console_handler.stream.buffer, 
                encoding='utf-8', 
                errors='replace'
            )
        except:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler]
    )
    
    return logging.getLogger(__name__)


def safe_print(message: str):
    """Print message with emoji fallback for Windows console"""
    if sys.platform == "win32":
        # Replace emojis with safe alternatives for Windows console
        emoji_map = {
            '🚀': '[START]',
            '✅': '[OK]',
            '🔐': '[LOGIN]',
            '📄': '[PAGE]',
            '🔍': '[SEARCH]',
            '🔄': '[RELOAD]',
            '💾': '[SAVE]',
            '🛒': '[CART]',
            '🎯': '[TARGET]',
            '🎉': '[SUCCESS]',
            '🔗': '[LINK]',
            '⏱️': '[TIME]',
            '💳': '[PAYMENT]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '📊': '[STATUS]',
            '⏰': '[WAIT]',
            '🛑': '[STOP]',
            '🤖': '[BOT]',
            '📝': '[CONFIG]',
            '🔒': '[CLOSE]',
            'ℹ️': '[INFO]',
            '📤': '[EXPORT]',
            '🔑': '[KEY]',
            '📱': '[MOBILE]',
            '💡': '[TIP]',
            '🎮': '[GAME]',
            '🌐': '[WEB]',
            '⚡': '[FAST]',
            '🔧': '[TOOL]',
            '📋': '[LIST]',
            '🎪': '[EVENT]',
            '🏆': '[WIN]',
            '🎊': '[PARTY]',
        }
        
        safe_message = message
        for emoji, replacement in emoji_map.items():
            safe_message = safe_message.replace(emoji, replacement)
        
        try:
            print(safe_message)
        except UnicodeEncodeError:
            # Final fallback - remove any remaining problematic characters
            print(safe_message.encode('ascii', errors='ignore').decode('ascii'))
    else:
        print(message)


def safe_log(level: str, message: str):
    """Log message with emoji handling"""
    logger = logging.getLogger(__name__)
    
    if sys.platform == "win32":
        # For logging, replace emojis with text
        emoji_map = {
            '🚀': 'START',
            '✅': 'OK',
            '🔐': 'LOGIN',
            '📄': 'PAGE',
            '🔍': 'SEARCH',
            '🔄': 'RELOAD',
            '💾': 'SAVE',
            '🛒': 'CART',
            '🎯': 'TARGET',
            '🎉': 'SUCCESS',
            '🔗': 'LINK',
            '⏱️': 'TIME',
            '💳': 'PAYMENT',
            '❌': 'ERROR',
            '⚠️': 'WARNING',
            '📊': 'STATUS',
            '⏰': 'WAIT',
            '🛑': 'STOP',
            '🤖': 'BOT',
            '📝': 'CONFIG',
            '🔒': 'CLOSE',
            'ℹ️': 'INFO',
            '📤': 'EXPORT',
            '🔑': 'KEY',
            '📱': 'MOBILE',
            '💡': 'TIP',
            '🎮': 'GAME',
            '🌐': 'WEB',
            '⚡': 'FAST',
            '🔧': 'TOOL',
            '📋': 'LIST',
            '🎪': 'EVENT',
            '🏆': 'WIN',
            '🎊': 'PARTY',
        }
        
        safe_message = message
        for emoji, replacement in emoji_map.items():
            safe_message = safe_message.replace(emoji, f'[{replacement}]')
    else:
        safe_message = message
    
    if level.lower() == 'info':
        logger.info(safe_message)
    elif level.lower() == 'error':
        logger.error(safe_message)
    elif level.lower() == 'warning':
        logger.warning(safe_message)
    elif level.lower() == 'debug':
        logger.debug(safe_message)
    else:
        logger.info(safe_message)


def print_banner():
    """Print ASCII banner with Windows console compatibility"""
    banner = """
    ██╗      █████╗ ██████╗ ██╗   ██╗██████╗  ██████╗ ████████╗
    ██║     ██╔══██╗██╔══██╗██║   ██║██╔══██╗██╔═══██╗╚══██╔══╝
    ██║     ███████║██████╔╝██║   ██║██████╔╝██║   ██║   ██║   
    ██║     ██╔══██║██╔══██╗██║   ██║██╔══██╗██║   ██║   ██║   
    ███████╗██║  ██║██████╔╝╚██████╔╝██████╔╝╚██████╔╝   ██║   
    ╚══════╝╚═╝  ╚═╝╚═════╝  ╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   
    """
    
    if sys.platform == "win32":
        subtitle = """
    [BOT] LabubuBot Python Edition - PopMart Automation
    [START] Selenium-powered with Login & Cookie Export
    """
    else:
        subtitle = """
    🤖 LabubuBot Python Edition - PopMart Automation
    🚀 Selenium-powered with Login & Cookie Export
    """
    
    safe_print(banner + subtitle)


def format_time(seconds: float) -> str:
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"


def validate_url(url: str) -> bool:
    """Validate if URL is properly formatted"""
    return url.startswith(('http://', 'https://'))


def extract_product_id(url: str) -> str:
    """Extract product ID from PopMart URL"""
    try:
        # Example: https://www.popmart.com/us/products/1372/product-name
        parts = url.split('/')
        if 'products' in parts:
            product_idx = parts.index('products')
            if product_idx + 1 < len(parts):
                return parts[product_idx + 1]
    except:
        pass
    return ""


def create_directories():
    """Create necessary directories for the bot"""
    directories = ['_data', 'logs']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)