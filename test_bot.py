#!/usr/bin/env python3
"""
Simple test script for MedusaXD Torrent Downloader Bot by @medusaXD
Run this to verify basic functionality before deployment
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from database import db_manager
from utils import TorrentValidator, format_file_size
from auth import AuthManager
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_configuration():
    """Test configuration loading"""
    print("🔧 Testing Configuration...")
    
    try:
        assert settings.API_ID, "API_ID not set"
        assert settings.API_HASH, "API_HASH not set"
        assert settings.BOT_TOKEN, "BOT_TOKEN not set"
        assert settings.ADMIN_USER_IDS, "No admin users configured"
        assert settings.SUPER_ADMIN_ID, "SUPER_ADMIN_ID not set"
        
        print("✅ Configuration is valid")
        print(f"   - Bot Name: {settings.BOT_NAME}")
        print(f"   - Max File Size: {settings.MAX_FILE_SIZE}MB")
        print(f"   - Admin Users: {len(settings.ADMIN_USER_IDS)}")
        print(f"   - Database: {settings.DATABASE_URL.split('://')[0]}")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def test_database():
    """Test database connection and operations"""
    print("\n💾 Testing Database...")
    
    try:
        # Initialize database
        await db_manager.init_db()
        print("✅ Database connection successful")
        
        # Test session
        async with db_manager.get_session() as session:
            print("✅ Database session created")
        
        print("✅ Database tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False


async def test_auth_manager():
    """Test authentication manager"""
    print("\n🔐 Testing Authentication...")
    
    try:
        auth_manager = AuthManager()
        
        # Test admin check
        is_admin = await auth_manager.is_admin(settings.SUPER_ADMIN_ID)
        print(f"✅ Super admin check: {is_admin}")
        
        # Test super admin check
        is_super = await auth_manager.is_super_admin(settings.SUPER_ADMIN_ID)
        print(f"✅ Super admin verification: {is_super}")
        
        # Test user permission check
        is_allowed = await auth_manager.is_user_allowed(settings.SUPER_ADMIN_ID)
        print(f"✅ User permission check: {is_allowed}")
        
        print("✅ Authentication tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False


async def test_torrent_validator():
    """Test torrent validation (without actual file)"""
    print("\n🔍 Testing Torrent Validator...")
    
    try:
        validator = TorrentValidator()
        print("✅ Torrent validator created")
        
        # Test utility functions
        size_str = format_file_size(1024 * 1024 * 50)  # 50MB
        print(f"✅ File size formatting: {size_str}")
        
        print("✅ Torrent validator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Torrent validator test failed: {e}")
        return False


async def test_imports():
    """Test all imports"""
    print("\n📦 Testing Imports...")
    
    try:
        # Test core imports
        from bot import TorrentBot
        print("✅ Bot import successful")
        
        from logging_config import setup_logging
        print("✅ Logging config import successful")
        
        # Test external dependencies
        import pyrogram
        print(f"✅ Pyrogram version: {pyrogram.__version__}")
        
        import sqlalchemy
        print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
        
        import bencodepy
        print("✅ Bencodepy import successful")
        
        print("✅ All imports successful")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Bot Tests")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Imports", test_imports),
        ("Database", test_database),
        ("Authentication", test_auth_manager),
        ("Torrent Validator", test_torrent_validator),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please fix issues before deployment.")
        return False


async def main():
    """Main test function"""
    try:
        success = await run_all_tests()
        
        if success:
            print("\n🚀 Ready to deploy!")
            print("Next steps:")
            print("1. Push code to your repository")
            print("2. Deploy to Render.com")
            print("3. Set environment variables")
            print("4. Start the bot!")
        else:
            print("\n🔧 Please fix the issues above before deployment.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            await db_manager.close()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
