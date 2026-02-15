# Telegram Video Downloader Bot 🎥

A powerful Telegram bot that downloads videos from various sources and delivers them directly to users with advanced features like caching, progress tracking, and admin panel.

## ✨ Features

- **Multi-Source Support**: Download videos from hundreds of websites
- **Direct Link Support**: Download from direct .mp4/.mkv links
- **Smart Caching System**: Store videos in Telegram to avoid re-downloading
- **Progress Tracking**: Real-time download progress with speed indicators
- **Auto-Cleanup**: Automatically deletes files after upload to save storage
- **Admin Panel**: Monitor bot statistics and manage cache
- **Thumbnail Support**: Automatically fetches and includes video thumbnails
- **Fast Downloads**: Optimized downloading with yt-dlp
- **Large File Support**: Upload files up to 2GB
- **User-Friendly**: Simple interface - just send a URL!

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram API ID and Hash (from [my.telegram.org](https://my.telegram.org))
- A Telegram channel/group for caching (optional but recommended)

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-video-bot.git
cd telegram-video-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file:
```env
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
ADMIN_ID=your_telegram_user_id
CACHE_CHANNEL_ID=-100xxxxxxxxxx
```

**How to get these values:**

- **BOT_TOKEN**: 
  1. Open [@BotFather](https://t.me/BotFather) on Telegram
  2. Send `/newbot` and follow instructions
  3. Copy the token provided

- **API_ID & API_HASH**:
  1. Go to [my.telegram.org](https://my.telegram.org)
  2. Log in with your phone number
  3. Go to "API Development Tools"
  4. Create an app and copy the credentials

- **ADMIN_ID**:
  1. Open [@userinfobot](https://t.me/userinfobot)
  2. Send any message
  3. Copy your user ID

- **CACHE_CHANNEL_ID**:
  1. Create a private channel or group
  2. Add your bot as admin
  3. Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
  4. Copy the channel ID (including the `-100` prefix)

4. **Run the bot**
```bash
python bot.py
```

## 🌐 Railway Deployment

### Step-by-Step Deployment

1. **Fork this repository** to your GitHub account

2. **Sign up on Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

3. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your forked repository

4. **Configure Environment Variables**
   
   In Railway dashboard, go to Variables tab and add:
   ```
   BOT_TOKEN = your_bot_token
   API_ID = your_api_id
   API_HASH = your_api_hash
   ADMIN_ID = your_telegram_user_id
   CACHE_CHANNEL_ID = your_cache_channel_id
   ```

5. **Deploy**
   - Railway will automatically detect the configuration
   - Wait for deployment to complete
   - Your bot is now live! 🎉

### Alternative: Deploy Button

Click the button below to deploy directly:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

## 📋 Supported Sources

The bot uses `yt-dlp` which supports **1000+ websites** including:

- YouTube
- Instagram
- Facebook
- Twitter/X
- TikTok
- Reddit
- Vimeo
- Dailymotion
- And many more!

Plus direct video links (.mp4, .mkv, .avi, etc.)

## 🎯 How to Use

1. **Start the bot**
   - Open your bot on Telegram
   - Send `/start`

2. **Send a video URL**
   - Just paste any video URL
   - The bot will automatically detect and download it

3. **Wait for download**
   - You'll see real-time progress
   - The video will be sent when ready

4. **Enjoy!**
   - The video is yours to watch
   - Next time you request the same video, it'll be instant (from cache)

## 👨‍💼 Admin Commands

- `/start` - Start the bot and see welcome message
- `/stats` - View bot statistics (admin only)
- Admin Panel Button - Access full admin dashboard with:
  - Total users count
  - Download statistics
  - Cache management
  - Clear cache option

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | ✅ | Your Telegram bot token |
| `API_ID` | ✅ | Telegram API ID |
| `API_HASH` | ✅ | Telegram API Hash |
| `ADMIN_ID` | ✅ | Your Telegram user ID for admin access |
| `CACHE_CHANNEL_ID` | ⚠️ | Channel/Group ID for caching videos (recommended) |

### Customization

You can modify these values in `bot.py`:

```python
MAX_FILE_SIZE = 2000 * 1024 * 1024  # Maximum file size (2GB)
DOWNLOAD_DIR = '/tmp/downloads'      # Download directory
```

## 🏗️ Architecture

### Caching System

The bot implements a two-tier caching system:

1. **In-Memory Cache**: Stores file_id for quick access
2. **Telegram Storage**: Videos stored in cache channel for persistence

When a user requests a video:
1. Check in-memory cache → Send instantly if found
2. If not cached → Download and process
3. Upload to cache channel
4. Send to user
5. Store file_id in cache

### Auto-Cleanup

Files are automatically deleted:
- Immediately after successful upload
- Every 5 minutes for orphaned files older than 10 minutes
- Cache entries older than 24 hours are removed

### Download Methods

The bot tries multiple methods in order:

1. **yt-dlp**: Best for video hosting sites (supports 1000+ sites)
2. **Direct Download**: For direct video file links
3. Falls back to error message if both fail

## 🛠️ Troubleshooting

### Bot not responding
- Check if `BOT_TOKEN` is correct
- Verify the bot is running (`python bot.py`)
- Check Railway logs for errors

### "Failed to download video"
- The site might not be supported
- Video might be private or geo-restricted
- URL might be expired
- Try a different video source

### Large files not uploading
- Railway has storage limits on free tier
- Consider upgrading Railway plan
- Reduce `MAX_FILE_SIZE` if needed

### Cache not working
- Ensure `CACHE_CHANNEL_ID` is set correctly
- Bot must be admin in the cache channel
- Check that the channel ID includes `-100` prefix

## 📊 Performance

- **Download Speed**: Depends on source and Railway bandwidth
- **Cache Hit Rate**: Typically 30-50% for popular content
- **Storage**: Auto-cleanup prevents storage issues
- **Concurrent Users**: Handles multiple users simultaneously

## 🔐 Privacy & Security

- Videos are deleted immediately after upload
- No permanent storage on server
- Cache stored in your private Telegram channel
- Only admin can access statistics
- No user data logging

## 📝 Notes

- **Legal Notice**: This bot is for personal use. Ensure you have rights to download content
- **Rate Limits**: Some sites have rate limits; the bot respects them
- **File Size**: Telegram has a 2GB limit for bot uploads
- **Storage**: Railway free tier has 1GB storage; auto-cleanup helps manage this

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## 📜 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This bot is provided as-is for educational purposes. Users are responsible for ensuring they comply with:
- Terms of service of video platforms
- Copyright laws
- Telegram's terms of service
- Local regulations

## 🆘 Support

If you encounter issues:

1. Check the [Issues](https://github.com/yourusername/telegram-video-bot/issues) page
2. Review Railway deployment logs
3. Verify all environment variables are set correctly
4. Ensure all dependencies are installed

## 🎉 Credits

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [aiohttp](https://github.com/aio-libs/aiohttp)

---

Made with ❤️ for the Telegram community
