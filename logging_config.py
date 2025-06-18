import logging
import sys
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Setup logging configuration"""
    
    # Remove default loguru handler
    logger.remove()
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Console handler with colors
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # File handler for all logs
    logger.add(
        logs_dir / "bot.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Error file handler
    logger.add(
        logs_dir / "errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # User actions log
    logger.add(
        logs_dir / "user_actions.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "User action:" in record["message"],
        rotation="5 MB",
        retention="90 days",
        compression="zip"
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set specific loggers
    for logger_name in ["pyrogram", "sqlalchemy", "aiosqlite"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        logging.getLogger(logger_name).propagate = False
    
    logger.info("Logging system initialized")


def log_startup_info():
    """Log startup information"""
    logger.info("=" * 50)
    logger.info(f"Starting {settings.BOT_NAME}")
    logger.info(f"Log Level: {settings.LOG_LEVEL}")
    logger.info(f"Workers: {settings.WORKERS}")
    logger.info(f"Max File Size: {settings.MAX_FILE_SIZE}MB")
    logger.info(f"Database: {settings.DATABASE_URL.split('://')[0]}")
    logger.info(f"Admins configured: {len(settings.ADMIN_USER_IDS)}")
    logger.info("=" * 50)


def log_shutdown_info():
    """Log shutdown information"""
    logger.info("=" * 50)
    logger.info(f"{settings.BOT_NAME} shutting down")
    logger.info(f"Shutdown time: {datetime.utcnow()}")
    logger.info("=" * 50)


class BotMetrics:
    """Simple metrics collection for monitoring"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.total_uploads = 0
        self.total_users = 0
        self.errors_count = 0
        self.last_error = None
    
    def increment_uploads(self):
        self.total_uploads += 1
        logger.info(f"Total uploads: {self.total_uploads}")
    
    def increment_users(self):
        self.total_users += 1
        logger.info(f"Total users: {self.total_users}")
    
    def log_error(self, error: str):
        self.errors_count += 1
        self.last_error = error
        logger.error(f"Error #{self.errors_count}: {error}")
    
    def get_uptime(self):
        return datetime.utcnow() - self.start_time
    
    def log_metrics(self):
        uptime = self.get_uptime()
        logger.info(f"Bot Metrics - Uptime: {uptime}, Uploads: {self.total_uploads}, "
                   f"Users: {self.total_users}, Errors: {self.errors_count}")


# Global metrics instance
metrics = BotMetrics()
