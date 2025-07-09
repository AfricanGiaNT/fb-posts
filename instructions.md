# AI Facebook Content Generator - Instructions

## 🎯 Project Overview

This system converts Markdown documentation about automation projects into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🚧 Current Development Status

**Active Enhancement**: Multi-Post Generation with Continuity  
**Status**: 🟢 Phase 2 Complete - Ready for Phase 3  
**Tracking Document**: `content/multi_post_enhancement_plan.md`

**✅ COMPLETED - Phase 2: AI Context System**:
- **Context-Aware Generation**: AI now uses session context and previous posts for coherent, connected content
- **6 Relationship Types**: Different Aspects, Different Angles, Series Continuation, Thematic Connection, Technical Deep Dive, Sequential Story
- **Reference Generation**: Natural post-to-post references ("In my last post...", "Building on what I shared...")
- **Content Variation**: Different strategies for each relationship type to ensure variety
- **Series Continuity**: Automatic relationship type suggestions based on previous posts
- **Context-Aware Regeneration**: Maintains series coherence while applying user feedback

**🚧 IN PROGRESS - Phase 3: User Interface Enhancement**:
- Enhanced approval workflow with relationship selection
- Relationship type selection interface
- Post connection preview system
- Advanced multi-post management interface

## 🔄 System Flow

### **Current (v1.0)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable
5. **Output**: Ready-to-post Facebook content

### **Enhanced (v2.0 - Phase 2 Complete)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable with series tracking
5. **Continuation**: Choose to generate another related post
6. **Context-Aware Generation**: AI uses session context and previous posts for continuity
7. **Relationship Selection**: System suggests optimal relationship type automatically
8. **Reference Generation**: Natural cross-post references maintain narrative flow
9. **Output**: Series of related, engaging Facebook posts with natural continuity

### **Target (v2.0 - Phase 3 in Development)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable with series tracking
5. **Continuation**: Choose to generate another related post
6. **Relationship Selection**: User selects relationship type with preview
7. **Context Selection**: Choose which previous post to build upon
8. **Preview**: See how posts connect before generation
9. **Context-Aware Generation**: AI uses selected context for targeted continuity
10. **Output**: Series of strategically related, engaging Facebook posts

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