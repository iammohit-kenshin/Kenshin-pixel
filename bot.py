import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError
import yt_dlp
import aiohttp
import aiofiles

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
CACHE_CHANNEL_ID = int(os.getenv('CACHE_CHANNEL_ID', '0'))  # Telegram channel/group for caching
DOWNLOAD_DIR = '/tmp/downloads'
MAX_FILE_SIZE = 2000 * 1024 * 1024  # 2GB max

# Create download directory
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory cache for video file_ids
video_cache: Dict[str, dict] = {}

# Statistics
stats = {
    'total_downloads': 0,
    'cached_sends': 0,
    'failed_downloads': 0,
    'total_users': set()
}


def get_video_hash(url: str) -> str:
    """Generate hash for URL to use as cache key"""
    return hashlib.md5(url.encode()).hexdigest()


class DownloadProgress:
    """Track download progress"""
    def __init__(self, message, total_size=0):
        self.message = message
        self.total_size = total_size
        self.downloaded = 0
        self.last_update = 0
        self.start_time = time.time()
        
    def update(self, downloaded):
        self.downloaded = downloaded
        current_time = time.time()
        
        # Update every 2 seconds
        if current_time - self.last_update > 2:
            self.last_update = current_time
            asyncio.create_task(self._update_message())
    
    async def _update_message(self):
        try:
            if self.total_size > 0:
                percentage = (self.downloaded / self.total_size) * 100
                speed = self.downloaded / (time.time() - self.start_time)
                speed_mb = speed / (1024 * 1024)
                
                progress_bar = self._create_progress_bar(percentage)
                text = (
                    f"📥 **Downloading...**\n\n"
                    f"{progress_bar}\n"
                    f"Progress: {percentage:.1f}%\n"
                    f"Downloaded: {self.downloaded / (1024*1024):.2f} MB / {self.total_size / (1024*1024):.2f} MB\n"
                    f"Speed: {speed_mb:.2f} MB/s"
                )
            else:
                text = f"📥 **Downloading...**\n\nDownloaded: {self.downloaded / (1024*1024):.2f} MB"
            
            await self.message.edit_text(text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error updating progress: {e}")
    
    def _create_progress_bar(self, percentage):
        filled = int(percentage / 5)
        bar = "█" * filled + "░" * (20 - filled)
        return f"[{bar}]"


async def download_with_ytdlp(url: str, progress_message) -> Optional[str]:
    """Download video using yt-dlp"""
    try:
        output_path = os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s')
        
        progress_tracker = DownloadProgress(progress_message)
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                
                if progress_tracker.total_size == 0 and total > 0:
                    progress_tracker.total_size = total
                
                progress_tracker.update(downloaded)
        
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': output_path,
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'cookiesfrombrowser': None,
            'nocheckcertificate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Get thumbnail
            thumbnail_url = info.get('thumbnail')
            thumb_path = None
            
            if thumbnail_url:
                thumb_path = os.path.join(DOWNLOAD_DIR, 'thumb.jpg')
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(thumbnail_url) as resp:
                            if resp.status == 200:
                                async with aiofiles.open(thumb_path, 'wb') as f:
                                    await f.write(await resp.read())
                except Exception as e:
                    logger.error(f"Error downloading thumbnail: {e}")
                    thumb_path = None
            
            return filename, thumb_path
    
    except Exception as e:
        logger.error(f"yt-dlp download error: {e}")
        return None, None


async def download_direct_link(url: str, progress_message) -> Optional[str]:
    """Download video from direct link"""
    try:
        progress_tracker = DownloadProgress(progress_message)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None, None
                
                total_size = int(response.headers.get('content-length', 0))
                progress_tracker.total_size = total_size
                
                # Generate filename
                filename = os.path.join(DOWNLOAD_DIR, f"video_{int(time.time())}.mp4")
                
                downloaded = 0
                async with aiofiles.open(filename, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                        await f.write(chunk)
                        downloaded += len(chunk)
                        progress_tracker.update(downloaded)
                
                return filename, None
    
    except Exception as e:
        logger.error(f"Direct download error: {e}")
        return None, None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    stats['total_users'].add(user.id)
    
    welcome_text = (
        f"👋 Welcome {user.first_name}!\n\n"
        "🎥 **Video Downloader Bot**\n\n"
        "Send me any video URL and I'll download it for you!\n\n"
        "✅ Supported:\n"
        "• Direct video links (.mp4, .mkv, etc.)\n"
        "• Video hosting sites\n"
        "• Social media videos\n"
        "• And many more!\n\n"
        "Just send me a link and I'll handle the rest! 🚀"
    )
    
    keyboard = []
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 Admin Panel", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video URL messages"""
    url = update.message.text.strip()
    user = update.effective_user
    
    # Check if URL is valid
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return
    
    # Generate cache key
    cache_key = get_video_hash(url)
    
    # Check cache
    if cache_key in video_cache:
        cached_data = video_cache[cache_key]
        try:
            status_msg = await update.message.reply_text("♻️ Found in cache! Sending video...")
            
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=cached_data['file_id'],
                caption=cached_data.get('caption', ''),
                supports_streaming=True
            )
            
            await status_msg.delete()
            stats['cached_sends'] += 1
            logger.info(f"Sent cached video to {user.id}")
            return
        except Exception as e:
            logger.error(f"Error sending cached video: {e}")
            # If cached send fails, continue to download
            del video_cache[cache_key]
    
    # Download video
    status_msg = await update.message.reply_text("🔄 Processing your request...")
    
    try:
        # Try yt-dlp first (supports many sites)
        await status_msg.edit_text("📥 Starting download...")
        
        video_path, thumb_path = await download_with_ytdlp(url, status_msg)
        
        # If yt-dlp fails, try direct download
        if not video_path:
            await status_msg.edit_text("📥 Trying alternative download method...")
            video_path, thumb_path = await download_direct_link(url, status_msg)
        
        if not video_path or not os.path.exists(video_path):
            await status_msg.edit_text(
                "❌ Failed to download video.\n\n"
                "This could be because:\n"
                "• The URL is invalid or expired\n"
                "• The site is not supported\n"
                "• The video is private or requires login\n"
                "• Network issues"
            )
            stats['failed_downloads'] += 1
            return
        
        file_size = os.path.getsize(video_path)
        
        if file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(
                f"❌ Video is too large ({file_size / (1024*1024):.2f} MB).\n"
                f"Maximum size: {MAX_FILE_SIZE / (1024*1024):.2f} MB"
            )
            os.remove(video_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
            return
        
        # Upload to Telegram
        await status_msg.edit_text("📤 Uploading to Telegram...")
        
        # First upload to cache channel
        cache_msg = None
        if CACHE_CHANNEL_ID != 0:
            try:
                with open(video_path, 'rb') as video_file:
                    cache_msg = await context.bot.send_video(
                        chat_id=CACHE_CHANNEL_ID,
                        video=video_file,
                        caption=f"Cache: {url[:100]}",
                        supports_streaming=True,
                        thumb=open(thumb_path, 'rb') if thumb_path and os.path.exists(thumb_path) else None
                    )
            except Exception as e:
                logger.error(f"Error uploading to cache channel: {e}")
        
        # Send to user
        with open(video_path, 'rb') as video_file:
            sent_message = await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=video_file,
                caption=f"✅ Downloaded successfully!\n\nSize: {file_size / (1024*1024):.2f} MB",
                supports_streaming=True,
                thumb=open(thumb_path, 'rb') if thumb_path and os.path.exists(thumb_path) else None
            )
        
        # Cache the file_id
        if cache_msg:
            video_cache[cache_key] = {
                'file_id': cache_msg.video.file_id,
                'caption': f"✅ Downloaded successfully!\n\nSize: {file_size / (1024*1024):.2f} MB",
                'timestamp': datetime.now()
            }
        
        await status_msg.delete()
        
        # Delete local files
        os.remove(video_path)
        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)
        
        stats['total_downloads'] += 1
        logger.info(f"Successfully processed video for {user.id}")
        
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await status_msg.edit_text(
            "❌ An error occurred while processing your video.\n"
            "Please try again or contact the admin."
        )
        stats['failed_downloads'] += 1


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ You are not authorized to access the admin panel.")
        return
    
    stats_text = (
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {len(stats['total_users'])}\n"
        f"📥 Total Downloads: {stats['total_downloads']}\n"
        f"♻️ Cached Sends: {stats['cached_sends']}\n"
        f"❌ Failed Downloads: {stats['failed_downloads']}\n"
        f"💾 Cache Size: {len(video_cache)}\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("🗑️ Clear Cache", callback_data="clear_cache")],
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_panel")],
        [InlineKeyboardButton("◀️ Back", callback_data="back_to_start")]
    ]
    
    await query.edit_message_text(
        stats_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear video cache"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ You are not authorized.")
        return
    
    cache_size = len(video_cache)
    video_cache.clear()
    
    await query.edit_message_text(
        f"✅ Cache cleared!\n\nRemoved {cache_size} cached videos.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Back to Admin", callback_data="admin_panel")]
        ])
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ This command is only available to admins.")
        return
    
    stats_text = (
        "📊 **Bot Statistics**\n\n"
        f"👥 Total Users: {len(stats['total_users'])}\n"
        f"📥 Total Downloads: {stats['total_downloads']}\n"
        f"♻️ Cached Sends: {stats['cached_sends']}\n"
        f"❌ Failed Downloads: {stats['failed_downloads']}\n"
        f"💾 Cache Size: {len(video_cache)}\n"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')


async def cleanup_old_files():
    """Periodically clean up old files from download directory"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            current_time = time.time()
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                # Delete files older than 10 minutes
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > 600:  # 10 minutes
                        try:
                            os.remove(filepath)
                            logger.info(f"Deleted old file: {filename}")
                        except Exception as e:
                            logger.error(f"Error deleting file {filename}: {e}")
            
            # Clean old cache entries (older than 24 hours)
            old_entries = []
            for key, data in video_cache.items():
                if datetime.now() - data['timestamp'] > timedelta(hours=24):
                    old_entries.append(key)
            
            for key in old_entries:
                del video_cache[key]
            
            if old_entries:
                logger.info(f"Removed {len(old_entries)} old cache entries")
                
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")


async def post_init(application: Application):
    """Start background tasks after bot initialization"""
    # Start cleanup task in background
    asyncio.create_task(cleanup_old_files())


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    application.add_handler(CallbackQueryHandler(clear_cache, pattern="^clear_cache$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
