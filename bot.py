import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

# ===== ENV VARIABLES =====
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ===== START BOT =====
app = Client(
    "video_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ===== START COMMAND =====
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Send me any video link and I will download & upload it."
    )

# ===== VIDEO HANDLER =====
@app.on_message(filters.private & filters.regex(r'https?://'))
async def download_video(client, message: Message):
    url = message.text.strip()

    status_msg = await message.reply_text("📥 Downloading video...")

    ydl_opts = {
        "format": "best",
        "outtmpl": "video.%(ext)s",
        "noplaylist": True,
        "quiet": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        await status_msg.edit("📤 Uploading to Telegram...")

        await client.send_video(
            chat_id=message.chat.id,
            video=file_name,
            caption=f"✅ {info.get('title', 'Video')}"
        )

        await status_msg.delete()

        # Auto delete file after upload
        os.remove(file_name)

    except Exception as e:
        await status_msg.edit(f"❌ Error:\n{str(e)}")

# ===== RUN =====
print("Bot is running...")
app.run()
