"""
Command-line interface for LabubuBot
"""

import os
import asyncio
from typing import Optional

from .bot import LabubuBot
from .config import Config, create_sample_config, validate_config
from .utils import safe_print, print_banner, setup_logging, create_directories


class LabubuBotCLI:
    """Command-line interface for LabubuBot"""
    
    def __init__(self, config_path: str = "_data/config.yml"):
        self.config_path = config_path
        self.bot: Optional[LabubuBot] = None
        
    def setup(self):
        """Setup logging and directories"""
        setup_logging()
        create_directories()
    
    def ensure_config_exists(self) -> bool:
        """Ensure configuration file exists, create sample if not"""
        if not os.path.exists(self.config_path):
            if create_sample_config(self.config_path):
                safe_print(f"📝 Sample config created at {self.config_path}")
                safe_print("Please edit the config file with your credentials and run again.")
                return False
            else:
                safe_print("❌ Failed to create sample config")
                return False
        return True
    
    def load_bot(self) -> bool:
        """Load bot with configuration validation"""
        try:
            config = Config.from_file(self.config_path)
            
            # Validate configuration
            is_valid, errors, needs_interactive_login = validate_config(config)
            
            if not is_valid:
                safe_print("❌ Configuration validation failed:")
                for error in errors:
                    safe_print(f"   - {error}")
                return False
            
            if needs_interactive_login:
                safe_print("⚠️  No credentials found in config - interactive login will be used")
                safe_print("💡 A browser window will open for you to log in manually")
            
            self.bot = LabubuBot(config)
            return True
            
        except Exception as e:
            safe_print(f"❌ Failed to load configuration: {e}")
            return False
    
    def show_menu(self):
        """Display the main menu"""
        safe_print("\n🤖 LabubuBot Menu:")
        safe_print("1. Login and Export Cookies (Selenium)")
        safe_print("2. Automated Purchase (Cookie-based)")
        safe_print("3. Full Login-based Purchase")
        safe_print("4. Check Product Availability (HTTP)")
        safe_print("5. Monitor Product for Restock (HTTP)")
        safe_print("6. Monitor + Auto Purchase")
        safe_print("7. API Login Test (Experimental)")
        safe_print("0. Exit")
    
    def get_user_choice(self) -> str:
        """Get user menu choice"""
        try:
            choice = input("\nSelect option (0-7): ").strip()
            return choice
        except (KeyboardInterrupt, EOFError):
            return "0"
    
    async def handle_choice_1(self):
        """Handle choice 1: Login and Export Cookies"""
        safe_print("🔐 Starting login and cookie export...")
        
        # Check if we have credentials
        if not self.bot.config.username or not self.bot.config.password:
            safe_print("💡 No credentials configured - opening browser for interactive login")
            safe_print("📱 Please complete the login process in the browser window")
            safe_print("⏳ The bot will automatically detect when you're logged in")
        
        try:
            self.bot.start_selenium_session(headless=False)  # Always keep visible for login
            session_data = self.bot.login_and_export_cookies()
            safe_print("✅ Session data exported successfully!")
            safe_print("💾 Cookies and storage data have been saved")
            safe_print("🚀 You can now use option 2 for faster automation.")
            
        except Exception as e:
            safe_print(f"❌ Login failed: {e}")
            safe_print("💡 Try refreshing the page or checking your internet connection")
    
    async def handle_choice_2(self):
        """Handle choice 2: Automated Purchase (Cookie-based)"""
        safe_print("🛒 Starting automated purchase...")
        
        try:
            self.bot.start_selenium_session()
            result = self.bot.automated_purchase()
            
            if result['success']:
                safe_print("🎉 Purchase process completed!")
                safe_print(f"⏱️  Processing time: {result['formatted_time']}")
                input("Press Enter to close browser...")
            else:
                safe_print("❌ Purchase process failed")
                
        except FileNotFoundError:
            safe_print("❌ Session data not found. Please run option 1 first to login and export cookies.")
        except Exception as e:
            safe_print(f"❌ Purchase failed: {e}")
    
    async def handle_choice_3(self):
        """Handle choice 3: Full Login-based Purchase"""
        safe_print("🔐 Starting full login-based purchase...")
        
        # Check if we have credentials
        if not self.bot.config.username or not self.bot.config.password:
            safe_print("💡 No credentials configured - opening browser for interactive login")
            safe_print("📱 Please complete the login process in the browser window")
        
        try:
            self.bot.start_selenium_session(headless=False)
            self.bot.login_and_export_cookies()
            safe_print("🔄 Now proceeding with purchase...")
            
            result = self.bot.automated_purchase()
            if result['success']:
                safe_print("🎉 Purchase process completed!")
                safe_print(f"⏱️  Processing time: {result['formatted_time']}")
                input("Press Enter to close browser...")
            else:
                safe_print("❌ Purchase process failed")
                
        except Exception as e:
            safe_print(f"❌ Login-based purchase failed: {e}")
    
    async def handle_choice_4(self):
        """Handle choice 4: Check Product Availability"""
        safe_print("🔍 Checking product availability...")
        
        try:
            result = await self.bot.check_product_availability()
            
            safe_print(f"\n📊 Product Status:")
            safe_print(f"   URL: {result.get('url', 'N/A')}")
            safe_print(f"   Available: {result.get('available', 'Unknown')}")
            safe_print(f"   In Stock: {result.get('in_stock', 'Unknown')}")
            safe_print(f"   Status: {result.get('stock_status', 'Unknown')}")
            if result.get('title'):
                safe_print(f"   Title: {result['title']}")
            safe_print(f"   Check Time: {result.get('check_time', 'N/A')}")
            
        except Exception as e:
            safe_print(f"❌ Availability check failed: {e}")
    
    async def handle_choice_5(self):
        """Handle choice 5: Monitor Product for Restock"""
        safe_print("🔄 Setting up product monitoring...")
        
        # Get monitoring parameters
        check_interval = input("Enter check interval in seconds (default 30): ").strip()
        max_checks = input("Enter maximum number of checks (default 100): ").strip()
        
        try:
            check_interval = int(check_interval) if check_interval else 30
            max_checks = int(max_checks) if max_checks else 100
        except ValueError:
            check_interval, max_checks = 30, 100
        
        safe_print(f"🔄 Starting monitoring (every {check_interval}s, max {max_checks} checks)")
        safe_print("Press Ctrl+C to stop monitoring")
        
        try:
            result = await self.bot.monitor_product_for_restock(check_interval, max_checks)
            
            if result and result.get('in_stock'):
                safe_print("🎉 Product is now in stock!")
                safe_print("Use option 2 or 6 to proceed with purchase.")
            else:
                safe_print("⏰ Monitoring completed - product not available")
                
        except KeyboardInterrupt:
            safe_print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            safe_print(f"❌ Monitoring failed: {e}")
    
    async def handle_choice_6(self):
        """Handle choice 6: Monitor + Auto Purchase"""
        safe_print("🔄 Setting up monitoring with auto-purchase...")
        
        # Check session data availability
        try:
            self.bot.load_session_data()
            safe_print("✅ Found existing session data")
        except FileNotFoundError:
            safe_print("⚠️  No session data found - you'll need to login first")
            safe_print("💡 The bot will open a browser for login when purchase is triggered")
        
        # Get monitoring parameters
        check_interval = input("Enter check interval in seconds (default 30): ").strip()
        max_checks = input("Enter maximum number of checks (default 100): ").strip()
        
        try:
            check_interval = int(check_interval) if check_interval else 30
            max_checks = int(max_checks) if max_checks else 100
        except ValueError:
            check_interval, max_checks = 30, 100
        
        safe_print(f"🔄 Starting monitoring with auto-purchase (every {check_interval}s, max {max_checks} checks)")
        safe_print("Press Ctrl+C to stop monitoring")
        
        try:
            result = await self.bot.monitor_and_purchase(check_interval, max_checks)
            
            if result['success']:
                safe_print("🎉 Monitoring and purchase completed successfully!")
                purchase_result = result.get('purchase_result', {})
                if purchase_result.get('formatted_time'):
                    safe_print(f"⏱️  Purchase time: {purchase_result['formatted_time']}")
                input("Press Enter to close browser...")
            else:
                safe_print("❌ Monitoring completed but purchase was not successful")
                safe_print(f"Reason: {result.get('message', 'Unknown error')}")
                
        except KeyboardInterrupt:
            safe_print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            safe_print(f"❌ Monitor and purchase failed: {e}")
    
    async def handle_choice_7(self):
        """Handle choice 7: API Login Test"""
        safe_print("🧪 Testing API login (experimental)...")
        
        try:
            result = await self.bot.api_login_test()
            
            safe_print(f"\n🔐 API Login Test Result:")
            safe_print(f"   Success: {result.get('success', False)}")
            if result.get('success'):
                safe_print(f"   Cookies: {len(result.get('cookies', {}))} cookies received")
                safe_print("   Note: This is experimental and may not work for actual purchases")
            else:
                safe_print(f"   Error: {result.get('error', 'Unknown error')}")
                if result.get('status_code'):
                    safe_print(f"   Status Code: {result['status_code']}")
                safe_print("   This is expected - PopMart likely doesn't have public API endpoints")
                
        except Exception as e:
            safe_print(f"❌ API login test failed: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.bot:
            self.bot.close_sessions()
    
    async def run_async_choice(self, choice: str):
        """Run async choice handler"""
        handlers = {
            "1": self.handle_choice_1,
            "2": self.handle_choice_2,
            "3": self.handle_choice_3,
            "4": self.handle_choice_4,
            "5": self.handle_choice_5,
            "6": self.handle_choice_6,
            "7": self.handle_choice_7,
        }
        
        handler = handlers.get(choice)
        if handler:
            await handler()
        else:
            safe_print("❌ Invalid option selected")
    
    def run(self):
        """Main CLI loop"""
        print_banner()
        self.setup()
        
        # Ensure config exists
        if not self.ensure_config_exists():
            return
        
        # Load bot
        if not self.load_bot():
            return
        
        try:
            while True:
                self.show_menu()
                choice = self.get_user_choice()
                
                if choice == "0":
                    safe_print("👋 Goodbye!")
                    break
                elif choice in ["1", "2", "3", "4", "5", "6", "7"]:
                    try:
                        asyncio.run(self.run_async_choice(choice))
                    except KeyboardInterrupt:
                        safe_print("\n🛑 Operation interrupted by user")
                    except Exception as e:
                        safe_print(f"❌ Operation failed: {e}")
                    
                    # Pause before showing menu again
                    input("\nPress Enter to continue...")
                else:
                    safe_print("❌ Invalid option. Please select 0-7.")
                    
        except KeyboardInterrupt:
            safe_print("\n🛑 LabubuBot interrupted by user")
        except Exception as e:
            safe_print(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()


def main():
    """Main entry point for CLI"""
    cli = LabubuBotCLI()
    cli.run()


if __name__ == "__main__":
    main()