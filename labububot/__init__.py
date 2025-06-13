"""
LabubuBot - PopMart Automation Package

A Python package for automating PopMart purchases using Selenium and HTTP requests.
"""

__version__ = "1.0.0"
__author__ = "LabubuBot Contributors"
__description__ = "PopMart Automation with Selenium and HTTP support"

from .bot import LabubuBot
from .config import Config
from .locators import PopMartLocators

__all__ = [
    "LabubuBot",
    "Config", 
    "PopMartLocators",
    "__version__",
]