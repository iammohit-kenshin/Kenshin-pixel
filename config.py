import os
from typing import Optional

class Config:
    """Bot configuration"""
    
    # Telegram Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    API_ID: Optional[int] = int(os.getenv('API_ID', '0')) if os.getenv('API_ID') else None
    API_HASH: str = os.getenv('API_HASH', '')
    
    # Admin Configuration
    ADMIN_ID: int = int(os.getenv('ADMIN_ID', '0'))
    
    # Cache Configuration
    CACHE_CHANNEL_ID: int = int(os.getenv('CACHE_CHANNEL_ID', '0'))
    CACHE_EXPIRY_HOURS: int = int(os.getenv('CACHE_EXPIRY_HOURS', '24'))
    
    # Download Configuration
    DOWNLOAD_DIR: str = os.getenv('DOWNLOAD_DIR', '/tmp/downloads')
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', str(2000 * 1024 * 1024)))  # 2GB default
    CLEANUP_INTERVAL: int = int(os.getenv('CLEANUP_INTERVAL', '300'))  # 5 minutes
    FILE_AGE_LIMIT: int = int(os.getenv('FILE_AGE_LIMIT', '600'))  # 10 minutes
    
    # Feature Flags
    ENABLE_CACHE: bool = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    ENABLE_THUMBNAILS: bool = os.getenv('ENABLE_THUMBNAILS', 'true').lower() == 'true'
    ENABLE_STATS: bool = os.getenv('ENABLE_STATS', 'true').lower() == 'true'
    
    # Download Options
    PREFER_QUALITY: str = os.getenv('PREFER_QUALITY', 'best')  # best, 1080p, 720p, 480p
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            print("Error: BOT_TOKEN is required")
            return False
        
        if cls.ADMIN_ID == 0:
            print("Warning: ADMIN_ID not set. Admin features will be disabled.")
        
        if cls.CACHE_CHANNEL_ID == 0:
            print("Warning: CACHE_CHANNEL_ID not set. Caching will be limited.")
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration (excluding sensitive data)"""
        print("\n" + "="*50)
        print("Bot Configuration")
        print("="*50)
        print(f"Admin ID: {cls.ADMIN_ID if cls.ADMIN_ID else 'Not Set'}")
        print(f"Cache Channel: {cls.CACHE_CHANNEL_ID if cls.CACHE_CHANNEL_ID else 'Not Set'}")
        print(f"Max File Size: {cls.MAX_FILE_SIZE / (1024*1024):.0f} MB")
        print(f"Cache Enabled: {cls.ENABLE_CACHE}")
        print(f"Thumbnails Enabled: {cls.ENABLE_THUMBNAILS}")
        print(f"Preferred Quality: {cls.PREFER_QUALITY}")
        print("="*50 + "\n")


# Validate config on import
if not Config.validate():
    raise ValueError("Invalid configuration. Please check your environment variables.")
