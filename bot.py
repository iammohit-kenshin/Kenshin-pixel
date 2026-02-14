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
import sys

# ==================== CONFIG ====================
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "0").split(",")]
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Check if config is set
if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Error: API_ID, API_HASH, and BOT_TOKEN must be set!")
    sys.exit(1)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot Client
app = Client(
    "pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=20
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
    """Extract direct download link from Pixeldrain"""
    try:
        # Try multiple methods
        methods = [
            f"https://pixeldrain.com/api/file/{file_id}",  # API
            f"https://pixeldrain.com/d/{file_id}"  # Webpage
        ]
        
        async with aiohttp.ClientSession() as session:
            # Method 1: Try API
            try:
                async with session.head(methods[0], allow_redirects=True) as resp:
                    if resp.status == 200:
                        # Get file info from API
                        async with session.get(f"https://pixeldrain.com/api/file/{file_id}/info") as info_resp:
                            if info_resp.status == 200:
                                info = await info_resp.json()
                                return methods[0], {
                                    'name': info.get('name', f'pixeldrain_{file_id}'),
                                    'size': info.get('size', 0),
                                    'mime': info.get('mime_type', 'application/octet-stream')
                                }
            except:
                pass
            
            # Method 2: Scrape webpage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with session.get(methods[1], headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    
                    # Try to find download URL in the page
                    patterns = [
                        r'<a[^>]*href="([^"]*pixeldrain[^"]*download[^"]*)"',
                        r'downloadUrl["\']\s*:\s*["\']([^"\']+)',
                        r'window\.location\s*=\s*["\']([^"\']+)',
                        r'<meta[^>]*url=([^"\s]+)',
                    ]
                    
                    download_url = None
                    for pattern in patterns:
                        match = re.search(pattern, html, re.IGNORECASE)
                        if match:
                            download_url = match.group(1)
                            if not download_url.startswith('http'):
                                download_url = 'https://pixeldrain.com' + download_url
                            break
                    
                    if not download_url:
                        download_url = f"https://pixeldrain.com/api/file/{file_id}"
                    
                    # Extract filename from title
                    title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                    filename = title_match.group(1) if title_match else f"pixeldrain_{file_id}.mp4"
                    
                    # Clean filename
                    filename = re.sub(r'[^\w\-_\. ]', '', filename)
                    
                    return download_url, {
                        'name': filename,
                        'size': 0,  # Size will be detected during download
                        'mime': 'video/mp4' if '.mp4' in filename.lower() else 'application/octet-stream'
                    }
    
    except Exception as e:
        logger.error(f"Error getting direct link: {e}")
        return None, None
    
    # Fallback to direct API
    return f"https://pixeldrain.com/api/file/{file_id}", {
        'name': f"pixeldrain_{file_id}.mp4",
        'size': 0,
        'mime': 'video/mp4'
    }

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

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
        "`https://pixeldrain.com/d/ZDSmxd52`\n\n"
        "**Supported links:**\n"
        "• pixeldrain.com/d/ID\n"
        "• pixeldrain.com/u/ID\n"
        "• pixeldrain.com/l/ID"
    )
    await message.reply_text(welcome)
    
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

@app.on_message(filters.command(["users"]) & filters.user(ADMIN_IDS))
async def users_command(client, message):
    if not user_data:
        await message.reply_text("No users found.")
        return
    
    users_list = "**📋 Users List:**\n\n"
    for uid, data in list(user_data.items())[:50]:
        joined = data.get('joined', datetime.now()).strftime("%Y-%m-%d")
        users_list += f"• `{uid}` - {joined}\n"
    
    users_list += f"\n**Total: {len(user_data)} users**"
    await message.reply_text(users_list)

@app.on_message(filters.text)
async def handle_message(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Store user
    if user_id not in user_data:
        user_data[user_id] = {'joined': datetime.now()}
    
    # Check for Pixeldrain link
    if "pixeldrain.com" in text:
        file_id = extract_file_id(text)
        
        if not file_id:
            await message.reply_text("❌ **Invalid Pixeldrain link!**")
            return
        
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
            
            file_name = file_info.get('name', f"pixeldrain_{file_id}.mp4")
            
            await status_msg.edit_text(f"📥 **Downloading:** `{file_name}`")
            
            # Download file
            os.makedirs("downloads", exist_ok=True)
            temp_file = f"downloads/{file_id}_{int(time.time())}.mp4"
            
            # Download with progress
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url, allow_redirects=True) as resp:
                    if resp.status == 200:
                        total = int(resp.headers.get('content-length', 0))
                        downloaded = 0
                        start_time = time.time()
                        
                        async with aiofiles.open(temp_file, 'wb') as f:
                            async for chunk in resp.content.iter_chunked(1024 * 1024):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress
                                if total > 0 and time.time() - start_time > 2:
                                    percent = (downloaded / total) * 100
                                    await status_msg.edit_text(f"📥 **Downloading:** {percent:.1f}%")
                                    start_time = time.time()
                        
                        # Check if download was successful
                        if downloaded > 0:
                            await status_msg.edit_text("✅ **Download complete! Uploading to Telegram...**")
                            
                            # Upload to Telegram
                            try:
                                # Check file size limit
                                if downloaded > MAX_FILE_SIZE and not is_admin(user_id):
                                    await status_msg.edit_text("❌ **File too large! Max 2GB**")
                                    os.remove(temp_file)
                                    downloading.discard(file_id)
                                    return
                                
                                # Send based on file type
                                if file_name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm')):
                                    await client.send_video(
                                        chat_id=message.chat.id,
                                        video=temp_file,
                                        caption=f"**{file_name}**\n\nDownloaded by @{client.me.username}",
                                        supports_streaming=True
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
                            await status_msg.edit_text("❌ **Download failed!**")
                    else:
                        await status_msg.edit_text(f"❌ **Download failed! Status code: {resp.status}**")
        
        except Exception as e:
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
            logger.error(f"Error: {e}")
        
        finally:
            downloading.discard(file_id)
    
    elif message.chat.type == enums.ChatType.PRIVATE:
        await message.reply_text("Please send a valid Pixeldrain link!")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Pixeldrain Downloader Bot Starting...")
    print(f"👤 Admin IDs: {ADMIN_IDS}")
    print(f"📊 Max File Size: 2GB")
    print("=" * 50)
    app.run()
