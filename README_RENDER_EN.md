# Pixabay Telegram Bot - Render Deployment Guide

This guide will help you deploy the Pixabay Telegram Bot to Render platform.

## Prerequisites

1. A Render account (free tier available)
2. A Telegram bot token from @BotFather
3. A Pixabay API key
4. Your Telegram user ID (for admin access)

## Quick Deploy to Render

### Option 1: Using render.yaml (Recommended)
1. Fork or download this repository
2. Connect your GitHub repository to Render
3. Render will automatically detect the `render.yaml` file and configure the service
4. Set your environment variables in the Render dashboard

### Option 2: Manual Deploy
1. Create a new Web Service on Render
2. Connect your repository
3. Configure the following settings:

## Environment Variables

Set these environment variables in your Render dashboard:

```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here
PIXABAY_API_KEY=your_pixabay_api_key_here
PORT=10000
PYTHONUNBUFFERED=1
```

## Render Configuration

- **Build Command**: `pip install -r render_requirements.txt`
- **Start Command**: `python main.py`
- **Environment**: Python 3.11.7
- **Plan**: Free (or upgrade as needed)
- **Port**: 10000

## Files for Render Deployment

This repository includes the following files specifically for Render:

- `render_requirements.txt` - Python dependencies with locked versions
- `runtime.txt` - Python version specification
- `render.yaml` - Automated service configuration
- `Procfile` - Process configuration
- `.env.example` - Environment variables template
- `README_RENDER.md` - Arabic deployment guide
- `README_RENDER_EN.md` - This English deployment guide

## Troubleshooting Common Issues

### Build Failures
- Ensure `runtime.txt` specifies a supported Python version
- Check that all dependencies in `render_requirements.txt` are compatible
- Verify your repository has all required files

### Runtime Errors
- Check Render logs for specific error messages
- Ensure all environment variables are set correctly
- Verify your bot token and API keys are valid

### Bot Not Responding
- Check if the webhook is properly set
- Verify the bot token is correct
- Ensure the service is running (not sleeping)

## Getting Your API Keys

### 1. Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow the instructions to create your bot
4. Copy the bot token

### 2. Pixabay API Key
1. Visit [Pixabay API](https://pixabay.com/api/docs/)
2. Create a free account
3. Get your API key from the dashboard

### 3. Your Telegram User ID
1. Message @userinfobot on Telegram
2. It will reply with your user ID

## Bot Features

- **Multi-Language Support**: Arabic interface with emoji support
- **Force Subscription**: Channel subscription verification system
- **Multi-Media Search**: Photos, illustrations, vectors, videos, music, GIFs
- **Interactive Navigation**: Browse through 100 search results
- **Admin Control Panel**: Button-based admin interface
- **User Management**: Statistics tracking, ban/unban users
- **Broadcasting System**: Send messages to all users
- **Error Handling**: Robust error handling with Arabic messages

## Performance Notes

- The free tier of Render may experience cold starts
- Consider upgrading to a paid plan for production use
- Bot supports up to 100 search results per query
- Efficient media handling for all content types

## Support

If you encounter any issues during deployment:
1. Check the Render build and runtime logs
2. Verify all environment variables are correctly set
3. Ensure your API keys are valid and have proper permissions
4. Review the troubleshooting section above

## License

This project is open source and available under the MIT License.