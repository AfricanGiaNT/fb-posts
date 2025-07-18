"""
Enhanced Telegram Bot with Multi-File Upload Support (Phase 5.1)
Extends the existing bot with batch upload capabilities while maintaining backward compatibility
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
import asyncio
import uuid
from typing import Dict, Optional, List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from airtable_connector import AirtableConnector
from project_analyzer import ProjectAnalyzer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedFacebookContentBot:
    """Enhanced bot with multi-file upload capabilities."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.ai_generator = AIContentGenerator(self.config)
        self.airtable = AirtableConnector(self.config)
        self.project_analyzer = ProjectAnalyzer(self.config)
        
        # User session storage (in production, use Redis or database)
        self.user_sessions: Dict[int, Dict] = {}
        
        # Initialize the bot application
        self.application = Application.builder().token(self.config.telegram_bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("series", self._series_command))
        self.application.add_handler(CommandHandler("continue", self._continue_command))
        
        # NEW: Multi-file commands
        self.application.add_handler(CommandHandler("batch", self._batch_command))
        self.application.add_handler(CommandHandler("project", self._project_command))
        self.application.add_handler(CommandHandler("strategy", self._strategy_command))
        self.application.add_handler(CommandHandler("files", self._files_command))
        self.application.add_handler(CommandHandler("done", self._done_command))
        self.application.add_handler(CommandHandler("cancel", self._cancel_command))
        
        # Document/file handler
        self.application.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Text message handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
    
    def _initialize_session(self, user_id: int, markdown_content: str, filename: str) -> Dict:
        """Initialize a new single-file session (backward compatibility)."""
        series_id = str(uuid.uuid4())
        
        session = {
            'series_id': series_id,
            'mode': 'single',  # NEW: Upload mode
            'original_markdown': markdown_content,
            'filename': filename,
            'posts': [],  # List of approved posts in this series
            'current_draft': None,  # Current post being reviewed
            'session_started': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'session_context': '',  # AI context summary for continuity
            'post_count': 0,
            'state': None,  # To manage multi-step commands like /continue
            
            # NEW: Multi-file support (empty for single-file mode)
            'source_files': [],
            'project_overview': {},
            'content_strategy': {},
            'user_customizations': {},
            'batch_timeout': None,
            'workflow_state': 'single_file'
        }
        
        self.user_sessions[user_id] = session
        return session
    
    def _initialize_multi_file_session(self, user_id: int) -> Dict:
        """Initialize a new multi-file session."""
        series_id = str(uuid.uuid4())
        
        session = {
            'series_id': series_id,
            'mode': 'multi',  # NEW: Upload mode
            'source_files': [],  # NEW: Multiple files support
            'project_overview': {},  # NEW: Project analysis
            'content_strategy': {},  # NEW: AI-generated strategy
            'user_customizations': {},  # NEW: User modifications
            'batch_timeout': datetime.now() + timedelta(minutes=30),  # NEW: Extended timeout
            'workflow_state': 'collecting_files',  # NEW: Workflow state
            'posts': [],  # Enhanced with cross-file references
            'current_draft': None,
            'session_started': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'session_context': '',  # Enhanced multi-file context
            'post_count': 0,
            'state': None,
            
            # Backward compatibility for single-file mode
            'original_markdown': '',
            'filename': ''
        }
        
        self.user_sessions[user_id] = session
        return session
    
    def _check_multi_file_timeout(self, user_id: int) -> bool:
        """Check timeout with extended rules for multi-file."""
        if user_id not in self.user_sessions:
            return True
        
        session = self.user_sessions[user_id]
        
        # Different timeout rules for different modes
        if session.get('mode') == 'multi':
            timeout = session.get('batch_timeout')
            if timeout and datetime.now() > timeout:
                return True
        else:
            # Standard timeout for single-file mode
            try:
                last_activity = datetime.fromisoformat(session.get('last_activity', datetime.now().isoformat()))
                if datetime.now() - last_activity > timedelta(minutes=15):
                    return True
            except (ValueError, TypeError):
                # If timestamp is invalid, consider it expired
                return True
        
        return False
    
    def _categorize_file(self, content: str, filename: str) -> str:
        """Categorize file into project phase using AI."""
        try:
            file_analysis = self.project_analyzer.categorize_file(content, filename)
            return file_analysis['file_phase']
        except Exception as e:
            logger.error(f"Error categorizing file: {e}")
            return 'implementation'  # Default fallback
    
    # NEW: Multi-file command handlers
    
    async def _batch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start batch upload mode for multiple dev_journal files."""
        user_id = update.effective_user.id
        
        # Initialize multi-file session
        session = self._initialize_multi_file_session(user_id)
        
        await update.message.reply_text(
            "📚 **Multi-File Project Mode Activated**\n\n"
            "Upload your dev journal files one by one (max 8 files).\n"
            "I'll analyze the complete project story and suggest an optimal content strategy.\n\n"
            "**Upload Process:**\n"
            "1. Send files (different project phases work best)\n"
            "2. I'll categorize and analyze each file\n"
            "3. Generate project overview and content strategy\n"
            "4. Create cohesive, interlinked posts\n\n"
            "**Commands:**\n"
            "• Send .md files one by one\n"
            "• `/project` - Generate project overview\n"
            "• `/strategy` - Show content strategy\n"
            "• `/done` - Finish uploading and proceed\n"
            "• `/cancel` - Exit batch mode\n\n"
            "⏰ **30-minute upload window**",
            parse_mode='Markdown'
        )
    
    async def _project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate project overview from uploaded files."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ No active session. Use `/batch` to start.")
            return
        
        session = self.user_sessions[user_id]
        
        if session.get('mode') != 'multi':
            await update.message.reply_text("❌ Not in multi-file mode. Use `/batch` to start.")
            return
        
        source_files = session.get('source_files', [])
        if len(source_files) < 2:
            await update.message.reply_text("❌ Need at least 2 files for project analysis.")
            return
        
        # Generate project analysis
        processing_msg = await update.message.reply_text("🔄 **Analyzing project...**\n\n⏳ Generating comprehensive project overview...")
        
        try:
            project_analysis = await asyncio.to_thread(
                self.project_analyzer.analyze_project_narrative,
                source_files
            )
            
            session['project_overview'] = project_analysis
            session['workflow_state'] = 'project_analyzed'
            
            await processing_msg.delete()
            
            # Display project analysis
            analysis_text = f"""🎯 **Project Analysis Complete**

**Project Theme:** {project_analysis['project_theme']}
**Narrative Arc:** {project_analysis['narrative_arc']}
**Files Analyzed:** {project_analysis['files_analyzed']} files

**Key Challenges Identified:**
{chr(10).join(f"• {challenge}" for challenge in project_analysis['key_challenges'][:5])}

**Solutions Implemented:**
{chr(10).join(f"• {solution}" for solution in project_analysis['solutions_implemented'][:5])}

**Technical Stack:**
{chr(10).join(f"• {tech}" for tech in project_analysis['technical_stack'][:8])}

**Business Outcomes:**
{chr(10).join(f"• {outcome}" for outcome in project_analysis['business_outcomes'][:5])}

**Estimated Posts:** {project_analysis['estimated_posts']}
**Completeness Score:** {project_analysis['completeness_score']:.1%}

Ready to generate content strategy? Use `/strategy`"""
            
            await update.message.reply_text(analysis_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating project analysis: {e}")
            await processing_msg.edit_text(f"❌ Error analyzing project: {str(e)}")
    
    async def _strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show content strategy based on project analysis."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ No active session. Use `/batch` to start.")
            return
        
        session = self.user_sessions[user_id]
        
        if session.get('mode') != 'multi':
            await update.message.reply_text("❌ Not in multi-file mode. Use `/batch` to start.")
            return
        
        project_overview = session.get('project_overview', {})
        if not project_overview:
            await update.message.reply_text("❌ No project analysis available. Use `/project` first.")
            return
        
        # Generate content strategy
        processing_msg = await update.message.reply_text("📋 **Generating content strategy...**\n\n⏳ Creating optimal posting sequence...")
        
        try:
            # Simple strategy generation (Phase 5.2 will enhance this)
            source_files = session.get('source_files', [])
            
            # Basic sequence based on file phases
            phase_order = ['planning', 'implementation', 'debugging', 'results']
            sorted_files = sorted(source_files, 
                                key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
            
            recommended_sequence = []
            for i, file in enumerate(sorted_files, 1):
                recommended_sequence.append({
                    'position': i,
                    'filename': file['filename'],
                    'phase': file['file_phase'],
                    'recommended_tone': self._suggest_tone_for_phase(file['file_phase']),
                    'estimated_engagement': 'High' if file['file_phase'] in ['implementation', 'results'] else 'Medium'
                })
            
            content_strategy = {
                'recommended_sequence': recommended_sequence,
                'estimated_posts': len(sorted_files),
                'narrative_flow': project_overview.get('narrative_arc', 'Sequential development'),
                'cross_references': self._generate_basic_cross_references(sorted_files),
                'audience_split': {'business': 60, 'technical': 40}
            }
            
            session['content_strategy'] = content_strategy
            session['workflow_state'] = 'strategy_generated'
            
            await processing_msg.delete()
            
            # Display strategy
            strategy_text = f"""📋 **Content Strategy Recommendation**

**Project:** {project_overview.get('project_theme', 'Development Project')}
**Estimated Posts:** {content_strategy['estimated_posts']} posts
**Narrative Flow:** {content_strategy['narrative_flow']}

**Recommended Sequence:**
{chr(10).join(f"{i}. {item['filename']} - {item['phase']} - {item['recommended_tone']}" 
              for i, item in enumerate(content_strategy['recommended_sequence'], 1))}

**Cross-References:**
{chr(10).join(f"• {ref['description']}" for ref in content_strategy['cross_references'][:3])}

**Audience Split:**
• Business: {content_strategy['audience_split']['business']}%
• Technical: {content_strategy['audience_split']['technical']}%

**Choose your approach:**
✅ Use AI Strategy - Generate posts with this sequence
📋 Manual Selection - Choose specific files
❌ Cancel - Exit batch mode"""
            
            # Add action buttons
            keyboard = [
                [InlineKeyboardButton("✅ Use AI Strategy", callback_data="use_ai_strategy")],
                [InlineKeyboardButton("📋 Manual Selection", callback_data="manual_selection")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(strategy_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error generating content strategy: {e}")
            await processing_msg.edit_text(f"❌ Error generating strategy: {str(e)}")
    
    async def _files_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List uploaded files and their status."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ No active session. Use `/batch` to start.")
            return
        
        session = self.user_sessions[user_id]
        
        if session.get('mode') != 'multi':
            await update.message.reply_text("❌ Not in multi-file mode. Use `/batch` to start.")
            return
        
        source_files = session.get('source_files', [])
        if not source_files:
            await update.message.reply_text("📁 No files uploaded yet. Send .md files to start.")
            return
        
        # Generate files list
        files_text = f"📁 **Uploaded Files ({len(source_files)}/8)**\n\n"
        
        for i, file in enumerate(source_files, 1):
            status_emoji = "✅" if file.get('processing_status') == 'analyzed' else "⏳"
            files_text += f"{status_emoji} **{file['filename']}**\n"
            files_text += f"   Phase: {file.get('file_phase', 'Unknown').title()} | Words: {file.get('word_count', 0):,}\n"
            
            themes = file.get('key_themes', [])
            if themes:
                files_text += f"   Themes: {', '.join(themes[:3])}\n"
            
            files_text += f"   Status: {file.get('processing_status', 'Unknown').title()}\n\n"
        
        # Add timeout info
        batch_timeout = session.get('batch_timeout')
        if batch_timeout:
            time_left = batch_timeout - datetime.now()
            minutes_left = int(time_left.total_seconds() / 60)
            files_text += f"⏰ Time remaining: {minutes_left} minutes\n\n"
        
        files_text += "Continue uploading or use `/strategy` to proceed"
        
        await update.message.reply_text(files_text, parse_mode='Markdown')
    
    async def _done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Finish uploading and proceed to strategy."""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ No active session. Use `/batch` to start.")
            return
        
        session = self.user_sessions[user_id]
        
        if session.get('mode') != 'multi':
            await update.message.reply_text("❌ Not in multi-file mode. Use `/batch` to start.")
            return
        
        source_files = session.get('source_files', [])
        if len(source_files) < 2:
            await update.message.reply_text("❌ Need at least 2 files for multi-file processing.")
            return
        
        session['workflow_state'] = 'upload_complete'
        
        await update.message.reply_text(
            f"✅ **Upload Complete!**\n\n"
            f"📁 Files uploaded: {len(source_files)}\n"
            f"🎯 Ready for project analysis\n\n"
            f"**Next steps:**\n"
            f"• `/project` - Generate project overview\n"
            f"• `/strategy` - Show content strategy\n"
            f"• `/files` - Review uploaded files",
            parse_mode='Markdown'
        )
    
    async def _cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel batch mode and clear session."""
        user_id = update.effective_user.id
        
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            files_count = len(session.get('source_files', []))
            del self.user_sessions[user_id]
            
            await update.message.reply_text(
                f"❌ **Batch mode canceled**\n\n"
                f"📁 {files_count} files discarded\n"
                f"💡 Use `/batch` to start a new multi-file session\n"
                f"📄 Or send a single .md file for regular processing",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ No active session to cancel.")
    
    # Enhanced document handler
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads with multi-file support."""
        document: Document = update.message.document
        user_id = update.effective_user.id
        
        # Check for timeout
        if self._check_multi_file_timeout(user_id):
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            await update.message.reply_text("⏰ Session timed out. Please start over.")
            return
        
        # Validate file
        if not (document.file_name.endswith('.md') or document.file_name.endswith('.mdc')):
            await update.message.reply_text(
                "❌ Please send a `.md` or `.mdc` (Markdown) file only.",
                parse_mode='Markdown'
            )
            return
        
        if document.file_size > self.config.max_file_size_mb * 1024 * 1024:
            await update.message.reply_text(
                f"❌ File too large. Max size: {self.config.max_file_size_mb}MB",
                parse_mode='Markdown'
            )
            return
        
        # Determine processing mode
        session = self.user_sessions.get(user_id, {})
        mode = session.get('mode', 'single')
        
        if mode == 'multi':
            await self._handle_document_batch_mode(update, context, document)
        else:
            await self._handle_document_single_mode(update, context, document)
    
    async def _handle_document_batch_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, document: Document):
        """Handle file uploads in batch mode."""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        
        # Check file limit
        if len(session.get('source_files', [])) >= 8:
            await update.message.reply_text(
                "❌ Maximum 8 files per batch. Use `/done` to proceed or `/cancel` to start over."
            )
            return
        
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                f"📄 **Processing file {len(session.get('source_files', [])) + 1}/8...**\n\n"
                "⏳ Analyzing content and categorizing...",
                parse_mode='Markdown'
            )
            
            # Download and read the file
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            markdown_content = file_content.decode('utf-8')
            
            # Categorize file using AI
            file_analysis = await asyncio.to_thread(
                self.project_analyzer.categorize_file,
                markdown_content,
                document.file_name
            )
            
            # Add to session
            session['source_files'].append(file_analysis)
            session['last_activity'] = datetime.now().isoformat()
            
            # Update processing message
            await processing_msg.edit_text(
                f"✅ **File {len(session['source_files'])}/8 Added**\n\n"
                f"📄 **{document.file_name}**\n"
                f"🏷️ **Phase:** {file_analysis['file_phase'].title()}\n"
                f"📊 **Words:** {file_analysis['word_count']:,}\n"
                f"🎯 **Themes:** {', '.join(file_analysis['key_themes'][:3])}\n\n"
                f"📁 **Total files:** {len(session['source_files'])}\n\n"
                f"**Continue uploading or use:**\n"
                f"• `/files` - Review uploaded files\n"
                f"• `/done` - Finish and proceed\n"
                f"• `/project` - Generate project overview",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing document in batch mode: {str(e)}")
            await update.message.reply_text(
                f"❌ **Error processing file:** {str(e)}",
                parse_mode='Markdown'
            )
    
    async def _handle_document_single_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, document: Document):
        """Handle single file upload (backward compatibility)."""
        user_id = update.effective_user.id
        
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "📄 **Processing your markdown file...**\n\n"
                "⏳ Analyzing content and preparing tone selection...",
                parse_mode='Markdown'
            )
            
            # Download and read the file
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            markdown_content = file_content.decode('utf-8')
            
            # Initialize single-file session
            session = self._initialize_session(user_id, markdown_content, document.file_name)
            
            # Delete processing message
            await processing_msg.delete()
            
            # Continue with existing single-file workflow
            await self._show_initial_tone_selection(update, context, session)
            
        except Exception as e:
            logger.error(f"Error processing document in single mode: {str(e)}")
            await update.message.reply_text(
                f"❌ **Error processing file:** {str(e)}",
                parse_mode='Markdown'
            )
    
    # Helper methods
    
    def _suggest_tone_for_phase(self, phase: str) -> str:
        """Suggest appropriate tone based on file phase."""
        tone_mapping = {
            'planning': 'Behind-the-Build',
            'implementation': 'Problem → Solution → Result',
            'debugging': 'What Broke',
            'results': 'Finished & Proud'
        }
        return tone_mapping.get(phase, 'Mini Lesson')
    
    def _generate_basic_cross_references(self, files: List[Dict]) -> List[Dict]:
        """Generate basic cross-references between files."""
        references = []
        
        for i, file in enumerate(files):
            if i > 0:
                prev_file = files[i-1]
                references.append({
                    'from_file': file['filename'],
                    'to_file': prev_file['filename'],
                    'type': 'sequential',
                    'description': f"Post {i+1} builds on Post {i}"
                })
        
        return references
    
    # Enhanced callback handler
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks with multi-file support."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        action = query.data
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        # Handle multi-file specific actions
        if action == "use_ai_strategy":
            await self._use_ai_strategy(query, session)
        elif action == "manual_selection":
            await self._manual_selection(query, session)
        elif action == "cancel_batch":
            await self._cancel_batch(query, user_id)
        else:
            # Handle existing single-file actions
            await self._handle_single_file_callback(query, session, action)
    
    async def _use_ai_strategy(self, query, session):
        """Use AI-generated strategy for content creation."""
        await query.edit_message_text(
            "🚀 **Using AI Strategy**\n\n"
            "⏳ Generating content series based on recommended sequence...\n\n"
            "This will create posts for each file with cross-file awareness.\n"
            "Each post will reference and build upon previous posts in the series.",
            parse_mode='Markdown'
        )
        
        # This would be implemented in Phase 5.3 (Content Generation)
        # For now, show placeholder
        await asyncio.sleep(2)
        await query.edit_message_text(
            "🔄 **Content Generation Coming Soon**\n\n"
            "Multi-file content generation will be implemented in Phase 5.3.\n"
            "For now, you can process files individually using single-file mode.\n\n"
            "Use `/cancel` to exit batch mode.",
            parse_mode='Markdown'
        )
    
    async def _manual_selection(self, query, session):
        """Manual file selection for content creation."""
        source_files = session.get('source_files', [])
        
        if not source_files:
            await query.edit_message_text("❌ No files to select from.")
            return
        
        # Create file selection interface
        keyboard = []
        for i, file in enumerate(source_files):
            keyboard.append([InlineKeyboardButton(
                f"📄 {file['filename']} ({file['file_phase']})",
                callback_data=f"select_file_{i}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_batch")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📋 **Manual File Selection**\n\n"
            "Choose a file to process individually:\n\n"
            "Note: Full multi-file content generation will be available in Phase 5.3.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _cancel_batch(self, query, user_id):
        """Cancel batch processing."""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await query.edit_message_text(
            "❌ **Batch mode canceled**\n\n"
            "💡 Use `/batch` to start a new multi-file session\n"
            "📄 Or send a single .md file for regular processing",
            parse_mode='Markdown'
        )
    
    async def _handle_single_file_callback(self, query, session, action):
        """Handle callbacks for single-file mode (backward compatibility)."""
        # This would delegate to the existing callback handling logic
        # For now, show placeholder
        await query.edit_message_text(
            "🔄 **Single-file processing**\n\n"
            "This will integrate with the existing single-file workflow.",
            parse_mode='Markdown'
        )
    
    # Additional commands (delegated to existing implementations)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command with multi-file info."""
        welcome_message = """
🚀 **Welcome to the Enhanced AI Facebook Content Generator!**

I help you transform your Markdown project documentation into engaging Facebook posts using AI.

**NEW: Multi-File Project Mode** 📚
Upload multiple dev journal files and I'll create a cohesive content series!

**How it works:**
1. **Single File**: Send a `.md` file for individual post generation
2. **Multi-File**: Use `/batch` to upload multiple files for project series

**Multi-File Commands:**
• `/batch` - Start multi-file project mode
• `/project` - Generate project overview
• `/strategy` - Show content strategy
• `/files` - List uploaded files
• `/done` - Finish uploading
• `/cancel` - Cancel batch mode

**Other Commands:**
• `/help` - Show this help message
• `/status` - Check system status
• `/series` - View current post series
• `/continue` - Generate follow-up posts

**Ready to get started?** 
Send a single markdown file or use `/batch` for multi-file mode! 📄
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help with multi-file info."""
        help_text = """
📖 **AI Facebook Content Generator Help**

**File Processing:**
• Send `.md` or `.mdc` files (max 10MB)
• Single file: Immediate processing
• Multi-file: Use `/batch` command first

**Multi-File Mode:**
• `/batch` - Start batch upload (max 8 files)
• `/project` - Analyze uploaded files
• `/strategy` - Generate content strategy
• `/files` - Review uploaded files
• `/done` - Finish uploading
• `/cancel` - Exit batch mode

**Single-File Mode:**
• Upload file → Choose tone → Review → Approve
• `/continue` - Generate follow-up posts
• `/series` - View post series

**System:**
• `/status` - Check bot status
• `/help` - Show this help

**Tips:**
• Use descriptive filenames for better categorization
• Different project phases work best for multi-file mode
• Files are analyzed for planning/implementation/debugging/results phases
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system status with multi-file info."""
        user_id = update.effective_user.id
        session = self.user_sessions.get(user_id, {})
        
        status_text = "🔍 **System Status**\n\n"
        
        # Basic system info
        status_text += f"🤖 **Bot Status:** Online\n"
        status_text += f"🧠 **AI Provider:** {self.config.content_generation_provider}\n"
        status_text += f"📊 **Model:** {self.ai_generator.model}\n\n"
        
        # Session info
        if session:
            mode = session.get('mode', 'single')
            status_text += f"📋 **Your Session:**\n"
            status_text += f"• Mode: {mode.title()}\n"
            
            if mode == 'multi':
                files_count = len(session.get('source_files', []))
                workflow_state = session.get('workflow_state', 'unknown')
                status_text += f"• Files uploaded: {files_count}/8\n"
                status_text += f"• Workflow state: {workflow_state}\n"
                
                # Timeout info
                batch_timeout = session.get('batch_timeout')
                if batch_timeout:
                    time_left = batch_timeout - datetime.now()
                    minutes_left = int(time_left.total_seconds() / 60)
                    status_text += f"• Time remaining: {minutes_left} minutes\n"
            else:
                posts_count = len(session.get('posts', []))
                status_text += f"• Posts in series: {posts_count}\n"
        else:
            status_text += "📋 **No active session**\n"
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def _series_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current series with multi-file support."""
        user_id = update.effective_user.id
        session = self.user_sessions.get(user_id, {})
        
        if not session:
            await update.message.reply_text("📋 No active session. Upload a file to start.")
            return
        
        posts = session.get('posts', [])
        mode = session.get('mode', 'single')
        
        if not posts:
            await update.message.reply_text("📋 No posts in current series.")
            return
        
        series_text = f"📚 **Current Series ({mode.title()} Mode)**\n\n"
        
        for i, post in enumerate(posts, 1):
            series_text += f"**Post {i}:**\n"
            series_text += f"• Tone: {post.get('tone_used', 'Unknown')}\n"
            series_text += f"• Status: {'✅ Approved' if post.get('approved', False) else '⏳ Draft'}\n"
            
            if mode == 'multi' and post.get('source_file'):
                series_text += f"• Source: {post['source_file']}\n"
            
            series_text += "\n"
        
        await update.message.reply_text(series_text, parse_mode='Markdown')
    
    async def _continue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate continuation posts."""
        # This would integrate with existing continue functionality
        await update.message.reply_text(
            "🔄 **Continue Command**\n\n"
            "This will integrate with the existing content continuation feature.",
            parse_mode='Markdown'
        )
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages with multi-file awareness."""
        user_id = update.effective_user.id
        session = self.user_sessions.get(user_id, {})
        
        if not session:
            await update.message.reply_text(
                "Thanks for your message! To get started:\n"
                "• Send a `.md` file for single post generation\n"
                "• Use `/batch` for multi-file project mode\n"
                "• Use `/help` to see all commands"
            )
            return
        
        # Handle different session states
        mode = session.get('mode', 'single')
        
        if mode == 'multi':
            await update.message.reply_text(
                "📚 **Multi-file mode active**\n\n"
                "Please send `.md` files or use these commands:\n"
                "• `/project` - Generate project overview\n"
                "• `/strategy` - Show content strategy\n"
                "• `/files` - List uploaded files\n"
                "• `/done` - Finish uploading\n"
                "• `/cancel` - Exit batch mode"
            )
        else:
            # Handle single-file mode text (existing functionality)
            await update.message.reply_text(
                "📄 **Single-file mode active**\n\n"
                "Waiting for file upload or use:\n"
                "• `/continue` - Generate follow-up posts\n"
                "• `/series` - View current series\n"
                "• `/help` - Show help"
            )
    
    def run(self):
        """Run the bot."""
        print("🚀 Enhanced Facebook Content Bot starting...")
        print("📚 Multi-file upload support enabled")
        print("🔄 Backward compatibility maintained")
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = EnhancedFacebookContentBot()
    bot.run() 