# Deployment Guide for MedusaXD Torrent Downloader

This guide provides step-by-step instructions for deploying the MedusaXD Torrent Downloader Bot by @medusaXD on Render.com and other platforms.

## Prerequisites

Before deployment, ensure you have:

1. **Telegram Bot Token**
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Save the bot token

2. **Telegram API Credentials**
   - Visit https://my.telegram.org
   - Login and go to "API development tools"
   - Create an application and note `api_id` and `api_hash`

3. **Admin User IDs**
   - Message @userinfobot to get your Telegram user ID
   - Collect user IDs for all admins

## Render.com Deployment (Recommended)

### Step 1: Prepare Repository

1. **Fork or clone this repository**
2. **Push to your GitHub/GitLab account**
3. **Verify files are present:**
   - `render.yaml` (deployment configuration)
   - `requirements.txt` (dependencies)
   - `main.py` (entry point)

### Step 2: Create Render Service

1. **Go to [Render.com](https://render.com)**
2. **Sign up/Login** with GitHub/GitLab
3. **Click "New +"** → **"Background Worker"**
4. **Connect your repository**
5. **Render will auto-detect** the `render.yaml` configuration

### Step 3: Configure Environment Variables

In the Render dashboard, set these environment variables:

**Required Variables:**
```
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_USER_IDS=123456789,987654321
SUPER_ADMIN_ID=123456789
```

**Optional Variables:**
```
DATABASE_URL=postgresql://user:pass@host:port/db
BOT_NAME=TorrentUploaderBot
MAX_FILE_SIZE=50
LOG_LEVEL=INFO
WORKERS=4
```

### Step 4: Database Setup (Optional)

For production, use PostgreSQL:

1. **In Render dashboard:** New + → PostgreSQL
2. **Create database** (free tier available)
3. **Copy the External Database URL**
4. **Set as `DATABASE_URL`** in your bot service

### Step 5: Deploy

1. **Click "Deploy"** in Render dashboard
2. **Monitor logs** for successful startup
3. **Test the bot** by messaging it on Telegram

## Alternative Deployment Methods

### Docker Deployment

1. **Build the image:**
```bash
docker build -t torrent-uploader-bot .
```

2. **Run with environment file:**
```bash
docker run -d --name torrent-bot --env-file .env torrent-uploader-bot
```

3. **Or use docker-compose:**
```bash
docker-compose up -d
```

### VPS/Server Deployment

1. **Install Python 3.8+:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

2. **Clone repository:**
```bash
git clone <your-repo-url>
cd torrent-uploader-bot
```

3. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your values
```

6. **Run the bot:**
```bash
python main.py
```

7. **Setup systemd service (optional):**
```bash
sudo nano /etc/systemd/system/torrent-bot.service
```

```ini
[Unit]
Description=Torrent Uploader Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/torrent-uploader-bot
Environment=PATH=/path/to/torrent-uploader-bot/venv/bin
ExecStart=/path/to/torrent-uploader-bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable torrent-bot
sudo systemctl start torrent-bot
```

## Environment Variables Reference

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `API_ID` | Telegram API ID | `12345678` | ✅ |
| `API_HASH` | Telegram API Hash | `abcdef123456...` | ✅ |
| `BOT_TOKEN` | Bot token from @BotFather | `123:ABC-DEF...` | ✅ |
| `ADMIN_USER_IDS` | Comma-separated admin IDs | `123,456,789` | ✅ |
| `SUPER_ADMIN_ID` | Super admin user ID | `123456789` | ✅ |
| `DATABASE_URL` | Database connection string | `sqlite:///bot.db` | ❌ |
| `BOT_NAME` | Display name for the bot | `TorrentUploaderBot` | ❌ |
| `MAX_FILE_SIZE` | Max file size in MB | `50` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `WORKERS` | Number of worker threads | `4` | ❌ |

## Testing Before Deployment

Run the test script to verify everything works:

```bash
python test_bot.py
```

This will check:
- Configuration validity
- Database connectivity
- Import dependencies
- Authentication system
- Core functionality

## Post-Deployment Checklist

1. **✅ Bot responds to `/start`**
2. **✅ Admin commands work**
3. **✅ File uploads are processed**
4. **✅ Database is storing data**
5. **✅ Logs are being generated**
6. **✅ Error handling works**

## Monitoring and Maintenance

### Logs
- **Render.com:** Check logs in dashboard
- **Docker:** `docker logs torrent-bot`
- **VPS:** Check `logs/` directory

### Health Checks
- Monitor bot responsiveness
- Check database connectivity
- Monitor file upload success rate
- Review error logs regularly

### Updates
1. **Update code** in repository
2. **Render auto-deploys** on git push
3. **For manual deployments:** restart service

## Troubleshooting

### Common Issues

**Bot not starting:**
- Check environment variables
- Verify API credentials
- Check logs for specific errors

**Database errors:**
- Verify DATABASE_URL format
- Check database permissions
- Ensure database is accessible

**File upload issues:**
- Check file size limits
- Verify torrent file validity
- Check available disk space

**Permission errors:**
- Verify admin user IDs
- Check bot permissions in groups
- Ensure user is not banned

### Getting Help

1. **Check logs** for error messages
2. **Run test script** to identify issues
3. **Verify configuration** against this guide
4. **Test in development** before production

## Security Best Practices

1. **Keep credentials secure**
   - Never commit `.env` files
   - Use environment variables
   - Rotate tokens periodically

2. **Database security**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups

3. **Bot permissions**
   - Limit admin users
   - Regular audit of permissions
   - Monitor user actions

4. **Server security**
   - Keep system updated
   - Use firewall rules
   - Monitor access logs

## Scaling Considerations

For high-traffic bots:

1. **Use PostgreSQL** instead of SQLite
2. **Increase worker count**
3. **Monitor resource usage**
4. **Consider load balancing**
5. **Implement rate limiting**

## Support

For deployment issues:
- Check this guide thoroughly
- Review error logs
- Test configuration locally
- Verify all prerequisites are met
