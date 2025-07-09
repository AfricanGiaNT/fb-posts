# AI Facebook Content Generator - Instructions

## 🎯 Project Overview

This system converts Markdown documentation about automation projects into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🚧 Current Development Status

**Active Enhancement**: Multi-Post Generation with Continuity  
**Status**: 🟡 Planning Phase  
**Tracking Document**: `content/multi_post_enhancement_plan.md`

**New Features in Development**:
- Generate multiple related posts from one markdown file
- 6 different relationship types (aspects, angles, series, themes, technical, story)
- Post continuity with natural references
- User-controlled post relationships
- Enhanced session management
- Connection previews

## 🔄 System Flow

### **Current (v1.0)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable
5. **Output**: Ready-to-post Facebook content

### **Enhanced (v2.0 - In Development)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable
5. **Continuation**: Choose to generate another related post
6. **Relationship**: Select how new post relates to previous posts
7. **Context**: AI uses session context for continuity
8. **Output**: Series of related, engaging Facebook posts

## 🎙️ Brand Tone Styles

1. **🧩 Behind-the-Build** - "Built this with Cursor AI..."
2. **💡 What Broke** - "I broke something I built. And I loved it."
3. **🚀 Finished & Proud** - "Just shipped this automation..."
4. **🎯 Problem → Solution → Result** - Clear pain point resolution
5. **📓 Mini Lesson** - Philosophical automation insights

## 🔗 New Relationship Types (v2.0)

1. **🔍 Different Aspects** - Focus on different sections/features
2. **📐 Different Angles** - Technical vs. business vs. personal perspective
3. **📚 Series Continuation** - Sequential parts (Part 1, 2, 3...)
4. **🔗 Thematic Connection** - Related philosophy/principles
5. **🔧 Technical Deep Dive** - Detailed technical explanation
6. **📖 Sequential Story** - "What happened next" narrative

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
5. **(v2.0)** Choose to generate another related post
6. **(v2.0)** Select relationship type and previous post to build on
7. Check Airtable for approved content

## 📁 Project Structure

```
/scripts/           # Core logic and automation
/config/           # Configuration files
/rules/            # AI behavior and tone rules
/content/          # Input/output content and project tracking
/docs/             # Documentation
```

## 🔧 Commands

- `/start` - Initialize bot
- `/help` - Show help message
- `/status` - Check system status
- Send .md file - Process markdown content

## 🔄 Development Timeline

**Phase 1 (Week 1)**: Core Infrastructure - Enhanced sessions, Airtable schema  
**Phase 2 (Week 1-2)**: AI Context System - Context-aware prompting, enhanced AI  
**Phase 3 (Week 2)**: UI Enhancement - New workflows, preview system  
**Phase 4 (Week 2-3)**: Advanced Features - Strategy engine, analytics  

## 📊 Progress Tracking

See `content/multi_post_enhancement_plan.md` for detailed progress tracking, technical implementation details, and development notes. 