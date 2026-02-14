import os
import re
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 1234567 # Apna API ID yahan dalein
API_HASH = "your_api_hash" # Apna API Hash yahan dalein
BOT_TOKEN = "your_bot_token" # @BotFather se liya gaya token

app = Client("PixeldrainPremium", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Regex to find Pixeldrain ID
PD_PATTERN = r"(?:https?://)?pixeldrain\.com/u/([a-zA-Z0-9]+)"

# --- PROGRESS BAR HELPER ---
async def progress_func(current, total, message, ud_type, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        time_to_completion = round((total - current) / speed)
        
        progress_str = "[{0}{1}] {2}%".format(
            ''.join(["▰" for i in range(int(percentage / 10))]),
            ''.join(["▱" for i in range(10 - int(percentage / 10))]),
            round(percentage, 2)
        )
        
        tmp = f"{ud_type}\n\n{progress_str}\n\n" \
              f"🚀 Speed: {round(speed / 1024, 2)} KB/s\n" \
              f"📦 Done: {round(current / (1024 * 1024), 2)} MB / {round(total / (1024 * 1024), 2)} MB"
        
        try:
            await message.edit_text(tmp)
        except:
            pass

@app.on_message(filters.regex(PD_PATTERN))
async def pixeldrain_handler(client, message):
    url = message.text
    file_id = re.search(PD_PATTERN, url).group(1)
    status_msg = await message.reply_text("⚡ **Analyzing link...**")
    
    # 1. API se info fetch karna
    info_url = f"https://pixeldrain.com/api/file/{file_id}/info"
    res = requests.get(info_url).json()
    
    if not res.get("success"):
        return await status_msg.edit("❌ **Invalid Link!** Pixeldrain ne file mana kar di.")

    file_name = res.get("name")
    file_size = res.get("size")
    direct_link = f"https://pixeldrain.com/api/file/{file_id}?download"

    # 2. Server par download start (with progress)
    await status_msg.edit(f"📥 **Downloading to Server...**\n`{file_name}`")
    
    start_time = time.time()
    try:
        r = requests.get(direct_link, stream=True)
        with open(file_name, 'wb') as f:
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Har 2MB par progress update (customized logic)
                    if downloaded % (5*1024*1024) == 0:
                        await progress_func(downloaded, file_size, status_msg, "📥 **Downloading...**", start_time)

        # 3. Telegram par Upload
        await status_msg.edit("📤 **Uploading to Telegram...**")
        start_time_up = time.time()
        
        await client.send_video(
            chat_id=message.chat.id,
            video=file_name,
            caption=f"✅ **File:** `{file_name}`\n💰 **Size:** {round(file_size/(1024*1024), 2)} MB",
            progress=progress_func,
            progress_args=(status_msg, "📤 **Uploading...**", start_time_up),
            supports_streaming=True
        )

    except Exception as e:
        await message.reply_text(f"💀 **Ghoda Lag Gaya! Error:** `{str(e)}`")
    
    finally:
        # Cleanup
        if os.path.exists(file_name):
            os.remove(file_name)
        await status_msg.delete()

print("Bahi Bot Chalu Ho Gaya Hai! Fadh Dega Sab...")
app.run()
