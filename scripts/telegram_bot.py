"""
Main Telegram Bot for AI Facebook Content Generator
"""

import logging
import os
from pathlib import Path
from datetime import datetime
import asyncio
import uuid
import random
import httpx
from typing import Dict, Optional, List
from io import BytesIO
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from telegram.request import HTTPXRequest, BaseRequest
from telegram.error import TimedOut, NetworkError, RetryAfter
from telegram.constants import ParseMode

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from airtable_connector import AirtableConnector

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RetryingRequest(HTTPXRequest):
    """Custom request handler with retry logic for failed requests"""
    
    def __init__(self, *args, **kwargs):
        # Extract timeout settings - only use supported parameters
        supported_kwargs = {}
        
        # Extract known supported parameters
        if 'read_timeout' in kwargs:
            supported_kwargs['read_timeout'] = kwargs.pop('read_timeout')
        if 'write_timeout' in kwargs:
            supported_kwargs['write_timeout'] = kwargs.pop('write_timeout')
        if 'connect_timeout' in kwargs:
            supported_kwargs['connect_timeout'] = kwargs.pop('connect_timeout')
        if 'pool_timeout' in kwargs:
            supported_kwargs['pool_timeout'] = kwargs.pop('pool_timeout')
        
        # Remove any unsupported kwargs that might cause issues
        kwargs.pop('http2', None)
        kwargs.pop('limits', None)
        kwargs.pop('connection_pool_size', None)
        
        # Initialize with only supported parameters
        super().__init__(*args, **supported_kwargs)
        
        # Store settings for retry logic
        self.max_retries = 5
        self.base_delay = 1.0
        self.max_delay = 30.0

    async def do_request(self, *args, **kwargs):
        """Perform request with retry logic"""
        attempt = 0
        last_exception = None
        
        while attempt < self.max_retries:
            try:
                # Attempt the request
                return await super().do_request(*args, **kwargs)
                
            except Exception as e:
                attempt += 1
                last_exception = e
                
                if attempt < self.max_retries:
                    # Calculate delay with exponential backoff and jitter
                    delay = min(self.base_delay * (2 ** (attempt - 1)) + random.uniform(0, 0.1), self.max_delay)
                    logger.warning(f"Request failed (attempt {attempt}/{self.max_retries}): {str(e)}. Retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {str(e)}")
                    raise last_exception

class FacebookContentBot:
    """Main bot class for handling Telegram interactions."""
    
    def __init__(self):
        """Initialize the bot with configuration."""
        # Load config and services
        self.config = ConfigManager()
        self.ai_generator = AIContentGenerator(self.config)
        self.airtable = AirtableConnector(self.config)
        
        # Configure request parameters with longer timeouts
        request = RetryingRequest(
            read_timeout=30.0,
            write_timeout=30.0,
            connect_timeout=20.0,
            pool_timeout=20.0
        )
        
        # Initialize bot and application
        self.application = Application.builder().token(self.config.telegram_bot_token).request(request).build()
        
        # Initialize user sessions
        self.user_sessions = {}
        
        # Set up command handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("series", self._series_command))
        self.application.add_handler(CommandHandler("continue", self._continue_command))
        self.application.add_handler(CommandHandler("batch", self._batch_command))
        self.application.add_handler(CommandHandler("project", self._project_command))
        self.application.add_handler(CommandHandler("done", self._done_command))
        self.application.add_handler(CommandHandler("strategy", self._strategy_command))
        self.application.add_handler(CommandHandler("cancel", self._cancel_batch_command))
        
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
            'post_count': 0,
            'state': None # To manage multi-step commands like /continue
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
        """Update the session context for AI continuity with 5-post limit."""
        if user_id not in self.user_sessions:
            return
        
        session = self.user_sessions[user_id]
        posts = session['posts']
        
        if not posts:
            session['session_context'] = ""
            return
        
        # Limit context to last 5 posts for better performance and focus
        recent_posts = posts[-5:]
        
        # Create context summary for AI
        context_parts = [
            f"Series: {len(recent_posts)}/{len(posts)} posts created from {session['filename']}",
            f"Original project: {session['original_markdown'][:200]}...",
            ""
        ]
        
        for post in recent_posts:
            context_parts.append(f"Post {post['post_id']}: {post['tone_used']} tone")
            context_parts.append(f"Content: {post['content_summary']}")
            if post['relationship_type']:
                context_parts.append(f"Relationship: {post['relationship_type']}")
            context_parts.append("")
        
        session['session_context'] = "\n".join(context_parts)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special characters for MarkdownV2 format."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _format_message(self, text: str, use_markdown: bool = False) -> Dict[str, str]:
        """Format message with proper escaping and parse mode."""
        if not use_markdown:
            return {'text': text, 'parse_mode': None}
        
        escaped_text = self._escape_markdown(text)
        return {'text': escaped_text, 'parse_mode': ParseMode.MARKDOWN_V2}

    async def _send_formatted_message(self, update_or_query, text: str, use_markdown: bool = False, 
                                    reply_markup: Optional[InlineKeyboardMarkup] = None, document: Optional[BytesIO] = None):
        """Send a properly formatted message with error handling."""
        try:
            message_params = self._format_message(text, use_markdown)
            
            if document:
                # Send document with caption
                if isinstance(update_or_query, Update):
                    return await update_or_query.message.reply_document(
                        document=document,
                        caption=message_params['text'][:1024],  # Telegram caption limit
                        parse_mode=message_params.get('parse_mode'),
                        reply_markup=reply_markup
                    )
                else:
                    # Can't edit a message to include a document, send new message
                    return await update_or_query.message.reply_document(
                        document=document,
                        caption=message_params['text'][:1024],
                        parse_mode=message_params.get('parse_mode'),
                        reply_markup=reply_markup
                    )
            
            # Regular text message
            if isinstance(update_or_query, Update):
                return await update_or_query.message.reply_text(
                    **message_params,
                    reply_markup=reply_markup
                )
            elif hasattr(update_or_query, 'message'):  # CallbackQuery
                try:
                    # Try to edit existing message
                    return await update_or_query.message.edit_text(
                        **message_params,
                        reply_markup=reply_markup
                    )
                except Exception as edit_error:
                    # If editing fails, send a new message
                    logger.warning(f"Failed to edit message: {edit_error}")
                    return await update_or_query.message.reply_text(
                        **message_params,
                        reply_markup=reply_markup
                    )
            else:  # Message object
                return await update_or_query.reply_text(
                    **message_params,
                    reply_markup=reply_markup
                )
                
        except Exception as e:
            logger.error(f"Failed to send formatted message: {str(e)}")
            # Send plain text as fallback
            try:
                fallback_text = text[:4000]  # Truncate if too long
                if isinstance(update_or_query, Update):
                    return await update_or_query.message.reply_text(
                        text=fallback_text,
                        reply_markup=reply_markup
                    )
                elif hasattr(update_or_query, 'message'):
                    return await update_or_query.message.reply_text(
                        text=fallback_text,
                        reply_markup=reply_markup
                    )
                else:
                    return await update_or_query.reply_text(
                        text=fallback_text,
                        reply_markup=reply_markup
                    )
            except Exception as fallback_error:
                logger.error(f"Failed to send fallback message: {fallback_error}")
                return None

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🚀 Welcome to the AI Facebook Content Generator!\n\n"
            "I help you transform your Markdown project documentation into engaging Facebook posts using AI.\n\n"
            "How it works:\n"
            "1. Send me a .md file with your project documentation\n"
            "2. I'll analyze it and generate a Facebook post using one of 5 brand tones\n"
            "3. You can review, approve, or ask me to regenerate\n"
            "4. Approved posts are saved to your Airtable for publishing\n\n"
            "Commands:\n"
            "• /help - Show this help message\n"
            "• /status - Check system status\n\n"
            "Ready to get started?\n"
            "Just send me a markdown file! 📄"
        )
        await self._send_formatted_message(update, welcome_message)
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🎯 AI Facebook Content Generator Help\n\n"
            "How to use:\n"
            "1. Send a markdown file (.md or .mdc extension)\n"
            "2. Choose a tone (optional) or let AI decide\n"
            "3. Review the generated post\n"
            "4. Approve ✅ or Regenerate 🔄\n\n"
            "Brand Tones Available:\n"
            "• 🧩 Behind-the-Build\n"
            "• 💡 What Broke\n"
            "• 🚀 Finished & Proud\n"
            "• 🎯 Problem → Solution → Result\n"
            "• 📓 Mini Lesson\n\n"
            "File Requirements:\n"
            "• .md or .mdc file extension\n"
            "• Max size: 10MB\n"
            "• Text content about your automation/AI projects\n\n"
            "Commands:\n"
            "• /start - Welcome message\n"
            "• /status - Check system status\n"
            "• /help - This help message\n\n"
            "Need help? Just send a markdown file to begin! 🚀"
        )
        await self._send_formatted_message(update, help_message)
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        try:
            # Test connections
            airtable_status = "✅ Connected" if self.airtable.test_connection() else "❌ Failed"
            
            # Get model information
            model_info = self.ai_generator.get_model_info()
            
            # Get recent drafts count
            recent_drafts = self.airtable.get_recent_drafts(limit=5)
            drafts_count = len(recent_drafts)
            
            status_message = f"""📊 System Status

Services:
• Airtable: {airtable_status}
• AI Provider: ✅ {model_info['provider']}
• Model: {model_info['model']}
• Telegram Bot: ✅ Running

AI Model Details:
• {model_info['description']}
• Max tokens: {model_info['max_tokens_supported']}

Recent Activity:
• Drafts in last 24h: {drafts_count}

System Ready! 🚀"""
            
            await self._send_formatted_message(update, status_message)
            
        except Exception as e:
            error_message = f"❌ System Error: {str(e)}"
            await self._send_formatted_message(update, error_message)
    
    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads."""
        document: Document = update.message.document
        user_id = update.effective_user.id
        
        # Validate file
        if not (document.file_name.endswith('.md') or document.file_name.endswith('.mdc')):
            await self._send_formatted_message(update, "❌ Please send a `.md` or `.mdc` (Markdown) file only.")
            return
        
        if document.file_size > self.config.max_file_size_mb * 1024 * 1024:
            await self._send_formatted_message(update, f"❌ File too large. Max size: {self.config.max_file_size_mb}MB")
            return
        
        try:
            # Send processing message
            processing_msg = await self._send_formatted_message(update, "📄 **Processing your markdown file...**\n\n"
                "⏳ Analyzing content...")
            
            # Download and read the file
            file = await document.get_file()
            file_content = await file.download_as_bytearray()
            markdown_content = file_content.decode('utf-8')
            
            # Check if we're in batch mode
            session = self.user_sessions.get(user_id, {})
            if session.get('mode') == 'multi' and session.get('state') == 'collecting_files':
                # Handle batch mode upload
                if len(session.get('files', [])) >= 8:
                    await self._send_formatted_message(processing_msg, "❌ Maximum number of files (8) reached. Use /done to proceed.")
                    return
                
                # Add file to batch
                file_data = {
                    'file_id': str(uuid.uuid4()),
                    'filename': document.file_name,
                    'content': markdown_content,
                    'upload_timestamp': datetime.now().isoformat(),
                    'processing_status': 'pending'
                }
                
                if 'files' not in session:
                    session['files'] = []
                session['files'].append(file_data)
                session['last_activity'] = datetime.now().isoformat()
                
                # Update processing message with batch status
                files_count = len(session['files'])
                await self._send_formatted_message(processing_msg, f"✅ **File {files_count}/8 Added to Batch**\n\n"
                    f"📁 {document.file_name}\n"
                    f"📊 Size: {document.file_size/1024:.1f}KB\n\n"
                    "Upload more files or use:\n"
                    "• `/project` - Generate project overview\n"
                    "• `/strategy` - Show content strategy\n"
                    "• `/done` - Finish uploading and proceed")
                
            else:
                # Single file mode
                session = self._initialize_session(user_id, markdown_content, document.file_name)
                await processing_msg.delete()
                await self._show_initial_tone_selection(update, context, session)
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            await self._send_formatted_message(update, f"❌ **Error processing file:** {str(e)}")

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
            
            # Generate the post with context awareness and business audience
            if is_regeneration and tone_preference:
                post_data = self.ai_generator.regenerate_post(
                    markdown_content, 
                    feedback=f"User requested {tone_preference} tone",
                    tone_preference=tone_preference,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=relationship_type,
                    parent_post_id=parent_post_id,
                    audience_type='business'
                )
            else:
                post_data = self.ai_generator.generate_facebook_post(
                    markdown_content, 
                    user_tone_preference=tone_preference,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=relationship_type,
                    parent_post_id=parent_post_id,
                    audience_type='business'
                )
            
            # Store in session
            self.user_sessions[user_id]['current_draft'] = post_data
            
            # Show the post to the user - create a response object for the update
            post_content = post_data.get('post_content', 'No content generated')
            tone_used = post_data.get('tone_used', 'Unknown')
            tone_reason = post_data.get('tone_reason', 'No reason provided')
            
            # Limit content display to prevent message overflow
            display_content = post_content[:1000] + "..." if len(post_content) > 1000 else post_content
            display_reason = tone_reason[:200] + "..." if len(tone_reason) > 200 else tone_reason
            
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
            
            # Create the message
            post_preview = f"""🎯 Generated Facebook Post

Tone: {tone_used}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?"""
            
            await self._send_formatted_message(update, self._truncate_message(post_preview), reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            await self._send_formatted_message(update, f"❌ Error generating post: {str(e)}")
    
    async def _show_generated_post(self, query, post_data: Dict, session: Dict):
        """Show the generated post with standard review options."""
        # Get post content and ensure it's not too long
        post_content = post_data.get('post_content', 'No content generated')
        tone_used = post_data.get('tone_used', 'Unknown')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Context information
        context_info = ""
        if session.get('posts'):
            context_info = f" (Post #{session['post_count'] + 1} in series)"
        
        # Use consistent content formatting
        display_content, display_reason = self._format_content_for_display(post_content, tone_reason)
        
        # Create inline keyboard
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
        
        # Create the message
        post_preview = f"""🎯 Generated Facebook Post

Tone Used: {tone_used}{context_info}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?"""
        
        await self._send_formatted_message(query, self._truncate_message(post_preview), reply_markup=reply_markup)
    
    def _format_content_for_display(self, post_content: str, tone_reason: str):
        """Format post content and tone reason for display."""
        # Limit content display to prevent message overflow
        display_content = post_content[:3000] + "..." if len(post_content) > 3000 else post_content
        display_reason = tone_reason[:200] + "..." if len(tone_reason) > 200 else tone_reason
        
        return display_content, display_reason

    async def _send_new_post_message_from_update(self, update: Update, post_data: Dict, session: Dict):
        """Send a new post message from an Update object (not CallbackQuery)."""
        # This is similar to _show_generated_post but works with Update objects
        post_content = post_data.get('post_content', 'No content generated')
        tone_used = post_data.get('tone_used', 'Unknown')
        tone_reason = post_data.get('tone_reason', 'No reason provided')
        
        # Context information
        context_info = ""
        if session.get('posts'):
            context_info = f" (Post #{session['post_count'] + 1} in series)"
        
        # Use consistent content formatting
        display_content, display_reason = self._format_content_for_display(post_content, tone_reason)
        
        # Create inline keyboard
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
        
        # Create the message
        post_preview = f"""🎯 Generated Facebook Post

Tone Used: {tone_used}{context_info}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?"""
        
        await self._send_formatted_message(update, self._truncate_message(post_preview), reply_markup=reply_markup)
    
    def _create_callback_data(self, action: str, **kwargs) -> str:
        """Create standardized callback data string."""
        data = {'action': action}
        data.update(kwargs)
        # Convert to string, max 64 bytes as per Telegram limits
        return str(data)[:64]

    def _parse_callback_data(self, callback_data: str) -> Dict:
        """Parse callback data string into dictionary."""
        try:
            # Handle empty callback data
            if not callback_data:
                logger.warning("Empty callback data received")
                return {'action': 'error', 'reason': 'empty_data'}
            
            # If the data is a simple string (not a dict format)
            if not (callback_data.startswith('{') and callback_data.endswith('}')):
                return {'action': callback_data}
            
            # Remove curly braces and split by comma
            data_str = callback_data.strip('{}')
            parts = data_str.split(',')
            
            # Parse each key-value pair
            data = {}
            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    data[key.strip(" '")] = value.strip(" '")
            
            return data
        except Exception as e:
            logger.error(f"Error parsing callback data: {str(e)}")
            return {'action': 'error', 'reason': str(e)}

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries with error handling."""
        query = update.callback_query
        user_id = query.from_user.id
        
        try:
            # Parse callback data
            callback_data = query.data
            
            # Handle file selection callbacks
            if callback_data.startswith('select_file_'):
                if user_id in self.user_sessions:
                    await self._handle_file_selection(query, self.user_sessions[user_id])
                return
            
            # Handle initial tone selection callbacks
            if callback_data.startswith('initial_'):
                if user_id in self.user_sessions:
                    await self._handle_initial_tone_selection(query, self.user_sessions[user_id], callback_data)
                return
            
            # Handle tone change callbacks
            if callback_data.startswith('tone_'):
                if user_id in self.user_sessions:
                    await self._handle_tone_change_selection(query, self.user_sessions[user_id], callback_data)
                return
            
            # Handle other special callbacks
            if callback_data == "show_tone_previews":
                if user_id in self.user_sessions:
                    await self._show_tone_previews(query, self.user_sessions[user_id])
                return
            
            if callback_data == "back_to_initial_tone_selection":
                if user_id in self.user_sessions:
                    await self._show_initial_tone_selection_from_callback(query, self.user_sessions[user_id])
                return
            
            # Handle strategy callbacks  
            if callback_data in ["cancel_strategy", "use_ai_strategy", "customize_strategy", "manual_selection"]:
                if user_id in self.user_sessions:
                    await self._handle_strategy_callback(query, self.user_sessions[user_id])
                return
            
            # Handle follow-up relationship selection callbacks
            if callback_data.startswith('followup_rel_'):
                if user_id in self.user_sessions:
                    relationship_type = callback_data.replace('followup_rel_', '')
                    await self._handle_followup_relationship_selection(query, self.user_sessions[user_id], relationship_type)
                return
            
            # Parse other callback data
            callback_data = self._parse_callback_data(callback_data)
            action = callback_data.get('action', '')
            
            # Log the action for debugging
            logger.info(f"Handling callback action: {action}")
            
            # Handle session expiry
            if user_id not in self.user_sessions and action not in ['start', 'help', 'error']:
                await self._send_formatted_message(query, "❌ Session expired. Please start a new session.")
                return
            
            # Get session if exists
            session = self.user_sessions.get(user_id, {})
            
            # Map actions to handlers
            action_handlers = {
                'approve': lambda: self._approve_post(query, session),
                'regenerate': lambda: self._regenerate_post(query, session),
                'cancel': lambda: self._cancel_session(query, user_id),
                'change_tone': lambda: self._show_tone_options(query, session),
                'tone': lambda: self._handle_tone_selection(query, session, callback_data),
                'strategy': lambda: self._handle_strategy_callback(query, session),
                'export': lambda: self._handle_export_action(query, user_id, callback_data.get('type', '')),
                'series': lambda: self._handle_series_action(query, user_id, callback_data.get('type', '')),
                'post': lambda: self._handle_post_action(query, user_id, callback_data.get('type', '')),
                'error': lambda: self._handle_error_callback(query, callback_data.get('reason', 'unknown')),
                'use_ai_strategy': lambda: self._handle_ai_strategy(query, session),
                'customize_strategy': lambda: self._show_strategy_customization(query, session),
                'manual_selection': lambda: self._show_manual_file_selection(query, session),
                'manual_generate': lambda: self._handle_manual_generation(query, session),
                'manual_clear': lambda: self._handle_manual_clear(query, session),
                'back_to_strategy': lambda: self._show_strategy_options(query, session),
                'view_batch_posts': lambda: self._view_batch_posts(query, session),
                'export_batch': lambda: self._export_batch_series(query, session),
                'new_batch': lambda: self._start_new_batch(query, user_id),
                'back_to_post': lambda: self._show_current_post(query, session),
                # New follow-up post handlers
                'generate_followup': lambda: self._handle_followup_generation(query, session),
                'view_series': lambda: self._view_series(query, session),
                'export_current': lambda: self._export_current_post(query, session),
                'done_session': lambda: self._done_session(query, session),
                'cancel_followup': lambda: self._cancel_followup(query, session),
                'back_to_options': lambda: self._show_post_approval_options(query, session),
                'export_series': lambda: self._export_series(query, session)
            }
            
            # Get and execute handler
            handler = action_handlers.get(action)
            if handler:
                await handler()
            else:
                logger.warning(f"Unknown callback action: {action}")
                await self._send_formatted_message(query, "❌ Invalid action. Please try again.")
            
        except Exception as e:
            logger.error(f"Error handling callback: {str(e)}", exc_info=True)
            try:
                await self._send_formatted_message(
                    query,
                    "❌ An error occurred. Please try again or start a new session."
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {str(e2)}")

    async def _handle_error_callback(self, query, reason: str = 'unknown'):
        """Handle error callbacks gracefully."""
        error_messages = {
            'empty_data': "❌ Invalid callback data received",
            'unknown': "❌ There was an error processing your request"
        }
        message = error_messages.get(reason, error_messages['unknown'])
        await self._send_formatted_message(query, f"{message}. Please try again.")

    async def _handle_tone_selection(self, query, session: Dict, callback_data: Dict):
        """Handle tone selection with error handling."""
        try:
            tone = callback_data.get('tone', '')
            if tone == 'ai':
                await self._generate_with_ai_chosen_tone(query, session)
            else:
                await self._generate_with_initial_tone(query, session, tone)
        except Exception as e:
            logger.error(f"Error handling tone selection: {str(e)}")
            await self._send_formatted_message(
                query,
                "❌ Error selecting tone. Please try again."
            )
    
    async def _handle_tone_change_selection(self, query, session: Dict, callback_data: str):
        """Handle tone change selection from the change tone interface."""
        try:
            # Extract tone from callback data (e.g., "tone_mini_lesson" -> "mini_lesson")
            tone_key = callback_data.replace("tone_", "")
            
            # Map callback data back to proper tone names
            tone_mapping = {
                "behind_the_build": "Behind-the-Build",
                "what_broke": "What Broke", 
                "finished_proud": "Finished & Proud",
                "problem_solution_result": "Problem → Solution → Result",
                "mini_lesson": "Mini Lesson"
            }
            
            # Get the actual tone name
            actual_tone = tone_mapping.get(tone_key, tone_key.replace("_", " ").title())
            
            # Regenerate with the selected tone
            await self._regenerate_with_tone(query, session, actual_tone)
            
        except Exception as e:
            logger.error(f"Error handling tone change selection: {str(e)}")
            await self._send_formatted_message(
                query,
                "❌ Error changing tone. Please try again."
            )

    async def _handle_series_action(self, query, user_id: int, action_type: str):
        """Handle series-related actions with error handling."""
        try:
            if action_type == 'view':
                await self._show_series_overview(query, None)
            elif action_type == 'export':
                await self._show_export_options(query, self.user_sessions[user_id])
            elif action_type == 'manage':
                await self._show_post_management(query, user_id)
            else:
                await self._send_formatted_message(
                    query,
                    "❌ Invalid series action. Please try again."
                )
        except Exception as e:
            logger.error(f"Error handling series action: {str(e)}")
            await self._send_formatted_message(
                query,
                "❌ Error processing series action. Please try again."
            )

    async def _handle_continuation_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE, previous_post_text: str):
        """Process the pasted post text to generate a continuation."""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        
        await self._send_formatted_message(update, "⏳ Analyzing your post and generating a follow-up... this might take a moment.")
        
        try:
            # Generate continuation post
            post_data = await asyncio.to_thread(
                self.ai_generator.generate_continuation_post,
                previous_post_text,
                audience_type=session.get('audience_type', 'business') # Default to business
            )

            # Reset state after processing
            session['state'] = None
            
            # Use existing methods to show the post and get feedback
            session['current_draft'] = post_data
            await self._send_new_post_message_from_update(update, post_data, session)

        except Exception as e:
            logger.error(f"Error generating continuation post: {e}", exc_info=True)
            await self._send_formatted_message(update, f"❌ An error occurred while generating the follow-up post: {e}")
            session['state'] = None

    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle plain text messages, checking for session states."""
        user_id = update.effective_user.id
        text = update.message.text
        
        session = self.user_sessions.get(user_id)
        
        if session and session.get('state') == 'awaiting_continuation_input':
            await self._handle_continuation_post(update, context, text)
        else:
            # Default behavior for unexpected text
            await self._send_formatted_message(update, "Thanks for your message! If you want to generate a post, please send me a `.md` file. "
                "Use `/help` to see all commands.")

    async def _approve_post(self, query, session):
        """Approve and save the post to Airtable."""
        try:
            post_data = session['current_draft']
            filename = session['filename']
            
            # Create a title from filename for display purposes only
            display_title = filename.replace('.md', '').replace('_', ' ').title()
            
            # Save to Airtable
            record_id = self.airtable.save_draft(post_data, display_title, "📝 To Review")
            session['airtable_record_id'] = record_id
            
            # Add post to series using existing multi-post infrastructure
            user_id = query.from_user.id
            self._add_post_to_series(user_id, post_data, record_id)
            
            # Show success message with follow-up options
            success_message = f"""✅ Post Approved & Saved!

File: {filename}
Status: Ready for Facebook publishing
Airtable Record ID: {record_id}

Your post is now saved in Airtable with:
• Generated draft content
• AI tone analysis and reasoning
• Auto-extracted tags
• Content summary and length metrics
• Improvement suggestions

What would you like to do next?"""
            
            # Create keyboard with follow-up options
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Generate Follow-up Post", callback_data="generate_followup"),
                    InlineKeyboardButton("📋 View Series", callback_data="view_series")
                ],
                [
                    InlineKeyboardButton("📤 Export Current Post", callback_data="export_current"),
                    InlineKeyboardButton("✨ Done", callback_data="done_session")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, success_message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error saving post: {str(e)}")

    async def _handle_followup_generation(self, query, session):
        """Handle follow-up post generation request."""
        try:
            # Check if we have previous posts
            posts = session.get('posts', [])
            if not posts:
                await self._send_formatted_message(query, "❌ No posts in series to build upon.")
                return
            
            # Show relationship type selection
            await self._show_followup_relationship_selection(query, session)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error setting up follow-up generation: {str(e)}")

    async def _show_followup_relationship_selection(self, query, session):
        """Show relationship type selection for follow-up posts."""
        try:
            # Get relationship types from AI generator
            relationship_types = self.ai_generator.get_relationship_types()
            
            message = f"""🔄 Generate Follow-up Post

You have {len(session.get('posts', []))} post(s) in your series.

How should the new post relate to your previous posts?

Choose a relationship type:"""
            
            # Create keyboard with relationship options
            keyboard = []
            for key, display_name in relationship_types.items():
                keyboard.append([InlineKeyboardButton(display_name, callback_data=f"followup_rel_{key}")])
            
            # Add special option for AI to choose
            keyboard.append([InlineKeyboardButton("🤖 Let AI Choose Best Relationship", callback_data="followup_rel_ai_choose")])
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_followup")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error showing relationship options: {str(e)}")

    async def _handle_followup_relationship_selection(self, query, session, relationship_type):
        """Handle relationship type selection for follow-up posts."""
        try:
            # Get session context
            session_context = session.get('session_context', '')
            previous_posts = session.get('posts', [])
            
            # Generate follow-up post with the selected relationship type
            await self._send_formatted_message(query, f"🔄 Generating follow-up post with {relationship_type} relationship...\n\n"
                "⏳ This may take a moment...")
            
            # Use the original markdown content with context awareness
            markdown_content = session['original_markdown']
            
            # Determine parent post (use the most recent post)
            parent_post_id = str(previous_posts[-1]['post_id']) if previous_posts else None
            
            # Generate the follow-up post
            if relationship_type == 'ai_choose':
                # Let AI choose the best relationship
                post_data = self.ai_generator.generate_facebook_post(
                    markdown_content,
                    user_tone_preference=None,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=None,  # Let AI choose
                    parent_post_id=parent_post_id,
                    audience_type='business'
                )
            else:
                # Use the selected relationship type
                post_data = self.ai_generator.generate_facebook_post(
                    markdown_content,
                    user_tone_preference=None,
                    session_context=session_context,
                    previous_posts=previous_posts,
                    relationship_type=relationship_type,
                    parent_post_id=parent_post_id,
                    audience_type='business'
                )
            
            # Store the generated post
            session['current_draft'] = post_data
            
            # Show the generated follow-up post
            await self._show_generated_post(query, post_data, session)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error generating follow-up post: {str(e)}")

    async def _view_series(self, query, session):
        """Show the current series of posts."""
        try:
            posts = session.get('posts', [])
            if not posts:
                await self._send_formatted_message(query, "❌ No posts in series yet.")
                return
            
            # Create series summary
            series_message = f"""📋 Your Post Series

File: {session['filename']}
Total Posts: {len(posts)}

Posts in Series:"""
            
            for i, post in enumerate(posts, 1):
                series_message += f"\n\n**Post {i}:**"
                series_message += f"\n• Tone: {post['tone_used']}"
                series_message += f"\n• Created: {post['approved_at'][:10]}"
                if post.get('relationship_type'):
                    series_message += f"\n• Relationship: {post['relationship_type']}"
                series_message += f"\n• Preview: {post['content_summary']}"
            
            # Add action buttons
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Generate Follow-up", callback_data="generate_followup"),
                    InlineKeyboardButton("📤 Export All", callback_data="export_series")
                ],
                [
                    InlineKeyboardButton("⬅️ Back", callback_data="back_to_options")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, series_message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error showing series: {str(e)}")

    async def _done_session(self, query, session):
        """Complete the session and show final summary."""
        try:
            posts = session.get('posts', [])
            filename = session['filename']
            
            summary_message = f"""✅ Session Complete!

File: {filename}
Posts Generated: {len(posts)}

All posts have been saved to Airtable and are ready for Facebook publishing.

Next Steps:
1. Open your Airtable Content Tracker
2. Find your approved posts
3. Copy the content to Facebook
4. Update the "Post URL (After Publishing)" field in Airtable

Send another markdown file to generate more posts!"""
            
            await self._send_formatted_message(query, summary_message)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error completing session: {str(e)}")

    async def _regenerate_post(self, query, session):
        """Regenerate the post with general feedback."""
        try:
            await self._send_formatted_message(query, "🔄 Regenerating your post...\n\n"
                "⏳ Creating a new version with different approach...")
            
            # Regenerate with general feedback
            markdown_content = session['original_markdown']
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback="User requested regeneration - try different tone or approach"
            )
            
            session['current_draft'] = post_data
            
            # Show the regenerated post
            await self._show_generated_post(query, post_data, session)
            
        except Exception as e:
            logger.error(f"Error in _regenerate_post: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error regenerating post: {str(e)}")
    
    async def _regenerate_with_tone(self, query, session, tone: str):
        """Regenerate the post with a specific tone."""
        try:
            await self._send_formatted_message(query, f"🎨 Regenerating with '{tone}' tone...\n\n"
                "⏳ Creating a new version with the selected tone...")
            
            # Get the original markdown content
            original_markdown = session.get('original_markdown', '')
            
            # Regenerate the post with specific tone
            post_data = self.ai_generator.regenerate_post(
                original_markdown, 
                feedback=f"User requested {tone} tone",
                tone_preference=tone
            )
            
            # Update session with new draft
            session['current_draft'] = post_data
            session['last_activity'] = datetime.now()
            
            # Show the regenerated post
            await self._show_generated_post(query, post_data, session)
            
        except Exception as e:
            logger.error(f"Error regenerating with tone {tone}: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error regenerating post: {str(e)}")

    async def _cancel_session(self, query, user_id):
        """Cancel current session."""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await self._send_formatted_message(query, "❌ Session cancelled.\n\n"
            "Send a new markdown file to start over! 📄")

    async def _handle_post_action(self, query, user_id: int, action: str):
        """Handle individual post actions like delete, edit, regenerate."""
        if user_id not in self.user_sessions:
            await self._send_formatted_message(query, "❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        try:
            if action.startswith("post_delete_"):
                post_id = int(action.replace("post_delete_", ""))
                await self._delete_post(query, session, post_id)
            elif action.startswith("post_regenerate_"):
                post_id = int(action.replace("post_regenerate_", ""))
                await self._regenerate_individual_post(query, session, post_id)
            elif action.startswith("post_view_"):
                post_id = int(action.replace("post_view_", ""))
                await self._view_individual_post(query, session, post_id)
            elif action == "post_confirm_delete":
                await self._confirm_delete_post(query, session)
            elif action == "post_cancel_delete":
                await self._cancel_delete_post(query, session)
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error managing post: {str(e)}")
    
    async def _delete_post(self, query, session, post_id: int):
        """Delete a post from the series."""
        posts = session.get('posts', [])
        post_to_delete = None
        
        for post in posts:
            if post['post_id'] == post_id:
                post_to_delete = post
                break
        
        if not post_to_delete:
            await self._send_formatted_message(query, "❌ Post not found.")
            return
        
        # Store deletion context in session
        session['pending_delete'] = {
            'post_id': post_id,
            'post_data': post_to_delete
        }
        
        # Show confirmation
        confirmation_message = f"""
⚠️ **Confirm Post Deletion**

**Post {post_id}:** {post_to_delete['tone_used']}
**Content:** {post_to_delete.get('content_summary', 'No summary')}
**Created:** {post_to_delete.get('approved_at', 'Unknown')}

**Warning:** This action cannot be undone. The post will be removed from your series and marked as deleted in Airtable.

Are you sure you want to delete this post?
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🗑️ Yes, Delete", callback_data="post_confirm_delete"),
                InlineKeyboardButton("❌ Cancel", callback_data="post_cancel_delete")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_formatted_message(query, confirmation_message.strip(), reply_markup=reply_markup)
    
    async def _confirm_delete_post(self, query, session):
        """Confirm and execute post deletion."""
        pending_delete = session.get('pending_delete')
        if not pending_delete:
            await self._send_formatted_message(query, "❌ No pending deletion found.")
            return
        
        post_id = pending_delete['post_id']
        post_data = pending_delete['post_data']
        
        # Remove from session
        posts = session.get('posts', [])
        session['posts'] = [p for p in posts if p['post_id'] != post_id]
        session['post_count'] -= 1
        
        # Update Airtable record to mark as deleted
        try:
            record_id = post_data.get('airtable_record_id')
            if record_id:
                self.airtable.airtable.update(record_id, {
                    'Review Status': '🗑️ Deleted',
                    'AI Notes or Edits': f"Post deleted from series on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                })
        except Exception as e:
            logger.warning(f"Failed to update Airtable record: {e}")
        
        # Clear pending deletion
        del session['pending_delete']
        
        # Update session context
        self._update_session_context(query.from_user.id)
        
        await self._send_formatted_message(query, f"✅ **Post {post_id} deleted successfully**\n\n"
            f"The post has been removed from your series and marked as deleted in Airtable.")
        
        # Return to series overview after 2 seconds
        await asyncio.sleep(2)
        await self._show_series_overview(query, None)
    
    async def _cancel_delete_post(self, query, session):
        """Cancel post deletion."""
        if 'pending_delete' in session:
            del session['pending_delete']
        
        await self._send_formatted_message(query, "❌ **Post deletion cancelled**\n\n"
            "No changes were made to your series.")
        
        # Return to series overview
        await asyncio.sleep(1)
        await self._show_series_overview(query, None)
    
    async def _regenerate_individual_post(self, query, session, post_id: int):
        """Regenerate a specific post from the series."""
        posts = session.get('posts', [])
        post_to_regenerate = None
        
        for post in posts:
            if post['post_id'] == post_id:
                post_to_regenerate = post
                break
        
        if not post_to_regenerate:
            await self._send_formatted_message(query, "❌ Post not found.")
            return
        
        await self._send_formatted_message(query, f"🔄 **Regenerating Post {post_id}...**\n\n"
            "⏳ Creating a new version while preserving context...")
        
        # Regenerate the post with same context
        try:
            # Get context for regeneration
            session_context = session.get('session_context', '')
            previous_posts = session.get('posts', [])
            
            # Create a mock current_draft to preserve context
            session['current_draft'] = {
                'relationship_type': post_to_regenerate.get('relationship_type'),
                'parent_post_id': post_to_regenerate.get('parent_post_id')
            }
            
            markdown_content = session['original_markdown']
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback=f"User requested regeneration of Post {post_id}",
                session_context=session_context,
                previous_posts=previous_posts,
                relationship_type=post_to_regenerate.get('relationship_type'),
                parent_post_id=post_to_regenerate.get('parent_post_id')
            )
            
            # Update the post in the series
            for i, post in enumerate(posts):
                if post['post_id'] == post_id:
                    posts[i].update({
                        'content': post_data.get('post_content', ''),
                        'tone_used': post_data.get('tone_used', 'Unknown'),
                        'content_summary': post_data.get('post_content', '')[:100] + '...' if len(post_data.get('post_content', '')) > 100 else post_data.get('post_content', ''),
                        'approved_at': datetime.now().isoformat()
                    })
                    break
            
            # Update Airtable record
            try:
                record_id = post_to_regenerate.get('airtable_record_id')
                if record_id:
                    self.airtable.airtable.update(record_id, {
                        'Generated Draft': post_data.get('post_content', ''),
                        'AI Notes or Edits': f"Post regenerated on {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{post_data.get('tone_reason', '')}"
                    })
            except Exception as e:
                logger.warning(f"Failed to update Airtable record: {e}")
            
            # Update session context
            self._update_session_context(query.from_user.id)
            
            await self._send_formatted_message(query, f"✅ Post {post_id} regenerated successfully\n\n"
                f"New tone: {post_data.get('tone_used', 'Unknown')}\n"
                f"Content preview: {post_data.get('post_content', '')[:100]}...\n\n"
                f"The post has been updated in your series and Airtable.")
            
            # Return to series overview after 3 seconds
            await asyncio.sleep(3)
            await self._show_series_overview(query, None)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error regenerating post: {str(e)}")
    
    async def _view_individual_post(self, query, session, post_id: int):
        """View details of an individual post."""
        posts = session.get('posts', [])
        post_to_view = None
        
        for post in posts:
            if post['post_id'] == post_id:
                post_to_view = post
                break
        
        if not post_to_view:
            await self._send_formatted_message(query, "❌ Post not found.")
            return
        
        # Format post details
        post_content = post_to_view.get('content', '')
        if len(post_content) > 3000:
            display_content = post_content[:3000] + "\n\n📝 [Content truncated for display]"
        else:
            display_content = post_content
        
        post_details = f"""📝 **Post {post_id} Details**

**Tone:** {post_to_view['tone_used']}
**Created:** {post_to_view.get('approved_at', 'Unknown')}
**Airtable ID:** {post_to_view.get('airtable_record_id', 'Unknown')}

**Relationship Info:**
• Type: {post_to_view.get('relationship_type', 'None')}
• Parent Post: {post_to_view.get('parent_post_id', 'None')}

**Content:**
───────────────────────────
{display_content}
───────────────────────────"""
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Regenerate", callback_data=f"post_regenerate_{post_id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"post_delete_{post_id}")
            ],
            [
                InlineKeyboardButton("⬅️ Back to Series", callback_data="series_refresh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_formatted_message(query, post_details.strip(), reply_markup=reply_markup)
    
    async def _show_post_management(self, query, user_id: int):
        """Show post management interface with all posts."""
        if user_id not in self.user_sessions:
            await self._send_formatted_message(query, "❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        posts = session.get('posts', [])
        
        if not posts:
            await self._send_formatted_message(query, "❌ **No posts to manage**\n\n"
                "Create some posts first before managing them.")
            return
        
        # Create post management message
        management_message = f"""
🔧 **Post Management**

Series: {session.get('filename', 'Unknown')}
Total Posts: {len(posts)}

**Select a post to manage:**
        """
        
        # Create buttons for each post
        keyboard = []
        for post in posts:
            post_snippet = post.get('content_summary', 'No summary')[:40] + '...'
            tone_emoji = self._get_tone_emoji(post['tone_used'])
            button_text = f"{tone_emoji} Post {post['post_id']}: {post_snippet}"
            callback_data = f"post_view_{post['post_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([InlineKeyboardButton("⬅️ Back to Series", callback_data="series_refresh")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_formatted_message(query, management_message.strip(), reply_markup=reply_markup)
    
    async def _show_initial_tone_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, session: Dict):
        """Show enhanced tone selection interface before generation."""
        user_id = update.effective_user.id
        
        # Set session state for tone selection
        session['workflow_state'] = 'awaiting_initial_tone_selection'
        
        # Analyze content to provide smart recommendations
        markdown_content = session['original_markdown']
        content_analysis = self._analyze_content_for_tone_recommendations(markdown_content)
        
        # Get all tone options
        tone_options = self.ai_generator.get_tone_options()
        
        # Create message with smart recommendations
        filename = session['filename']
        file_display = filename.replace('.md', '').replace('_', ' ').title()
        
        message_parts = [
            f"🎨 **Choose Your Tone Style**",
            f"📄 File: {file_display}",
            ""
        ]
        
        # Add dynamic recommendations (only if we have good matches)
        if content_analysis['recommended_tones']:
            message_parts.extend([
                "**Smart Recommendations:**",
                f"• 🎯 **{content_analysis['recommended_tones'][0]}** - {content_analysis['reasons'][content_analysis['recommended_tones'][0]]}",
                ""
            ])
        
        message_parts.extend([
            "**All Available Tones:**",
            "Choose the style that best fits your content:"
        ])
        
        # Create 2-column keyboard layout for all tone options
        keyboard = []
        
        # Create tone buttons in 2 columns
        for i in range(0, len(tone_options), 2):
            row = []
            
            # First column
            tone1 = tone_options[i]
            is_recommended1 = tone1 in content_analysis['recommended_tones']
            emoji1 = "🎯" if is_recommended1 else "🎨"
            label1 = f"{emoji1} {tone1}"
            if is_recommended1:
                label1 += " ⭐"
            
            callback_data1 = self._create_tone_callback_data(tone1)
            row.append(InlineKeyboardButton(label1, callback_data=f"initial_{callback_data1}"))
            
            # Second column (if available)
            if i + 1 < len(tone_options):
                tone2 = tone_options[i + 1]
                is_recommended2 = tone2 in content_analysis['recommended_tones']
                emoji2 = "🎯" if is_recommended2 else "🎨"
                label2 = f"{emoji2} {tone2}"
                if is_recommended2:
                    label2 += " ⭐"
                
                callback_data2 = self._create_tone_callback_data(tone2)
                row.append(InlineKeyboardButton(label2, callback_data=f"initial_{callback_data2}"))
            
            keyboard.append(row)
        
        # Add special options in a separate row
        keyboard.extend([
            [
                InlineKeyboardButton("🤖 AI Choose", callback_data="initial_ai_choose"),
                InlineKeyboardButton("📊 Previews", callback_data="show_tone_previews")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_formatted_message(update, "\n".join(message_parts), reply_markup=reply_markup)
    
    def _analyze_content_for_tone_recommendations(self, markdown_content: str) -> Dict:
        """Analyze content to provide intelligent tone recommendations."""
        content_lower = markdown_content.lower()
        
        # Content analysis patterns with scoring
        tone_scores = {
            'Behind-the-Build': 0,
            'What Broke': 0,
            'Problem → Solution → Result': 0,
            'Finished & Proud': 0,
            'Mini Lesson': 0
        }
        
        # Behind-the-Build indicators
        build_indicators = ['built', 'created', 'developed', 'implemented', 'constructed', 'assembled']
        if any(word in content_lower for word in build_indicators):
            tone_scores['Behind-the-Build'] += 3
        if any(word in content_lower for word in ['cursor', 'ai', 'automation', 'bot', 'system']):
            tone_scores['Behind-the-Build'] += 2
        
        # What Broke indicators
        broke_indicators = ['broke', 'failed', 'error', 'bug', 'fix', 'debug', 'issue', 'problem', 'trouble']
        if any(word in content_lower for word in broke_indicators):
            tone_scores['What Broke'] += 3
        if any(word in content_lower for word in ['solved', 'resolved', 'fixed', 'working']):
            tone_scores['What Broke'] += 1
        
        # Problem → Solution → Result indicators
        problem_indicators = ['problem', 'issue', 'challenge', 'solved', 'solution', 'result', 'outcome']
        if any(word in content_lower for word in problem_indicators):
            tone_scores['Problem → Solution → Result'] += 3
        if any(word in content_lower for word in ['because', 'so', 'therefore', 'thus']):
            tone_scores['Problem → Solution → Result'] += 1
        
        # Finished & Proud indicators
        finished_indicators = ['completed', 'finished', 'shipped', 'deployed', 'launched', 'done', 'successful']
        if any(word in content_lower for word in finished_indicators):
            tone_scores['Finished & Proud'] += 3
        if any(word in content_lower for word in ['working', 'functional', 'operational']):
            tone_scores['Finished & Proud'] += 1
        
        # Mini Lesson indicators
        lesson_indicators = ['learned', 'insight', 'principle', 'lesson', 'discovered', 'realized', 'found']
        if any(word in content_lower for word in lesson_indicators):
            tone_scores['Mini Lesson'] += 3
        if any(word in content_lower for word in ['important', 'key', 'critical', 'essential']):
            tone_scores['Mini Lesson'] += 1
        
        # Add some randomness to avoid always showing the same recommendations
        for tone in tone_scores:
            tone_scores[tone] += random.uniform(0, 1)
        
        # Sort tones by score and get top recommendations
        sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Only recommend tones with meaningful scores (at least 2 points)
        recommendations = [tone for tone, score in sorted_tones if score >= 2]
        
        # Limit to top 2-3 recommendations
        recommendations = recommendations[:min(3, len(recommendations))]
        
        # If no strong recommendations, suggest the top 2 based on general content
        if not recommendations:
            recommendations = [sorted_tones[0][0], sorted_tones[1][0]]
        
        # Create reasons for recommendations
        reasons = {
            'Behind-the-Build': 'Content shows building/development process',
            'What Broke': 'Content involves troubleshooting/fixing issues',
            'Problem → Solution → Result': 'Content follows problem-solving narrative',
            'Finished & Proud': 'Content celebrates completion/achievement',
            'Mini Lesson': 'Content shares learning/insights'
        }
        
        return {
            'recommended_tones': recommendations,
            'reasons': reasons,
            'content_keywords': self._extract_content_keywords(markdown_content),
            'tone_scores': tone_scores  # For debugging
        }
    
    def _extract_content_keywords(self, content: str) -> List[str]:
        """Extract key technical terms from content."""
        keywords = []
        technical_terms = [
            'ai', 'automation', 'bot', 'api', 'database', 'machine learning',
            'telegram', 'python', 'javascript', 'react', 'backend', 'frontend',
            'cursor', 'openai', 'gpt', 'claude', 'airtable', 'webhook'
        ]
        
        content_lower = content.lower()
        for term in technical_terms:
            if term in content_lower:
                keywords.append(term)
        
        return keywords[:5]  # Return top 5 keywords
    
    def _create_tone_callback_data(self, tone: str) -> str:
        """Create callback data for tone selection."""
        # Create callback data from tone (consistent with existing method)
        if ' ' in tone:
            callback_data = f"tone_{tone.split(' ', 1)[1].replace(' ', '_').replace('→', 'to').lower()}"
        else:
            callback_data = f"tone_{tone.replace('→', 'to').lower()}"
        
        # Ensure callback_data is not too long (Telegram limit is 64 characters)
        if len(callback_data) > 60:
            callback_data = callback_data[:60]
        
        return callback_data
    
    async def _show_tone_previews(self, query, session):
        """Show tone previews with examples."""
        tone_examples = {
            'Behind-the-Build': "I built this system to solve a specific problem I was having...",
            'What Broke': "Something didn't work as expected with my latest automation...",
            'Finished & Proud': "Got this working after some trial and error...",
            'Problem → Solution → Result': "I was spending hours manually processing data...",
            'Mini Lesson': "Building this reminded me that simple solutions often work best..."
        }
        
        message_parts = [
            "📖 **Tone Style Previews**",
            "",
            "Here's how each tone typically starts:"
        ]
        
        for tone, example in tone_examples.items():
            message_parts.extend([
                f"**{tone}:**",
                f"_{example}_",
                ""
            ])
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Back to Selection", callback_data="back_to_initial_tone_selection")]
        ]
        
        await self._send_formatted_message(query, "\n".join(message_parts), reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _handle_export_action(self, query, user_id: int, action: str):
        """Handle export actions for series data."""
        if user_id not in self.user_sessions:
            await self._send_formatted_message(query, "❌ Session expired. Please upload a new file.")
            return
        
        session = self.user_sessions[user_id]
        
        try:
            if action == "export_markdown":
                await self._export_markdown(query, session)
            elif action == "export_summary":
                await self._export_summary(query, session)
            elif action == "export_airtable":
                await self._export_airtable_link(query, session)
        except Exception as e:
            await self._send_formatted_message(query, f"❌ **Error exporting series:** {str(e)}")
    
    def run(self):
        """Start the bot."""
        try:
            # Validate configuration
            self.config.validate_config()
            
            logger.info("Starting Facebook Content Generator Bot...")
            
            # Log the correct AI provider and model
            model_info = self.ai_generator.get_model_info()
            logger.info(f"Using {model_info['provider']} model: {model_info['model']}")
            logger.info(f"Model description: {model_info['description']}")
            
            # Test Airtable connection
            if not self.airtable.test_connection():
                logger.warning("Airtable connection test failed - check your configuration")
            
            # Run the bot
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    async def _continue_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /continue command for content continuation."""
        user_id = update.effective_user.id
        
        # Ensure a session exists or create a placeholder
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {'state': None}

        self.user_sessions[user_id]['state'] = 'awaiting_continuation_input'
        
        await self._send_formatted_message(update, "📝 Content Continuation\n\n"
            "Please paste the full text of the Facebook post you want to continue. I'll analyze it and generate a natural follow-up for you.")
    
    def _truncate_message(self, message: str, max_length: int = 4000) -> str:
        """Truncate message if it's too long for Telegram."""
        if len(message) <= max_length:
            return message
        
        # Truncate the message to the maximum length allowed by Telegram
        # Telegram's MarkdownV2 has a limit of 4096 characters for messages.
        # We need to ensure we don't exceed this limit.
        # The original code had a max_length of 2000, but Telegram's limit is 4096.
        # Let's use 4000 as a safe truncation point.
        return message[:max_length] + "\n\n📝 [Content truncated for display - full version saved to Airtable]."
    
    async def _series_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /series command to show series overview."""
        user_id = update.effective_user.id
        
        # Check if user has an active session
        if user_id not in self.user_sessions:
            await self._send_formatted_message(update, "❌ **No active series found.**\n\n"
                "Upload a markdown file to start a new series! 📄")
            return
        
        # Show series overview
        await self._show_series_overview(update, context)
    
    async def _show_series_overview(self, update_or_query, context: ContextTypes.DEFAULT_TYPE):
        """Display comprehensive series overview."""
        # Handle both Update and CallbackQuery
        if hasattr(update_or_query, 'callback_query'):
            # This is a CallbackQuery from inline button
            user_id = update_or_query.from_user.id
            query = update_or_query
        else:
            # This is an Update from command
            user_id = update_or_query.effective_user.id
            query = None
        
        session = self.user_sessions[user_id]
        
        # Calculate series statistics
        stats = self._calculate_series_statistics(session['posts'])
        
        # Format series tree
        tree_display = self._format_series_tree(session['posts'])
        
        # Create series metadata info
        series_info = self._format_series_info(session)
        
        # Create overview message
        overview_message = f"""
📊 **Series Overview**

{series_info}

**Series Structure:**
{tree_display}

**Statistics:**
• Total Posts: {stats['total_posts']}
• Relationship Types: {', '.join(stats['relationship_types_used']) if stats['relationship_types_used'] else 'None'}
• Most Used Tone: {stats['most_used_tone']}
• Creation Timespan: {stats['creation_timespan']}

**Tone Distribution:**
{self._format_tone_distribution(stats['tone_distribution'])}
        """
        
        # Create navigation keyboard
        keyboard = self._create_series_navigation_keyboard(session)
        
        # Send the overview
        if query:
            # This is a callback query, edit the message
            await self._send_formatted_message(query, self._truncate_message(overview_message.strip()), reply_markup=keyboard)
        else:
            # This is a command, send new message
            await self._send_formatted_message(update_or_query, self._truncate_message(overview_message.strip()), reply_markup=keyboard)
    
    def _build_relationship_tree(self, posts: List[Dict]) -> Dict:
        """Build relationship tree structure from posts."""
        if not posts:
            return {'roots': [], 'children': {}}
        
        # Initialize tree structure
        tree = {'roots': [], 'children': {}}
        
        # Create a mapping of post_id to post for quick lookup
        post_map = {post['post_id']: post for post in posts}
        
        # Find root posts (posts with no parent) and build children mapping
        for post in posts:
            post_id = post['post_id']
            parent_id = post.get('parent_post_id')
            
            if parent_id is None:
                # This is a root post
                tree['roots'].append(post_id)
            else:
                # This post has a parent
                if parent_id not in tree['children']:
                    tree['children'][parent_id] = []
                tree['children'][parent_id].append(post_id)
        
        return tree
    
    def _calculate_series_statistics(self, posts: List[Dict]) -> Dict:
        """Calculate comprehensive series statistics."""
        if not posts:
            return {
                'total_posts': 0,
                'relationship_types_used': [],
                'tone_distribution': {},
                'creation_timespan': 'No posts',
                'most_used_tone': 'None'
            }
        
        # Count relationship types
        relationship_types = []
        for post in posts:
            rel_type = post.get('relationship_type')
            if rel_type and rel_type not in relationship_types:
                relationship_types.append(rel_type)
        
        # Count tone distribution
        tone_counts = {}
        for post in posts:
            tone = post.get('tone_used', 'Unknown')
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
        
        # Find most used tone
        most_used_tone = max(tone_counts, key=tone_counts.get) if tone_counts else 'None'
        
        # Calculate creation timespan
        creation_timespan = self._calculate_timespan(posts)
        
        return {
            'total_posts': len(posts),
            'relationship_types_used': relationship_types,
            'tone_distribution': tone_counts,
            'creation_timespan': creation_timespan,
            'most_used_tone': most_used_tone
        }
    
    def _format_series_tree(self, posts: List[Dict]) -> str:
        """Format series tree for display."""
        if not posts:
            return "📝 No posts in this series yet."
        
        # Build the relationship tree
        tree = self._build_relationship_tree(posts)
        
        # Create a mapping of post_id to post for quick lookup
        post_map = {post['post_id']: post for post in posts}
        
        # Format the tree display
        lines = []
        
        def format_post_line(post_id: int, prefix: str = "", is_last: bool = True) -> str:
            """Format a single post line with tree structure."""
            post = post_map.get(post_id)
            if not post:
                return f"{prefix}❌ Post {post_id} (Missing)"
            
            # Choose tree connector based on whether this is the last item
            connector = "└── " if is_last else "├── "
            
            # Format post info
            tone_emoji = self._get_tone_emoji(post['tone_used'])
            relationship_emoji = self._get_relationship_emoji(post.get('relationship_type', ''))
            
            # Truncate content summary
            summary = post.get('content_summary', 'No summary')[:50]
            if len(summary) > 50:
                summary += "..."
            
            # Create the continuation prefix for the next line
            continuation_prefix = prefix + ("    " if is_last else "│   ")
            
            return f"{prefix}{connector}{tone_emoji} **Post {post_id}** ({post['tone_used']})\n{continuation_prefix}↳ {relationship_emoji} {summary}"
        
        def add_children(parent_id: int, prefix: str = "") -> None:
            """Recursively add children to the tree display."""
            children = tree['children'].get(parent_id, [])
            for i, child_id in enumerate(children):
                is_last_child = (i == len(children) - 1)
                lines.append(format_post_line(child_id, prefix, is_last_child))
                
                # Add children of this child with proper prefix
                child_prefix = prefix + ("    " if is_last_child else "│   ")
                add_children(child_id, child_prefix)
        
        # Add root posts and their children
        for i, root_id in enumerate(tree['roots']):
            is_last_root = (i == len(tree['roots']) - 1)
            lines.append(format_post_line(root_id, "", is_last_root))
            
            # Add children of this root with proper prefix
            root_prefix = "    " if is_last_root else "│   "
            add_children(root_id, root_prefix)
        
        return "\n".join(lines)
    
    def _format_series_info(self, session: Dict) -> str:
        """Format series metadata information."""
        filename = session.get('filename', 'Unknown file')
        series_id = session.get('series_id', 'Unknown')[:8]
        post_count = session.get('post_count', 0)
        
        # Parse creation date
        session_started = session.get('session_started', '')
        if session_started:
            try:
                from datetime import datetime
                created_date = datetime.fromisoformat(session_started.replace('Z', '+00:00'))
                creation_date = created_date.strftime('%Y-%m-%d %H:%M')
            except:
                creation_date = 'Unknown'
        else:
            creation_date = 'Unknown'
        
        return f"""
**Series:** {filename}
**Series ID:** {series_id}...
**Posts Created:** {post_count}
**Created:** {creation_date}
        """.strip()
    
    def _format_tone_distribution(self, tone_distribution: Dict) -> str:
        """Format tone distribution for display."""
        if not tone_distribution:
            return "No tones used yet"
        
        lines = []
        for tone, count in sorted(tone_distribution.items(), key=lambda x: x[1], reverse=True):
            emoji = self._get_tone_emoji(tone)
            lines.append(f"{emoji} {tone}: {count}")
        
        return "\n".join(lines)
    
    def _calculate_timespan(self, posts: List[Dict]) -> str:
        """Calculate the timespan of post creation."""
        if not posts:
            return "No posts"
        
        # Get timestamps
        timestamps = []
        for post in posts:
            approved_at = post.get('approved_at')
            if approved_at:
                try:
                    from datetime import datetime
                    ts = datetime.fromisoformat(approved_at.replace('Z', '+00:00'))
                    timestamps.append(ts)
                except:
                    continue
        
        if not timestamps:
            return "Unknown"
        
        # Calculate timespan
        if len(timestamps) == 1:
            return "Single post"
        
        earliest = min(timestamps)
        latest = max(timestamps)
        diff = latest - earliest
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "Same time"
    
    def _get_tone_emoji(self, tone: str) -> str:
        """Get emoji for tone type."""
        tone_emojis = {
            'Behind-the-Build': '🧩',
            'What Broke': '💡',
            'Finished & Proud': '🚀',
            'Problem → Solution → Result': '🎯',
            'Mini Lesson': '📓',
            'Technical Deep Dive': '🔧',
            'Different Aspects': '🔍',
            'Different Angles': '📐',
            'Series Continuation': '📚',
            'Thematic Connection': '🔗',
            'Sequential Story': '📖'
        }
        return tone_emojis.get(tone, '📝')
    
    def _create_series_navigation_keyboard(self, session: Dict):
        """Create navigation keyboard for series management."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        posts = session.get('posts', [])
        
        # Create keyboard with post management options
        keyboard = [
            [
                InlineKeyboardButton("📊 Post Details", callback_data="series_post_details"),
                InlineKeyboardButton("📤 Export Series", callback_data="series_export")
            ]
        ]
        
        # Add individual post management if posts exist
        if posts:
            keyboard.append([
                InlineKeyboardButton("🔧 Manage Posts", callback_data="series_manage_posts"),
                InlineKeyboardButton("🔄 Refresh", callback_data="series_refresh")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="series_refresh")
            ])
        
        keyboard.append([
            InlineKeyboardButton("❌ Close", callback_data="series_close")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _export_series(self, query, session):
        """Export series in various formats."""
        try:
            # Show export options
            export_message = """
📤 **Export Series**

Choose export format:

• **Markdown** - Full series as markdown document
• **Summary** - Text summary of all posts
• **Airtable** - Direct link to your Airtable records
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📄 Markdown", callback_data="export_markdown"),
                    InlineKeyboardButton("📝 Summary", callback_data="export_summary")
                ],
                [
                    InlineKeyboardButton("🔗 Airtable Link", callback_data="export_airtable"),
                    InlineKeyboardButton("⬅️ Back", callback_data="series_refresh")
                ]
            ]
            
            from telegram import InlineKeyboardMarkup
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, export_message.strip(), reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ **Error showing export options:** {str(e)}")
    
    async def _export_markdown(self, query, session):
        """Export series as markdown document."""
        posts = session.get('posts', [])
        filename = session.get('filename', 'series')
        series_id = session.get('series_id', 'unknown')[:8]
        
        # Create markdown content
        markdown_content = f"# {filename.replace('.md', '').replace('_', ' ').title()}\n\n"
        markdown_content += f"**Series ID:** {series_id}...\n"
        markdown_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        markdown_content += f"**Total Posts:** {len(posts)}\n\n"
        
        # Add series structure
        markdown_content += "## Series Structure\n\n"
        for i, post in enumerate(posts, 1):
            markdown_content += f"### Post {i}: {post['tone_used']}\n"
            if post.get('relationship_type'):
                markdown_content += f"**Relationship:** {post['relationship_type']}\n"
            if post.get('parent_post_id'):
                markdown_content += f"**Builds on:** Post {post['parent_post_id']}\n"
            markdown_content += f"**Approved:** {post.get('approved_at', 'Unknown')}\n\n"
            markdown_content += f"{post['content']}\n\n"
            markdown_content += "---\n\n"
        
        # Add original markdown source
        markdown_content += "## Original Source\n\n"
        markdown_content += f"```markdown\n{session.get('original_markdown', '')}\n```\n"
        
        # Send as file
        from io import BytesIO
        file_buffer = BytesIO(markdown_content.encode('utf-8'))
        file_buffer.name = f"series_{series_id}.md"
        
        await self._send_formatted_message(query, "📄 **Series exported as Markdown**\n\nComplete series with all posts and metadata.", document=file_buffer)
        
        # Return to series overview
        await self._show_series_overview(query, None)
    
    async def _export_summary(self, query, session):
        """Export series as text summary."""
        posts = session.get('posts', [])
        filename = session.get('filename', 'series')
        series_id = session.get('series_id', 'unknown')[:8]
        
        # Create summary content
        summary_content = f"📊 SERIES SUMMARY: {filename.replace('.md', '').replace('_', ' ').title()}\n"
        summary_content += f"Series ID: {series_id}...\n"
        summary_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        summary_content += f"Total Posts: {len(posts)}\n\n"
        
        # Add post summaries
        for i, post in enumerate(posts, 1):
            summary_content += f"📝 POST {i}: {post['tone_used']}\n"
            if post.get('relationship_type'):
                summary_content += f"   🔗 Relationship: {post['relationship_type']}\n"
            if post.get('parent_post_id'):
                summary_content += f"   📋 Builds on: Post {post['parent_post_id']}\n"
            summary_content += f"   📅 Created: {post.get('approved_at', 'Unknown')}\n"
            summary_content += f"   📄 Content: {post.get('content_summary', 'No summary')}\n\n"
        
        # Add statistics
        stats = self._calculate_series_statistics(posts)
        summary_content += f"📈 STATISTICS:\n"
        summary_content += f"   • Most Used Tone: {stats['most_used_tone']}\n"
        summary_content += f"   • Creation Timespan: {stats['creation_timespan']}\n"
        summary_content += f"   • Relationship Types: {', '.join(stats['relationship_types_used']) if stats['relationship_types_used'] else 'None'}\n"
        
        # Send as file
        from io import BytesIO
        file_buffer = BytesIO(summary_content.encode('utf-8'))
        file_buffer.name = f"series_summary_{series_id}.txt"
        
        await self._send_formatted_message(query, "📝 **Series exported as Summary**\n\nQuick overview of all posts and statistics.", document=file_buffer)
        
        # Return to series overview
        await self._show_series_overview(query, None)
    
    async def _export_airtable_link(self, query, session):
        """Export series as Airtable link."""
        posts = session.get('posts', [])
        series_id = session.get('series_id', 'unknown')
        
        # Create Airtable link message
        airtable_message = f"""
🔗 **Airtable Records for Series**

**Series ID:** {series_id[:8]}...
**Base ID:** {self.config.airtable_base_id}
**Table:** {self.config.airtable_table_name}

**Direct Records:**
"""
        
        for i, post in enumerate(posts, 1):
            record_id = post.get('airtable_record_id', 'Unknown')
            airtable_message += f"• Post {i}: https://airtable.com/{self.config.airtable_base_id}/{record_id}\n"
        
        airtable_message += f"""
**View All Records:**
https://airtable.com/{self.config.airtable_base_id}

**Filter by Series ID:**
Use filter: `Post Series ID = {series_id}`
        """
        
        await self._send_formatted_message(query, airtable_message.strip())
        
        # Add back button
        keyboard = [[InlineKeyboardButton("⬅️ Back to Series", callback_data="series_refresh")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self._send_formatted_message(query, "", reply_markup=reply_markup)

    async def _batch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /batch command to start multi-file upload mode."""
        user_id = update.effective_user.id
        
        # Initialize or reset batch session
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        # Create new batch session
        self.user_sessions[user_id] = {
            'mode': 'multi',
            'files': [],
            'session_started': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'state': 'collecting_files'
        }
        
        try:
            # Send a simple initial message
            await self._send_formatted_message(update, "📚 Multi-File Mode Started\n\nPlease send your markdown files (max 8).")
            
            # Then send the detailed instructions
            await self._send_formatted_message(update, "Available commands:\n"
                "/project - View project analysis\n"
                "/strategy - Get content strategy\n"
                "/done - Finish uploading\n"
                "/cancel - Exit batch mode")
            
        except Exception as e:
            logger.error(f"Error in batch command: {str(e)}")
            # Try one more time with minimal message
            try:
                await self._send_formatted_message(update, "Multi-File Mode Started. Send your files.")
            except Exception as e:
                logger.error(f"Error sending minimal message: {str(e)}")

    async def _project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /project command with background processing."""
        user_id = update.effective_user.id
        
        session = self.user_sessions.get(user_id, {})
        if not session or session.get('mode') != 'multi':
            await self._send_formatted_message(update, "❌ No active batch session. Use /batch to start multi-file mode.")
            return
        
        files = session.get('files', [])
        if not files:
            await self._send_formatted_message(update, "❌ No files uploaded yet. Upload some markdown files first.")
            return
        
        # Send analyzing message
        analyzing_msg = await self._send_formatted_message(update, "🔍 **Analyzing Project Files...**\n\n"
            "⏳ Generating comprehensive project overview...")
        
        try:
            # Run analysis in background
            analysis = await self._analyze_project_files(files)
            
            # Format analysis message
            analysis_message = f"""
📊 **Project Analysis**

*Theme:* {analysis['theme']}

*Narrative Arc:*
{analysis['narrative_arc']}

*Key Challenges:*
{self._format_bullet_points(analysis['key_challenges'])}

*Solutions:*
{self._format_bullet_points(analysis['solutions'])}

*Technical Stack:*
{self._format_bullet_points(analysis['technical_stack'])}

*Business Outcomes:*
{self._format_bullet_points(analysis['business_outcomes'])}

Use /strategy to generate a content strategy based on this analysis.
"""
            
            await self._send_formatted_message(analyzing_msg, analysis_message.strip())
            
        except Exception as e:
            logger.error(f"Error analyzing project: {str(e)}")
            await self._send_formatted_message(analyzing_msg, f"❌ **Error analyzing project:** {str(e)}")
    
    def _extract_project_theme(self, files: List[Dict]) -> str:
        """Extract overall project theme from files."""
        # Combine all file contents
        combined_content = "\n".join(f['content'] for f in files)
        # TODO: Implement actual theme extraction logic
        return "AI/Automation Development"
    
    def _analyze_narrative_arc(self, files: List[Dict]) -> str:
        """Analyze the narrative progression across files."""
        # TODO: Implement actual narrative arc analysis
        return "Planning → Implementation → Testing → Optimization"
    
    def _extract_key_challenges(self, files: List[Dict]) -> List[str]:
        """Extract key challenges from files."""
        # TODO: Implement actual challenge extraction
        return [
            "Complex system integration",
            "Performance optimization",
            "Error handling"
        ]
    
    def _extract_solutions(self, files: List[Dict]) -> List[str]:
        """Extract implemented solutions from files."""
        # TODO: Implement actual solution extraction
        return [
            "Modular architecture",
            "Caching system",
            "Robust error recovery"
        ]
    
    def _extract_technical_stack(self, files: List[Dict]) -> List[str]:
        """Extract technical stack information from files."""
        # TODO: Implement actual tech stack extraction
        return [
            "Python",
            "AI/ML",
            "APIs"
        ]
    
    def _extract_business_outcomes(self, files: List[Dict]) -> List[str]:
        """Extract business outcomes from files."""
        # TODO: Implement actual outcome extraction
        return [
            "Improved efficiency",
            "Reduced errors",
            "Better user experience"
        ]
    
    def _format_bullet_points(self, items: List[str]) -> str:
        """Format a list of items as bullet points."""
        return "\n".join(f"• {item}" for item in items)

    async def _done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /done command to finish batch upload and process files."""
        user_id = update.effective_user.id
        
        # Check if user has an active batch session
        session = self.user_sessions.get(user_id, {})
        if not session or session.get('mode') != 'multi':
            await self._send_formatted_message(update, "❌ No active batch session. Use /batch to start multi-file mode.")
            return
        
        files = session.get('files', [])
        if not files:
            await self._send_formatted_message(update, "❌ No files uploaded yet. Upload some markdown files first.")
            return
        
        # Send processing message
        processing_msg = await self._send_formatted_message(update, "🔄 **Processing Batch Upload**\n\n"
            f"📚 Processing {len(files)} files...\n"
            "⏳ This may take a few minutes...")
        
        try:
            # Update session state
            session['state'] = 'processing'
            
            # Analyze all files
            project_analysis = {
                'project_theme': self._extract_project_theme(files),
                'narrative_arc': self._analyze_narrative_arc(files),
                'key_challenges': self._extract_key_challenges(files),
                'solutions': self._extract_solutions(files),
                'technical_stack': self._extract_technical_stack(files),
                'business_outcomes': self._extract_business_outcomes(files)
            }
            
            # Generate content strategy
            content_strategy = {
                'recommended_sequence': self._suggest_posting_sequence(files),
                'cross_references': self._generate_cross_references(files),
                'tone_suggestions': self._suggest_tones(files),
                'audience_split': self._analyze_audience_split(files)
            }
            
            # Update session with analysis and strategy
            session['project_analysis'] = project_analysis
            session['content_strategy'] = content_strategy
            session['state'] = 'ready_for_generation'
            
            # Show strategy summary
            strategy_message = f"""
📋 **Content Strategy Ready**

**Project Theme:** {project_analysis['project_theme']}
**Files Processed:** {len(files)}

**Recommended Post Sequence:**
{self._format_post_sequence(content_strategy['recommended_sequence'])}

**Suggested Audience Split:**
{self._format_audience_split(content_strategy['audience_split'])}

**Next Steps:**
1. Review the strategy
2. Choose post generation order
3. Start content generation

Would you like to:
A) Use AI recommended sequence
B) Customize sequence
C) Generate posts one by one
            """
            
            # Create inline keyboard for options
            keyboard = [
                [
                    InlineKeyboardButton("✅ Use AI Strategy", callback_data="use_ai_strategy"),
                    InlineKeyboardButton("✏️ Customize", callback_data="customize_strategy")
                ],
                [
                    InlineKeyboardButton("📝 Manual Selection", callback_data="manual_selection")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(processing_msg, strategy_message.strip(), reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            await self._send_formatted_message(processing_msg, f"❌ **Error processing batch:** {str(e)}")
    
    def _suggest_posting_sequence(self, files: List[Dict]) -> List[Dict]:
        """Suggest optimal posting sequence for files."""
        # Sort files by upload timestamp as a basic sequence
        sequence = sorted(files, key=lambda x: x['upload_timestamp'])
        return [{'file': f, 'reason': 'Chronological order'} for f in sequence]
    
    def _generate_cross_references(self, files: List[Dict]) -> List[Dict]:
        """Generate cross-reference suggestions between files."""
        # TODO: Implement actual cross-reference generation
        return []
    
    def _suggest_tones(self, files: List[Dict]) -> List[Dict]:
        """Suggest tones for each file based on content."""
        # TODO: Implement actual tone suggestion logic
        return [{'file': f, 'tone': 'Behind-the-Build'} for f in files]
    
    def _analyze_audience_split(self, files: List[Dict]) -> Dict:
        """Analyze optimal audience targeting split."""
        return {
            'technical': len(files) // 2,
            'business': len(files) - (len(files) // 2)
        }
    
    def _format_post_sequence(self, sequence: List[Dict]) -> str:
        """Format post sequence for display."""
        return "\n".join(f"{i+1}. {post['file']['filename']} ({post['reason']})"
                        for i, post in enumerate(sequence))
    
    def _format_audience_split(self, split: Dict) -> str:
        """Format audience split for display."""
        return f"• Technical Posts: {split['technical']}\n• Business Posts: {split['business']}"

    async def _strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /strategy command to show content strategy in batch mode."""
        user_id = update.effective_user.id
        
        # Check if user has an active batch session
        session = self.user_sessions.get(user_id, {})
        if not session or session.get('mode') != 'multi':
            await self._send_formatted_message(update, "❌ No active batch session. Use /batch to start multi-file mode.")
            return
        
        files = session.get('files', [])
        if not files:
            await self._send_formatted_message(update, "❌ No files uploaded yet. Upload some markdown files first.")
            return
        
        # Send analyzing message
        analyzing_msg = await self._send_formatted_message(update, "🎯 Generating Content Strategy\n\n"
            "⏳ Analyzing files...")
        
        try:
            # Generate content strategy
            content_strategy = {
                'recommended_sequence': self._suggest_posting_sequence(files),
                'cross_references': self._generate_cross_references(files),
                'tone_suggestions': self._suggest_tones(files),
                'audience_split': self._analyze_audience_split(files),
                'posting_timeline': self._suggest_posting_timeline(len(files))
            }
            
            # Store strategy in session
            session['content_strategy'] = content_strategy
            
            # Format strategy message
            strategy_message = (
                "📋 Content Strategy\n\n"
                f"Files: {len(files)} files\n"
                f"Posts: {len(content_strategy['recommended_sequence'])} planned\n"
                f"Timeline: {content_strategy['posting_timeline']}\n\n"
                "Choose your approach:"
            )
            
            # Create inline keyboard with consistent callback data
            keyboard = [
                [
                    InlineKeyboardButton("✅ Use AI Strategy", callback_data="use_ai_strategy"),
                    InlineKeyboardButton("✏️ Customize", callback_data="customize_strategy")
                ],
                [
                    InlineKeyboardButton("📝 Manual Selection", callback_data="manual_selection"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_strategy")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(analyzing_msg, text=strategy_message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error generating strategy: {str(e)}")
            await self._send_formatted_message(analyzing_msg, "❌ Error generating strategy. Please try again.")

    async def _cancel_batch_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command to exit batch mode."""
        user_id = update.effective_user.id
        
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            if session.get('mode') == 'multi':
                del self.user_sessions[user_id]
                await self._send_formatted_message(update, "✅ Batch mode cancelled. All uploaded files have been cleared.")
            else:
                await self._send_formatted_message(update, "❌ No active batch session to cancel.")
        else:
            await self._send_formatted_message(update, "❌ No active session to cancel.")

    def _suggest_posting_timeline(self, file_count: int) -> str:
        """Suggest optimal posting timeline based on file count."""
        if file_count <= 3:
            return "1 week (2-3 posts per week)"
        elif file_count <= 5:
            return "2 weeks (2-3 posts per week)"
        else:
            return "3 weeks (2-3 posts per week)"

    def _format_tone_distribution(self, tone_suggestions: List[Dict]) -> str:
        """Format tone distribution for display."""
        tone_counts = {}
        for suggestion in tone_suggestions:
            tone = suggestion['tone']
            tone_counts[tone] = tone_counts.get(tone, 0) + 1
        
        return "\n".join(f"• {tone}: {count} post(s)" for tone, count in tone_counts.items())

    def _format_cross_references(self, cross_refs: List[Dict]) -> str:
        """Format cross-references for display."""
        if not cross_refs:
            return "No explicit cross-references suggested"
        
        formatted_refs = []
        for ref in cross_refs:
            formatted_refs.append(f"• {ref['from_file']} → {ref['to_file']}: {ref['type']}")
        return "\n".join(formatted_refs)

    async def _handle_strategy_callback(self, query, session: Dict):
        """Handle strategy selection callbacks."""
        callback_data = query.data
        
        try:
            if callback_data == "use_ai_strategy":
                await self._handle_ai_strategy(query, session)
            elif callback_data == "customize_strategy":
                await self._show_strategy_customization(query, session)
            elif callback_data == "manual_selection":
                await self._show_manual_file_selection(query, session)
            elif callback_data == "cancel_strategy":
                await self._cancel_batch_command(query, None)
            else:
                # Log unexpected callback data
                logger.warning(f"Unexpected callback data: {callback_data}")
                await query.answer("Invalid option")
                
        except Exception as e:
            logger.error(f"Error in strategy callback: {str(e)}")
            await query.answer("Error processing selection")

    async def _handle_ai_strategy(self, query, session: Dict):
        """Handle AI strategy selection."""
        try:
            # Update message to show processing
            processing_message = (
                "🔄 Processing Files\n\n"
                "Analyzing files and generating content sequence..."
            )
            
            await self._send_formatted_message(query, processing_message)
            
            # Generate posts using AI strategy
            await self._generate_batch_posts(query, session)
            
        except Exception as e:
            logger.error(f"Error handling AI strategy: {str(e)}")
            await self._send_formatted_message(query, "❌ Error processing AI strategy. Please try again.")

    async def _show_strategy_customization(self, query, session: Dict):
        """Show interface for customizing content strategy."""
        try:
            sequence = session['content_strategy']['recommended_sequence']
            
            # Create message with current sequence
            message = "✏️ **Customize Post Sequence**\n\n"
            message += "Current sequence:\n"
            for i, post in enumerate(sequence, 1):
                message += f"{i}. {post['file']['filename']} ({post['reason']})\n"
            
            message += "\nUse the buttons below to modify the sequence:"
            
            # Create keyboard for reordering
            keyboard = []
            for i, post in enumerate(sequence):
                keyboard.append([
                    InlineKeyboardButton(
                        f"📝 Edit #{i+1}: {post['file']['filename'][:20]}...",
                        callback_data=f"edit_post_{i}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("✅ Confirm Sequence", callback_data="confirm_sequence"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_strategy")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing customization: {str(e)}")
            await self._send_formatted_message(query, f"❌ **Error:** {str(e)}")

    async def _show_manual_file_selection(self, query, session: Dict):
        """Show interface for manual file selection."""
        try:
            files = session.get('files', [])
            selected_files = session.get('selected_files', [])
            
            message = "📝 **Manual File Selection**\n\n"
            message += f"Selected: {len(selected_files)}/{len(files)} files\n\n"
            
            # Create keyboard with all files
            keyboard = []
            for i, file in enumerate(files):
                is_selected = any(sf['file_id'] == file['file_id'] for sf in selected_files)
                status = "✅" if is_selected else "⭕️"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{status} {file['filename']}",
                        callback_data=f"select_file_{file['file_id']}"
                    )
                ])
            
            # Add control buttons
            if selected_files:
                keyboard.append([
                    InlineKeyboardButton("✨ Generate Posts", callback_data="manual_generate"),
                    InlineKeyboardButton("🔄 Clear Selection", callback_data="manual_clear")
                ])
            
            keyboard.append([
                InlineKeyboardButton("⬅️ Back", callback_data="back_to_strategy")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await self._send_formatted_message(query, message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing file selection: {str(e)}")
            await self._send_formatted_message(query, f"❌ **Error:** {str(e)}")

    async def _handle_file_selection(self, query, session: Dict):
        """Handle individual file selection."""
        try:
            callback_data = query.data
            file_id = callback_data.replace("select_file_", "")
            
            # Initialize selected files if not exists
            if 'selected_files' not in session:
                session['selected_files'] = []
            
            # Find the file in the files list
            selected_file = None
            for file in session['files']:
                if file['file_id'] == file_id:
                    selected_file = file
                    break
            
            if not selected_file:
                await query.answer("File not found")
                return
            
            # Toggle selection
            is_selected = any(sf['file_id'] == file_id for sf in session['selected_files'])
            if is_selected:
                session['selected_files'] = [sf for sf in session['selected_files'] if sf['file_id'] != file_id]
                await query.answer(f"Removed {selected_file['filename']}")
            else:
                session['selected_files'].append(selected_file)
                await query.answer(f"Added {selected_file['filename']}")
            
            # Refresh the selection interface
            await self._handle_manual_file_selection(query, session)
            
        except Exception as e:
            logger.error(f"Error handling file selection: {str(e)}")
            await self._send_formatted_message(query, f"❌ **Error:** {str(e)}")

    async def _handle_manual_generation(self, query, session: Dict):
        """Handle generation of posts for manually selected files."""
        try:
            selected_files = session.get('selected_files', [])
            if not selected_files:
                await query.answer("No files selected")
                return
            
            # Update message to show processing
            await self._send_formatted_message(query, 
                f"🔄 Processing {len(selected_files)} Files\n\n"
                "Generating posts in your selected order...")
            
            # Process files sequentially
            for file in selected_files:
                try:
                    # Generate post for this file
                    post_data = await self._process_in_background(
                        self.ai_generator.generate_facebook_post,
                        file['content'],
                        user_tone_preference=session.get('selected_tone'),
                        audience_type='business'
                    )
                    
                    # Store the post
                    if 'posts' not in session:
                        session['posts'] = []
                    session['posts'].append(post_data)
                    
                    # Show progress
                    current_count = len(session['posts'])
                    await self._send_formatted_message(
                        query,
                        f"✅ Generated post {current_count}/{len(selected_files)}\n"
                        f"File: {file['filename']}\n"
                        f"Tone: {post_data.get('tone_used', 'Unknown')}"
                    )
                    
                except Exception as e:
                    logger.error(f"Error generating post for {file['filename']}: {str(e)}")
                    await self._send_formatted_message(
                        query,
                        f"⚠️ Failed to generate post for {file['filename']}: {str(e)}"
                    )
            
            # Show completion message
            await self._show_batch_completion(query, session)
            
        except Exception as e:
            logger.error(f"Error in manual generation: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error: {str(e)}")

    async def _handle_manual_clear(self, query, session: Dict):
        """Clear manual file selection."""
        try:
            session['selected_files'] = []
            await query.answer("Selection cleared")
            await self._handle_manual_file_selection(query, session)
        except Exception as e:
            logger.error(f"Error clearing selection: {str(e)}")
            await self._send_formatted_message(query, f"❌ **Error:** {str(e)}")

    async def _process_in_background(self, func, *args, **kwargs):
        """Process heavy operations in background."""
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Background processing error: {str(e)}")
            raise

    async def _analyze_project_files(self, files: List[Dict]) -> Dict:
        """Analyze project files in background."""
        try:
            # Run heavy analysis in background
            results = await asyncio.gather(
                self._process_in_background(self._extract_project_theme, files),
                self._process_in_background(self._analyze_narrative_arc, files),
                self._process_in_background(self._extract_key_challenges, files),
                self._process_in_background(self._extract_solutions, files),
                self._process_in_background(self._extract_technical_stack, files),
                self._process_in_background(self._extract_business_outcomes, files)
            )
            
            return {
                'theme': results[0],
                'narrative_arc': results[1],
                'key_challenges': results[2],
                'solutions': results[3],
                'technical_stack': results[4],
                'business_outcomes': results[5]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project files: {str(e)}")
            raise

    async def _generate_content_strategy(self, files: List[Dict]) -> Dict:
        """Generate content strategy in background."""
        try:
            # Run strategy generation in background
            results = await asyncio.gather(
                self._process_in_background(self._suggest_posting_sequence, files),
                self._process_in_background(self._generate_cross_references, files),
                self._process_in_background(self._suggest_tones, files),
                self._process_in_background(self._analyze_audience_split, files)
            )
            
            return {
                'recommended_sequence': results[0],
                'cross_references': results[1],
                'tone_suggestions': results[2],
                'audience_split': results[3],
                'posting_timeline': self._suggest_posting_timeline(len(files))
            }
            
        except Exception as e:
            logger.error(f"Error generating content strategy: {str(e)}")
            raise

    async def _generate_batch_posts(self, query, session: Dict):
        """Generate posts for all files in batch mode."""
        try:
            files = session.get('files', [])
            total_files = len(files)
            
            # Initialize progress message
            progress_msg = await self._send_formatted_message(query, "🚀 Generating Content Series\n\n"
                "Processing files...\n"
                "⏳ This may take a few minutes...")
            
            # Process files in parallel batches
            batch_size = 3  # Process 3 files at a time
            posts = []
            
            for i in range(0, total_files, batch_size):
                batch = files[i:i + batch_size]
                tasks = []
                
                # Create tasks for parallel processing
                for file_data in batch:
                    previous_files = files[:i]  # Files processed before this one
                    task = self._process_in_background(
                        self.ai_generator.generate_facebook_post,
                        file_data['content'],
                        user_tone_preference=session.get('selected_tone'),
                        audience_type='business'
                    )
                    tasks.append(task)
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"Error generating post: {str(result)}")
                        continue
                    
                    posts.append(result)
                    
                    # Update progress
                    current_count = i + j + 1
                    await self._send_formatted_message(
                        progress_msg,
                        f"🚀 Generating Content Series\n\n"
                        f"Processed {current_count}/{total_files} files\n"
                        f"✅ Generated {len(posts)} posts\n\n"
                        "⏳ Processing..."
                    )
            
            # Store generated posts
            session['posts'] = posts
            session['state'] = 'batch_complete'
            
            # Show completion message
            await self._show_batch_completion(query, session)
            
        except Exception as e:
            logger.error(f"Error generating batch posts: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error generating posts: {str(e)}")

    async def _show_batch_completion(self, query, session: Dict):
        """Show completion message and options after generating all posts."""
        try:
            posts = session.get('posts', [])
            
            message = f"""✅ Batch Processing Complete!

Generated {len(posts)} posts from {len(session['files'])} files.

Options:
• View all posts
• Export series
• Start new batch"""
            
            keyboard = [
                [
                    InlineKeyboardButton("👀 View Posts", callback_data="view_batch_posts"),
                    InlineKeyboardButton("📤 Export", callback_data="export_batch")
                ],
                [
                    InlineKeyboardButton("🆕 New Batch", callback_data="new_batch")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, message.strip(), reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing completion: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error: {str(e)}")

    async def _view_batch_posts(self, query, session: Dict):
        """View all posts generated in the batch."""
        try:
            posts = session.get('posts', [])
            files = session.get('files', [])
            
            if not posts:
                await self._send_formatted_message(query, "❌ No posts found in this batch.")
                return
            
            message_parts = [f"📚 Batch Posts ({len(posts)} posts)"]
            
            for i, post in enumerate(posts, 1):
                tone = post.get('tone_used', 'Unknown')
                content_preview = post.get('post_content', '')[:100] + '...' if len(post.get('post_content', '')) > 100 else post.get('post_content', '')
                
                # Try to match with original file
                file_name = "Unknown file"
                if i <= len(files):
                    file_name = files[i-1].get('filename', 'Unknown file')
                
                message_parts.append(f"\n{i}. {file_name}")
                message_parts.append(f"   Tone: {tone}")
                message_parts.append(f"   Preview: {content_preview}")
            
            message = "\n".join(message_parts)
            
            # Add navigation buttons
            keyboard = [
                [
                    InlineKeyboardButton("📤 Export All", callback_data="export_batch"),
                    InlineKeyboardButton("🆕 New Batch", callback_data="new_batch")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, self._truncate_message(message), reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error viewing batch posts: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error viewing posts: {str(e)}")

    async def _export_batch_series(self, query, session: Dict):
        """Export the batch series as a document."""
        try:
            posts = session.get('posts', [])
            files = session.get('files', [])
            
            if not posts:
                await self._send_formatted_message(query, "❌ No posts to export.")
                return
            
            # Create export content
            export_content = f"# Batch Generated Posts\n\n"
            export_content += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            export_content += f"**Total Posts:** {len(posts)}\n"
            export_content += f"**Total Files:** {len(files)}\n\n"
            
            for i, post in enumerate(posts, 1):
                tone = post.get('tone_used', 'Unknown')
                content = post.get('post_content', 'No content')
                
                # Try to match with original file
                file_name = "Unknown file"
                if i <= len(files):
                    file_name = files[i-1].get('filename', 'Unknown file')
                
                export_content += f"## Post {i}: {file_name}\n\n"
                export_content += f"**Tone:** {tone}\n\n"
                export_content += f"**Content:**\n{content}\n\n"
                export_content += "---\n\n"
            
            # Send as file
            from io import BytesIO
            file_buffer = BytesIO(export_content.encode('utf-8'))
            file_buffer.name = f"batch_posts_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            
            await self._send_formatted_message(query, "📤 Batch Posts Export", document=file_buffer)
            
        except Exception as e:
            logger.error(f"Error exporting batch: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error exporting: {str(e)}")

    async def _start_new_batch(self, query, user_id: int):
        """Start a new batch session."""
        try:
            # Clear existing session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            
            # Create new batch session
            self.user_sessions[user_id] = {
                'mode': 'multi',
                'files': [],
                'session_started': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'state': 'collecting_files'
            }
            
            message = """🆕 New Batch Started!

Upload your markdown files (max 8).

Commands:
• /project - View project analysis
• /strategy - Get content strategy  
• /done - Finish uploading
• /cancel - Exit batch mode"""
            
            await self._send_formatted_message(query, message)
            
        except Exception as e:
            logger.error(f"Error starting new batch: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error starting new batch: {str(e)}")

    async def _show_strategy_options(self, query, session: Dict):
        """Show strategy options to the user."""
        message = """🎯 Choose Your Strategy

How would you like to proceed with content generation?

Options:
• AI Strategy - Let AI optimize the sequence and tone selection
• Custom Strategy - Manually arrange posts and select tones
• Manual Selection - Process files one by one"""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Use AI Strategy", callback_data="use_ai_strategy"),
                InlineKeyboardButton("✏️ Customize", callback_data="customize_strategy")
            ],
            [
                InlineKeyboardButton("📝 Manual Selection", callback_data="manual_selection"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_formatted_message(query, message.strip(), reply_markup=reply_markup)

    async def _handle_initial_tone_selection(self, query, session: Dict, callback_data: str):
        """Handle initial tone selection from the enhanced interface."""
        try:
            if callback_data == "initial_ai_choose":
                # Let AI choose the best tone
                await self._generate_with_ai_chosen_tone(query, session)
            elif callback_data.startswith("initial_tone_"):
                # Extract tone from callback data
                tone = callback_data.replace("initial_tone_", "").replace("_", " ")
                # Map callback data back to proper tone names
                tone_mapping = {
                    "behind_the_build": "Behind-the-Build",
                    "what_broke": "What Broke",
                    "finished_proud": "Finished & Proud",
                    "problem_solution_result": "Problem → Solution → Result",
                    "mini_lesson": "Mini Lesson"
                }
                actual_tone = tone_mapping.get(tone.lower().replace(" ", "_"), tone.title())
                await self._generate_with_initial_tone(query, session, actual_tone)
            else:
                logger.warning(f"Unknown initial tone callback: {callback_data}")
                await self._send_formatted_message(query, "❌ Invalid tone selection. Please try again.")
        except Exception as e:
            logger.error(f"Error handling initial tone selection: {str(e)}")
            await self._send_formatted_message(query, "❌ Error processing tone selection. Please try again.")

    async def _generate_with_ai_chosen_tone(self, query, session: Dict):
        """Generate post with AI-chosen tone."""
        try:
            await self._send_formatted_message(query, "🤖 AI is choosing the best tone for your content...")
            
            # Generate post with AI tone selection
            markdown_content = session['original_markdown']
            post_data = self.ai_generator.generate_facebook_post(
                markdown_content,
                user_tone_preference=None,  # Let AI choose
                audience_type='business'
            )
            
            # Store and show the post
            session['current_draft'] = post_data
            await self._show_generated_post(query, post_data, session)
            
        except Exception as e:
            logger.error(f"Error generating with AI tone: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error generating post: {str(e)}")

    async def _generate_with_initial_tone(self, query, session: Dict, tone: str):
        """Generate post with specific initial tone."""
        try:
            await self._send_formatted_message(query, f"🎨 Generating post with {tone} tone...")
            
            # Generate post with specified tone
            markdown_content = session['original_markdown']
            post_data = self.ai_generator.generate_facebook_post(
                markdown_content,
                user_tone_preference=tone,
                audience_type='business'
            )
            
            # Store and show the post
            session['current_draft'] = post_data
            await self._show_generated_post(query, post_data, session)
            
        except Exception as e:
            logger.error(f"Error generating with tone {tone}: {str(e)}")
            await self._send_formatted_message(query, f"❌ Error generating post: {str(e)}")

    async def _show_initial_tone_selection_from_callback(self, query, session: Dict):
        """Show initial tone selection interface from callback."""
        try:
            # This recreates the initial tone selection interface
            await self._show_initial_tone_selection_interface(query, session)
        except Exception as e:
            logger.error(f"Error showing tone selection: {str(e)}")
            await self._send_formatted_message(query, "❌ Error showing tone selection. Please try again.")

    async def _show_initial_tone_selection_interface(self, query, session: Dict):
        """Show the initial tone selection interface."""
        try:
            # Get tone options
            tone_options = self.ai_generator.get_tone_options()
            
            # Analyze content for recommendations
            markdown_content = session['original_markdown']
            content_analysis = self._analyze_content_for_tone_recommendations(markdown_content)
            
            # Create message
            filename = session['filename']
            file_display = filename.replace('.md', '').replace('_', ' ').title()
            
            message_parts = [
                "🎨 Choose Your Tone Style",
                f"📄 File: {file_display}",
                "",
                "Smart Recommendations:"
            ]
            
            # Add content-based recommendations
            if content_analysis['recommended_tones']:
                for tone in content_analysis['recommended_tones'][:2]:
                    message_parts.append(f"• 🎯 {tone} - {content_analysis['reasons'][tone]}")
            
            message_parts.extend([
                "",
                "Available Tones:",
                "Choose the style that best fits your content:"
            ])
            
            # Create keyboard
            keyboard = []
            
            # Add recommended tones first
            if content_analysis['recommended_tones']:
                for tone in content_analysis['recommended_tones'][:2]:
                    callback_data = self._create_tone_callback_data(tone)
                    keyboard.append([InlineKeyboardButton(f"🎯 {tone} (Recommended)", callback_data=f"initial_{callback_data}")])
            
            # Add all tone options
            for tone in tone_options:
                if tone not in content_analysis['recommended_tones']:
                    callback_data = self._create_tone_callback_data(tone)
                    keyboard.append([InlineKeyboardButton(f"🎨 {tone}", callback_data=f"initial_{callback_data}")])
            
            # Add special options
            keyboard.extend([
                [InlineKeyboardButton("🤖 Let AI Choose Best Tone", callback_data="initial_ai_choose")],
                [InlineKeyboardButton("📊 Show Tone Previews", callback_data="show_tone_previews")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, "\n".join(message_parts), reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing tone selection interface: {str(e)}")
            await self._send_formatted_message(query, "❌ Error showing tone selection. Please try again.")

    async def _show_tone_options(self, query, session: Dict):
        """Show tone options for regenerating post."""
        try:
            # Get available tones
            tone_options = self.ai_generator.get_tone_options()
            
            message = "🎨 Choose a different tone for your post:\n\n"
            
            # Create keyboard with tone options
            keyboard = []
            for tone in tone_options:
                callback_data = self._create_tone_callback_data(tone)
                keyboard.append([InlineKeyboardButton(f"🎨 {tone}", callback_data=f"tone_{callback_data}")])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_post")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, message, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error showing tone options: {str(e)}")
            await self._send_formatted_message(query, "❌ Error showing tone options. Please try again.")

    async def _show_current_post(self, query, session: Dict):
        """Show the current post being reviewed."""
        try:
            current_draft = session.get('current_draft')
            if not current_draft:
                await self._send_formatted_message(query, "❌ No current post to show.")
                return
            
            # Show the current post
            await self._show_generated_post(query, current_draft, session)
            
        except Exception as e:
            logger.error(f"Error showing current post: {str(e)}")
            await self._send_formatted_message(query, "❌ Error showing current post. Please try again.")

    async def _cancel_followup(self, query, session):
        """Cancel follow-up post generation and return to options."""
        try:
            await self._show_post_approval_options(query, session)
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error cancelling follow-up: {str(e)}")

    async def _show_post_approval_options(self, query, session):
        """Show the post approval options after successful save."""
        try:
            posts = session.get('posts', [])
            filename = session['filename']
            
            message = f"""✅ Post Approved & Saved!

File: {filename}
Posts in Series: {len(posts)}

What would you like to do next?"""
            
            # Create keyboard with follow-up options
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Generate Follow-up Post", callback_data="generate_followup"),
                    InlineKeyboardButton("📋 View Series", callback_data="view_series")
                ],
                [
                    InlineKeyboardButton("📤 Export Current Post", callback_data="export_current"),
                    InlineKeyboardButton("✨ Done", callback_data="done_session")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error showing options: {str(e)}")

    async def _export_current_post(self, query, session):
        """Export the current post content."""
        try:
            posts = session.get('posts', [])
            if not posts:
                await self._send_formatted_message(query, "❌ No posts to export.")
                return
            
            # Get the most recent post
            current_post = posts[-1]
            
            export_message = f"""📤 Current Post Export

**Post {current_post['post_id']}:**
**Tone:** {current_post['tone_used']}
**Created:** {current_post['approved_at'][:10]}

**Content:**
{current_post['content']}

**Airtable Record:** {current_post['airtable_record_id']}"""
            
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Options", callback_data="back_to_options")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self._send_formatted_message(query, export_message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error exporting post: {str(e)}")

    async def _export_series(self, query, session):
        """Export all posts in the series."""
        try:
            posts = session.get('posts', [])
            if not posts:
                await self._send_formatted_message(query, "❌ No posts to export.")
                return
            
            filename = session['filename']
            export_message = f"""📤 Series Export

**File:** {filename}
**Total Posts:** {len(posts)}

"""
            
            for i, post in enumerate(posts, 1):
                export_message += f"""**Post {i}:**
**Tone:** {post['tone_used']}
**Created:** {post['approved_at'][:10]}
**Airtable ID:** {post['airtable_record_id']}

**Content:**
{post['content']}

---

"""
            
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Series", callback_data="view_series")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Split message if too long
            if len(export_message) > 4000:
                # Send in chunks
                chunks = [export_message[i:i+4000] for i in range(0, len(export_message), 4000)]
                for chunk in chunks[:-1]:
                    await self._send_formatted_message(query, chunk)
                await self._send_formatted_message(query, chunks[-1], reply_markup=reply_markup)
            else:
                await self._send_formatted_message(query, export_message, reply_markup=reply_markup)
            
        except Exception as e:
            await self._send_formatted_message(query, f"❌ Error exporting series: {str(e)}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Create and run the bot
    bot = FacebookContentBot()
    bot.run() 