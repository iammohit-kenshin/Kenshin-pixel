import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

import config
import cache

app = Client(
    "video_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

# ✅ URL validation
def is_valid_url(text):
    url_pattern = re.compile(r'https?://\S+')
    return re.match(url_pattern, text)

# ================= START =================

@app.on_message(filters.command("start") & filters.private)
async def start(_, msg):
    await msg.reply_text("Send me a valid video link 🎬")

# ================= HANDLE LINK =================

@app.on_message(filters.private & filters.text)
async def handle_link(client, message):

    url = message.text.strip()

    if not is_valid_url(url):
        return  # ignore normal text

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Video", callback_data=f"video|{url}")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"audio|{url}")]
    ])

    await message.reply_text("Choose format:", reply_markup=buttons)

# ================= CALLBACK =================

@app.on_callback_query()
async def callback_handler(client, callback):

    data = callback.data.split("|")
    mode = data[0]
    url = data[1]

    await callback.answer()

    if mode == "video":

        await callback.message.edit_text("🔍 Fetching qualities...")

        ydl_opts = {'quiet': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info["formats"]:
            if f.get("height") and f.get("ext") == "mp4":
                formats.append((f["format_id"], f["height"]))

        # remove duplicates
        formats = list({f[1]: f for f in formats}.values())
        formats = sorted(formats, key=lambda x: x[1], reverse=True)

        buttons = []
        for f in formats[:5]:
            buttons.append([
                InlineKeyboardButton(
                    f"{f[1]}p",
                    callback_data=f"download|{f[0]}|{url}"
                )
            ])

        await callback.message.edit_text(
            "Select quality:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif mode == "audio":

        await download_and_send(callback, url, audio=True)

# ================= DOWNLOAD =================

async def download_and_send(callback, url, format_id=None, audio=False):

    await callback.message.edit_text("⬇ Downloading...")

    if audio:
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }
    else:
        ydl_opts = {
            'format': format_id,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4'
        }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

        if audio:
            file_path = file_path.rsplit(".", 1)[0] + ".mp3"

    await callback.message.edit_text("⬆ Uploading...")

    sent = await app.send_document(
        config.LOG_GROUP_ID,
        file_path,
        caption=info.get("title")
    )

    await app.copy_message(
        callback.message.chat.id,
        config.LOG_GROUP_ID,
        sent.id
    )

    os.remove(file_path)

# ================= QUALITY DOWNLOAD =================

@app.on_callback_query(filters.regex("^download"))
async def quality_download(client, callback):
    _, format_id, url = callback.data.split("|")
    await download_and_send(callback, url, format_id=format_id)

# ================= RUN =================

app.run()
