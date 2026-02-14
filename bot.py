import os
import logging
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserNotParticipant
from datetime import datetime
import re
import time

# ==================== CONFIG ====================
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))  # Isko replace karo
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")  # Isko replace karo
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")  # Isko replace karo
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "123456789").split(",")]  # Apna ID dalo
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")  # @channelusername
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

# Database (simple dict)
user_data = {}
downloading = set()

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def force_sub_check(user_id):
    if not FORCE_SUB_CHANNEL:
        return True
    try:
        await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return True
    except:
        return False

def extract_pixeldrain_id(url):
    patterns = [
        r'pixeldrain\.com/u/([a-zA-Z0-9]+)',
        r'pixeldrain\.com/d/([a-zA-Z0-9]+)',
        r'pixeldrain\.com/l/([a-zA-Z0-9]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def get_pixeldrain_info(file_id):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://pixeldrain.com/api/file/{file_id}/info") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        'name': data.get('name', 'Unknown'),
                        'size': data.get('size', 0),
                        'mime': data.get('mime_type', 'application/octet-stream'),
                        'download_url': f"https://pixeldrain.com/api/file/{file_id}"
                    }
        except:
            pass
        return {
            'name': f"pixeldrain_{file_id}",
            'size': 0,
            'mime': 'application/octet-stream',
            'download_url': f"https://pixeldrain.com/api/file/{file_id}"
        }

def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    user_id = message.from_user.id
    
    if not await force_sub_check(user_id):
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
        ]])
        await message.reply_text("❌ Please join channel first!", reply_markup=btn)
        return
    
    welcome = "**Welcome to Pixeldrain Downloader Bot!**\n\nSend me any Pixeldrain link, I'll download and send the file."
    await message.reply_text(welcome)
    
    if user_id not in user_data:
        user_data[user_id] = {'joined': datetime.now()}

@app.on_message(filters.command(["stats"]) & filters.user(ADMIN_IDS))
async def stats_command(client, message):
    total = len(user_data)
    await message.reply_text(f"**Stats**\n\nTotal Users: {total}\nActive Downloads: {len(downloading)}")

@app.on_message(filters.text)
async def handle_message(client, message):
    user_id = message.from_user.id
    text = message.text
    
    # Force sub check
    if message.chat.type == enums.ChatType.PRIVATE:
        if not await force_sub_check(user_id):
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
            ]])
            await message.reply_text("❌ Please join channel first!", reply_markup=btn)
            return
    
    # Check for Pixeldrain link
    if "pixeldrain.com" in text:
        file_id = extract_pixeldrain_id(text)
        
        if not file_id:
            await message.reply_text("❌ Invalid link!")
            return
        
        if file_id in downloading:
            await message.reply_text("⏳ Already downloading, please wait...")
            return
        
        downloading.add(file_id)
        status = await message.reply_text("🔄 Getting file info...")
        
        try:
            # Get file info
            info = await get_pixeldrain_info(file_id)
            
            # Check size limits
            if info['size'] > MAX_FILE_SIZE and not is_admin(user_id):
                await status.edit_text(f"❌ File too large! Max 2GB")
                downloading.discard(file_id)
                return
            
            # Group limit for non-admins
            if message.chat.type != enums.ChatType.PRIVATE and not is_admin(user_id):
                if info['size'] > 50 * 1024 * 1024:  # 50MB
                    await status.edit_text("❌ In groups, max 50MB for non-admins. Use private chat.")
                    downloading.discard(file_id)
                    return
            
            # Download file
            await status.edit_text(f"📥 Downloading: {info['name']}")
            
            # Create downloads folder
            os.makedirs("downloads", exist_ok=True)
            temp_file = f"downloads/{file_id}.tmp"
            
            # Download with progress
            async with aiohttp.ClientSession() as session:
                async with session.get(info['download_url']) as resp:
                    if resp.status == 200:
                        downloaded = 0
                        total = info['size'] or 1
                        
                        async with aiofiles.open(temp_file, 'wb') as f:
                            async for chunk in resp.content.iter_chunked(1024 * 1024):
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress
                                if downloaded % (10 * 1024 * 1024) == 0:  # Every 10MB
                                    percent = (downloaded / total) * 100
                                    await status.edit_text(f"📥 Downloading: {percent:.1f}%")
                        
                        # Upload to Telegram
                        await status.edit_text("📤 Uploading to Telegram...")
                        
                        if info['mime'].startswith('video/'):
                            await client.send_video(
                                message.chat.id,
                                video=temp_file,
                                caption=f"**{info['name']}**"
                            )
                        else:
                            await client.send_document(
                                message.chat.id,
                                document=temp_file,
                                caption=f"**{info['name']}**"
                            )
                        
                        await status.delete()
                        os.remove(temp_file)
                    else:
                        await status.edit_text("❌ Download failed")
        
        except Exception as e:
            await status.edit_text(f"❌ Error: {str(e)}")
            logger.error(f"Error: {e}")
        
        finally:
            downloading.discard(file_id)

print("Bot Started!")
app.run()
