# AI Facebook Content Generator - Instructions

## 🎯 Project Overview

This system converts Markdown documentation about automation projects into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🔄 System Flow

1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable
5. **Output**: Ready-to-post Facebook content

## 🎙️ Brand Tone Styles

1. **🧩 Behind-the-Build** - "Built this with Cursor AI..."
2. **💡 What Broke** - "I broke something I built. And I loved it."
3. **🚀 Finished & Proud** - "Just shipped this automation..."
4. **🎯 Problem → Solution → Result** - Clear pain point resolution
5. **📓 Mini Lesson** - Philosophical automation insights

## 📋 Setup Requirements

### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o
- `AIRTABLE_API_KEY`: Airtable personal access token
- `AIRTABLE_BASE_ID`: Your Airtable base ID
- `AIRTABLE_TABLE_NAME`: Content Tracker table name

### Dependencies
- python-telegram-bot
- openai
- airtable-python-wrapper
- python-dotenv

## 🚀 Usage

1. Start the bot: `python scripts/telegram_bot.py`
2. Send markdown file to bot
3. Review generated draft
4. Approve/reject/regenerate as needed
5. Check Airtable for approved content

## 📁 Project Structure

```
/scripts/           # Core logic and automation
/config/           # Configuration files
/rules/            # AI behavior and tone rules
/content/          # Input/output content
/docs/             # Documentation
```

## 🔧 Commands

- `/start` - Initialize bot
- `/help` - Show help message
- `/status` - Check system status
- Send .md file - Process markdown content 