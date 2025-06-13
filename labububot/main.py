#!/usr/bin/env python3
"""
LabubuBot - PopMart Automation Script
Main entry point

This is a Python port of the original LabubuBot (JavaScript/Puppeteer) 
with enhanced Selenium features for login automation and cookie management.
"""

import sys
import os

# Add the current directory to Python path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from labububot.cli import main

if __name__ == "__main__":
    main()