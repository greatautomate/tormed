#!/usr/bin/env python3
"""
MedusaXD Torrent Downloader Bot by @medusaXD
A comprehensive bot for uploading and managing torrent files with admin features.
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from bot import TorrentBot
from logging_config import setup_logging, log_startup_info, log_shutdown_info, metrics
from config import settings
from loguru import logger


class BotManager:
    """Manages the bot lifecycle"""
    
    def __init__(self):
        self.bot = None
        self.shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the bot with proper error handling"""
        try:
            # Setup logging
            setup_logging()
            log_startup_info()
            
            # Create and start bot
            self.bot = TorrentBot()
            
            # Setup signal handlers for graceful shutdown
            self.setup_signal_handlers()
            
            logger.info("Starting bot...")
            await self.bot.start()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Fatal error starting bot: {e}")
            metrics.log_error(f"Fatal startup error: {e}")
            raise
        finally:
            await self.shutdown()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.shutdown_event.set()
        
        # Handle SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            log_shutdown_info()
            
            if self.bot:
                logger.info("Stopping bot...")
                await self.bot.stop()
            
            # Log final metrics
            metrics.log_metrics()
            
            logger.info("Shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


async def main():
    """Main entry point"""
    try:
        # Validate configuration
        if not all([settings.API_ID, settings.API_HASH, settings.BOT_TOKEN]):
            logger.error("Missing required configuration: API_ID, API_HASH, or BOT_TOKEN")
            sys.exit(1)
        
        if not settings.ADMIN_USER_IDS:
            logger.warning("No admin users configured!")
        
        # Create and start bot manager
        bot_manager = BotManager()
        await bot_manager.start()
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Python 3.8 or higher is required!")
            sys.exit(1)
        
        # Run the bot
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
