"""
Test suite for Phase 4: Enhanced Follow-up functionality.

This test suite covers:
- Follow-up context prompting after relationship selection
- Context integration with relationship types
- Skip context functionality
- Enhanced follow-up generation with both relationship and context
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from telegram import Update, User, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes

# Import the bot class
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from telegram_bot import FacebookContentBot


@pytest.fixture
def bot():
    """Create a bot instance for testing."""
    return FacebookContentBot()


@pytest.fixture
def user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = 12345
    user.username = "testuser"
    return user


@pytest.fixture
def chat():
    """Create a mock chat."""
    chat = MagicMock(spec=Chat)
    chat.id = 67890
    chat.type = "private"
    return chat


@pytest.fixture
def message(user, chat):
    """Create a mock message."""
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.from_user = user
    message.chat = chat
    message.text = "Test message"
    return message


@pytest.fixture
def update(message):
    """Create a mock update."""
    update = MagicMock(spec=Update)
    update.effective_user = message.from_user
    update.message = message
    return update


@pytest.fixture
def callback_query(user, chat):
    """Create a mock callback query."""
    query = MagicMock(spec=CallbackQuery)
    query.from_user = user
    query.chat_instance = "test_chat"
    query.data = "test_callback"
    return query


@pytest.fixture
def context():
    """Create a mock context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    return context


@pytest.fixture
def test_session():
    """Create a test session with follow-up data."""
    return {
        'user_id': 12345,
        'original_markdown': '# Test Post\n\nThis is a test post content.',
        'filename': 'test.md',
        'posts': [
            {
                'post_id': 1,
                'content': 'First post content',
                'tone_used': 'professional',
                'created_at': datetime.now().isoformat()
            }
        ],
        'session_context': 'Test session context',
        'state': None,
        'last_activity': datetime.now().isoformat()
    }


@pytest.fixture
def bot_with_session(bot, test_session):
    """Create a bot instance with a test session."""
    bot.user_sessions = {12345: test_session}
    return bot


class TestPhase4EnhancedFollowup:
    """Test suite for Phase 4: Enhanced Follow-up functionality."""

    @pytest.mark.asyncio
    async def test_handle_followup_relationship_selection_stores_relationship(self, bot_with_session, callback_query, test_session):
        """Test that relationship selection stores the relationship type and asks for context."""
        # Arrange
        relationship_type = "integration_expansion"
        
        # Mock the _ask_for_followup_context method
        bot_with_session._ask_for_followup_context = AsyncMock()
        
        # Act
        await bot_with_session._handle_followup_relationship_selection(callback_query, test_session, relationship_type)
        
        # Assert
        assert test_session['selected_relationship_type'] == relationship_type
        assert test_session['last_activity'] is not None
        bot_with_session._ask_for_followup_context.assert_called_once_with(callback_query, test_session, relationship_type)

    @pytest.mark.asyncio
    async def test_ask_for_followup_context_sets_state_and_sends_message(self, bot_with_session, callback_query, test_session):
        """Test that asking for follow-up context sets the correct state and sends the right message."""
        # Arrange
        relationship_type = "integration_expansion"
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Mock the AI generator's relationship types
        bot_with_session.ai_generator.get_relationship_types = MagicMock(return_value={
            'integration_expansion': 'Integration & Expansion'
        })
        
        # Act
        await bot_with_session._ask_for_followup_context(callback_query, test_session, relationship_type)
        
        # Assert
        assert test_session['state'] == 'awaiting_followup_context'
        assert test_session['last_activity'] is not None
        
        # Check that the message was sent
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert call_args[0][0] == callback_query  # First argument should be the query
        assert "Follow-up Context" in call_args[0][1]  # Message should contain the title
        assert "Integration & Expansion" in call_args[0][1]  # Should show the relationship type
        assert "skip_followup_context" in str(call_args[1]['reply_markup'])  # Should have skip button

    @pytest.mark.asyncio
    async def test_handle_followup_context_input_validates_and_stores_context(self, bot_with_session, update, context, test_session):
        """Test that follow-up context input is validated and stored correctly."""
        # Arrange
        test_session['state'] = 'awaiting_followup_context'
        test_session['selected_relationship_type'] = 'integration_expansion'
        
        # Mock the _generate_followup_with_relationship_and_context method
        bot_with_session._generate_followup_with_relationship_and_context = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._handle_followup_context_input(update, context, "Focus on lessons learned")
        
        # Assert
        assert test_session['followup_context'] == "Focus on lessons learned"
        assert test_session['last_activity'] is not None
        bot_with_session._generate_followup_with_relationship_and_context.assert_called_once_with(update, context, test_session)

    @pytest.mark.asyncio
    async def test_handle_followup_context_input_rejects_invalid_input(self, bot_with_session, update, context, test_session):
        """Test that invalid follow-up context input is rejected."""
        # Arrange
        test_session['state'] = 'awaiting_followup_context'
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act - Test with input that's too long
        long_input = "x" * 501  # Over 500 character limit
        await bot_with_session._handle_followup_context_input(update, context, long_input)
        
        # Assert
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert "Invalid input" in call_args[0][1]
        assert "500 characters" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_generate_followup_with_relationship_and_context_combines_both(self, bot_with_session, update, context, test_session):
        """Test that follow-up generation combines both relationship type and context."""
        # Arrange
        test_session['selected_relationship_type'] = 'integration_expansion'
        test_session['followup_context'] = 'Focus on lessons learned'
        
        # Mock the AI generator
        mock_post_data = {
            'post_content': 'Generated follow-up content',
            'tone_used': 'professional',
            'tone_reason': 'Professional tone chosen for business context'
        }
        bot_with_session.ai_generator.generate_facebook_post = MagicMock(return_value=mock_post_data)
        bot_with_session.ai_generator.get_relationship_types = MagicMock(return_value={
            'integration_expansion': 'Integration & Expansion'
        })
        
        # Mock the _send_formatted_message and _show_generated_post methods
        bot_with_session._send_formatted_message = AsyncMock()
        bot_with_session._show_generated_post = AsyncMock()
        
        # Act
        await bot_with_session._generate_followup_with_relationship_and_context(update, context, test_session)
        
        # Assert
        # Check that the AI generator was called with both relationship type and context
        bot_with_session.ai_generator.generate_facebook_post.assert_called_once()
        call_args = bot_with_session.ai_generator.generate_facebook_post.call_args
        assert call_args[1]['relationship_type'] == 'integration_expansion'
        assert call_args[1]['followup_context'] == 'Focus on lessons learned'
        
        # Check that the session was updated
        assert test_session['current_draft'] == mock_post_data
        assert test_session['state'] is None
        assert 'selected_relationship_type' not in test_session
        assert 'followup_context' not in test_session
        
        # Check that the generated post was shown
        bot_with_session._show_generated_post.assert_called_once_with(update, mock_post_data, test_session)

    @pytest.mark.asyncio
    async def test_generate_followup_with_ai_choose_relationship(self, bot_with_session, update, context, test_session):
        """Test that AI choose relationship type works correctly."""
        # Arrange
        test_session['selected_relationship_type'] = 'ai_choose'
        test_session['followup_context'] = 'Focus on lessons learned'
        
        # Mock the AI generator
        mock_post_data = {
            'post_content': 'Generated follow-up content',
            'tone_used': 'professional',
            'tone_reason': 'Professional tone chosen for business context'
        }
        bot_with_session.ai_generator.generate_facebook_post = MagicMock(return_value=mock_post_data)
        bot_with_session.ai_generator.get_relationship_types = MagicMock(return_value={
            'ai_choose': 'AI Choose'
        })
        
        # Mock the _send_formatted_message and _show_generated_post methods
        bot_with_session._send_formatted_message = AsyncMock()
        bot_with_session._show_generated_post = AsyncMock()
        
        # Act
        await bot_with_session._generate_followup_with_relationship_and_context(update, context, test_session)
        
        # Assert
        # Check that the AI generator was called with None relationship type (AI choose)
        bot_with_session.ai_generator.generate_facebook_post.assert_called_once()
        call_args = bot_with_session.ai_generator.generate_facebook_post.call_args
        assert call_args[1]['relationship_type'] is None
        assert call_args[1]['followup_context'] == 'Focus on lessons learned'

    @pytest.mark.asyncio
    async def test_handle_skip_followup_context_generates_without_context(self, bot_with_session, callback_query, test_session):
        """Test that skipping follow-up context generates the follow-up without context."""
        # Arrange
        test_session['selected_relationship_type'] = 'integration_expansion'
        
        # Mock the _generate_followup_with_relationship_and_context method
        bot_with_session._generate_followup_with_relationship_and_context = AsyncMock()
        
        # Act
        await bot_with_session._handle_skip_followup_context(callback_query, test_session)
        
        # Assert
        bot_with_session._generate_followup_with_relationship_and_context.assert_called_once_with(callback_query, None, test_session)

    @pytest.mark.asyncio
    async def test_followup_context_preserved_across_regeneration(self, bot_with_session, update, context, test_session):
        """Test that follow-up context is preserved when regenerating posts."""
        # Arrange
        test_session['followup_context'] = 'Focus on lessons learned'
        test_session['selected_relationship_type'] = 'integration_expansion'
        
        # Mock the AI generator
        mock_post_data = {
            'post_content': 'Regenerated follow-up content',
            'tone_used': 'professional',
            'tone_reason': 'Professional tone chosen for business context'
        }
        bot_with_session.ai_generator.generate_facebook_post = MagicMock(return_value=mock_post_data)
        bot_with_session.ai_generator.get_relationship_types = MagicMock(return_value={
            'integration_expansion': 'Integration & Expansion'
        })
        
        # Mock the _send_formatted_message and _show_generated_post methods
        bot_with_session._send_formatted_message = AsyncMock()
        bot_with_session._show_generated_post = AsyncMock()
        
        # Act - Generate follow-up with context
        await bot_with_session._generate_followup_with_relationship_and_context(update, context, test_session)
        
        # Assert - Context should be cleared after generation
        assert 'followup_context' not in test_session
        assert 'selected_relationship_type' not in test_session

    @pytest.mark.asyncio
    async def test_followup_context_timeout_handling(self, bot_with_session, test_session):
        """Test that follow-up context timeout is handled correctly."""
        # Arrange - Set last activity to more than 5 minutes ago
        test_session['last_activity'] = (datetime.now() - timedelta(minutes=6)).isoformat()
        test_session['state'] = 'awaiting_followup_context'
        
        # Act
        result = bot_with_session._check_freeform_timeout(test_session)
        
        # Assert
        assert result is True  # Should indicate timeout

    @pytest.mark.asyncio
    async def test_followup_context_without_previous_posts(self, bot_with_session, update, context, test_session):
        """Test that follow-up generation fails gracefully when no previous posts exist."""
        # Arrange
        test_session['posts'] = []  # No previous posts
        test_session['selected_relationship_type'] = 'integration_expansion'
        test_session['followup_context'] = 'Focus on lessons learned'
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._generate_followup_with_relationship_and_context(update, context, test_session)
        
        # Assert
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert "No previous posts" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_followup_context_error_handling(self, bot_with_session, update, context, test_session):
        """Test that errors in follow-up generation are handled gracefully."""
        # Arrange
        test_session['selected_relationship_type'] = 'integration_expansion'
        test_session['followup_context'] = 'Focus on lessons learned'
        
        # Mock the AI generator to raise an exception
        bot_with_session.ai_generator.generate_facebook_post = MagicMock(side_effect=Exception("AI generation failed"))
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._generate_followup_with_relationship_and_context(update, context, test_session)
        
        # Assert - Should be called twice: once for generation message, once for error
        assert bot_with_session._send_formatted_message.call_count == 2
        
        # Check that the error message was sent
        calls = bot_with_session._send_formatted_message.call_args_list
        error_call = calls[-1]  # Last call should be the error message
        assert "Error generating follow-up post" in error_call[0][1]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 