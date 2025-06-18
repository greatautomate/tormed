# MedusaXD Torrent Downloader by @medusaXD

A comprehensive Telegram bot for uploading, validating, and managing torrent files with advanced admin features. Built with Pyrogram and designed for deployment on Render.com as a background worker.

## Features

### Core Features
- 🔄 **Torrent Upload & Validation**: Upload and validate .torrent files with metadata extraction
- 👥 **Multi-Chat Support**: Works in private chats, groups, and supergroups
- 🔐 **Admin Authentication**: Comprehensive admin system with user management
- 📊 **Statistics Tracking**: User and global upload statistics
- 🚫 **User Management**: Ban/unban users, promote admins
- 📝 **Comprehensive Logging**: Detailed logging with rotation and monitoring

### Admin Features
- User management (ban/unban/promote)
- Global statistics viewing
- Bot configuration management
- User information lookup
- Admin panel with inline keyboards

### Security Features
- Admin-only commands protection
- File size validation
- Torrent file validation
- User input sanitization
- Comprehensive error handling

## Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Telegram API credentials (from https://my.telegram.org)

### Local Development

1. **Clone and Setup**
```bash
git clone <your-repo>
cd torrent-uploader-bot
pip install -r requirements.txt
```

2. **Configuration**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Environment Variables**
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
ADMIN_USER_IDS=123456789,987654321
SUPER_ADMIN_ID=123456789
DATABASE_URL=sqlite:///bot.db
```

4. **Run the Bot**
```bash
python main.py
```

## Deployment on Render.com

### Step 1: Prepare Your Repository
1. Push your code to GitHub/GitLab
2. Ensure `render.yaml` is in the root directory
3. Make sure all dependencies are in `requirements.txt`

### Step 2: Create Render Service
1. Go to [Render.com](https://render.com)
2. Connect your repository
3. Choose "Background Worker" service type
4. Render will automatically detect the `render.yaml` configuration

### Step 3: Configure Environment Variables
Set these environment variables in Render dashboard:

**Required:**
- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash  
- `BOT_TOKEN`: Your bot token from @BotFather
- `ADMIN_USER_IDS`: Comma-separated admin user IDs
- `SUPER_ADMIN_ID`: Super admin user ID

**Optional:**
- `DATABASE_URL`: PostgreSQL URL (Render provides free PostgreSQL)
- `MAX_FILE_SIZE`: Maximum file size in MB (default: 50)
- `LOG_LEVEL`: Logging level (default: INFO)

### Step 4: Database Setup (Optional)
For production, use PostgreSQL:
1. Create a PostgreSQL database on Render
2. Set `DATABASE_URL` to the provided connection string
3. The bot will automatically create tables on startup

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `API_ID` | Telegram API ID | - | ✅ |
| `API_HASH` | Telegram API Hash | - | ✅ |
| `BOT_TOKEN` | Bot token from @BotFather | - | ✅ |
| `ADMIN_USER_IDS` | Comma-separated admin IDs | - | ✅ |
| `SUPER_ADMIN_ID` | Super admin user ID | - | ✅ |
| `DATABASE_URL` | Database connection URL | `sqlite:///bot.db` | ❌ |
| `BOT_NAME` | Bot display name | `TorrentUploaderBot` | ❌ |
| `MAX_FILE_SIZE` | Max file size in MB | `50` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |
| `WORKERS` | Number of workers | `4` | ❌ |

### Getting Telegram Credentials

1. **API ID & Hash**: Visit https://my.telegram.org
   - Login with your phone number
   - Go to "API development tools"
   - Create a new application
   - Note down `api_id` and `api_hash`

2. **Bot Token**: Message @BotFather on Telegram
   - Send `/newbot`
   - Follow the instructions
   - Save the bot token

3. **Admin User IDs**: 
   - Message @userinfobot to get your user ID
   - Add multiple IDs separated by commas

## Usage

### Basic Commands
- `/start` - Start the bot and see welcome message
- `/help` - Show detailed help information
- `/stats` - View your upload statistics
- `/admin` - Access admin panel (admins only)

### Uploading Torrents
1. Send a `.torrent` file to the bot
2. Bot validates the file and extracts metadata
3. Receive confirmation with torrent details
4. Use inline buttons for additional actions

### Admin Features
Admins can access additional features:
- User management (ban/unban)
- Global statistics
- Bot configuration viewing
- User information lookup

## File Structure

```
torrent-uploader-bot/
├── main.py              # Main application entry point
├── bot.py               # Core bot implementation
├── config.py            # Configuration management
├── database.py          # Database models and manager
├── auth.py              # Authentication and authorization
├── utils.py             # Utility functions
├── logging_config.py    # Logging configuration
├── requirements.txt     # Python dependencies
├── render.yaml          # Render.com deployment config
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Database Schema

### Users Table
- `id`: Telegram user ID (primary key)
- `username`: Telegram username
- `first_name`: User's first name
- `last_name`: User's last name
- `is_admin`: Admin status
- `is_banned`: Ban status
- `created_at`: Registration date
- `last_seen`: Last activity date

### Torrent Uploads Table
- `id`: Auto-increment ID
- `user_id`: Uploader's user ID
- `file_name`: Original filename
- `file_size`: File size in bytes
- `chat_id`: Chat where uploaded
- `message_id`: Message ID
- `upload_date`: Upload timestamp
- `torrent_info`: JSON metadata

### Chat Settings Table
- `chat_id`: Chat ID (primary key)
- `chat_type`: Type of chat
- `chat_title`: Chat title
- `is_enabled`: Whether bot is enabled
- `max_file_size`: Max file size for chat

## Monitoring and Logs

The bot includes comprehensive logging:
- **Console logs**: Colored output for development
- **File logs**: Rotated log files in `logs/` directory
- **Error logs**: Separate error tracking
- **User action logs**: Audit trail for user actions

Log files are automatically rotated and compressed.

## Security Considerations

- Admin user IDs are validated against database
- File uploads are validated for type and size
- User input is sanitized
- Banned users are blocked from using the bot
- Super admin cannot be banned or demoted
- Comprehensive error handling prevents crashes

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if bot token is correct
   - Verify API credentials
   - Check logs for errors

2. **Database errors**
   - Ensure DATABASE_URL is correct
   - Check database permissions
   - Verify database is accessible

3. **File upload issues**
   - Check file size limits
   - Verify file is valid torrent
   - Check disk space

4. **Permission errors**
   - Verify admin user IDs are correct
   - Check user is not banned
   - Ensure proper bot permissions in groups

### Getting Help

1. Check the logs in `logs/` directory
2. Verify all environment variables are set
3. Test with a simple torrent file
4. Check Render.com deployment logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error messages
- Ensure all configuration is correct
- Test in a development environment first
