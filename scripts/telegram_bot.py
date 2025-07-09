"""
Main Telegram Bot for AI Facebook Content Generator
"""

import logging
from pathlib import Path
from datetime import datetime
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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class FacebookContentBot:
    """Main bot class for handling Telegram interactions."""
    
    def __init__(self):
        self.config = ConfigManager()
        self.ai_generator = AIContentGenerator(self.config)
        self.airtable = AirtableConnector(self.config)
        
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
        
        # Document/file handler
        self.application.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        
        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Text message handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text))
    
    def _initialize_session(self, user_id: int, markdown_content: str, filename: str) -> Dict:
        """Initialize a new multi-post session."""
        series_id = str(uuid.uuid4())
        
        session = {
            'series_id': series_id,
            'original_markdown': markdown_content,
            'filename': filename,
            'posts': [],  # List of approved posts in this series
            'current_draft': None,  # Current post being reviewed
            'session_started': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'session_context': '',  # AI context summary for continuity
            'post_count': 0
        }
        
        self.user_sessions[user_id] = session
        return session
    
    def _add_post_to_series(self, user_id: int, post_data: Dict, airtable_record_id: str, 
                           parent_post_id: Optional[str] = None, relationship_type: Optional[str] = None):
        """Add an approved post to the user's series."""
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        session['post_count'] += 1
        
        post_entry = {
            'post_id': session['post_count'],
            'content': post_data.get('post_content', ''),
            'tone_used': post_data.get('tone_used', 'Unknown'),
            'airtable_record_id': airtable_record_id,
            'approved_at': datetime.now().isoformat(),
            'parent_post_id': parent_post_id,
            'relationship_type': relationship_type,
            'content_summary': post_data.get('post_content', '')[:100] + '...' if len(post_data.get('post_content', '')) > 100 else post_data.get('post_content', '')
        }
        
        session['posts'].append(post_entry)
        session['last_activity'] = datetime.now().isoformat()
        
        # Update session context for AI continuity
        self._update_session_context(user_id)
    
    def _update_session_context(self, user_id: int):
        """Update the session context for AI continuity."""
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        posts = session['posts']
        
        if not posts:
            session['session_context'] = ""
            return
        
        # Create context summary for AI
        context_parts = [
            f"Series: {len(posts)} posts created from {session['filename']}",
            f"Original project: {session['original_markdown'][:200]}...",
            ""
        ]
        
        for post in posts:
            context_parts.append(f"Post {post['post_id']}: {post['tone_used']} tone")
            context_parts.append(f"Content: {post['content_summary']}")
            if post['relationship_type']:
                context_parts.append(f"Relationship: {post['relationship_type']}")
            context_parts.append("")
        
        session['session_context'] = "\n".join(context_parts)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🚀 **Welcome to the AI Facebook Content Generator!**

I help you transform your Markdown project documentation into engaging Facebook posts using AI.

**How it works:**
1. Send me a `.md` file with your project documentation
2. I'll analyze it and generate a Facebook post using one of 5 brand tones
3. You can review, approve, or ask me to regenerate
4. Approved posts are saved to your Airtable for publishing

**Commands:**
• `/help` - Show this help message
• `/status` - Check system status

**Ready to get started?** 
Just send me a markdown file! 📄
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
🎯 **AI Facebook Content Generator Help**

**How to use:**
1. **Send a markdown file** (.md extension)
2. **Choose a tone** (optional) or let AI decide
3. **Review the generated post**
4. **Approve** ✅ or **Regenerate** 🔄

**Brand Tones Available:**
• 🧩 Behind-the-Build
• 💡 What Broke
• 🚀 Finished & Proud
• 🎯 Problem → Solution → Result
• 📓 Mini Lesson

**File Requirements:**
• `.md` file extension
• Max size: 10MB
• Text content about your automation/AI projects

**Commands:**
• `/start` - Welcome message
• `/status` - Check system status
• `/help` - This help message

Need help? Just send a markdown file to begin! 🚀
        """
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        try:
            # Test connections
            airtable_status = "✅ Connected" if self.airtable.test_connection() else "❌ Failed"
            
            # Get recent drafts count
            recent_drafts = self.airtable.get_recent_drafts(limit=5)
            drafts_count = len(recent_drafts)
            
            status_message = f"""
📊 **System Status**

**Services:**
• Airtable: {airtable_status}
• OpenAI: ✅ Ready
• Telegram Bot: ✅ Running

**Recent Activity:**
• Drafts in last 24h: {drafts_count}
• AI Model: {self.config.openai_model}

**System Ready!** 🚀
            """
            await update.message.reply_text(status_message, parse_mode='Markdown')
            
        except Exception as e:
            error_message = f"❌ **System Error:** {str(e)}"
            await update.message.reply_text(error_message, parse_mode='Markdown')
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads."""
        document: Document = update.message.document
        user_id = update.effective_user.id
        
        # Validate file
        if not document.file_name.endswith('.md'):
            await update.message.reply_text(
                "❌ Please send a `.md` (Markdown) file only.",
                parse_mode='Markdown'
            )
            return
        
        if document.file_size > self.config.max_file_size_mb * 1024 * 1024:
            await update.message.reply_text(
                f"❌ File too large. Max size: {self.config.max_file_size_mb}MB",
                parse_mode='Markdown'
            )
            return
        
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "📄 **Processing your markdown file...**\n\n"
                "⏳ This may take a moment while I analyze the content and generate your Facebook post.",
                parse_mode='Markdown'
            )
            
            # Download and read the file
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            markdown_content = file_content.decode('utf-8')
            
            # Initialize or update session
            if user_id in self.user_sessions:
                # If user already has a session, add the new file to it
                self._add_post_to_series(user_id, {'post_content': markdown_content}, '', parent_post_id='initial_upload')
            else:
                # If no session, start a new one
                self._initialize_session(user_id, markdown_content, document.file_name)
            
            # Generate Facebook post
            await self._generate_and_show_post(update, context, markdown_content)
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error processing file:** {str(e)}",
                parse_mode='Markdown'
            )
    
    def _escape_markdown(self, text: str) -> str:
        """Escape markdown characters for Telegram."""
        if not text:
            return text
        
        # Escape special markdown characters that can cause parsing errors
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    def _truncate_message(self, message: str, max_length: int = 4000) -> str:
        """Truncate message if it's too long for Telegram."""
        if len(message) <= max_length:
            return message
        
        # Find a good place to truncate (try to break at word boundaries)
        truncated = message[:max_length-50]  # Leave space for truncation notice
        
        # Try to break at the last complete word
        last_space = truncated.rfind(' ')
        if last_space > max_length - 200:  # Only if we don't cut too much
            truncated = truncated[:last_space]
        
        return truncated + "\n\n📝 *[Message truncated - full content saved to Airtable]*"
    
    async def _generate_and_show_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     markdown_content: str, tone_preference: Optional[str] = None,
                                     is_regeneration: bool = False, relationship_type: Optional[str] = None,
                                     parent_post_id: Optional[str] = None):
        """Generate and display a Facebook post with context awareness."""
        user_id = update.effective_user.id
        
        try:
            # Get session context if available
            session_context = None
            previous_posts = None
            
            if user_id in self.user_sessions:
                session = self.user_sessions[user_id]
                session_context = session.get('session_context', '')
                previous_posts = session.get('posts', [])
            
            # Generate the post with context awareness
            if is_regeneration and tone_preference:
                post_data = self.ai_generator.regenerate_post(
                    markdown_content, 
                    feedback=f"User requested {tone_preference} tone",
                    tone_preference=tone_preference,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=relationship_type,
                    parent_post_id=parent_post_id
                )
            else:
                post_data = self.ai_generator.generate_facebook_post(
                    markdown_content, 
                    tone_preference,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=relationship_type,
                    parent_post_id=parent_post_id
                )
            
            # Store in session
            self.user_sessions[user_id]['current_draft'] = post_data
            
            # Create inline keyboard for user actions
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data="approve"),
                    InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
                ],
                [
                    InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get post content and ensure it's not too long
            post_content = post_data.get('post_content', 'No content generated')
            tone_reason = post_data.get('tone_reason', 'No reason provided')
            
            # Escape markdown characters to prevent Telegram parsing errors
            post_content = self._escape_markdown(post_content)
            tone_reason = self._escape_markdown(tone_reason)
            
            # Truncate content if needed for Telegram display
            if len(post_content) > 2000:  # Leave room for other message parts
                display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display - full version saved to Airtable]*"
            else:
                display_content = post_content
            
            # Truncate reasoning if needed
            if len(tone_reason) > 500:
                display_reason = tone_reason[:500] + "..."
            else:
                display_reason = tone_reason
            
            # Add context-aware information to the display
            context_info = ""
            if post_data.get('is_context_aware', False):
                context_info = f"\n\n🔗 **Context-Aware Generation**"
                if relationship_type:
                    context_info += f"\n• Relationship: {relationship_type}"
                if previous_posts:
                    context_info += f"\n• Building on {len(previous_posts)} previous posts"
            
            # Format the message
            post_preview = f"""
🎯 Generated Facebook Post

Tone Used: {post_data.get('tone_used', 'Unknown')}{context_info}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?
            """
            
            # Final safety check and truncation
            post_preview = self._truncate_message(post_preview)
            
            # Send the message with better error handling
            try:
                await update.message.reply_text(
                    post_preview,
                    reply_markup=reply_markup
                )
            except Exception as telegram_error:
                # If Telegram fails, try without reply_markup
                try:
                    await update.message.reply_text(
                        post_preview + "\n\n❌ Button interface failed - please send a new file."
                    )
                except Exception as fallback_error:
                    # Last resort - send simple error message
                    await update.message.reply_text(
                        "✅ Post generated successfully but display failed. Please try again."
                    )
            
        except Exception as e:
            logger.error(f"Error in _generate_and_show_post: {str(e)}")
            try:
                await update.message.reply_text(
                    f"❌ **Error generating post:** {str(e)}"
                )
            except Exception:
                # If even error message fails, log it
                logger.error(f"Failed to send error message: {str(e)}")
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        action = query.data
        
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        if action == "approve":
            await self._approve_post(query, session)
        elif action == "regenerate":
            await self._regenerate_post(query, session)
        elif action == "change_tone":
            await self._show_tone_options(query, session)
        elif action == "cancel":
            await self._cancel_session(query, user_id)
        elif action == "generate_another":
            await self._generate_another_post(query, session)
        elif action == "new_file":
            await self._new_file_session(query, user_id)
        elif action == "done":
            await self._finish_session(query, user_id)
        elif action.startswith("tone_"):
            # Handle tone selection
            tone_name = action.replace("tone_", "").replace("_", " ")
            await self._regenerate_with_tone(query, session, tone_name)
        elif action.startswith("rel_"):
            # Handle relationship selection
            await self._handle_relationship_choice(query, user_id)
        elif action.startswith("prev_post_"):
            # Handle previous post selection
            await self._handle_previous_post_selection(query, user_id)
        elif action == "confirm_generation":
            # Handle generation confirmation
            await self._confirm_generation(query, user_id)
    
    async def _approve_post(self, query, session):
        """Approve and save the post to Airtable."""
        try:
            post_data = session['current_draft']
            filename = session['filename']
            
            # Create a title from filename for display purposes only
            display_title = filename.replace('.md', '').replace('_', ' ').title()
            
            # Save to Airtable with FULL multi-post support
            record_id = self.airtable.save_draft_with_multi_post_fields(
                post_data=post_data,
                title=display_title,
                review_status="📝 To Review",
                series_id=session['series_id'],
                sequence_number=session['post_count'] + 1,
                parent_post_id=None,  # TODO: Will be set when building on previous posts
                relationship_type=None,  # TODO: Will be set when building on previous posts
                session_context=session['session_context']
            )
            
            # Add to series
            self._add_post_to_series(query.from_user.id, post_data, record_id)
            
            # Create success message with action buttons
            success_message = f"""✅ **Post Approved & Saved\\!**

📊 **Series Info:**
• File: {self._escape_markdown(filename)}
• Posts in series: {session['post_count']}
• Series ID: {session['series_id'][:8]}\\.\\.\\. 
• Record ID: {record_id}

🚀 **v2\\.0 Multi\\-Post Ready\\!**
• Series tracking active
• Post sequence: {session['post_count']}
• AI context saved
• Relationship support enabled

📝 **Saved to Airtable for review & publishing**"""
            
            # Create inline keyboard for next actions
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Generate Another Post", callback_data="generate_another"),
                    InlineKeyboardButton("📁 New File", callback_data="new_file")
                ],
                [
                    InlineKeyboardButton("✅ Done", callback_data="done")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                success_message,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            # Fallback to simple message if formatting fails
            try:
                simple_message = f"✅ Post approved and saved to Airtable!\n\nRecord ID: {record_id}\nSeries: {session['post_count']} posts\n\nSend another .md file to continue or type 'done' to finish."
                await query.edit_message_text(simple_message)
            except:
                # Final fallback
                await query.edit_message_text("✅ Post approved and saved successfully!")
            
            print(f"Warning: Success message formatting error: {e}")
    
    async def _regenerate_post(self, query, session):
        """Regenerate the post with general feedback and context awareness."""
        try:
            await query.edit_message_text(
                "🔄 **Regenerating your post...**\n\n"
                "⏳ Creating a new version with different approach...",
                parse_mode='Markdown'
            )
            
            # Get context for regeneration
            session_context = session.get('session_context', '')
            previous_posts = session.get('posts', [])
            
            # Regenerate with context awareness
            markdown_content = session['original_markdown'] 
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback="User requested regeneration - try different tone or approach",
                session_context=session_context,
                previous_posts=previous_posts
            )
            
            session['current_draft'] = post_data
            
            # Create new inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data="approve"),
                    InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
                ],
                [
                    InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get post content and ensure it's not too long
            post_content = post_data.get('post_content', 'No content generated')
            tone_reason = post_data.get('tone_reason', 'No reason provided')
            
            # Escape markdown characters to prevent Telegram parsing errors
            post_content = self._escape_markdown(post_content)
            tone_reason = self._escape_markdown(tone_reason)
            
            # Truncate content if needed for Telegram display
            if len(post_content) > 2000:
                display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
            else:
                display_content = post_content
            
            # Truncate reasoning if needed
            if len(tone_reason) > 500:
                display_reason = tone_reason[:500] + "..."
            else:
                display_reason = tone_reason
            
            # Add context-aware information
            context_info = ""
            if post_data.get('is_context_aware', False):
                context_info = f"\n\n🔗 **Context-Aware Regeneration**"
                if previous_posts:
                    context_info += f"\n• Building on {len(previous_posts)} previous posts"
            
            # Format the message
            post_preview = f"""
🔄 **Regenerated Post**

**Tone:** {post_data.get('tone_used', 'Unknown')}{context_info}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?
            """
            
            await query.edit_message_text(
                self._truncate_message(post_preview),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error regenerating post:** {str(e)}"
            )
    
    async def _show_tone_options(self, query, session):
        """Show tone selection options."""
        tone_options = self.ai_generator.get_tone_options()
        
        keyboard = []
        for tone in tone_options:
            # Create callback data from tone (make it more robust)
            if ' ' in tone:
                # Handle tones with spaces (e.g., "Behind-the-Build")
                callback_data = f"tone_{tone.split(' ', 1)[1].replace(' ', '_').replace('→', 'to').lower()}"
            else:
                # Handle single word tones
                callback_data = f"tone_{tone.replace('→', 'to').lower()}"
            
            # Ensure callback_data is not too long (Telegram limit is 64 characters)
            if len(callback_data) > 60:
                callback_data = callback_data[:60]
            
            keyboard.append([InlineKeyboardButton(tone, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎨 **Choose a tone style:**\n\n"
            "Select the tone you'd like for your Facebook post:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _regenerate_with_tone(self, query, session, tone_name):
        """Regenerate post with specific tone and context awareness."""
        try:
            await query.edit_message_text(
                f"🎨 **Regenerating with '{tone_name}' tone...**\n\n"
                "⏳ Creating a new version with your selected style...",
                parse_mode='Markdown'
            )
            
            # Find the full tone name
            tone_options = self.ai_generator.get_tone_options()
            selected_tone = None
            for tone in tone_options:
                if tone_name.lower() in tone.lower():
                    selected_tone = tone
                    break
            
            if not selected_tone:
                selected_tone = tone_name
            
            # Get context for regeneration
            session_context = session.get('session_context', '')
            previous_posts = session.get('posts', [])
            
            # Regenerate with specific tone and context awareness
            markdown_content = session['original_markdown']
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback=f"User specifically requested {selected_tone} tone",
                tone_preference=selected_tone,
                session_context=session_context,
                previous_posts=previous_posts
            )
            
            session['current_draft'] = post_data
            
            # Create new inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data="approve"),
                    InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
                ],
                [
                    InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get post content and ensure it's not too long
            post_content = post_data.get('post_content', 'No content generated')
            tone_reason = post_data.get('tone_reason', 'No reason provided')
            
            # Escape markdown characters to prevent Telegram parsing errors
            post_content = self._escape_markdown(post_content)
            tone_reason = self._escape_markdown(tone_reason)
            
            # Truncate content if needed for Telegram display
            if len(post_content) > 2000:
                display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
            else:
                display_content = post_content
            
            # Truncate reasoning if needed
            if len(tone_reason) > 500:
                display_reason = tone_reason[:500] + "..."
            else:
                display_reason = tone_reason
            
            # Add context-aware information
            context_info = ""
            if post_data.get('is_context_aware', False):
                context_info = f"\n\n🔗 **Context-Aware Regeneration**"
                if previous_posts:
                    context_info += f"\n• Building on {len(previous_posts)} previous posts"
            
            # Format the message
            post_preview = f"""
🎨 **Regenerated with {selected_tone} Tone**

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}{context_info}

What would you like to do?
            """
            
            await query.edit_message_text(
                self._truncate_message(post_preview),
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error regenerating with tone:** {str(e)}",
                parse_mode='Markdown'
            )
    
    async def _cancel_session(self, query, user_id):
        """Cancel current session."""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await query.edit_message_text(
            "❌ **Session cancelled.**\n\n"
            "Send a new markdown file to start over! 📄",
            parse_mode='Markdown'
        )
    
    async def _generate_another_post(self, query, session):
        """Generate another post from the same markdown with context awareness."""
        try:
            # Instead of automatically generating, show relationship selection
            await self._show_relationship_selection(query, query.from_user.id)
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error starting post generation:** {str(e)}"
            )
    
    async def _show_relationship_selection(self, query, user_id: int):
        """Show relationship type selection interface."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        # Set workflow state
        session['workflow_state'] = 'awaiting_relationship_selection'
        
        # Initialize pending generation data
        session['pending_generation'] = {
            'relationship_type': None,
            'parent_post_id': None,
            'connection_preview': None,
            'user_confirmed': False
        }
        
        # Get context information
        posts_count = len(session.get('posts', []))
        
        # Create message based on whether there are previous posts
        if posts_count == 0:
            message = """
🎯 **Generate Another Post**

This will be your first related post in the series.

**Choose relationship type for your next post:**
            """
        else:
            message = f"""
🎯 **Generate Another Post**

Series: {posts_count} posts created
Building on: {session.get('filename', 'your project')}

**Choose relationship type for your next post:**
            """
        
        # Create inline keyboard with relationship types
        keyboard = [
            [
                InlineKeyboardButton("🔍 Different Aspects", callback_data="rel_different_aspects"),
                InlineKeyboardButton("📐 Different Angles", callback_data="rel_different_angles")
            ],
            [
                InlineKeyboardButton("📚 Series Continuation", callback_data="rel_series_continuation"),
                InlineKeyboardButton("🔗 Thematic Connection", callback_data="rel_thematic_connection")
            ],
            [
                InlineKeyboardButton("🔧 Technical Deep Dive", callback_data="rel_technical_deep_dive"),
                InlineKeyboardButton("📖 Sequential Story", callback_data="rel_sequential_story")
            ],
            [
                InlineKeyboardButton("🤖 AI Decide", callback_data="rel_ai_decide")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _handle_relationship_choice(self, query, user_id: int):
        """Handle relationship type selection."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        # Map callback data to relationship type
        relationship_map = {
            'rel_different_aspects': 'Different Aspects',
            'rel_different_angles': 'Different Angles', 
            'rel_series_continuation': 'Series Continuation',
            'rel_thematic_connection': 'Thematic Connection',
            'rel_technical_deep_dive': 'Technical Deep Dive',
            'rel_sequential_story': 'Sequential Story',
            'rel_ai_decide': 'AI Decide'
        }
        
        relationship_type = relationship_map.get(query.data, 'Unknown')
        
        # Store the relationship type in pending generation
        session['pending_generation']['relationship_type'] = relationship_type
        session['workflow_state'] = 'awaiting_previous_post_selection'
        
        # Show previous post selection
        await self._show_previous_post_selection(query, user_id)
    
    async def _show_previous_post_selection(self, query, user_id: int):
        """Show previous post selection interface."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        posts = session.get('posts', [])
        relationship_type = session['pending_generation']['relationship_type']
        
        if not posts:
            # No previous posts, go directly to generation
            await self._confirm_generation(query, user_id)
            return
        
        message = f"""
🎯 **Choose Previous Post to Build On**

**Selected Relationship:** {relationship_type}

**Choose which post to build upon:**
        """
        
        # Create buttons for each previous post
        keyboard = []
        for post in posts:
            post_snippet = post.get('content_summary', post.get('content', ''))[:50] + '...'
            button_text = f"Post {post['post_id']}: {post_snippet}"
            callback_data = f"prev_post_{post['post_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add default option
        keyboard.append([InlineKeyboardButton("📝 Build on most recent", callback_data="prev_post_recent")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def _handle_previous_post_selection(self, query, user_id: int):
        """Handle selection of a previous post to build on."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        posts = session.get('posts', [])
        
        # Get the selected post ID from the callback data
        selected_post_id_str = query.data.replace("prev_post_", "")
        
        if selected_post_id_str == "recent":
            # Handle "most recent" option
            selected_post = posts[-1] if posts else None
            parent_post_id = selected_post['post_id'] if selected_post else None
        else:
            # Handle specific post ID
            try:
                selected_post_id = int(selected_post_id_str)
                selected_post = None
                for post in posts:
                    if post['post_id'] == selected_post_id:
                        selected_post = post
                        break
                parent_post_id = selected_post_id if selected_post else None
            except ValueError:
                await query.edit_message_text("❌ Invalid post selection. Please try again.")
                return
        
        if not selected_post:
            await query.edit_message_text("❌ Could not find the selected post. Please try again.")
            return
        
        # Store the selected post ID
        session['pending_generation']['parent_post_id'] = parent_post_id
        session['workflow_state'] = 'awaiting_generation_confirmation'
        
        # Show generation confirmation instead of immediately generating
        await self._show_generation_confirmation(query, user_id, selected_post)
        
    async def _show_generation_confirmation(self, query, user_id: int, selected_post: Dict):
        """Show generation confirmation with connection preview."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        relationship_type = session['pending_generation']['relationship_type']
        posts = session.get('posts', [])
        
        # Generate enhanced connection preview
        connection_preview = self._generate_connection_preview(selected_post, relationship_type, posts)
        connection_strength = self._calculate_connection_strength(relationship_type, selected_post, posts)
        relationship_emoji = self._get_relationship_emoji(relationship_type)
        reading_sequence = self._estimate_reading_sequence(posts, selected_post['post_id'])
        
        # Store the connection preview in session
        session['pending_generation']['connection_preview'] = connection_preview
        
        # Get strength indicator emoji
        strength_emoji = {
            'Strong': '🟢',
            'Medium': '🟡',
            'Weak': '🔴'
        }.get(connection_strength, '🔗')
        
        message = f"""
🎯 **Ready to Generate Post**

{relationship_emoji} **Relationship:** {relationship_type}
📊 **Connection Strength:** {strength_emoji} {connection_strength}
🔗 **Building on:** Post {selected_post['post_id']} ({selected_post['tone_used']} tone)

**Previous post preview:** {selected_post['content_summary'][:80]}...

**Connection Preview:**
{connection_preview}

**Reading Sequence:** {reading_sequence}

Ready to generate your new post?
        """
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Generate Post", callback_data="confirm_generation"),
                InlineKeyboardButton("⬅️ Back", callback_data="back_to_relationship_selection")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    def _generate_connection_preview(self, selected_post: Dict, relationship_type: str, all_posts: List[Dict]) -> str:
        """Generate an intelligent connection preview based on relationship type and context."""
        post_id = selected_post['post_id']
        post_tone = selected_post['tone_used']
        post_summary = selected_post['content_summary'][:100]
        
        # Base connection text
        base_text = f"This post will build on Post {post_id} ({post_tone} tone)"
        
        # Relationship-specific preview text
        relationship_descriptions = {
            'Different Aspects': f"{base_text} using a Different Aspects approach by exploring different aspects of the same topic. While the previous post covered {post_summary.lower()}, this new post will examine other facets and perspectives.",
            
            'Different Angles': f"{base_text} using a Different Angles approach by taking a different angle on the same subject. This will provide an alternative viewpoint to complement the {post_tone.lower()} perspective.",
            
            'Series Continuation': f"{base_text} as a Series Continuation, serving as the next part in a sequential series. This continues the narrative flow from the previous post.",
            
            'Thematic Connection': f"{base_text} through a Thematic Connection, linking posts through shared themes and principles. The posts will be connected by underlying concepts rather than direct narrative flow.",
            
            'Technical Deep Dive': f"{base_text} with a Technical Deep Dive approach by providing detailed technical insights. This will dive deeper into the technical aspects mentioned in the previous post.",
            
            'Sequential Story': f"{base_text} as a Sequential Story by continuing the story chronologically. This shows what happened next in the timeline.",
            
            'AI Decide': f"{base_text} using an AI Decide approach with AI-determined optimal relationship type based on content analysis."
        }
        
        return relationship_descriptions.get(relationship_type, base_text)
    
    def _calculate_connection_strength(self, relationship_type: str, selected_post: Dict, all_posts: List[Dict]) -> str:
        """Calculate connection strength based on relationship type and post context."""
        # Strong connections - direct narrative flow
        strong_relationships = ['Sequential Story', 'Series Continuation', 'Technical Deep Dive']
        
        # Medium connections - related but not sequential
        medium_relationships = ['Different Aspects', 'Different Angles']
        
        # Weak connections - thematic only
        weak_relationships = ['Thematic Connection', 'AI Decide']
        
        if relationship_type in strong_relationships:
            return 'Strong'
        elif relationship_type in medium_relationships:
            return 'Medium'
        else:
            return 'Weak'
    
    def _get_relationship_emoji(self, relationship_type: str) -> str:
        """Get emoji representation for relationship types."""
        emoji_map = {
            'Different Aspects': '🔍',
            'Different Angles': '📐',
            'Series Continuation': '📚',
            'Thematic Connection': '🔗',
            'Technical Deep Dive': '🔧',
            'Sequential Story': '📖',
            'AI Decide': '🤖'
        }
        return emoji_map.get(relationship_type, '📝')
    
    def _estimate_reading_sequence(self, all_posts: List[Dict], building_on_post_id: int) -> str:
        """Estimate the optimal reading sequence for the post series."""
        if not all_posts:
            return "Post 1 → New Post"
        
        # Find the post we're building on
        building_post = None
        for post in all_posts:
            if post['post_id'] == building_on_post_id:
                building_post = post
                break
        
        if not building_post:
            return f"Post {building_on_post_id} → New Post"
        
        # Build sequence up to the building post
        sequence_parts = []
        current_post_id = building_on_post_id
        
        # Trace back to find the chain
        post_chain = [building_post]
        current_parent = building_post.get('parent_post_id')
        
        while current_parent:
            parent_post = None
            for post in all_posts:
                if post['post_id'] == current_parent:
                    parent_post = post
                    break
            if parent_post:
                post_chain.insert(0, parent_post)
                current_parent = parent_post.get('parent_post_id')
            else:
                break
        
        # Build the sequence string
        sequence_parts = [f"Post {post['post_id']}" for post in post_chain]
        sequence_parts.append("New Post")
        
        return " → ".join(sequence_parts)
    
    async def _confirm_generation(self, query, user_id: int):
        """Confirm the generation process."""
        if user_id not in self.user_sessions:
            await query.edit_message_text("❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        # Get pending generation data
        relationship_type = session['pending_generation']['relationship_type']
        parent_post_id = session['pending_generation']['parent_post_id']
        
        # Clear pending generation state
        session['pending_generation'] = {
            'relationship_type': None,
            'parent_post_id': None,
            'connection_preview': None,
            'user_confirmed': False
        }
        session['workflow_state'] = 'awaiting_tone_selection' # Reset workflow
        
        # Generate the post with context awareness
        markdown_content = session['original_markdown']
        post_data = self.ai_generator.generate_facebook_post(
            markdown_content,
            user_tone_preference=None,  # Let AI decide based on context
            session_context=session['session_context'],
            previous_posts=session['posts'],
            relationship_type=relationship_type,
            parent_post_id=parent_post_id
        )
        
        session['current_draft'] = post_data
        
        # Create inline keyboard for user actions
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data="approve"),
                InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
            ],
            [
                InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get post content and ensure it's not too long
        post_content = post_data.get('post_content', 'No content generated')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Escape markdown characters to prevent Telegram parsing errors
        post_content = self._escape_markdown(post_content)
        tone_reason = self._escape_markdown(tone_reason)
        
        # Truncate content if needed for Telegram display
        if len(post_content) > 2000:
            display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
        else:
            display_content = post_content
        
        # Truncate reasoning if needed
        if len(tone_reason) > 500:
            display_reason = tone_reason[:500] + "..."
        else:
            display_reason = tone_reason
        
        # Add context-aware information
        context_info = ""
        if post_data.get('is_context_aware', False):
            context_info = f"\n\n🔗 **Context-Aware Generation**"
            if post_data.get('relationship_type'):
                context_info += f"\n• Relationship: {post_data.get('relationship_type')}"
            if session.get('posts'):
                context_info += f"\n• Building on {len(session.get('posts', []))} previous posts"
        
        # Create the message
        post_preview = f"""
🎯 **New Post Generated (#{session['post_count'] + 1})**

**Tone:** {post_data.get('tone_used', 'Unknown')}{context_info}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?
        """
        
        await query.edit_message_text(
            self._truncate_message(post_preview),
            reply_markup=reply_markup
        )
    
    async def _send_new_post_message(self, query, post_data: Dict, session: Dict):
        """Send a new message with the generated post (preserves previous messages)."""
        # Create inline keyboard for the new post
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data="approve"),
                InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
            ],
            [
                InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get and format post content
        post_content = post_data.get('post_content', 'No content generated')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Escape and truncate content
        post_content = self._escape_markdown(post_content)
        tone_reason = self._escape_markdown(tone_reason)
        
        if len(post_content) > 2000:
            display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
        else:
            display_content = post_content
        
        if len(tone_reason) > 500:
            display_reason = tone_reason[:500] + "..."
        else:
            display_reason = tone_reason
        
        # Add context-aware information
        context_info = ""
        if post_data.get('is_context_aware', False):
            context_info = f"\n\n🔗 **Context-Aware Generation**"
            if post_data.get('relationship_type'):
                context_info += f"\n• Relationship: {post_data.get('relationship_type')}"
            if session.get('posts'):
                context_info += f"\n• Building on {len(session.get('posts', []))} previous posts"
        
        # Create the message
        post_preview = f"""
🔄 **New Post Generated \\(#{session['post_count'] + 1}\\)**

**Tone:** {post_data.get('tone_used', 'Unknown')}{context_info}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?
        """
        
        await query.message.reply_text(
            self._truncate_message(post_preview),
            reply_markup=reply_markup
        )
    
    async def _new_file_session(self, query, user_id):
        """Clear session and wait for new file."""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await query.edit_message_text(
            "📁 **Ready for new file!**\n\n"
            "Send me a new `.md` file to start a fresh content series! 📄",
            parse_mode='Markdown'
        )
    
    async def _finish_session(self, query, user_id):
        """Finish the session."""
        session_info = ""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session_info = f"\n\n**Session Summary:**\n• {session['post_count']} posts created\n• Series ID: {session['series_id'][:8]}..."
            del self.user_sessions[user_id]
        
        await query.edit_message_text(
            f"✅ **Session Complete!**{session_info}\n\n"
            "All posts have been saved to Airtable. 📝\n\n"
            "Send a new markdown file when you're ready to create more content! 🚀",
            parse_mode='Markdown'
        )
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user_id = update.effective_user.id
        text = update.message.text.lower().strip()
        
        # Check if user has an active session and is responding to "generate another post"
        if user_id in self.user_sessions and text in ['yes', 'y', 'sure', 'okay', 'ok']:
            session = self.user_sessions[user_id]
            
            # Check if they just approved a post (have posts in series)
            if session.get('post_count', 0) > 0:
                # Simulate a callback query for generate_another
                try:
                    await update.message.reply_text(
                        "🔄 **Generating another post from your project...**\n\n"
                        "⏳ Creating a new perspective on your content...",
                        parse_mode='Markdown'
                    )
                    
                    # Use the AI generator's suggestion system for relationship type
                    previous_posts = session.get('posts', [])
                    suggested_relationship = self.ai_generator.suggest_relationship_type(
                        previous_posts, 
                        session['original_markdown']
                    )
                    
                    # Generate with full context awareness
                    markdown_content = session['original_markdown']
                    session_context = session.get('session_context', '')
                    
                    post_data = self.ai_generator.generate_facebook_post(
                        markdown_content,
                        user_tone_preference=None,  # Let AI decide based on context
                        session_context=session_context,
                        previous_posts=previous_posts,
                        relationship_type=suggested_relationship
                    )
                    
                    # Store the new draft
                    session['current_draft'] = post_data
                    session['last_activity'] = datetime.now().isoformat()
                    
                    # Show the new post as a new message
                    await self._send_new_post_message_from_update(update, post_data, session)
                    return
                    
                except Exception as e:
                    await update.message.reply_text(
                        f"❌ **Error generating another post:** {str(e)}"
                    )
                    return
        
        # Default response for other text messages
        await update.message.reply_text(
            "👋 Hi! I work with markdown files.\n\n"
            "📄 **Send me a `.md` file** to generate a Facebook post!\n\n"
            "Use `/help` for more information.",
            parse_mode='Markdown'
        )
    
    async def _send_new_post_message_from_update(self, update: Update, post_data: Dict, session: Dict):
        """Send a new message with the generated post from an update (preserves previous messages)."""
        # Create inline keyboard for the new post
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data="approve"),
                InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
            ],
            [
                InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get and format post content
        post_content = post_data.get('post_content', 'No content generated')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Escape and truncate content
        post_content = self._escape_markdown(post_content)
        tone_reason = self._escape_markdown(tone_reason)
        
        if len(post_content) > 2000:
            display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
        else:
            display_content = post_content
        
        if len(tone_reason) > 500:
            display_reason = tone_reason[:500] + "..."
        else:
            display_reason = tone_reason
        
        # Add context-aware information
        context_info = ""
        if post_data.get('is_context_aware', False):
            context_info = f"\n\n🔗 **Context-Aware Generation**"
            if post_data.get('relationship_type'):
                context_info += f"\n• Relationship: {post_data.get('relationship_type')}"
            if session.get('posts'):
                context_info += f"\n• Building on {len(session.get('posts', []))} previous posts"
        
        # Create the message
        post_preview = f"""
🔄 **New Post Generated \\(#{session['post_count'] + 1}\\)**

**Tone:** {post_data.get('tone_used', 'Unknown')}{context_info}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?
        """
        
        await update.message.reply_text(
            self._truncate_message(post_preview),
            reply_markup=reply_markup
        )
    
    async def _show_generated_post(self, update: Update, post_data: Dict, session: Dict):
        """Show a generated post with action buttons."""
        # Create inline keyboard for the new post
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data="approve"),
                InlineKeyboardButton("🔄 Regenerate", callback_data="regenerate")
            ],
            [
                InlineKeyboardButton("🎨 Change Tone", callback_data="change_tone"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get and format post content
        post_content = post_data.get('post_content', 'No content generated')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Escape and truncate content
        post_content = self._escape_markdown(post_content)
        tone_reason = self._escape_markdown(tone_reason)
        
        if len(post_content) > 2000:
            display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display]*"
        else:
            display_content = post_content
        
        if len(tone_reason) > 500:
            display_reason = tone_reason[:500] + "..."
        else:
            display_reason = tone_reason
        
        # Create the message
        post_preview = f"""
🔄 **New Post Generated \\(#{session['post_count'] + 1}\\)**

**Tone:** {post_data.get('tone_used', 'Unknown')}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?
        """
        
        await update.message.reply_text(
            self._truncate_message(post_preview),
            reply_markup=reply_markup
        )
    
    def run(self):
        """Start the bot."""
        try:
            # Validate configuration
            self.config.validate_config()
            
            logger.info("Starting Facebook Content Generator Bot...")
            logger.info(f"Using OpenAI model: {self.config.openai_model}")
            
            # Test Airtable connection
            if not self.airtable.test_connection():
                logger.warning("Airtable connection test failed - check your configuration")
            
            # Run the bot
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

if __name__ == "__main__":
    bot = FacebookContentBot()
    bot.run() 