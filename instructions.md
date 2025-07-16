# Instructions for AI Facebook Content Generator

## Current Status
- **Phase 1**: ✅ Core Infrastructure - Enhanced sessions, Airtable schema  
- **Phase 2**: ✅ AI Context System - Context-aware prompting, enhanced AI  
- **Phase 3**: ✅ UI Enhancement - New workflows, preview system, series management  
- **Phase 4**: 📋 **SIMPLIFIED FEATURES** - Audience-aware content, Chichewa humor, content continuation  

## File Format Requirements

### Developer Journal Files
- **Location**: `content/dev_journal/`
- **Format**: `milestone-name-001.md` (sequential numbering, no dates)
- **Content**: Development milestones and achievements
- **Guidelines**:
  - No time references or duration mentions
  - Focus on Problem → Solution → Result narrative
  - Present completed work, not ongoing projects
  - Use milestone-first naming: `implement-feature-001.md`, `fix-bug-001.md`

### Content Structure
Files should follow the `.mdc` format guidelines:
- `## What I Built` - Clear summary of the feature/fix
- `## The Problem` - Specific pain point addressed
- `## My Solution` - How the problem was solved
- `## How It Works: The Technical Details` - Technical implementation
- `## The Impact / Result` - Quantified outcomes
- `## Key Lessons Learned` - Insights and takeaways

**Important**: All content should avoid time references and focus on the achievement itself.

## AI Content Generation

### Content Processing
The AI system processes developer journal entries with these key instructions:
- Files follow `milestone-name-001.md` format (sequential, no dates)
- Content represents completed work without time references
- Focus on Problem → Solution → Result narrative
- Present work as finished accomplishments

### Voice Guidelines
- **First-person only**: "I built...", "I discovered...", "I learned..."
- **Never use "we"**: No "We built", "Our system", "Our solution"
- **No time references**: Never "took 3 days", "spent hours", "recently"
- **Completed achievements**: Present work as finished, not ongoing

### Content Tones
AI chooses from 5 brand tones:
- 🧩 **Behind-the-Build** - Matter-of-fact process sharing
- 💡 **What Broke** - Honest reflection on mistakes and fixes
- 🚀 **Finished & Proud** - Quiet satisfaction with completion
- 🎯 **Problem → Solution → Result** - Direct, practical approach
- 📓 **Mini Lesson** - Thoughtful insights from development

## 🎯 **Enhanced AI System Features**

### **Phase 1: Core Infrastructure** ✅ **COMPLETED**
- Enhanced session management with post tracking
- Improved Airtable schema for better data organization
- Multi-post series support with relationship tracking

### **Phase 2: AI Context System** ✅ **COMPLETED**
- Context-aware prompting for consistent series generation
- Enhanced AI response parsing and error handling
- Relationship-based content variation (different aspects, angles, continuations)

### **Phase 3: UI Enhancement** ✅ **COMPLETED**
- New Telegram bot workflows for improved user experience
- Enhanced preview system with better formatting
- Series management commands (`/series`, `/status`)
- Improved help system and status tracking

### **Phase 4: Simplified Enhancement** 📋 **PLANNING**
**Timeline**: 2 Weeks  
**Status**: 📋 **PLANNING COMPLETE**

**Key Focus**: "Nthambi the hustla" - busy business operators who want practical content, not technical deep dives.

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
  ├── dev_journal/               # Developer journal entries (milestone-name-001.md)
  ├── generated_drafts/          # AI-generated Facebook post drafts
  ├── reviewed_drafts/           # Final edited versions post-review
  └── markdown_logs/             # Legacy markdown content
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
**Phase 3 (Week 2)**: ✅ UI Enhancement - New workflows, preview system, series management  
**Phase 4 (Week 3-4)**: 📋 **SIMPLIFIED FEATURES** - Audience-aware content, Chichewa humor, content continuation  

## 📊 Progress Tracking

**Active Reference Documents:**
- `content/multi_post_enhancement_plan.md` - Overall project progress and technical details
- `content/phase_3_ui_enhancement_plan.md` - Detailed Phase 3 implementation plan and tracking
- `content/phase_4_simplified_plan.md` - **UPDATED** - Focused Phase 4 features for business audience

**Current Status**: Phase 3 complete, Phase 4 simplified planning complete with focus on business owner audience and practical features.

## File Naming Updates

**Previous Format**: `milestone-name_YYYY-MM-DD.md`
**New Format**: `milestone-name-001.md`

All existing files have been renamed to the new sequential format. The AI system has been updated to:
- Understand the new file naming convention
- Process content without time references
- Focus on completed achievements and their impact
- Present work as finished accomplishments

**Benefits of New Format**:
- Eliminates misleading time implications
- Focuses on achievement rather than duration
- Simplifies file management and scanning
- Avoids false impression of development speed 