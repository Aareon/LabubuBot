"""
Configuration management for LabubuBot
"""

import os
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .utils import safe_log


@dataclass
class Config:
    """Configuration class for LabubuBot"""
    username: str
    password: str
    target_product: str
    cookie_file: str
    storage_file: str
    headless: bool = False
    timeout: int = 10
    
    @classmethod
    def from_file(cls, config_path: str = "_data/config.yml") -> 'Config':
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
                
            return cls(
                username=config_data['login_base']['creds']['username'],
                password=config_data['login_base']['creds']['password'],
                target_product=config_data['target_product'],
                cookie_file=config_data['cookie_base']['cookie_file'],
                storage_file=config_data['cookie_base']['storage_file'],
                headless=config_data.get('headless', False),
                timeout=config_data.get('timeout', 10)
            )
        except Exception as e:
            safe_log('error', f"Failed to load config: {e}")
            raise


def create_sample_config(config_path: str = "_data/config.yml") -> bool:
    """Create a sample configuration file"""
    try:
        os.makedirs("_data", exist_ok=True)
        
        sample_config = {
            'login_base': {
                'creds': {
                    'username': '',
                    'password': ''
                }
            },
            'cookie_base': {
                'cookie_file': 'www.popmart.com.cookies.json',
                'storage_file': 'www.popmart.com.storage.json'
            },
            'target_product': 'https://www.popmart.com/us/products/1372/THE-MONSTERS---Have-a-Seat-Vinyl-Plush-Blind-Box',
            'headless': False,
            'timeout': 10
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(sample_config, f, default_flow_style=False)
        
        return True
        
    except Exception as e:
        safe_log('error', f"Failed to create sample config: {e}")
        return False


def validate_config(config: Config) -> tuple[bool, list[str], bool]:
    """
    Validate configuration and return errors if any
    Returns: (is_valid, errors, needs_interactive_login)
    """
    errors = []
    needs_interactive_login = False
    
    # Check if username/password are missing
    if not config.username or not config.password:
        needs_interactive_login = True
        # Don't add these as "errors" since we can handle interactively
    
    if not config.target_product:
        errors.append("Target product URL is required")
    elif not config.target_product.startswith('http'):
        errors.append("Target product must be a valid URL")
    
    if config.timeout <= 0:
        errors.append("Timeout must be positive")
        
    return len(errors) == 0, errors, needs_interactive_login