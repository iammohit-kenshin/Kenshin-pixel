import re
import os
import asyncio
import aiohttp
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

client = TelegramClient("pixeldrain_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

PIXEL_REGEX = r"(https?://pixeldrain\.com/d/([a-zA-Z0-9]+))"

USER_LIMIT = 50 * 1024 * 1024  # 50MB

# Extract Direct Download Link
def get_direct_link(url):
    match = re.search(PIXEL_REGEX, url)
    if match:
        file_id = match.group(2)
        return f"https://pixeldrain.com/api/file/{file_id}"
    return None

# Download File
async def download_file(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                with open(filename, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                return True
    return False

@client.on(events.NewMessage)
async def handler(event):
    if not event.message.text:
        return

    link = re.search(PIXEL_REGEX, event.message.text)
    if not link:
        return

    await event.reply("⚡ Processing Pixeldrain Link...")

    direct_url = get_direct_link(event.message.text)
    if not direct_url:
        await event.reply("❌ Invalid Pixeldrain Link")
        return

    filename = "video.mp4"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(direct_url) as resp:
                size = int(resp.headers.get("Content-Length", 0))

        # Size Check
        if event.sender_id != ADMIN_ID and size > USER_LIMIT:
            await event.reply("❌ File above 50MB limit. Upgrade to Premium 😎")
            return

        await event.reply("⬇️ Downloading...")

        success = await download_file(direct_url, filename)
        if not success:
            await event.reply("❌ Download Failed")
            return

        await event.reply("📤 Uploading...")

        await client.send_file(
            event.chat_id,
            filename,
            attributes=[DocumentAttributeVideo()],
            supports_streaming=True
        )

        os.remove(filename)

    except Exception as e:
        await event.reply(f"⚠️ Error: {str(e)}")

print("🚀 Pixeldrain Premium Bot Running...")
client.run_until_disconnected()
