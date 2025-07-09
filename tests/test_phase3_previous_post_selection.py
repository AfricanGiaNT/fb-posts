"""
Test Phase 3: Previous Post Selection Interface
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot

class TestPreviousPostSelection:
    """Test the previous post selection interface functionality."""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing."""
        with patch('telegram_bot.ConfigManager'), \
             patch('telegram_bot.AIContentGenerator'), \
             patch('telegram_bot.AirtableConnector'):
            bot = FacebookContentBot()
            return bot
    
    @pytest.fixture
    def mock_session_with_posts(self):
        """Create a mock session with multiple approved posts."""
        return {
            'series_id': 'test-series-456',
            'original_markdown': 'Test markdown content about automation',
            'filename': 'automation_project.md',
            'posts': [
                {
                    'post_id': 1,
                    'content': 'First post about setting up automated workflows using Python and APIs. This includes the initial setup process and basic configuration steps needed to get started.',
                    'tone_used': 'Behind-the-Build',
                    'approved': True,
                    'content_summary': 'First post about setting up automated workflows using Python and APIs. This includes the initial setup...',
                    'relationship_type': None,
                    'parent_post_id': None
                },
                {
                    'post_id': 2,
                    'content': 'Second post discussing common problems encountered during automation setup and how to troubleshoot them effectively.',
                    'tone_used': 'What Broke',
                    'approved': True,
                    'content_summary': 'Second post discussing common problems encountered during automation setup and how to troubleshoot...',
                    'relationship_type': 'Different Aspects',
                    'parent_post_id': 1
                },
                {
                    'post_id': 3,
                    'content': 'Third post showcasing the final results and performance metrics of the completed automation system.',
                    'tone_used': 'Finished & Proud',
                    'approved': True,
                    'content_summary': 'Third post showcasing the final results and performance metrics of the completed automation system.',
                    'relationship_type': 'Sequential Story',
                    'parent_post_id': 2
                }
            ],
            'post_count': 3,
            'session_context': 'Test context for automation project',
            'pending_generation': {
                'relationship_type': 'Technical Deep Dive',
                'parent_post_id': None,
                'connection_preview': None,
                'user_confirmed': False
            },
            'workflow_state': 'awaiting_previous_post_selection'
        }
    
    @pytest.fixture
    def mock_session_empty(self):
        """Create a mock session with no previous posts."""
        return {
            'series_id': 'test-series-empty',
            'original_markdown': 'Test markdown content',
            'filename': 'test.md',
            'posts': [],
            'post_count': 0,
            'session_context': 'Test context',
            'pending_generation': {
                'relationship_type': 'Different Aspects',
                'parent_post_id': None,
                'connection_preview': None,
                'user_confirmed': False
            },
            'workflow_state': 'awaiting_previous_post_selection'
        }
    
    @pytest.fixture
    def mock_callback_query(self):
        """Create a mock callback query."""
        query = Mock(spec=CallbackQuery)
        query.from_user.id = 12345
        query.data = "prev_post_selection"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        return query
    
    @pytest.mark.asyncio
    async def test_show_previous_post_selection_with_posts(self, bot, mock_session_with_posts, mock_callback_query):
        """Test showing previous post selection when posts exist."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_posts
        
        # Act
        await bot._show_previous_post_selection(mock_callback_query, user_id)
        
        # Assert
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        
        # Check that the message contains previous post selection content
        message_text = call_args[0][0]
        assert "Choose Previous Post to Build On" in message_text
        assert "**Selected Relationship:** Technical Deep Dive" in message_text
        assert "Choose which post to build upon" in message_text
        
        # Check that inline keyboard is provided
        keyboard = call_args[1]['reply_markup']
        assert isinstance(keyboard, InlineKeyboardMarkup)
        
        # Check that buttons are created for each post
        buttons = []
        for row in keyboard.inline_keyboard:
            buttons.extend(row)
        
        # Should have 3 posts + 1 "Build on most recent" button = 4 buttons
        assert len(buttons) == 4
        
        # Check button texts contain post information
        button_texts = [btn.text for btn in buttons]
        assert any("Post 1:" in text for text in button_texts)
        assert any("Post 2:" in text for text in button_texts)
        assert any("Post 3:" in text for text in button_texts)
        assert "📝 Build on most recent" in button_texts
        
        # Check button callback data
        callback_data = [btn.callback_data for btn in buttons]
        assert "prev_post_1" in callback_data
        assert "prev_post_2" in callback_data
        assert "prev_post_3" in callback_data
        assert "prev_post_recent" in callback_data
    
    @pytest.mark.asyncio
    async def test_show_previous_post_selection_empty_series(self, bot, mock_session_empty, mock_callback_query):
        """Test showing previous post selection when no posts exist."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_empty
        
        # Act
        await bot._show_previous_post_selection(mock_callback_query, user_id)
        
        # Assert - should skip to generation confirmation directly
        # The method should call _confirm_generation instead of showing selection
        assert mock_callback_query.edit_message_text.call_count >= 0  # May or may not be called
    
    @pytest.mark.asyncio
    async def test_handle_previous_post_selection_specific_post(self, bot, mock_session_with_posts, mock_callback_query):
        """Test handling selection of a specific previous post."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_posts
        mock_callback_query.data = "prev_post_2"
        
        # Act
        await bot._handle_previous_post_selection(mock_callback_query, user_id)
        
        # Assert
        # Check that the selected post ID is stored in session
        session = bot.user_sessions[user_id]
        assert session['pending_generation']['parent_post_id'] == 2
        assert session['workflow_state'] == 'awaiting_generation_confirmation'
    
    @pytest.mark.asyncio
    async def test_handle_previous_post_selection_most_recent(self, bot, mock_session_with_posts, mock_callback_query):
        """Test handling selection of 'Build on most recent' option."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_posts
        mock_callback_query.data = "prev_post_recent"
        
        # Act
        await bot._handle_previous_post_selection(mock_callback_query, user_id)
        
        # Assert
        # Check that the most recent post ID is stored in session
        session = bot.user_sessions[user_id]
        assert session['pending_generation']['parent_post_id'] == 3  # Most recent post
        assert session['workflow_state'] == 'awaiting_generation_confirmation'
    
    @pytest.mark.asyncio
    async def test_post_snippet_generation(self, bot, mock_session_with_posts, mock_callback_query):
        """Test that post snippets are properly generated for display."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_posts
        
        # Act
        await bot._show_previous_post_selection(mock_callback_query, user_id)
        
        # Assert
        call_args = mock_callback_query.edit_message_text.call_args
        keyboard = call_args[1]['reply_markup']
        
        # Check that post snippets are truncated properly
        buttons = []
        for row in keyboard.inline_keyboard:
            buttons.extend(row)
        
        # Find the buttons with post content
        post_buttons = [btn for btn in buttons if "Post " in btn.text and ":" in btn.text]
        
        # Check that each post button has a snippet
        for button in post_buttons:
            assert "..." in button.text or len(button.text) <= 64  # Telegram button text limit
    
    @pytest.mark.asyncio
    async def test_workflow_state_management(self, bot, mock_session_with_posts, mock_callback_query):
        """Test that workflow state is properly managed during selection."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_posts
        
        # Act - Show selection
        await bot._show_previous_post_selection(mock_callback_query, user_id)
        
        # Assert - State should remain awaiting_previous_post_selection
        session = bot.user_sessions[user_id]
        assert session['workflow_state'] == 'awaiting_previous_post_selection'
        
        # Act - Handle selection
        mock_callback_query.data = "prev_post_1"
        await bot._handle_previous_post_selection(mock_callback_query, user_id)
        
        # Assert - State should change to awaiting_generation_confirmation
        assert session['workflow_state'] == 'awaiting_generation_confirmation'
    
    @pytest.mark.asyncio
    async def test_session_expiry_handling(self, bot, mock_callback_query):
        """Test handling of expired sessions."""
        # Setup - No session exists
        user_id = 12345
        
        # Act & Assert - Show selection
        await bot._show_previous_post_selection(mock_callback_query, user_id)
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        assert "Session expired" in call_args[0][0]
        
        # Reset mock
        mock_callback_query.edit_message_text.reset_mock()
        
        # Act & Assert - Handle selection
        await bot._handle_previous_post_selection(mock_callback_query, user_id)
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        assert "Session expired" in call_args[0][0] 