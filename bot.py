import asyncio
import logging
from datetime import datetime
from typing import Optional
from pyrogram import Client, filters, types
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, update
from database import db_manager, User, TorrentUpload, ChatSettings
from config import settings
from utils import TorrentValidator, format_file_size, is_admin, get_user_info
from auth import AuthManager

logger = logging.getLogger(__name__)


class TorrentBot:
    def __init__(self):
        self.app = Client(
            name=settings.SESSION_NAME,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            bot_token=settings.BOT_TOKEN,
            workers=settings.WORKERS
        )
        self.auth_manager = AuthManager()
        self.torrent_validator = TorrentValidator()
        
    async def start(self):
        """Start the bot"""
        try:
            await db_manager.init_db()
            await self.app.start()
            logger.info(f"Bot {settings.BOT_NAME} started successfully!")
            
            # Register handlers
            self.register_handlers()
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot"""
        await self.app.stop()
        await db_manager.close()
        logger.info("Bot stopped")
    
    def register_handlers(self):
        """Register all message and callback handlers"""
        # Command handlers
        self.app.add_handler(MessageHandler(self.start_command, filters.command("start")))
        self.app.add_handler(MessageHandler(self.help_command, filters.command("help")))
        self.app.add_handler(MessageHandler(self.stats_command, filters.command("stats")))
        self.app.add_handler(MessageHandler(self.admin_command, filters.command("admin")))
        
        # Document/file handlers
        self.app.add_handler(MessageHandler(self.handle_document, filters.document))
        
        # Callback query handlers
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, client: Client, message: Message):
        """Handle /start command"""
        try:
            await self.register_user(message.from_user, message.chat.id)
            
            welcome_text = f"""
🐍 **Welcome to {settings.BOT_NAME}!**
*by @medusaXD*

I'm a powerful torrent downloader bot that helps you manage and share torrent files with advanced features.

**🔥 Features:**
• Upload and validate torrent files
• Support for both private chats and groups
• Admin authentication system
• File size validation up to 2GB
• Torrent metadata extraction
• Multi-user concurrent support

**📋 Commands:**
/help - Show detailed help
/stats - View upload statistics
/admin - Admin panel (admins only)

**🚀 Usage:**
Simply send me a .torrent file and I'll process it for you!

**✅ Supported in:**
• Private chats
• Groups and supergroups
• Multi-user environments
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📚 Help", callback_data="help")],
                [InlineKeyboardButton("📊 Stats", callback_data="stats")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.reply_text("❌ An error occurred. Please try again later.")
    
    async def help_command(self, client: Client, message: Message):
        """Handle /help command"""
        help_text = f"""
📚 **{settings.BOT_NAME} Help**
*by @medusaXD*

**🚀 Basic Usage:**
1. Send me a .torrent file
2. I'll validate and process it
3. Get detailed torrent information

**📋 Commands:**
/start - Start the bot
/help - Show this help message
/stats - View your upload statistics
/admin - Admin panel (admins only)

**📁 File Requirements:**
• File type: .torrent only
• Max size: {settings.MAX_FILE_SIZE}MB (2GB)
• Must be a valid torrent file

**👑 Admin Features:**
• User management
• Ban/unban users
• View all statistics
• Chat settings management

**🌐 Multi-Platform Support:**
This bot works in both private chats and groups!
Perfect for torrent communities and individual users.

**🔥 Powered by MedusaXD**
"""
        
        await message.reply_text(help_text)
    
    async def register_user(self, user: types.User, chat_id: int):
        """Register or update user in database"""
        try:
            async with db_manager.get_session() as session:
                # Check if user exists
                result = await session.execute(
                    select(User).where(User.id == user.id)
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    existing_user.username = user.username
                    existing_user.first_name = user.first_name
                    existing_user.last_name = user.last_name
                    existing_user.last_seen = datetime.utcnow()
                else:
                    # Create new user
                    new_user = User(
                        id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        is_admin=user.id in settings.ADMIN_USER_IDS
                    )
                    session.add(new_user)
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error registering user {user.id}: {e}")

    async def handle_document(self, client: Client, message: Message):
        """Handle document uploads"""
        try:
            # Register user first
            await self.register_user(message.from_user, message.chat.id)

            # Check if user is banned
            if not await self.auth_manager.is_user_allowed(message.from_user.id):
                await message.reply_text("❌ You are banned from using this bot.")
                return

            document = message.document

            # Check file extension
            if not any(document.file_name.lower().endswith(ext) for ext in settings.ALLOWED_TORRENT_EXTENSIONS):
                await message.reply_text(
                    f"❌ Invalid file type. Only {', '.join(settings.ALLOWED_TORRENT_EXTENSIONS)} files are allowed."
                )
                return

            # Check file size
            max_size_bytes = settings.MAX_FILE_SIZE * 1024 * 1024
            if document.file_size > max_size_bytes:
                await message.reply_text(
                    f"❌ File too large. Maximum size is {settings.MAX_FILE_SIZE}MB. "
                    f"Your file is {format_file_size(document.file_size)}."
                )
                return

            # Send processing message
            processing_msg = await message.reply_text("🔄 Processing torrent file...")

            # Download and validate torrent
            file_path = await message.download()
            validation_result = await self.torrent_validator.validate_torrent(file_path)

            if not validation_result.is_valid:
                await processing_msg.edit_text(f"❌ Invalid torrent file: {validation_result.error}")
                return

            # Save to database
            await self.save_torrent_upload(
                user_id=message.from_user.id,
                file_name=document.file_name,
                file_size=document.file_size,
                chat_id=message.chat.id,
                message_id=message.id,
                torrent_info=validation_result.metadata
            )

            # Create response
            response_text = f"""
✅ **Torrent Uploaded Successfully!**

📁 **File:** `{document.file_name}`
📏 **Size:** {format_file_size(document.file_size)}
🔗 **Info Hash:** `{validation_result.metadata.get('info_hash', 'N/A')}`
📊 **Files:** {validation_result.metadata.get('file_count', 'N/A')}
💾 **Total Size:** {format_file_size(validation_result.metadata.get('total_size', 0))}

**Torrent Details:**
{validation_result.metadata.get('name', 'N/A')}
"""

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 My Stats", callback_data="user_stats")],
                [InlineKeyboardButton("ℹ️ Torrent Info", callback_data=f"torrent_info_{message.id}")]
            ])

            await processing_msg.edit_text(response_text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error handling document: {e}")
            await message.reply_text("❌ An error occurred while processing your file.")

    async def save_torrent_upload(self, user_id: int, file_name: str, file_size: int,
                                 chat_id: int, message_id: int, torrent_info: dict):
        """Save torrent upload to database"""
        try:
            async with db_manager.get_session() as session:
                upload = TorrentUpload(
                    user_id=user_id,
                    file_name=file_name,
                    file_size=file_size,
                    chat_id=chat_id,
                    message_id=message_id,
                    torrent_info=str(torrent_info)
                )
                session.add(upload)
                await session.commit()

        except Exception as e:
            logger.error(f"Error saving torrent upload: {e}")

    async def stats_command(self, client: Client, message: Message):
        """Handle /stats command"""
        try:
            await self.register_user(message.from_user, message.chat.id)

            async with db_manager.get_session() as session:
                # Get user stats
                result = await session.execute(
                    select(TorrentUpload).where(TorrentUpload.user_id == message.from_user.id)
                )
                user_uploads = result.scalars().all()

                total_uploads = len(user_uploads)
                total_size = sum(upload.file_size for upload in user_uploads)

                stats_text = f"""
📊 **Your Statistics**

👤 **User:** {get_user_info(message.from_user)}
📁 **Total Uploads:** {total_uploads}
💾 **Total Size:** {format_file_size(total_size)}
📅 **Member Since:** {user_uploads[0].upload_date.strftime('%Y-%m-%d') if user_uploads else 'Today'}

**Recent Uploads:**
"""

                # Show last 5 uploads
                recent_uploads = sorted(user_uploads, key=lambda x: x.upload_date, reverse=True)[:5]
                for upload in recent_uploads:
                    stats_text += f"• {upload.file_name} ({format_file_size(upload.file_size)})\n"

                if not recent_uploads:
                    stats_text += "No uploads yet."

                await message.reply_text(stats_text)

        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await message.reply_text("❌ An error occurred while fetching statistics.")

    async def admin_command(self, client: Client, message: Message):
        """Handle /admin command"""
        try:
            if not await self.auth_manager.is_admin(message.from_user.id):
                await message.reply_text("❌ You don't have admin permissions.")
                return

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
                [InlineKeyboardButton("📊 Global Stats", callback_data="admin_stats")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")]
            ])

            admin_text = f"""
🔧 **{settings.BOT_NAME} - Admin Panel**
*by @medusaXD*

Welcome, {get_user_info(message.from_user)}!

Use the buttons below to manage the bot:
"""

            await message.reply_text(admin_text, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error in admin command: {e}")
            await message.reply_text("❌ An error occurred.")

    async def handle_callback(self, client: Client, callback_query: CallbackQuery):
        """Handle callback queries from inline keyboards"""
        try:
            data = callback_query.data

            if data == "help":
                await self.help_command(client, callback_query.message)
            elif data == "stats":
                await self.stats_command(client, callback_query.message)
            elif data == "user_stats":
                await self.stats_command(client, callback_query.message)
            elif data.startswith("admin_"):
                await self.handle_admin_callback(client, callback_query)
            elif data.startswith("torrent_info_"):
                await self.handle_torrent_info_callback(client, callback_query)

            await callback_query.answer()

        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await callback_query.answer("❌ An error occurred.")

    async def handle_admin_callback(self, client: Client, callback_query: CallbackQuery):
        """Handle admin-specific callbacks"""
        if not await self.auth_manager.is_admin(callback_query.from_user.id):
            await callback_query.answer("❌ Access denied.")
            return

        data = callback_query.data

        if data == "admin_stats":
            await self.show_global_stats(client, callback_query)
        elif data == "admin_users":
            await self.show_user_management(client, callback_query)
        elif data == "admin_settings":
            await self.show_admin_settings(client, callback_query)
        elif data == "admin_refresh":
            await self.admin_command(client, callback_query.message)

    async def handle_torrent_info_callback(self, client: Client, callback_query: CallbackQuery):
        """Handle torrent info callbacks"""
        try:
            message_id = int(callback_query.data.split("_")[-1])

            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(TorrentUpload).where(TorrentUpload.message_id == message_id)
                )
                upload = result.scalar_one_or_none()

                if upload:
                    info_text = f"""
📋 **Detailed Torrent Information**

📁 **File:** `{upload.file_name}`
👤 **Uploaded by:** User ID {upload.user_id}
📅 **Date:** {upload.upload_date.strftime('%Y-%m-%d %H:%M:%S')}
💾 **Size:** {format_file_size(upload.file_size)}

**Torrent Metadata:**
{upload.torrent_info}
"""
                else:
                    info_text = "❌ Torrent information not found."

                await callback_query.message.reply_text(info_text)

        except Exception as e:
            logger.error(f"Error showing torrent info: {e}")
            await callback_query.answer("❌ Error loading torrent info.")

    async def show_global_stats(self, client: Client, callback_query: CallbackQuery):
        """Show global statistics for admins"""
        try:
            async with db_manager.get_session() as session:
                # Get total uploads
                uploads_result = await session.execute(select(TorrentUpload))
                all_uploads = uploads_result.scalars().all()

                # Get total users
                users_result = await session.execute(select(User))
                all_users = users_result.scalars().all()

                total_uploads = len(all_uploads)
                total_size = sum(upload.file_size for upload in all_uploads)
                total_users = len(all_users)
                active_users = len([u for u in all_users if (datetime.utcnow() - u.last_seen).days <= 7])

                stats_text = f"""
📊 **Global Statistics**

👥 **Total Users:** {total_users}
🟢 **Active Users (7d):** {active_users}
📁 **Total Uploads:** {total_uploads}
💾 **Total Data:** {format_file_size(total_size)}

**Top Uploaders:**
"""

                # Get top uploaders
                user_upload_counts = {}
                for upload in all_uploads:
                    user_upload_counts[upload.user_id] = user_upload_counts.get(upload.user_id, 0) + 1

                top_uploaders = sorted(user_upload_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                for user_id, count in top_uploaders:
                    stats_text += f"• User {user_id}: {count} uploads\n"

                await callback_query.message.reply_text(stats_text)

        except Exception as e:
            logger.error(f"Error showing global stats: {e}")
            await callback_query.answer("❌ Error loading statistics.")

    async def show_user_management(self, client: Client, callback_query: CallbackQuery):
        """Show user management panel"""
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user")],
            [InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user")],
            [InlineKeyboardButton("👑 Promote Admin", callback_data="admin_promote")],
            [InlineKeyboardButton("👤 User Info", callback_data="admin_user_info")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]
        ])

        text = """
👥 **User Management**

Select an action:
• Ban/Unban users
• Promote to admin
• View user information

Send user ID after selecting action.
"""

        await callback_query.message.edit_text(text, reply_markup=keyboard)

    async def show_admin_settings(self, client: Client, callback_query: CallbackQuery):
        """Show admin settings panel"""
        settings_text = f"""
⚙️ **Bot Settings**

**Current Configuration:**
• Max File Size: {settings.MAX_FILE_SIZE}MB
• Allowed Extensions: {', '.join(settings.ALLOWED_TORRENT_EXTENSIONS)}
• Workers: {settings.WORKERS}
• Log Level: {settings.LOG_LEVEL}

**Database:** {settings.DATABASE_URL.split('://')[0]}
**Admins:** {len(settings.ADMIN_USER_IDS)} configured
"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")]
        ])

        await callback_query.message.edit_text(settings_text, reply_markup=keyboard)
