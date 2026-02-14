import os
import logging
import asyncio
import aiohttp
import aiofiles
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait, UserNotParticipant
from datetime import datetime
import re
import time

# ==================== CONFIG ====================
API_ID = int(os.environ.get("API_ID", "YOUR_API_ID"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.environ.get("ADMIN_IDS", "123456789,987654321").split(",")]
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")  # @channelusername without @
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB (Telegram limit)

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
    bot_token=BOT_TOKEN
)

# ==================== DATABASE (Simple dict) ====================
# In production, use MongoDB or SQLite
user_data = {}
downloading = set()

# ==================== HELPERS ====================

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def force_sub_check(user_id: int) -> bool:
    """Check if user is subscribed to force sub channel"""
    if not FORCE_SUB_CHANNEL:
        return True
    
    try:
        user = await app.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if user.status in [enums.ChatMemberStatus.BANNED]:
            return False
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.error(f"Force sub error: {e}")
        return True
    
    return True

async def get_force_sub_button():
    """Get force subscribe button"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")
    ]])

def extract_pixeldrain_id(url: str) -> str:
    """Extract file ID from Pixeldrain URL"""
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

async def get_pixeldrain_info(file_id: str):
    """Get file info from Pixeldrain API"""
    async with aiohttp.ClientSession() as session:
        # Try info endpoint first
        info_url = f"https://pixeldrain.com/api/file/{file_id}/info"
        
        try:
            async with session.get(info_url) as resp:
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
        
        # Fallback to direct download
        return {
            'name': f"pixeldrain_{file_id}",
            'size': 0,
            'mime': 'application/octet-stream',
            'download_url': f"https://pixeldrain.com/api/file/{file_id}"
        }

def human_readable_size(size: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

async def download_progress(current, total, message: Message, start_time):
    """Download progress callback"""
    try:
        percent = current * 100 / total
        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        
        progress_text = (
            f"📥 **Downloading...**\n\n"
            f"**Progress:** {percent:.1f}%\n"
            f"**Done:** {human_readable_size(current)} / {human_readable_size(total)}\n"
            f"**Speed:** {human_readable_size(speed)}/s\n"
            f"**ETA:** {eta:.0f}s"
        )
        
        await message.edit_text(progress_text)
    except:
        pass

# ==================== COMMANDS ====================

@app.on_message(filters.command(["start"]))
async def start_command(client: Client, message: Message):
    """Start command handler"""
    user_id = message.from_user.id
    
    # Force sub check
    if not await force_sub_check(user_id):
        btn = await get_force_sub_button()
        await message.reply_text(
            "❌ **Please join our channel first to use this bot!**",
            reply_markup=btn
        )
        return
    
    welcome_text = (
        "**👋 Welcome to Pixeldrain Downloader Bot!**\n\n"
        "I can download any video/file from Pixeldrain and send it to you.\n\n"
        "**How to use:**\n"
        "1. Send me any Pixeldrain link\n"
        "2. I'll download and send the file\n"
        "3. Up to 2GB files supported\n\n"
        "**Supported links:**\n"
        "• pixeldrain.com/u/ID\n"
        "• pixeldrain.com/d/ID\n"
        "• pixeldrain.com/l/ID\n\n"
        "**Admin Features:**\n"
        "• /broadcast - Send message to all users\n"
        "• /stats - Bot statistics\n"
        "• /users - Total users count"
    )
    
    # Store user
    if user_id not in user_data:
        user_data[user_id] = {
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
            'joined': datetime.now()
        }
    
    await message.reply_text(welcome_text)

@app.on_message(filters.command(["stats"]) & filters.user(ADMIN_IDS))
async def stats_command(client: Client, message: Message):
    """Stats command for admin"""
    total_users = len(user_data)
    currently_downloading = len(downloading)
    
    stats_text = (
        f"**📊 Bot Statistics**\n\n"
        f"**Total Users:** {total_users}\n"
        f"**Active Downloads:** {currently_downloading}\n"
        f"**Admins:** {len(ADMIN_IDS)}\n"
        f"**File Limit:** 2GB\n"
        f"**Force Sub:** {'✅ Yes' if FORCE_SUB_CHANNEL else '❌ No'}"
    )
    
    await message.reply_text(stats_text)

@app.on_message(filters.command(["users"]) & filters.user(ADMIN_IDS))
async def users_command(client: Client, message: Message):
    """List all users"""
    if not user_data:
        await message.reply_text("No users found.")
        return
    
    users_list = "**📋 Users List:**\n\n"
    for uid, data in list(user_data.items())[:50]:  # Show first 50
        name = data.get('first_name', 'Unknown')
        username = data.get('username', 'None')
        joined = data.get('joined', datetime.now()).strftime("%Y-%m-%d")
        users_list += f"• {name} (@{username}) - {joined}\n"
    
    users_list += f"\n**Total: {len(user_data)} users**"
    
    await message.reply_text(users_list)

@app.on_message(filters.command(["broadcast"]) & filters.user(ADMIN_IDS))
async def broadcast_command(client: Client, message: Message):
    """Broadcast message to all users"""
    if len(message.command) < 2:
        await message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_text = message.text.split(" ", 1)[1]
    success = 0
    failed = 0
    
    status_msg = await message.reply_text("🔄 Broadcasting...")
    
    for user_id in user_data:
        try:
            await client.send_message(user_id, broadcast_text)
            success += 1
            await asyncio.sleep(0.3)  # Avoid flood
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"**📢 Broadcast Complete**\n\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed: {failed}\n"
        f"Total: {len(user_data)}"
    )

# ==================== MAIN DOWNLOAD HANDLER ====================

@app.on_message(filters.text & filters.private | filters.text & filters.group)
async def handle_message(client: Client, message: Message):
    """Handle Pixeldrain links"""
    user_id = message.from_user.id
    text = message.text
    
    # Force sub check for private only
    if message.chat.type == enums.ChatType.PRIVATE:
        if not await force_sub_check(user_id):
            btn = await get_force_sub_button()
            await message.reply_text(
                "❌ **Please join our channel first to use this bot!**",
                reply_markup=btn
            )
            return
    
    # Check for Pixeldrain link
    if "pixeldrain.com" in text:
        file_id = extract_pixeldrain_id(text)
        
        if not file_id:
            await message.reply_text("❌ **Invalid Pixeldrain link!**")
            return
        
        # Check if already downloading
        if file_id in downloading:
            await message.reply_text("⏳ **This file is already being downloaded. Please wait...**")
            return
        
        # Start download
        downloading.add(file_id)
        status_msg = await message.reply_text("🔄 **Getting file information...**")
        
        try:
            # Get file info
            file_info = await get_pixeldrain_info(file_id)
            file_size = file_info['size']
            
            # Check file size
            if file_size > MAX_FILE_SIZE and not is_admin(user_id):
                await status_msg.edit_text(
                    f"❌ **File too large!**\n\n"
                    f"File size: {human_readable_size(file_size)}\n"
                    f"Max allowed: 2GB\n\n"
                    f"**Note:** Admins can download larger files."
                )
                downloading.discard(file_id)
                return
            
            # Check if group and file is too large for non-admin
            if message.chat.type != enums.ChatType.PRIVATE and not is_admin(user_id):
                if file_size > 50 * 1024 * 1024:  # 50MB
                    await status_msg.edit_text(
                        f"❌ **In groups, non-admins can only download files up to 50MB!**\n\n"
                        f"File size: {human_readable_size(file_size)}\n"
                        f"Please use bot in private for larger files."
                    )
                    downloading.discard(file_id)
                    return
            
            # Download file
            await status_msg.edit_text(
                f"**📥 Starting download...**\n\n"
                f"**File:** `{file_info['name']}`\n"
                f"**Size:** {human_readable_size(file_size)}"
            )
            
            # Download with progress
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get(file_info['download_url']) as resp:
                    if resp.status == 200:
                        # Generate temp filename
                        temp_file = f"downloads/{file_id}_{int(time.time())}.tmp"
                        os.makedirs("downloads", exist_ok=True)
                        
                        downloaded = 0
                        async with aiofiles.open(temp_file, 'wb') as f:
                            async for chunk in resp.content.iter_chunked(1024 * 1024):  # 1MB chunks
                                await f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress every 2 seconds
                                if time.time() - start_time > 2:
                                    await download_progress(downloaded, file_size, status_msg, start_time)
                                    start_time = time.time()
                        
                        # Download complete
                        await status_msg.edit_text("✅ **Download complete! Now uploading to Telegram...**")
                        
                        # Upload to Telegram
                        upload_start = time.time()
                        
                        try:
                            if file_info['mime'].startswith('video/'):
                                await client.send_video(
                                    chat_id=message.chat.id,
                                    video=temp_file,
                                    caption=f"**{file_info['name']}**\n\nDownloaded by @{client.me.username}",
                                    supports_streaming=True,
                                    progress=download_progress,
                                    progress_args=(status_msg, upload_start)
                                )
                            else:
                                await client.send_document(
                                    chat_id=message.chat.id,
                                    document=temp_file,
                                    caption=f"**{file_info['name']}**",
                                    progress=download_progress,
                                    progress_args=(status_msg, upload_start)
                                )
                            
                            await status_msg.delete()
                            
                        except Exception as e:
                            await status_msg.edit_text(f"❌ **Upload failed:** {str(e)}")
                        
                        # Cleanup
                        os.remove(temp_file)
                    else:
                        await status_msg.edit_text("❌ **Failed to download file from Pixeldrain**")
        
        except Exception as e:
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
            logger.error(f"Download error: {e}")
        
        finally:
            downloading.discard(file_id)
    
    # Ignore non-Pixeldrain messages in groups
    elif message.chat.type != enums.ChatType.PRIVATE:
        pass

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🚀 Pixeldrain Downloader Bot Started!")
    print(f"👥 Admins: {ADMIN_IDS}")
    print(f"📢 Force Sub: {FORCE_SUB_CHANNEL if FORCE_SUB_CHANNEL else 'Disabled'}")
    app.run()
