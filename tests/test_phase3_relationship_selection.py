"""
Test Phase 3: Relationship Selection Interface
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot

class TestRelationshipSelectionInterface:
    """Test the relationship selection interface functionality."""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing."""
        with patch('telegram_bot.ConfigManager'), \
             patch('telegram_bot.AIContentGenerator'), \
             patch('telegram_bot.AirtableConnector'):
            bot = FacebookContentBot()
            return bot
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session with approved posts."""
        return {
            'series_id': 'test-series-123',
            'original_markdown': 'Test markdown content',
            'filename': 'test.md',
            'posts': [
                {
                    'post_id': 1,
                    'content': 'First post content',
                    'tone_used': 'Behind-the-Build',
                    'approved': True,
                    'content_summary': 'First post about testing...'
                }
            ],
            'current_draft': {
                'post_content': 'Test post content',
                'tone_used': 'Behind-the-Build'
            },
            'post_count': 1,
            'session_context': 'Test context',
            'pending_generation': {
                'relationship_type': None,
                'parent_post_id': None,
                'connection_preview': None,
                'user_confirmed': False
            }
        }
    
    @pytest.fixture
    def mock_callback_query(self):
        """Create a mock callback query."""
        query = Mock(spec=CallbackQuery)
        query.from_user.id = 12345
        query.data = "generate_another"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        return query
    
    @pytest.mark.asyncio
    async def test_show_relationship_selection_interface(self, bot, mock_session, mock_callback_query):
        """Test that relationship selection interface is shown after clicking generate another."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session
        
        # Act
        await bot._show_relationship_selection(mock_callback_query, user_id)
        
        # Assert
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        
        # Check that the message contains relationship selection content
        message_text = call_args[0][0]
        assert "Choose relationship type" in message_text
        assert "Generate Another Post" in message_text
        
        # Check that inline keyboard is provided
        keyboard = call_args[1]['reply_markup']
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Check that keyboard has 7 buttons (6 relationship types + AI decide)
        buttons = []
        for row in keyboard.inline_keyboard:
            buttons.extend(row)
        assert len(buttons) == 7
        
        # Check button text contains relationship types
        button_texts = [btn.text for btn in buttons]
        assert "🔍 Different Aspects" in button_texts
        assert "📐 Different Angles" in button_texts
        assert "📚 Series Continuation" in button_texts
        assert "🔗 Thematic Connection" in button_texts
        assert "🔧 Technical Deep Dive" in button_texts
        assert "📖 Sequential Story" in button_texts
        assert "🤖 AI Decide" in button_texts
        
        # Check button callback data
        callback_data = [btn.callback_data for btn in buttons]
        expected_callbacks = [
            "rel_different_aspects",
            "rel_different_angles", 
            "rel_series_continuation",
            "rel_thematic_connection",
            "rel_technical_deep_dive",
            "rel_sequential_story",
            "rel_ai_decide"
        ]
        assert all(expected in callback_data for expected in expected_callbacks)
    
    @pytest.mark.asyncio
    async def test_handle_relationship_choice(self, bot, mock_session, mock_callback_query):
        """Test handling of relationship type selection."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session
        mock_callback_query.data = "rel_different_aspects"
        
        # Act
        await bot._handle_relationship_choice(mock_callback_query, user_id)
        
        # Assert
        # Check that the relationship type is stored in session
        session = bot.user_sessions[user_id]
        assert 'pending_generation' in session
        assert session['pending_generation']['relationship_type'] == 'Different Aspects'
        
        # Check that previous post selection is shown next
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        assert "Choose Previous Post to Build On" in message_text
        
        # Check that inline keyboard is provided with post options
        keyboard = call_args[1]['reply_markup']
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Check that buttons include "Build on most recent" option
        buttons = []
        for row in keyboard.inline_keyboard:
            buttons.extend(row)
        button_texts = [btn.text for btn in buttons]
        assert "📝 Build on most recent" in button_texts
    
    @pytest.mark.asyncio  
    async def test_relationship_selection_with_empty_series(self, bot, mock_callback_query):
        """Test relationship selection when no previous posts exist."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = {
            'series_id': 'test-series-123',
            'posts': [],  # No previous posts
            'post_count': 0
        }
        
        # Act
        await bot._show_relationship_selection(mock_callback_query, user_id)
        
        # Assert
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Should show different message for first post
        assert "This will be your first related post" in message_text
        
    @pytest.mark.asyncio
    async def test_workflow_state_tracking(self, bot, mock_session, mock_callback_query):
        """Test that workflow state is properly tracked."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session
        
        # Act
        await bot._show_relationship_selection(mock_callback_query, user_id)
        
        # Assert
        session = bot.user_sessions[user_id]
        assert session.get('workflow_state') == 'awaiting_relationship_selection' 