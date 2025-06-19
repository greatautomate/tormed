import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Telegram Bot Configuration
    API_ID: int
    API_HASH: str
    BOT_TOKEN: str
    
    # Admin Configuration
    ADMIN_USER_IDS: List[int] = []
    SUPER_ADMIN_ID: int
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///bot.db"
    
    # Bot Configuration
    BOT_NAME: str = "MedusaXD Torrent Downloader"
    MAX_FILE_SIZE: int = 2048  # MB (2GB)
    ALLOWED_TORRENT_EXTENSIONS: List[str] = [".torrent"]
    LOG_LEVEL: str = "INFO"
    
    # Session Configuration
    SESSION_NAME: str = "medusaxd_bot_session"
    WORKERS: int = 4
    
    # Server Configuration (for Render.com)
    PORT: int = 10000
    
    @field_validator('ADMIN_USER_IDS', mode='before')
    @classmethod
    def parse_admin_user_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',') if x.strip()]
        elif isinstance(v, int):
            return [v]  # Convert single int to list
        return v
    
    @field_validator('ALLOWED_TORRENT_EXTENSIONS', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        return v
    
    model_config = {"env_file": ".env", "case_sensitive": True}


# Global settings instance
settings = Settings()

# Ensure super admin is in admin list
if settings.SUPER_ADMIN_ID not in settings.ADMIN_USER_IDS:
    settings.ADMIN_USER_IDS.append(settings.SUPER_ADMIN_ID)
