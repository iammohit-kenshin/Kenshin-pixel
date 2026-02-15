# Setup Guide for Telegram Video Downloader Bot

This guide will walk you through setting up your Telegram video downloader bot step by step.

## Table of Contents
1. [Getting Telegram Credentials](#getting-telegram-credentials)
2. [Local Setup](#local-setup)
3. [Railway Deployment](#railway-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Heroku Deployment](#heroku-deployment)

---

## Getting Telegram Credentials

### Step 1: Create Your Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Choose a name for your bot (e.g., "My Video Downloader")
4. Choose a username for your bot (must end with 'bot', e.g., "myvideo_dl_bot")
5. Copy the **BOT_TOKEN** - it looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get API Credentials

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Click on "API Development Tools"
4. If you don't have an app, create one:
   - App title: "Video Downloader"
   - Short name: "videobot"
   - Platform: Other
5. Copy **API_ID** (a number like 12345678)
6. Copy **API_HASH** (a string like "abcdef1234567890abcdef1234567890")

### Step 3: Get Your User ID

1. Open [@userinfobot](https://t.me/userinfobot) on Telegram
2. Send any message or `/start`
3. Copy your **User ID** (e.g., 123456789)
4. This will be your **ADMIN_ID**

### Step 4: Create Cache Channel (Optional but Recommended)

1. Create a new **private channel** in Telegram:
   - Open Telegram
   - Click on "New Channel"
   - Name it "Video Cache" or similar
   - Make it **Private**
   - Skip adding members
2. Add your bot as an admin:
   - Go to channel settings
   - Click "Administrators"
   - Click "Add Administrator"
   - Search for your bot username
   - Add it with all permissions
3. Get the channel ID:
   - Forward any message from the channel to [@userinfobot](https://t.me/userinfobot)
   - Copy the channel ID (it will look like `-1001234567890`)
   - This is your **CACHE_CHANNEL_ID**

---

## Local Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-video-bot.git
cd telegram-video-bot
```

2. **Create virtual environment** (recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Copy the example file:
```bash
cp .env.example .env
```

Edit `.env` with your favorite text editor and fill in your credentials:
```env
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
ADMIN_ID=your_user_id_here
CACHE_CHANNEL_ID=your_channel_id_here
```

5. **Run the bot**
```bash
python bot.py
```

You should see:
```
INFO - Bot started!
```

6. **Test your bot**
- Open Telegram
- Search for your bot
- Send `/start`
- Try sending a video URL

---

## Railway Deployment

Railway offers free tier with automatic deployments from GitHub.

### Step 1: Prepare Repository

1. Fork this repository to your GitHub account
2. Or create a new repository and push this code

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Railway will detect the configuration automatically

### Step 3: Add Environment Variables

1. Click on your project
2. Go to "Variables" tab
3. Add each variable:
   ```
   BOT_TOKEN=your_bot_token_here
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   ADMIN_ID=your_user_id_here
   CACHE_CHANNEL_ID=your_channel_id_here
   ```
4. Click "Deploy" or wait for automatic deployment

### Step 4: Monitor Deployment

1. Go to "Deployments" tab
2. Watch the build logs
3. Once deployed, check "Logs" tab to see if bot started successfully

### Troubleshooting Railway

**Bot not starting:**
- Check logs for error messages
- Verify all environment variables are set
- Ensure BOT_TOKEN is correct

**Out of resources:**
- Railway free tier has limits
- Consider upgrading for better performance
- Or use Heroku/VPS

---

## Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose installed (optional)

### Method 1: Using Docker Compose (Recommended)

1. **Create `.env` file** with your credentials

2. **Build and run**
```bash
docker-compose up -d
```

3. **View logs**
```bash
docker-compose logs -f
```

4. **Stop the bot**
```bash
docker-compose down
```

### Method 2: Using Docker CLI

1. **Build image**
```bash
docker build -t telegram-video-bot .
```

2. **Run container**
```bash
docker run -d \
  --name video-bot \
  -e BOT_TOKEN="your_token" \
  -e API_ID="your_api_id" \
  -e API_HASH="your_api_hash" \
  -e ADMIN_ID="your_admin_id" \
  -e CACHE_CHANNEL_ID="your_channel_id" \
  telegram-video-bot
```

3. **View logs**
```bash
docker logs -f video-bot
```

4. **Stop container**
```bash
docker stop video-bot
docker rm video-bot
```

---

## Heroku Deployment

### Step 1: Prepare Heroku

1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login:
```bash
heroku login
```

### Step 2: Create App

```bash
heroku create your-app-name
```

### Step 3: Set Config Vars

```bash
heroku config:set BOT_TOKEN="your_token"
heroku config:set API_ID="your_api_id"
heroku config:set API_HASH="your_api_hash"
heroku config:set ADMIN_ID="your_admin_id"
heroku config:set CACHE_CHANNEL_ID="your_channel_id"
```

### Step 4: Deploy

```bash
git push heroku main
```

### Step 5: Scale Worker

```bash
heroku ps:scale worker=1
```

### View Logs

```bash
heroku logs --tail
```

---

## Verification Checklist

After deployment, verify everything works:

- [ ] Bot responds to `/start` command
- [ ] Bot shows welcome message
- [ ] Can download a simple video URL
- [ ] Progress bar shows during download
- [ ] Video uploads successfully
- [ ] File is deleted after upload
- [ ] `/stats` command works (for admin)
- [ ] Admin panel accessible
- [ ] Second request for same video uses cache

---

## Common Issues

### "Bot token is invalid"
- Double-check your BOT_TOKEN
- Make sure there are no extra spaces
- Get a new token from @BotFather if needed

### "Could not connect to Telegram"
- Check your internet connection
- Verify firewall settings
- Try different deployment platform

### "Video download failed"
- Check if the URL is correct
- Some sites may be blocked
- Try a different video source

### "Cache not working"
- Verify CACHE_CHANNEL_ID is correct
- Ensure bot is admin in the channel
- Check that channel ID has `-100` prefix

---

## Next Steps

Once your bot is running:

1. **Test thoroughly** with different video sources
2. **Share with friends** (if desired)
3. **Monitor performance** using admin panel
4. **Customize** settings in `config.py`
5. **Report issues** on GitHub

---

## Support

Need help? 

1. Check the [README](README.md)
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Open an issue on GitHub
4. Check Railway/Heroku logs for errors

---

Happy downloading! 🎉
