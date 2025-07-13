# AI Facebook Content Generator - Instructions

## 🎯 Project Overview

This system converts Markdown documentation about automation projects into engaging Facebook posts using AI, delivered through a Telegram bot interface.

## 🚧 Current Development Status

**Active Enhancement**: Phase 4 - Audience-Aware Content Generation  
**Status**: 🔄 **IMPLEMENTING WEEK 1**  
**Timeline**: January 2025 - Week 1 (Days 1-5)

## 📋 Phase 4 Week 1 Implementation Plan

### **🎯 Goal**: Make content accessible to business owners (not just developers)

### **Target Audience**: "Nthambi the hustla" 
- Business owner/operator (25-45 years old)
- Needs simple, practical language
- Wants business impact, not technical jargon
- Uses mobile-first communication

### **Week 1 Implementation Schedule**

#### **Day 1-2: Audience Selection System**
**Status**: ✅ **COMPLETED**

**Technical Implementation**:
- ✅ Added audience selection to Telegram bot interface
- ✅ Created audience selection inline keyboard
- ✅ Modified session management to store audience preference
- ✅ Added callback handlers for audience selection

**Code Changes**:
- ✅ `scripts/telegram_bot.py`: Added audience selection UI and handlers
- ✅ `scripts/ai_content_generator.py`: Implemented audience-aware prompts
- ✅ Session storage: Added `audience_type` field
- ✅ Callback handlers: `audience_business`, `audience_technical` working

**User Experience**:
1. ✅ Upload markdown file
2. ✅ Select audience: "🏢 Business Owner" or "💻 Technical"
3. ✅ AI generates appropriate content
4. ✅ Review and approve as normal

**Test Results**:
- ✅ Business audience generation: WORKING
- ✅ Technical audience generation: WORKING  
- ✅ Default (no audience) generation: WORKING
- ✅ Audience type metadata stored: WORKING
- ✅ All instruction methods validated: WORKING

**Content Quality Examples**:
- **Business**: "Hey fellow entrepreneurs! 📣 I've just tackled a big hurdle that many of us face: churning out consistent and engaging content..."
- **Technical**: "🚀 Just shipped a Telegram bot that transforms markdown files into engaging Facebook posts with the power of AI! Here's how I brought it to life: 🔧 **Tech Stack:** - **Python** with async/await patterns..."

**Achievement**: Successfully created audience-aware content generation that makes technical content accessible to business owners while maintaining technical depth for developers.

#### **Day 3-4: Content Adaptation Prompts**
**Status**: 📋 **PLANNED**

**Business-Friendly Prompt System**:
- Create separate prompt templates for business audience
- Modify AI content generator to use audience-specific prompts
- Replace technical jargon with relatable business language
- Focus on business impact: time saved, money made, problems solved

**Content Adaptation Examples**:
```
BEFORE (Technical): "Implemented API integration with webhook endpoints"
AFTER (Business): "Connected my apps so they talk to each other automatically"

BEFORE (Technical): "Optimized database queries for better performance"  
AFTER (Business): "Made my system faster - now customers don't wait"
```

#### **Day 5: Testing & Refinement**
**Status**: 📋 **PLANNED**

**Testing Strategy**:
- Generate posts for both audiences using same markdown
- Compare technical vs business-friendly language
- Refine prompts based on results
- Document changes and usage patterns

**Success Metrics**:
- Business content is understandable to non-technical users
- Technical content remains unchanged
- Audience selection flow works smoothly
- Content quality maintained for both audiences

### **Implementation Architecture**

```python
# Session Structure (Enhanced)
session = {
    'audience_type': 'business|technical',  # NEW
    'series_id': str,
    'original_markdown': str,
    'posts': [],
    'current_draft': None,
    # ... existing fields
}

# Audience Types
AUDIENCE_TYPES = {
    'business': 'Business Owner/General',
    'technical': 'Developer/Technical'
}
```

### **Alternative Approaches Considered**:
1. **Chosen**: AI prompt modification for different audiences
2. **Alternative**: Separate AI models (more complex, unnecessary)
3. **Chosen**: Simple audience selection UI
4. **Alternative**: Detailed persona questionnaire (too complex)

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
3. **NEW**: Select target audience (Business Owner or Technical)
4. Review generated draft
5. Approve/reject/regenerate as needed
6. **(v2.0)** Choose to generate another related post
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

## 📋 Phase 4 Feature Enhancement Plan

### **NEW FEATURES - Phase 4 Implementation**
**Timeline**: Week 3-4  
**Status**: 🚧 **PLANNING & DESIGN**

#### **Feature 1: Multi-Language & Audience Support**
- **Customer-Focused Language**: Generate simpler English for customer-facing content
- **Chichewa Integration**: Add relevant Chichewa words and phrases for local audience
- **Audience Type Selection**: Choose between "Developer/Technical" vs "Customer/General" audience
- **Language Blending**: Natural integration of local language elements

#### **Feature 2: Content Continuation & Revival**
- **Post Resurrection**: Input previously generated posts to create follow-ups
- **Content Analysis**: AI analyzes existing content to suggest continuation strategies
- **Cross-Session Context**: Retrieve and reference posts from previous sessions
- **Content Evolution**: Transform existing posts into new perspectives

#### **Feature 3: Airtable AI Development Context**
- **Tool Integration**: Add "built with Airtable AI" context to all generations
- **Development Story**: Incorporate Airtable AI as primary development tool
- **Process Highlighting**: Emphasize AI-powered development workflow
- **Tool Crediting**: Natural mentions of Airtable AI in content

#### **Feature 4: Multi-Platform Content Generation**
- **Platform Variants**: Generate Facebook and Twitter versions from same content
- **Platform Optimization**: Adapt content for platform-specific best practices
- **Cross-Platform Series**: Maintain narrative consistency across platforms
- **Platform-Specific Tones**: Adjust tone and length for each platform

#### **Feature 5: Historical Context & Retrieval**
- **Post Database**: Searchable database of all generated posts
- **Topic Clustering**: Group posts by project/topic for context retrieval
- **Smart Suggestions**: AI suggests relevant previous posts for new content
- **Context Inheritance**: Use historical posts as context for new generations

### **Implementation Strategy**

#### **Week 3: Core Feature Development**
- **Days 1-2**: Multi-language support with audience selection
- **Days 3-4**: Content continuation and post revival features
- **Day 5**: Airtable AI context integration

#### **Week 4: Platform & Historical Features**
- **Days 1-2**: Multi-platform content generation (Facebook + Twitter)
- **Days 3-4**: Historical context retrieval and post database
- **Day 5**: Integration testing and user experience refinement

### **Technical Architecture - Phase 4**

#### **New Components**
- **Language Manager**: Handle English simplification and Chichewa integration
- **Content Revival System**: Process existing posts for continuation
- **Platform Adapter**: Generate platform-specific content variants
- **Historical Context Engine**: Search and retrieve relevant previous posts
- **Audience Selector**: Choose target audience for appropriate language level

#### **Enhanced AI Prompts**
- **Audience-Aware Prompts**: Adjust complexity based on target audience
- **Language Integration**: Natural Chichewa phrase incorporation
- **Platform-Specific Instructions**: Optimize for Facebook vs Twitter
- **Historical Context Integration**: Reference relevant previous posts

#### **Database Enhancements**
- **Post Archival**: Long-term storage of all generated content
- **Topic Tagging**: Automatic categorization of posts by project/topic
- **Search Indexing**: Fast retrieval of relevant historical posts
- **Cross-Platform Linking**: Track content variants across platforms

### **REVISED - Phase 4 Simplified Enhancement**
**Timeline**: 2 Weeks  
**Status**: 📋 **PLANNING COMPLETE**

**Key Insight**: Focus on "Nthambi the hustla" - busy business operators who want practical content, not technical deep dives.

#### **Feature 1: Audience-Aware Content Generation** 🔥 **HIGHEST PRIORITY**
- **Audience Selection**: "Business Owner/General" vs "Developer/Technical" 
- **Language Adaptation**: Simple, clear language for business owners
- **Jargon Avoidance**: Replace technical terms with relatable examples
- **Business Impact Focus**: Time saved, money made, problems solved

#### **Feature 2: Chichewa Humor Integration** 🟡 **MEDIUM PRIORITY**
- **Natural Integration**: Phrases that enhance, don't complicate
- **Contextual Usage**: Different phrases for different situations  
- **Cultural Sensitivity**: Appropriate usage with context
- **Humor Addition**: Add personality without confusion

#### **Feature 3: Content Continuation** 🟢 **MEDIUM PRIORITY**
- **Input Method**: `/continue` command + paste existing post text
- **Analysis**: AI identifies continuation opportunities
- **Natural References**: "In my last post...", "Building on what I shared..."
- **Value Addition**: New perspective, not just repetition

#### **Simplified Implementation Strategy**
- **Week 1**: Audience selection system + business-friendly content adaptation
- **Week 2**: Chichewa phrase integration + content continuation feature
- **Focus**: Practical value over complex features

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
**Phase 4 (Week 3-4)**: 📋 **SIMPLIFIED FEATURES** - Audience-aware content, Chichewa humor, content continuation  

## 📊 Progress Tracking

**Active Reference Documents:**
- `content/multi_post_enhancement_plan.md` - Overall project progress and technical details
- `content/phase_3_ui_enhancement_plan.md` - Detailed Phase 3 implementation plan and tracking
- `content/phase_4_simplified_plan.md` - **UPDATED** - Focused Phase 4 features for business audience

**Current Status**: Phase 3 in progress, Phase 4 simplified planning complete with focus on business owner audience and practical features. 