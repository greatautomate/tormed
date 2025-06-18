import asyncio
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from config import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)


class TorrentUpload(Base):
    __tablename__ = "torrent_uploads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # in bytes
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_valid = Column(Boolean, default=True)
    torrent_info = Column(Text, nullable=True)  # JSON string with torrent metadata


class ChatSettings(Base):
    __tablename__ = "chat_settings"
    
    chat_id = Column(BigInteger, primary_key=True)
    chat_type = Column(String(50), nullable=False)  # 'private', 'group', 'supergroup'
    chat_title = Column(String(500), nullable=True)
    is_enabled = Column(Boolean, default=True)
    max_file_size = Column(Integer, default=50)  # MB
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        self.engine = None
        self.session_factory = None
        
    async def init_db(self):
        """Initialize database connection and create tables"""
        try:
            if self.database_url.startswith("sqlite"):
                # For SQLite
                self.database_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
                self.engine = create_async_engine(self.database_url, echo=False)
            else:
                # For PostgreSQL
                self.database_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
                self.engine = create_async_engine(self.database_url, echo=False)
            
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            await self.init_db()
        return self.session_factory()
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager()
