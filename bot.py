import os
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

# ========= START COMMAND =========

@app.on_message(filters.private & filters.command("start"))
async def start(_, msg):
    await msg.reply_text("Send me a video link 🎬")

# ========= HANDLE LINK =========

@app.on_message(filters.private & filters.text)
async def handle_link(client, message):
    url = message.text.strip()

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Video", callback_data=f"video|{url}")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"audio|{url}")]
    ])

    await message.reply_text("Choose format:", reply_markup=buttons)

# ========= CALLBACK HANDLER =========

@app.on_callback_query()
async def callback_handler(client, callback):
    data = callback.data.split("|")
    mode = data[0]
    url = data[1]

    await callback.message.edit_text("🔍 Fetching available qualities...")

    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    if mode == "video":
        qualities = []
        for f in info["formats"]:
            if f.get("height") and f.get("ext") == "mp4":
                qualities.append((f["format_id"], f["height"]))

        # Remove duplicates
        qualities = list({q[1]: q for q in qualities}.values())
        qualities = sorted(qualities, key=lambda x: x[1], reverse=True)

        buttons = []
        for q in qualities[:6]:  # show top 6
            buttons.append([
                InlineKeyboardButton(
                    f"{q[1]}p",
                    callback_data=f"download|video|{q[0]}|{url}"
                )
            ])

        await callback.message.edit_text(
            "Select quality:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif mode == "audio":
        await download_and_send(callback, url, "audio", "mp3", None)

# ========= DOWNLOAD FUNCTION =========

async def download_and_send(callback, url, mode, format_id, quality_id):

    cached = cache.get_cached(url, format_id)
    if cached:
        await callback.message.edit_text("⚡ Sending from cache...")
        await app.copy_message(
            callback.message.chat.id,
            config.LOG_GROUP_ID,
            cached
        )
        return

    await callback.message.edit_text("⬇ Downloading...")

    output = "downloads/%(title)s.%(ext)s"

    if mode == "video":
        ydl_opts = {
            'format': format_id,
            'outtmpl': output,
            'merge_output_format': 'mp4'
        }
    else:
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': output,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if mode == "audio":
            file_path = file_path.rsplit(".", 1)[0] + ".mp3"

    await callback.message.edit_text("⬆ Uploading...")

    sent = await app.send_document(
        config.LOG_GROUP_ID,
        file_path,
        thumb=info.get("thumbnail"),
        caption=info.get("title")
    )

    file_id = sent.document.file_id
    cache.save_cache(url, format_id, sent.id)

    await app.copy_message(
        callback.message.chat.id,
        config.LOG_GROUP_ID,
        sent.id
    )

    os.remove(file_path)

# ========= DOWNLOAD QUALITY HANDLER =========

@app.on_callback_query(filters.regex("^download"))
async def quality_download(client, callback):
    _, mode, format_id, url = callback.data.split("|")
    await download_and_send(callback, url, mode, format_id, format_id)

# ========= RUN =========

app.run()
