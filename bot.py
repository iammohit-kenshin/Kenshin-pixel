import os
import logging
import asyncio
import aiohttp
import aiofiles
import re
import json
from bs4 import BeautifulSoup
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import time

# ==================== CONFIG ====================
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "YOUR_ADMIN_ID").split(",")]
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Client
app = Client(
    "pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Database
user_data = {}
downloading = set()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def extract_file_id(url):
    """Extract file ID from Pixeldrain URL"""
    patterns = [
        r'pixeldrain\.com/d/([a-zA-Z0-9]+)',
        r'pixeldrain\.com/u/([a-zA-Z0-9]+)',
        r'pixeldrain\.com/l/([a-zA-Z0-9]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def get_direct_link(file_id):
    """Extract direct download link from Pixeldrain page"""
    try:
        # Method 1: Try API first
        api_url = f"https://pixeldrain.com/api/file/{file_id}"
        
        async with aiohttp.ClientSession() as session:
            # Try API
            async with session.head(api_url, allow_redirects=True) as resp:
                if resp.status == 200:
                    return api_url, None
            
            # Method 2: Scrape webpage
            page_url = f"https://pixeldrain.com/d/{file_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with session.get(page_url, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Try to find file info in meta tags
                    title_tag = soup.find('title')
                    if title_tag:
                        title = title_tag.text.strip()
                    else:
                        title = f"pixeldrain_{file_id}"
                    
                    # Try to find download link in page source
                    download_patterns = [
                        r'href="(https?://[^"]*?pixeldrain[^"]*?download[^"]*?)"',
                        r'data-url="(https?://[^"]*?)"',
                        r'url:\s*"([^"]*?)"',
                        r'downloadUrl["\']\s*:\s*["\']([^"\']+)',
                        r'file["\']]\s*:\s*["\']([^"\']+)',
                    ]
                    
                    direct_url = None
                    for pattern in download_patterns:
                        match = re.search(pattern, html)
                        if match:
                            direct_url = match.group(1)
                            if not direct_url.startswith('http'):
                                direct_url = 'https://pixeldrain.com' + direct_url
                            break
                    
                    # If no direct URL found, use API as fallback
                    if not direct_url:
                        direct_url = api_url
                    
                    # Get file size from content-length or meta
                    file_size = 0
                    
                    # Try to get size from meta
                    size_patterns = [
                        r'Size["\']:?\s*["\']([\d.]+)\s*(GB|MB|KB)',
                        r'data-size["\']\s*=\s*["\'](\d+)',
                        r'"size":\s*(\d+)',
                    ]
                    
                    for pattern in size_patterns:
                        size_match = re.search(pattern, html, re.IGNORECASE)
                        if size_match:
                            try:
                                if pattern == size_patterns[0]:  # Human readable
                                    size_val = float(size_match.group(1))
                                    size_unit = size_match.group(2).upper()
                                    if size_unit == 'GB':
                                        file_size = int(size_val * 1024 * 1024 * 1024)
                                    elif size_unit == 'MB':
                                        file_size = int(size_val * 1024 * 1024)
                                    elif size_unit == 'KB':
                                        file_size = int(size_val * 1024)
                                else:
                                    file_size = int(size_match.group(1))
                                break
                            except:
                                pass
                    
                    # Try head request to get content-length
                    try:
                        async with session.head(direct_url, allow_redirects=True) as head_resp:
                            if 'content-length' in head_resp.headers:
                                file_size = int(head_resp.headers['content-length'])
                    except:
                        pass
                    
                    # Determine mime type from title
                    mime = 'video/mp4' if '.mp4' in title.lower() else 'application/octet-stream'
                    
                    return direct_url, {
                        'name': title,
                        'size': file_size,
                        'mime': mime
                    }
    
    except Exception as e:
        logger.error(f"Error getting direct link: {e}")
        return None, None
    
    return None, None

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

async def download_with_progress(url, file_path, status_msg, file_size=0):
    """Download file with progress"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    total = int(resp.headers.get('content-length', file_size)) or 1
                    downloaded = 0
                    start_time = time.time()
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(1024 * 1024):  # 1MB chunks
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 2 seconds
                            if time.time() - start_time > 2:
                                percent = (downloaded / total) * 100
                                speed = downloaded / (time.time() - start_time)
                                eta = (total - downloaded) / speed if speed > 0 else 0
                                
                                progress_text = (
                                    f"📥 **Downloading...**\n\n"
                                    f"**Progress:** {percent:.1f}%\n"
                                    f"**Done:** {human_readable_size(downloaded)} / {human_readable_size(total)}\n"
                                    f"**Speed:** {human_readable_size(speed)}/s\n"
                                    f"**ETA:** {eta:.0f}s"
                                )
                                await status_msg.edit_text(progress_text)
                                start_time = time.time()
                    
                    return True, downloaded
                else:
                    return False, 0
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False, 0

@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    welcome = (
        "**👋 Welcome to Pixeldrain Downloader Bot!**\n\n"
        "I can download any file from Pixeldrain and send it to you.\n\n"
        "**How to use:**\n"
        "• Send me any Pixeldrain link\n"
        "• I'll download and send the file\n"
        "• Up to 2GB files supported\n\n"
        "**Example:**\n"
        "`https://pixeldrain.com/d/ZDSmxd52`"
    )
    await message.reply_text(welcome)
    
    # Store user
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {'joined': datetime.now()}

@app.on_message(filters.command(["stats"]) & filters.user(ADMIN_IDS))
async def stats_command(client, message):
    total_users = len(user_data)
    active_downloads = len(downloading)
    await message.reply_text(
        f"**📊 Bot Statistics**\n\n"
        f"**Total Users:** {total_users}\n"
        f"**Active Downloads:** {active_downloads}"
    )

@app.on_message(filters.text)
async def handle_message(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Check for Pixeldrain link
    if "pixeldrain.com" in text:
        file_id = extract_file_id(text)
        
        if not file_id:
            await message.reply_text("❌ **Invalid Pixeldrain link!**")
            return
        
        # Check if already downloading
        if file_id in downloading:
            await message.reply_text("⏳ **This file is already being downloaded. Please wait...**")
            return
        
        downloading.add(file_id)
        status_msg = await message.reply_text("🔄 **Extracting download link...**")
        
        try:
            # Get direct download link
            direct_url, file_info = await get_direct_link(file_id)
            
            if not direct_url:
                await status_msg.edit_text("❌ **Failed to extract download link!**")
                downloading.discard(file_id)
                return
            
            # Get file info
            file_name = file_info.get('name', f"pixeldrain_{file_id}") if file_info else f"pixeldrain_{file_id}"
            file_size = file_info.get('size', 0) if file_info else 0
            
            # Check size limits
            if file_size > MAX_FILE_SIZE and not is_admin(user_id):
                await status_msg.edit_text(
                    f"❌ **File too large!**\n\n"
                    f"Size: {human_readable_size(file_size)}\n"
                    f"Max: 2GB"
                )
                downloading.discard(file_id)
                return
            
            # Group limit
            if message.chat.type != enums.ChatType.PRIVATE and not is_admin(user_id):
                if file_size > 50 * 1024 * 1024:  # 50MB
                    await status_msg.edit_text(
                        f"❌ **In groups, non-admins can only download files up to 50MB!**\n\n"
                        f"Size: {human_readable_size(file_size)}"
                    )
                    downloading.discard(file_id)
                    return
            
            await status_msg.edit_text(
                f"**📥 Downloading...**\n\n"
                f"**File:** `{file_name}`\n"
                f"**Size:** {human_readable_size(file_size)}"
            )
            
            # Download file
            os.makedirs("downloads", exist_ok=True)
            temp_file = f"downloads/{file_id}_{int(time.time())}.tmp"
            
            success, downloaded_size = await download_with_progress(direct_url, temp_file, status_msg, file_size)
            
            if success and downloaded_size > 0:
                await status_msg.edit_text("✅ **Download complete! Uploading to Telegram...**")
                
                # Upload to Telegram
                try:
                    if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                        await client.send_video(
                            chat_id=message.chat.id,
                            video=temp_file,
                            caption=f"**{file_name}**\n\nDownloaded by @{client.me.username}",
                            supports_streaming=True,
                            duration=0  # Auto-detect
                        )
                    else:
                        await client.send_document(
                            chat_id=message.chat.id,
                            document=temp_file,
                            caption=f"**{file_name}**"
                        )
                    
                    await status_msg.delete()
                    
                except Exception as e:
                    await status_msg.edit_text(f"❌ **Upload failed:** {str(e)}")
                
                # Cleanup
                try:
                    os.remove(temp_file)
                except:
                    pass
            else:
                await status_msg.edit_text("❌ **Download failed! Please try again later.**")
        
        except Exception as e:
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
            logger.error(f"Error: {e}")
        
        finally:
            downloading.discard(file_id)
    
    # Ignore non-Pixeldrain messages
    else:
        if message.chat.type == enums.ChatType.PRIVATE:
            await message.reply_text("Please send a Pixeldrain link only!")

print("🚀 Bot Started!")
print(f"👤 Admins: {ADMIN_IDS}")
app.run()
