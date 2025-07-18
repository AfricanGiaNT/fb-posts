# Deployment Guide - Facebook Content Generator Bot

## Overview
This guide will help you deploy your Facebook Content Generator Telegram bot to Render as a background service.

## Prerequisites
- Render account (free tier available)
- Telegram Bot Token (from @BotFather)
- OpenAI API Key
- Airtable API Key, Base ID, and Table Name

## Step 1: Prepare Your Repository
Ensure your repository contains all the necessary files:
- `render.yaml` - Render configuration
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `scripts/telegram_bot.py` - Main bot script
- `scripts/health_check.py` - Health check script

## Step 2: Connect to Render
1. Go to [render.com](https://render.com) and sign in
2. Click "New +" and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file

## Step 3: Configure Environment Variables
In the Render dashboard, set these environment variables:

### Required Variables:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `OPENAI_API_KEY` - Your OpenAI API key
- `AIRTABLE_API_KEY` - Your Airtable API key
- `AIRTABLE_BASE_ID` - Your Airtable base ID
- `AIRTABLE_TABLE_NAME` - Your Airtable table name

### Optional Variables:
- `LOG_LEVEL` - Set to "INFO" or "DEBUG" for logging
- `PYTHON_VERSION` - Set to "3.9.16" (default)

## Step 4: Deploy
1. Click "Create New Service"
2. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Build the Docker container
   - Start the bot using `python scripts/telegram_bot.py`

## Step 5: Verify Deployment
1. Check the logs in Render dashboard
2. Look for "Starting Facebook Content Generator Bot..." message
3. Test your bot on Telegram by sending `/start`

## Monitoring and Maintenance

### Health Checks
The bot includes a health check script that validates:
- Environment variables are set
- Configuration can be loaded
- All required services are accessible

### Logs
Monitor logs in the Render dashboard for:
- Bot startup messages
- Error messages
- User interactions

### Scaling
- Free tier: 1 instance, sleeps after 15 minutes of inactivity
- Paid tier: Always-on instances with custom scaling

## Troubleshooting

### Common Issues:

1. **Bot not responding**
   - Check if the service is running in Render dashboard
   - Verify TELEGRAM_BOT_TOKEN is correct
   - Check logs for error messages

2. **Import errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

3. **Environment variable issues**
   - Verify all required variables are set in Render
   - Check variable names match exactly

4. **Airtable connection issues**
   - Verify AIRTABLE_API_KEY, BASE_ID, and TABLE_NAME
   - Check Airtable permissions

### Debug Mode
To enable debug logging, set `LOG_LEVEL=DEBUG` in environment variables.

## Security Notes
- Never commit API keys to your repository
- Use Render's environment variable system
- The Dockerfile runs as a non-root user for security
- All sensitive data is stored in environment variables

## Cost Optimization
- Free tier: $0/month (sleeps after inactivity)
- Paid tier: $7/month for always-on service
- Monitor usage in Render dashboard

## Support
If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test locally before deploying
4. Check Telegram bot token validity 