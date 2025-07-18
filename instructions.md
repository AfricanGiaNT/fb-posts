# Instructions for AI Facebook Content Generator

## Current Status
- **Phase 1**: ✅ Core Infrastructure - Enhanced sessions, Airtable schema  
- **Phase 2**: ✅ AI Context System - Context-aware prompting, enhanced AI  
- **Phase 3**: ✅ UI Enhancement - New workflows, preview system, series management  
- **Phase 4**: ✅ **COMPLETED** - Audience-aware content, Chichewa humor, content continuation  
- **Phase 5**: 🚧 **IN PROGRESS** - Multi-file upload system, Phase 5.1 and 5.2 implementation

## PHASE 5: Multi-File Upload System Enhancement - ACTIVE IMPLEMENTATION

### Current Implementation Status
**Phase 5.1**: Enhanced Session Architecture (Week 1-2) - 🚧 IN PROGRESS
**Phase 5.2**: AI Project Analysis Engine (Week 2-3) - 🚧 IN PROGRESS

### Implementation Plan for Phase 5.1 & 5.2

#### Phase 5.1: Enhanced Session Architecture
**Features to Implement**:
- Multi-file session structure with backward compatibility
- File categorization system (planning|implementation|debugging|results)
- Basic batch upload workflow with `/batch` command
- Extended timeout management (30 minutes)
- Progressive file upload feedback

**Key Components**:
- `_initialize_multi_file_session()` - Enhanced session initialization
- `_handle_document_batch_mode()` - Batch-aware file processing
- `_categorize_file()` - AI-powered file categorization
- `_check_multi_file_timeout()` - Extended timeout management
- Enhanced session structure with `mode`, `source_files`, `project_overview`

#### Phase 5.2: AI Project Analysis Engine
**Features to Implement**:
- `ProjectAnalyzer` class for intelligent file analysis
- Cross-file relationship mapping
- Project narrative extraction
- Content completeness assessment
- Theme and thread identification

**Key Components**:
- `ProjectAnalyzer.categorize_file()` - File phase detection
- `ProjectAnalyzer.analyze_project_narrative()` - Cross-file analysis
- `ProjectAnalyzer.identify_cross_file_relationships()` - Relationship mapping
- `ProjectAnalyzer.extract_narrative_threads()` - Story thread identification
- Enhanced AI prompting for project-wide analysis

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-file workflow testing
- **Backward Compatibility**: Ensure existing single-file workflow continues
- **Performance Tests**: Handle up to 8 files efficiently
- **User Experience Tests**: Intuitive batch upload process

### Success Metrics
- **File Processing Speed**: <30 seconds per file analysis
- **File Categorization**: >90% accuracy rate
- **Session Management**: 30-minute extended sessions without issues
- **Backward Compatibility**: 100% existing functionality preserved
- **User Workflow**: Intuitive batch upload process

## PHASE 5: Multi-File Upload System Enhancement

### Overview
**Vision**: Transform the current single-file system into an intelligent multi-file project narrative system that can analyze multiple development phases, suggest optimal content strategies, and generate cohesive, interlinked content series.

**Key Enhancement**: Multiple project phase files → intelligent content ecosystem with cross-file awareness and strategic content generation.

### Technical Architecture

#### Enhanced Session Structure
```python
# Multi-file session structure (backward compatible)
session = {
    'series_id': str,
    'mode': 'single|multi',               # NEW: Upload mode
    'source_files': [                     # NEW: Multiple files support
        {
            'filename': str,
            'content': str,
            'upload_timestamp': str,
            'file_phase': str,                # planning|implementation|debugging|results
            'content_summary': str,           # AI-generated summary
            'file_id': str                    # Unique identifier
        }
    ],
    'project_overview': str,              # NEW: AI-generated project summary
    'content_strategy': Dict,             # NEW: AI-suggested content strategy
    'batch_timeout': datetime,            # NEW: Extended timeout (30 min)
    'posts': [],                          # Enhanced with cross-file references
    'current_draft': None,
    'session_started': datetime,
    'last_activity': datetime,
    'session_context': str,               # Enhanced with multi-file context
    'post_count': 0,
    'state': None,
    
    # Backward compatibility for single-file mode
    'original_markdown': str,             # For single-file compatibility
    'filename': str,                      # For single-file compatibility
}
```

#### New Telegram Commands
- `/batch` - Start batch upload mode (30-minute timeout)
- `/project` - Generate project overview from uploaded files
- `/strategy` - Show/modify AI content strategy
- `/sequence` - Show/modify posting sequence
- `/generate_series` - Generate posts based on strategy
- `/files` - List uploaded files and their status

#### Content Limits
- **Maximum Files**: 8 files per batch session
- **Session Duration**: 30 minutes for multi-file mode
- **File Size**: Existing 10MB limit per file maintained

### Implementation Phases

#### Phase 5.1: Enhanced Session Architecture (Week 1-2)
**Features**:
- Multi-file session structure implementation
- File categorization system (planning, implementation, debugging, results)
- Basic multi-file upload workflow
- Project analysis engine

**Technical Components**:
- Enhanced `_initialize_session()` with multi-file support
- `ProjectAnalyzer` class for file categorization
- `_handle_document()` enhancement for batch mode
- Extended timeout management

#### Phase 5.2: Intelligent Content Strategy System (Week 2-3)
**Features**:
- AI project analysis from multiple files
- Content strategy generation and recommendation
- Cross-file relationship mapping
- Posting sequence optimization

**Technical Components**:
- `ContentStrategyGenerator` class
- Multi-file prompt engineering
- Strategy presentation interface
- User customization options

#### Phase 5.3: Cross-File Content Generation (Week 3-4)
**Features**:
- Multi-file aware AI prompting
- Explicit and subtle cross-file references
- Narrative continuity across posts
- Context-aware regeneration

**Technical Components**:
- Enhanced `_build_multi_file_prompt()` method
- Reference generation system
- Cross-file relationship analysis
- Narrative arc management

#### Phase 5.4: User Experience Enhancement (Week 4-5)
**Features**:
- Batch upload interface
- Progressive file analysis feedback
- Interactive sequence customization
- Enhanced session management

**Technical Components**:
- `_batch_upload_command()` implementation
- Real-time file analysis feedback
- Interactive sequence editor
- Session timeout optimization

#### Phase 5.5: Advanced Features (Week 5-6)
**Features**:
- Cross-file regeneration system
- Performance optimization
- Error handling enhancement
- Comprehensive testing

**Technical Components**:
- `regenerate_with_multi_file_context()` method
- Caching and optimization
- Error recovery mechanisms
- Integration testing suite

### User Workflow

#### Multi-File Upload Process
1. **Initiate Batch Mode**: User sends `/batch` command
2. **File Collection**: User uploads 2-8 dev journal files
3. **Analysis**: AI categorizes files and analyzes project narrative
4. **Strategy Generation**: AI suggests optimal content strategy
5. **Strategy Review**: User reviews and customizes strategy
6. **Content Generation**: AI generates cohesive, interlinked posts
7. **Review and Approval**: User reviews each post with full context
8. **Series Completion**: All posts saved with cross-references

#### Reference Types
- **Explicit References**: "In my previous post about X, I mentioned Y..."
- **Subtle Connections**: Thematic links and narrative continuity
- **Cross-File Insights**: Connecting insights across development phases

### Success Metrics

**Technical Metrics**:
- Support for 2-8 files per batch session
- 30-minute extended session timeout
- Cross-file context accuracy > 90%
- Reference generation success rate > 85%

**User Experience Metrics**:
- Reduced content creation time by 60%
- Improved narrative coherence scores
- User satisfaction with AI strategy suggestions
- Successful multi-file workflow completion rate > 80%

**Content Quality Metrics**:
- Cross-file reference accuracy
- Narrative arc consistency
- Audience-appropriate language maintenance
- Engagement metrics on generated posts

### Implementation Priority
🔥 **HIGHEST PRIORITY**: Multi-file session architecture and basic workflow
🟡 **MEDIUM PRIORITY**: AI strategy generation and customization
🟢 **LOW PRIORITY**: Advanced features and optimization

---

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

### Personal Project Perspective
**CRITICAL**: These are PERSONAL projects built to solve YOUR OWN problems, not services for others.

✅ **CORRECT PERSPECTIVE**:
- "I built this tool to solve my own problem with..."
- "I needed a way to handle my own..."
- "This helps me manage my own..."
- "I created this for my own use because..."

❌ **INCORRECT PERSPECTIVE**:
- "I built this for farmers to..."
- "This helps farmers with..."
- "Farmers can now..."
- "This system serves farmers by..."

### Voice Guidelines
- **First-person only**: "I built...", "I discovered...", "I learned..."
- **Never use "we"**: No "We built", "Our system", "Our solution"
- **No time references**: Never "took 3 days", "spent hours", "recently"
- **Completed achievements**: Present work as finished, not ongoing
- **Personal ownership**: Emphasize these are tools you built for yourself

### Content Tones
AI chooses from 5 brand tones:
- 🧩 **Behind-the-Build** - Matter-of-fact process sharing
- 💡 **What Broke** - Honest reflection on mistakes and fixes
- 🚀 **Finished & Proud** - Quiet satisfaction with completion
- 🎯 **Problem → Solution → Result** - Direct, practical approach
- 📓 **Mini Lesson** - Thoughtful insights from development

### Technical Specifications
- **Token Limit**: 4000 max_tokens to prevent text cutoff
- **Target Length**: 400-600 words for optimal engagement
- **Temperature**: 0.7 for creativity balance
- **Language Level**: 15-year-old reading level for business audience

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

#### **Feature 2: Pre-Generation Tone Selection** 🔥 **HIGHEST PRIORITY** (NEW)
- **Tone Selection Interface**: User selects tone before AI generation
- **Audience-Aware Recommendations**: Suggest optimal tones based on audience
- **Tone Previews**: Show example content for each tone
- **Learning System**: Track user preferences and suggest frequently used tones
- **Integration**: Combine with audience selection for optimal results

#### **Feature 3: Chichewa Humor Integration** 🟡 **MEDIUM PRIORITY**
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