# AI Facebook Content Generator - Instructions

## 🎯 Project Overview

This system converts Markdown documentation about automation projects into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🚧 Current Development Status

**Active Enhancement**: Multi-Post Generation with Continuity  
**Status**: 🟡 Phase 3 Planning Complete - Ready for Implementation  
**Tracking Document**: `content/multi_post_enhancement_plan.md`  
**Phase 3 Reference**: `content/phase_3_ui_enhancement_plan.md`

**✅ COMPLETED - Phase 2: AI Context System**:
- **Context-Aware Generation**: AI now uses session context and previous posts for coherent, connected content
- **6 Relationship Types**: Different Aspects, Different Angles, Series Continuation, Thematic Connection, Technical Deep Dive, Sequential Story
- **Reference Generation**: Natural post-to-post references ("In my last post...", "Building on what I shared...")
- **Content Variation**: Different strategies for each relationship type to ensure variety
- **Series Continuity**: Automatic relationship type suggestions based on previous posts
- **Context-Aware Regeneration**: Maintains series coherence while applying user feedback

**📋 PLANNED - Phase 3: User Interface Enhancement**:
- **Enhanced Post-Approval Workflow**: Relationship selection interface after post approval
- **Previous Post Selection**: User can choose which previous post to build upon
- **Series Management Dashboard**: View, edit, and manage entire post series
- **Connection Previews**: Simple text previews showing how posts connect
- **Progressive Enhancement**: Smart defaults with expert-level control options

## 🔄 System Flow

### **Current (v2.0 - Phase 2)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable with series tracking
5. **Continuation**: Choose to generate another related post
6. **Context-Aware Generation**: AI uses session context and previous posts for continuity
7. **Relationship Selection**: System suggests optimal relationship type automatically
8. **Reference Generation**: Natural cross-post references maintain narrative flow
9. **Output**: Series of related, engaging Facebook posts with natural continuity

### **Target (v2.0 - Phase 3 Implementation)**
1. **Input**: Send markdown file to Telegram bot
2. **Processing**: AI analyzes content using 5 brand tone styles
3. **Review**: Interactive approval/rejection via Telegram
4. **Storage**: Approved drafts saved to Airtable with series tracking
5. **Enhanced Continuation**: "Generate another post?" with relationship type selection
6. **Relationship Selection**: Manual selection from 6 types with descriptions and smart defaults
7. **Previous Post Selection**: Choose which previous post to build upon with post previews
8. **Connection Preview**: See how posts connect before generation ("This post continues from...")
9. **Context-Aware Generation**: AI uses selected context for targeted continuity
10. **Series Management**: View, edit, regenerate, and export entire post series
11. **Output**: Strategically connected, user-controlled Facebook post series

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

## 📋 Phase 3 Implementation Plan

### **Week 1: Core Workflow Enhancement**
- **Days 1-2**: Relationship selection interface with 6 types + "AI Decide" option
- **Days 3-4**: Previous post selection with post previews and smart defaults
- **Day 5**: Simple connection previews ("This post continues from...")

### **Week 2: Series Management**
- **Days 1-2**: Series dashboard with `/series` command and visual overview
- **Days 3-4**: Post management actions (edit, regenerate, delete, export)
- **Day 5**: Testing, refinement, and documentation

### **Technical Architecture**
- **UI Pattern**: Progressive enhancement with smart defaults
- **Enhanced Session State**: Workflow state tracking and pending generation data
- **Series Metadata**: Post count, relationship types used, connection strength
- **Connection Previews**: Simple text format with relationship badges

## 📁 Project Structure

```
/scripts/           # Core logic and automation
/config/           # Configuration files
/rules/            # AI behavior and tone rules
/content/          # Input/output content and project tracking
  ├── phase_3_ui_enhancement_plan.md  # Phase 3 detailed implementation plan
  └── multi_post_enhancement_plan.md  # Overall project tracking
/docs/             # Documentation
```

## 🔧 Commands

- `/start` - Initialize bot
- `/help` - Show help message
- `/status` - Check system status
- `/series` - View current post series (Phase 3)
- Send .md file - Process markdown content

## 🔄 Development Timeline

**Phase 1 (Week 1)**: ✅ Core Infrastructure - Enhanced sessions, Airtable schema  
**Phase 2 (Week 1-2)**: ✅ AI Context System - Context-aware prompting, enhanced AI  
**Phase 3 (Week 2)**: 🚧 UI Enhancement - New workflows, preview system, series management  
**Phase 4 (Week 2-3)**: ⏳ Advanced Features - Strategy engine, analytics  

## 📊 Progress Tracking

**Active Reference Documents:**
- `content/multi_post_enhancement_plan.md` - Overall project progress and technical details
- `content/phase_3_ui_enhancement_plan.md` - Detailed Phase 3 implementation plan and tracking

**Current Status**: Phase 3 planning complete - ready for implementation with detailed technical specifications and user experience flows. 