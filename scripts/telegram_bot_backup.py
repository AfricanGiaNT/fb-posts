"""
Main Telegram Bot for AI Facebook Content Generator
"""

import logging
from pathlib import Path
from datetime import datetime
import asyncio
from typing import Dict, Optional

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
            
            # Store in user session
            self.user_sessions[user_id] = {
                'markdown_content': markdown_content,
                'filename': document.file_name,
                'current_draft': None,
                'airtable_record_id': None
            }
            
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
                                     is_regeneration: bool = False):
        """Generate and display a Facebook post."""
        user_id = update.effective_user.id
        
        try:
            # Generate the post
            if is_regeneration and tone_preference:
                post_data = self.ai_generator.regenerate_post(
                    markdown_content, 
                    feedback=f"User requested {tone_preference} tone",
                    tone_preference=tone_preference
                )
            else:
                post_data = self.ai_generator.generate_facebook_post(
                    markdown_content, 
                    tone_preference
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
            
            # Format the message
            post_preview = f"""
🎯 Generated Facebook Post

Tone Used: {post_data.get('tone_used', 'Unknown')}

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
        elif action.startswith("tone_"):
            # Handle tone selection
            tone_name = action.replace("tone_", "").replace("_", " ")
            await self._regenerate_with_tone(query, session, tone_name)
    
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
            
            success_message = f"""
✅ **Post Approved & Saved!**

**File:** {filename}
**Status:** Ready for Facebook publishing
**Airtable Record ID:** {record_id}

Your post is now saved in Airtable with:
• Generated draft content
• AI tone analysis and reasoning
• Auto-extracted tags
• Content summary and length metrics
• Improvement suggestions

**Next Steps:**
1. Open your Airtable Content Tracker
2. Find the approved post
3. Copy the content to Facebook
4. Update the "Post URL (After Publishing)" field in Airtable

*Send another markdown file to generate more posts!*
            """
            
            await query.edit_message_text(success_message, parse_mode='Markdown')
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error saving post:** {str(e)}",
                parse_mode='Markdown'
            )
    
    async def _regenerate_post(self, query, session):
        """Regenerate the post with general feedback."""
        try:
            await query.edit_message_text(
                "🔄 **Regenerating your post...**\n\n"
                "⏳ Creating a new version with different approach...",
                parse_mode='Markdown'
            )
            
            # Regenerate with general feedback
            markdown_content = session['markdown_content']
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback="User requested regeneration - try different tone or approach"
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
            if len(post_content) > 2000:  # Leave room for other message parts
                display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display - full version saved to Airtable]*"
            else:
                display_content = post_content
            
            # Truncate reasoning if needed
            if len(tone_reason) > 500:
                display_reason = tone_reason[:500] + "..."
            else:
                display_reason = tone_reason
            
            # Update message with new content
            updated_message = f"""
🔄 Regenerated Facebook Post

Tone Used: {post_data.get('tone_used', 'Unknown')}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?
            """
            
            # Final safety check and truncation
            updated_message = self._truncate_message(updated_message)
            
            await query.edit_message_text(
                updated_message,
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in _regenerate_post: {str(e)}")
            try:
                await query.edit_message_text(
                    f"❌ Error regenerating post: {str(e)}"
                )
            except Exception:
                logger.error(f"Failed to send regenerate error message: {str(e)}")
    
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
        """Regenerate post with specific tone."""
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
            
            # Regenerate with specific tone
            markdown_content = session['markdown_content']
            post_data = self.ai_generator.regenerate_post(
                markdown_content,
                feedback=f"User specifically requested {selected_tone} tone",
                tone_preference=selected_tone
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
            if len(post_content) > 2000:  # Leave room for other message parts
                display_content = post_content[:2000] + "\n\n📝 *[Content truncated for display - full version saved to Airtable]*"
            else:
                display_content = post_content
            
            # Truncate reasoning if needed
            if len(tone_reason) > 500:
                display_reason = tone_reason[:500] + "..."
            else:
                display_reason = tone_reason
            
            # Update message with new content
            updated_message = f"""
🎨 Regenerated with '{selected_tone}' tone

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?
            """
            
            # Final safety check and truncation
            updated_message = self._truncate_message(updated_message)
            
            await query.edit_message_text(
                updated_message,
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
    
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        await update.message.reply_text(
            "👋 Hi! I work with markdown files.\n\n"
            "📄 **Send me a `.md` file** to generate a Facebook post!\n\n"
            "Use `/help` for more information.",
            parse_mode='Markdown'
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