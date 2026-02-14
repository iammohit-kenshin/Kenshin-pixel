import re
import os
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# Load Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# Create Pyrogram Client
app = Client(
    "premium_pixeldrain_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Extract Pixeldrain File ID
def extract_file_id(url):
    match = re.search(r"pixeldrain\.com/d/([a-zA-Z0-9]+)", url)
    if match:
        return match.group(1)
    return None

# Download with Progress
async def download_file(url, file_name, status_message):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            total = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(file_name, "wb") as f:
                async for chunk in response.content.iter_chunked(1024 * 512):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total:
                        percent = int(downloaded * 100 / total)
                        try:
                            await status_message.edit_text(
                                f"⬇ Downloading...\n📦 {percent}%"
                            )
                        except:
                            pass

    return file_name

# Handle Messages
@app.on_message(filters.text & (filters.private | filters.group))
async def handle_pixeldrain(client: Client, message: Message):

    if not message.text:
        return

    if "pixeldrain.com" not in message.text:
        return

    file_id = extract_file_id(message.text)

    if not file_id:
        await message.reply("❌ Invalid Pixeldrain Link.")
        return

    status = await message.reply("🔍 Processing Link...")

    download_url = f"https://pixeldrain.com/api/file/{file_id}"
    file_name = f"{file_id}.mp4"

    try:
        # Download
        file_path = await download_file(download_url, file_name, status)

        file_size = os.path.getsize(file_path)

        # Normal user limit 50MB
        if message.from_user.id != ADMIN_ID and file_size > 50 * 1024 * 1024:
            await status.edit("⚠ File exceeds 50MB limit for normal users.")
            os.remove(file_path)
            return

        await status.edit("📤 Uploading to Telegram...")

        await message.reply_video(
            video=file_path,
            supports_streaming=True
        )

        await status.delete()
        os.remove(file_path)

    except Exception as e:
        await status.edit(f"⚠ Error: {str(e)}")

print("🔥 Premium Pixeldrain Bot Running...")
app.run()
