import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from database import db_manager, User
from config import settings

logger = logging.getLogger(__name__)


class AuthManager:
    """Handles authentication and authorization for the bot"""
    
    def __init__(self):
        self.admin_cache = set(settings.ADMIN_USER_IDS)
        self.banned_cache = set()
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        try:
            # Check cache first
            if user_id in self.admin_cache:
                return True
            
            # Check database
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user and user.is_admin:
                    self.admin_cache.add(user_id)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False
    
    async def is_super_admin(self, user_id: int) -> bool:
        """Check if user is the super admin"""
        return user_id == settings.SUPER_ADMIN_ID
    
    async def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot (not banned)"""
        try:
            # Check cache first
            if user_id in self.banned_cache:
                return False
            
            # Check database
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user and user.is_banned:
                    self.banned_cache.add(user_id)
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking user permission for {user_id}: {e}")
            return True  # Default to allowing if error occurs
    
    async def ban_user(self, user_id: int, admin_id: int) -> bool:
        """Ban a user"""
        try:
            # Check if admin has permission
            if not await self.is_admin(admin_id):
                return False
            
            # Super admin cannot be banned
            if user_id == settings.SUPER_ADMIN_ID:
                return False
            
            async with db_manager.get_session() as session:
                # Update user ban status
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(is_banned=True)
                )
                await session.commit()
                
                # Update cache
                self.banned_cache.add(user_id)
                
                logger.info(f"User {user_id} banned by admin {admin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int, admin_id: int) -> bool:
        """Unban a user"""
        try:
            # Check if admin has permission
            if not await self.is_admin(admin_id):
                return False
            
            async with db_manager.get_session() as session:
                # Update user ban status
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(is_banned=False)
                )
                await session.commit()
                
                # Update cache
                self.banned_cache.discard(user_id)
                
                logger.info(f"User {user_id} unbanned by admin {admin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    async def promote_admin(self, user_id: int, super_admin_id: int) -> bool:
        """Promote a user to admin (only super admin can do this)"""
        try:
            # Only super admin can promote
            if not await self.is_super_admin(super_admin_id):
                return False
            
            async with db_manager.get_session() as session:
                # Update user admin status
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(is_admin=True)
                )
                await session.commit()
                
                # Update cache
                self.admin_cache.add(user_id)
                
                logger.info(f"User {user_id} promoted to admin by super admin {super_admin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error promoting user {user_id} to admin: {e}")
            return False
    
    async def demote_admin(self, user_id: int, super_admin_id: int) -> bool:
        """Demote an admin to regular user (only super admin can do this)"""
        try:
            # Only super admin can demote
            if not await self.is_super_admin(super_admin_id):
                return False
            
            # Cannot demote super admin
            if user_id == settings.SUPER_ADMIN_ID:
                return False
            
            async with db_manager.get_session() as session:
                # Update user admin status
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(is_admin=False)
                )
                await session.commit()
                
                # Update cache
                self.admin_cache.discard(user_id)
                
                logger.info(f"User {user_id} demoted from admin by super admin {super_admin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error demoting user {user_id} from admin: {e}")
            return False
    
    async def get_user_info(self, user_id: int) -> Optional[dict]:
        """Get detailed user information"""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    return {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_admin': user.is_admin,
                        'is_banned': user.is_banned,
                        'created_at': user.created_at,
                        'last_seen': user.last_seen
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info for {user_id}: {e}")
            return None
    
    async def get_all_admins(self) -> List[dict]:
        """Get list of all admins"""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(User).where(User.is_admin == True)
                )
                admins = result.scalars().all()
                
                return [
                    {
                        'id': admin.id,
                        'username': admin.username,
                        'first_name': admin.first_name,
                        'last_name': admin.last_name,
                        'created_at': admin.created_at,
                        'last_seen': admin.last_seen
                    }
                    for admin in admins
                ]
                
        except Exception as e:
            logger.error(f"Error getting admin list: {e}")
            return []
    
    async def get_banned_users(self) -> List[dict]:
        """Get list of all banned users"""
        try:
            async with db_manager.get_session() as session:
                result = await session.execute(
                    select(User).where(User.is_banned == True)
                )
                banned_users = result.scalars().all()
                
                return [
                    {
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'created_at': user.created_at,
                        'last_seen': user.last_seen
                    }
                    for user in banned_users
                ]
                
        except Exception as e:
            logger.error(f"Error getting banned users list: {e}")
            return []
    
    def clear_cache(self):
        """Clear authentication cache"""
        self.admin_cache = set(settings.ADMIN_USER_IDS)
        self.banned_cache = set()
        logger.info("Authentication cache cleared")
