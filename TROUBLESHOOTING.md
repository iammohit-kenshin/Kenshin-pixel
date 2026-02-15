# Troubleshooting Guide

Common issues and their solutions for the Telegram Video Downloader Bot.

## Table of Contents
1. [Bot Issues](#bot-issues)
2. [Download Issues](#download-issues)
3. [Upload Issues](#upload-issues)
4. [Cache Issues](#cache-issues)
5. [Deployment Issues](#deployment-issues)
6. [Performance Issues](#performance-issues)

---

## Bot Issues

### Bot doesn't respond to commands

**Symptoms:**
- Bot doesn't reply to `/start`
- No response to any messages

**Solutions:**

1. **Check if bot is running**
   ```bash
   # For local deployment
   ps aux | grep bot.py
   
   # For Docker
   docker ps
   
   # For Railway
   Check "Deployments" tab
   ```

2. **Verify BOT_TOKEN**
   - Check for typos
   - Ensure no extra spaces
   - Try creating a new bot and token

3. **Check logs**
   ```bash
   # Local
   tail -f bot.log
   
   # Docker
   docker logs -f video-bot
   
   # Railway
   Check "Logs" tab in dashboard
   ```

4. **Test token manually**
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
   ```
   Should return bot information

### Bot crashes on startup

**Common errors:**

**Error: "BOT_TOKEN is required"**
- Solution: Set BOT_TOKEN environment variable
- Check spelling: it's `BOT_TOKEN`, not `BOT_TOKEN_KEY`

**Error: "No module named 'telegram'"**
```bash
pip install -r requirements.txt
```

**Error: "Invalid API_ID"**
- API_ID must be a number
- Get new credentials from my.telegram.org

---

## Download Issues

### "Failed to download video"

**Possible causes:**

1. **Site not supported**
   - Check if site is in yt-dlp supported list
   - Try alternative download method
   - Some sites require cookies/login

2. **Invalid URL**
   - Ensure URL starts with http:// or https://
   - Check for typos
   - Try copying URL again

3. **Video is private/restricted**
   - Bot cannot download private videos
   - Geographic restrictions may apply
   - Login-required videos won't work

4. **Network issues**
   - Check internet connection
   - Some hosts may block requests
   - Try VPN if available

**Testing downloads:**

Test with a known working URL:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Download starts but fails midway

**Solutions:**

1. **Check file size**
   - Maximum size is 2GB (configurable)
   - Reduce MAX_FILE_SIZE if needed

2. **Storage space**
   ```bash
   df -h /tmp
   ```
   - Clear space if needed
   - Bot auto-cleans old files

3. **Network timeout**
   - Slow connections may timeout
   - Try smaller videos first
   - Check Railway/Heroku network status

### Progress bar not updating

**Cause:** Normal behavior
- Updates every 2 seconds
- Some videos don't report total size

**If stuck at 0%:**
- Wait a bit longer
- Cancel and retry
- Check logs for errors

---

## Upload Issues

### "File too large" error

**Solutions:**

1. **Check file size**
   - Telegram limit: 2GB for bots
   - Check actual file size:
     ```bash
     ls -lh /tmp/downloads/
     ```

2. **Adjust MAX_FILE_SIZE**
   In `.env`:
   ```env
   MAX_FILE_SIZE=1500000000  # 1.5GB
   ```

3. **Use compression**
   - Bot downloads best quality by default
   - Lower quality = smaller file

### Upload stalls or times out

**Solutions:**

1. **Check upload speed**
   - Railway/Heroku have bandwidth limits
   - Large files take time
   - Be patient

2. **Verify API credentials**
   - API_ID and API_HASH must be correct
   - Get new credentials if needed

3. **Bot rate limits**
   - Telegram limits upload speed
   - Multiple large uploads may be throttled
   - Wait and retry

### Video uploads but is corrupted

**Possible causes:**

1. **Incomplete download**
   - Check download completed successfully
   - Verify file integrity before upload

2. **File format issues**
   - Some formats may not work well
   - Try different source

3. **ffmpeg missing** (if using custom processing)
   ```bash
   ffmpeg -version
   ```

---

## Cache Issues

### Cache not working

**Check:**

1. **CACHE_CHANNEL_ID is set**
   ```bash
   echo $CACHE_CHANNEL_ID
   ```

2. **Bot is admin in channel**
   - Open cache channel
   - Check administrators
   - Bot should be listed

3. **Channel ID format**
   - Must start with `-100`
   - Example: `-1001234567890`
   - Get from @userinfobot

4. **Enable caching**
   In `.env`:
   ```env
   ENABLE_CACHE=true
   ```

### "Cannot access cache channel"

**Solutions:**

1. **Verify channel ID**
   - Forward message from channel to @userinfobot
   - Copy the correct ID

2. **Check bot permissions**
   - Bot needs "Post Messages" permission
   - Should be admin with all rights

3. **Channel must be private**
   - Public channels may have issues
   - Use private channel/group

### Cache serving old videos

**Normal behavior:**
- Cache expires after 24 hours (default)
- Clear cache manually from admin panel

**To adjust cache expiry:**
```env
CACHE_EXPIRY_HOURS=48  # 48 hours
```

---

## Deployment Issues

### Railway Deployment

**Build fails:**

1. **Check Python version**
   - `runtime.txt` specifies Python 3.11.7
   - Compatible with Railway

2. **Missing dependencies**
   - All listed in `requirements.txt`
   - Railway installs automatically

3. **Build logs**
   - Check "Deployments" tab
   - Look for specific error messages

**Bot deploys but doesn't work:**

1. **Environment variables**
   - All must be set in Railway dashboard
   - Check "Variables" tab
   - No quotes needed in Railway

2. **Worker process**
   - `Procfile` should contain: `worker: python bot.py`
   - Check if worker is running

3. **Resource limits**
   - Free tier has limits
   - Check resource usage
   - Upgrade if needed

### Heroku Deployment

**Common issues:**

1. **No web process**
   - This is a worker bot, not web app
   - Scale worker: `heroku ps:scale worker=1`

2. **Slug too large**
   - Clear unnecessary files
   - Use `.slugignore`

3. **Free dyno sleeping**
   - Free dynos sleep after 30 minutes
   - Upgrade to hobby dyno
   - Or use UptimeRobot to ping

### Docker Issues

**Container exits immediately:**

```bash
docker logs video-bot
```
Check for:
- Missing environment variables
- Python errors
- Permission issues

**Cannot connect to Telegram:**
- Check network settings
- Verify Docker has internet access
- Check firewall rules

---

## Performance Issues

### Slow downloads

**Causes:**

1. **Source server slow**
   - Nothing bot can do
   - Try different source

2. **Network limitations**
   - Railway/Heroku free tier limits
   - Consider paid plan
   - Use VPS for better performance

3. **Multiple concurrent downloads**
   - Bot processes one at a time per user
   - Wait for current download to finish

### High memory usage

**Solutions:**

1. **Reduce MAX_FILE_SIZE**
   ```env
   MAX_FILE_SIZE=1000000000  # 1GB
   ```

2. **Enable auto-cleanup**
   - Already enabled by default
   - Adjust cleanup interval if needed

3. **Restart bot periodically**
   - Railway: automatic
   - Docker: `docker restart video-bot`

### Bot becomes unresponsive

**Quick fixes:**

1. **Restart bot**
   ```bash
   # Local
   kill <pid>
   python bot.py
   
   # Docker
   docker restart video-bot
   
   # Railway
   Redeploy from dashboard
   ```

2. **Check disk space**
   ```bash
   df -h
   ```
   Clear if needed

3. **Monitor logs**
   Look for errors or warnings

---

## Debugging Tips

### Enable detailed logging

Modify `bot.py`:
```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed from INFO
)
```

### Test individual components

**Test download only:**
```python
python -c "
import yt_dlp
ydl_opts = {'format': 'best'}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['YOUR_URL'])
"
```

**Test bot connection:**
```python
python -c "
from telegram import Bot
bot = Bot('YOUR_BOT_TOKEN')
print(bot.get_me())
"
```

### Check dependencies versions

```bash
pip freeze | grep -E '(telegram|yt-dlp|aiohttp)'
```

Should match `requirements.txt` versions

---

## Getting Help

If you're still stuck:

1. **Check bot logs** for specific errors
2. **Search GitHub issues** for similar problems
3. **Create new issue** with:
   - Python version
   - Platform (Railway/Heroku/Local)
   - Error messages
   - Steps to reproduce

4. **Provide logs** (remove sensitive data):
   ```bash
   # Get last 100 lines
   tail -n 100 bot.log
   ```

---

## Quick Checklist

When something goes wrong, check:

- [ ] Bot is running
- [ ] All environment variables are set
- [ ] BOT_TOKEN is valid
- [ ] Bot has admin rights in cache channel
- [ ] Internet connection is working
- [ ] Enough disk space available
- [ ] No firewall blocking connections
- [ ] Python version is 3.11+
- [ ] All dependencies installed
- [ ] Logs show no errors

---

## Useful Commands

```bash
# Check if bot process is running
ps aux | grep bot.py

# View live logs
tail -f bot.log

# Check disk space
df -h

# Check memory usage
free -h

# Test network connectivity
ping telegram.org

# Check Python version
python --version

# List installed packages
pip list

# Restart bot (local)
pkill -f bot.py && python bot.py
```

---

**Still having issues?** Open an issue on GitHub with detailed information!
