import os
import hashlib
import json
import bencodepy
from datetime import datetime
from typing import Dict, Any, Optional, NamedTuple
from pyrogram.types import User
from config import settings
import logging

logger = logging.getLogger(__name__)


class ValidationResult(NamedTuple):
    is_valid: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TorrentValidator:
    """Validates and extracts metadata from torrent files"""
    
    async def validate_torrent(self, file_path: str) -> ValidationResult:
        """Validate a torrent file and extract metadata"""
        try:
            # Read and decode torrent file
            with open(file_path, 'rb') as f:
                torrent_data = f.read()
            
            # Parse bencode
            try:
                decoded = bencodepy.decode(torrent_data)
            except Exception as e:
                return ValidationResult(False, f"Invalid bencode format: {str(e)}")
            
            # Validate required fields
            if b'info' not in decoded:
                return ValidationResult(False, "Missing 'info' section")
            
            if b'announce' not in decoded:
                return ValidationResult(False, "Missing 'announce' field")
            
            info = decoded[b'info']
            
            # Extract metadata
            metadata = await self._extract_metadata(decoded, info)
            
            # Calculate info hash
            info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()
            metadata['info_hash'] = info_hash
            
            # Calculate file hash
            file_hash = hashlib.sha256(torrent_data).hexdigest()
            metadata['file_hash'] = file_hash
            
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return ValidationResult(True, None, metadata)
            
        except Exception as e:
            logger.error(f"Error validating torrent: {e}")
            # Clean up temporary file
            if os.path.exists(file_path):
                os.remove(file_path)
            return ValidationResult(False, f"Validation error: {str(e)}")
    
    async def _extract_metadata(self, decoded: dict, info: dict) -> Dict[str, Any]:
        """Extract metadata from torrent info"""
        metadata = {}
        
        try:
            # Basic info
            metadata['name'] = info.get(b'name', b'').decode('utf-8', errors='ignore')
            metadata['piece_length'] = info.get(b'piece length', 0)
            
            # Announce URLs
            announce_list = []
            if b'announce' in decoded:
                announce_list.append(decoded[b'announce'].decode('utf-8', errors='ignore'))
            
            if b'announce-list' in decoded:
                for tier in decoded[b'announce-list']:
                    for url in tier:
                        announce_list.append(url.decode('utf-8', errors='ignore'))
            
            metadata['announce_urls'] = announce_list
            
            # Files info
            if b'files' in info:
                # Multi-file torrent
                files = []
                total_size = 0
                for file_info in info[b'files']:
                    file_size = file_info.get(b'length', 0)
                    file_path = '/'.join([p.decode('utf-8', errors='ignore') for p in file_info.get(b'path', [])])
                    files.append({
                        'path': file_path,
                        'size': file_size
                    })
                    total_size += file_size
                
                metadata['files'] = files
                metadata['file_count'] = len(files)
                metadata['total_size'] = total_size
                metadata['is_single_file'] = False
            else:
                # Single file torrent
                file_size = info.get(b'length', 0)
                metadata['files'] = [{
                    'path': metadata['name'],
                    'size': file_size
                }]
                metadata['file_count'] = 1
                metadata['total_size'] = file_size
                metadata['is_single_file'] = True
            
            # Creation date
            if b'creation date' in decoded:
                metadata['creation_date'] = decoded[b'creation date']
            
            # Comment
            if b'comment' in decoded:
                metadata['comment'] = decoded[b'comment'].decode('utf-8', errors='ignore')
            
            # Created by
            if b'created by' in decoded:
                metadata['created_by'] = decoded[b'created by'].decode('utf-8', errors='ignore')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {'error': str(e)}


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def get_user_info(user: User) -> str:
    """Get formatted user information"""
    if user.username:
        return f"@{user.username}"
    elif user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    else:
        return f"User {user.id}"


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.ADMIN_USER_IDS


def is_super_admin(user_id: int) -> bool:
    """Check if user is super admin"""
    return user_id == settings.SUPER_ADMIN_ID


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def validate_user_input(text: str, max_length: int = 1000) -> bool:
    """Validate user input for safety"""
    if not text or len(text) > max_length:
        return False
    
    # Check for potentially dangerous content
    dangerous_patterns = ['<script', 'javascript:', 'data:', 'vbscript:']
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False
    
    return True


def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Create a progress bar string"""
    if total == 0:
        return "█" * length
    
    filled = int(length * current / total)
    bar = "█" * filled + "░" * (length - filled)
    percentage = (current / total) * 100
    
    return f"{bar} {percentage:.1f}%"


async def log_user_action(user_id: int, action: str, details: str = ""):
    """Log user actions for audit purposes"""
    log_entry = {
        'user_id': user_id,
        'action': action,
        'details': details,
        'timestamp': str(datetime.utcnow())
    }
    
    logger.info(f"User action: {json.dumps(log_entry)}")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
