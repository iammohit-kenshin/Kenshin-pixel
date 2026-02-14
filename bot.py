import os
import re
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- RAILWAY VARIABLES ---
# Code ab direct Railway ke 'Variables' tab se data uthayega
API_ID = int(os.environ.get("API_ID")) 
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client(
    "PixeldrainPremium", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN
)

# Regex to find Pixeldrain ID
PD_PATTERN = r"(?:https?://)?pixeldrain\.com/[du]/([a-zA-Z0-9]+)"

# --- PROGRESS BAR HELPER ---
async def progress_func(current, total, message, ud_type, start_time):
    now = time.time()
    diff = now - start_time
    # Har 5 second mein update karega taaki Telegram flood na ho
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff if diff > 0 else 0
        
        progress_str = "[{0}{1}] {2}%".format(
            ''.join(["▰" for i in range(int(percentage / 10))]),
            ''.join(["▱" for i in range(10 - int(percentage / 10))]),
            round(percentage, 2)
        )
        
        tmp = f"⚡ **{ud_type}**\n\n" \
              f"{progress_str}\n\n" \
              f"🚀 **Speed:** {round(speed / (1024 * 1024), 2)} MB/s\n" \
              f"📦 **Status:** {round(current / (1024 * 1024), 2)}MB / {round(total / (1024 * 1024), 2)}MB"
        
        try:
            await message.edit_text(tmp)
        except:
            pass

@app.on_message(filters.regex(PD_PATTERN))
async def pixeldrain_handler(client, message):
    url = message.text
    file_id = re.search(PD_PATTERN, url).group(1)
    status_msg = await message.reply_text("🔎 **Link Analyze ho raha hai...**")
    
    # 1. API se info fetch karna
    info_url = f"https://pixeldrain.com/api/file/{file_id}/info"
    try:
        res = requests.get(info_url).json()
        if not res.get("success"):
            return await status_msg.edit("❌ **Invalid Link!** File ya toh delete ho gayi hai ya link galat hai.")
        
        file_name = res.get("name")
        file_size = res.get("size")
        direct_link = f"https://pixeldrain.com/api/file/{file_id}?download"

        # 2. Server par download start
        await status_msg.edit(f"📥 **Downloading to Server...**\n`{file_name}`")
        
        start_time = time.time()
        r = requests.get(direct_link, stream=True)
        with open(file_name, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Progress update
                    await progress_func(downloaded, file_size, status_msg, "Downloading...", start_time)

        # 3. Telegram par Upload
        await status_msg.edit("📤 **Telegram par bhej raha hoon...**")
        start_time_up = time.time()
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file_name,
            caption=f"✅ **File:** `{file_name}`\n💰 **Size:** {round(file_size/(1024*1024), 2)} MB\n\n🔥 **Bot by Kenshin**",
            progress=progress_func,
            progress_args=(status_msg, "Uploading...", start_time_up),
            supports_streaming=True
        )

    except Exception as e:
        await message.reply_text(f"💀 **Error Aa Gaya!**\n`{str(e)}`")
    
    finally:
        # Cleanup: File delete karna zaroori hai Railway ka space bachane ke liye
        if os.path.exists(file_name):
            os.remove(file_name)
        try:
            await status_msg.delete()
        except:
            pass

print("Bahi Bot Ready Hai! Railway Variables se connected...")
app.run()
