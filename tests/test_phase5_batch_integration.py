"""
Test suite for Phase 5: Batch Processing Integration functionality.

This test suite covers:
- Batch context prompting before generation
- Context integration with batch post generation
- Skip context functionality for batch processing
- Enhanced batch generation with context applied to all posts
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
    """Create a test session with batch data."""
    return {
        'user_id': 12345,
        'mode': 'multi',
        'files': [
            {
                'file_id': 'file1',
                'filename': 'test1.md',
                'content': '# Test Post 1\n\nThis is test content 1.',
                'upload_timestamp': datetime.now().isoformat()
            },
            {
                'file_id': 'file2',
                'filename': 'test2.md',
                'content': '# Test Post 2\n\nThis is test content 2.',
                'upload_timestamp': datetime.now().isoformat()
            }
        ],
        'content_strategy': {
            'recommended_sequence': [
                {'file': {'filename': 'test1.md'}, 'reason': 'First post'},
                {'file': {'filename': 'test2.md'}, 'reason': 'Second post'}
            ]
        },
        'state': 'ready_for_generation',
        'last_activity': datetime.now().isoformat()
    }


@pytest.fixture
def bot_with_session(bot, test_session):
    """Create a bot instance with a test session."""
    bot.user_sessions = {12345: test_session}
    return bot


class TestPhase5BatchIntegration:
    """Test suite for Phase 5: Batch Processing Integration functionality."""

    @pytest.mark.asyncio
    async def test_handle_ai_strategy_asks_for_batch_context(self, bot_with_session, callback_query, test_session):
        """Test that AI strategy selection asks for batch context."""
        # Arrange
        # Mock the _ask_for_batch_context method
        bot_with_session._ask_for_batch_context = AsyncMock()
        
        # Act
        await bot_with_session._handle_ai_strategy(callback_query, test_session)
        
        # Assert
        bot_with_session._ask_for_batch_context.assert_called_once_with(callback_query, test_session)

    @pytest.mark.asyncio
    async def test_ask_for_batch_context_sets_state_and_sends_message(self, bot_with_session, callback_query, test_session):
        """Test that asking for batch context sets the correct state and sends the right message."""
        # Arrange
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._ask_for_batch_context(callback_query, test_session)
        
        # Assert
        assert test_session['state'] == 'awaiting_batch_context'
        assert test_session['last_activity'] is not None
        
        # Check that the message was sent
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert call_args[0][0] == callback_query  # First argument should be the query
        assert "Batch Context" in call_args[0][1]  # Message should contain the title
        assert "2 files" in call_args[0][1]  # Should show the number of files
        assert "skip_batch_context" in str(call_args[1]['reply_markup'])  # Should have skip button

    @pytest.mark.asyncio
    async def test_handle_batch_context_input_validates_and_stores_context(self, bot_with_session, update, context, test_session):
        """Test that batch context input is validated and stored correctly."""
        # Arrange
        test_session['state'] = 'awaiting_batch_context'
        
        # Mock the _generate_batch_posts_with_context method
        bot_with_session._generate_batch_posts_with_context = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._handle_batch_context_input(update, context, "Focus on technical details")
        
        # Assert
        assert test_session['batch_context'] == "Focus on technical details"
        assert test_session['last_activity'] is not None
        bot_with_session._generate_batch_posts_with_context.assert_called_once_with(update, context, test_session)

    @pytest.mark.asyncio
    async def test_handle_batch_context_input_rejects_invalid_input(self, bot_with_session, update, context, test_session):
        """Test that invalid batch context input is rejected."""
        # Arrange
        test_session['state'] = 'awaiting_batch_context'
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act - Test with input that's too long
        long_input = "x" * 501  # Over 500 character limit
        await bot_with_session._handle_batch_context_input(update, context, long_input)
        
        # Assert
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert "Invalid input" in call_args[0][1]
        assert "500 characters" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_generate_batch_posts_with_context_shows_context_info(self, bot_with_session, update, context, test_session):
        """Test that batch generation shows context information when available."""
        # Arrange
        test_session['batch_context'] = 'Focus on technical details'
        
        # Mock the _generate_batch_posts method
        bot_with_session._generate_batch_posts = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._generate_batch_posts_with_context(update, context, test_session)
        
        # Assert
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert "Generating batch posts" in call_args[0][1]
        assert "Focus on technical details" in call_args[0][1]  # Should show context
        
        # Check that the batch generation was called
        bot_with_session._generate_batch_posts.assert_called_once_with(update, test_session)

    @pytest.mark.asyncio
    async def test_generate_batch_posts_with_context_no_context(self, bot_with_session, update, context, test_session):
        """Test that batch generation works without context."""
        # Arrange
        # No batch context set
        
        # Mock the _generate_batch_posts method
        bot_with_session._generate_batch_posts = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._generate_batch_posts_with_context(update, context, test_session)
        
        # Assert
        bot_with_session._send_formatted_message.assert_called_once()
        call_args = bot_with_session._send_formatted_message.call_args
        assert "Generating batch posts" in call_args[0][1]
        assert "context" not in call_args[0][1]  # Should not mention context when none provided
        
        # Check that the batch generation was called
        bot_with_session._generate_batch_posts.assert_called_once_with(update, test_session)

    @pytest.mark.asyncio
    async def test_handle_skip_batch_context_generates_without_context(self, bot_with_session, callback_query, test_session):
        """Test that skipping batch context generates posts without context."""
        # Arrange
        # Mock the _generate_batch_posts_with_context method
        bot_with_session._generate_batch_posts_with_context = AsyncMock()
        
        # Act
        await bot_with_session._handle_skip_batch_context(callback_query, test_session)
        
        # Assert
        bot_with_session._generate_batch_posts_with_context.assert_called_once_with(callback_query, None, test_session)

    @pytest.mark.asyncio
    async def test_generate_batch_posts_applies_context_to_all_posts(self, bot_with_session, update, test_session):
        """Test that batch generation applies context to all posts."""
        # Arrange
        test_session['batch_context'] = 'Focus on technical details'
        test_session['selected_tone'] = 'professional'
        
        # Mock the _process_in_background method
        bot_with_session._process_in_background = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Mock asyncio.gather to return successful results
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = [
                {'post_content': 'Generated post 1', 'tone_used': 'professional'},
                {'post_content': 'Generated post 2', 'tone_used': 'professional'}
            ]
            
            # Act
            await bot_with_session._generate_batch_posts(update, test_session)
            
            # Assert
            # Check that _process_in_background was called for each file
            assert bot_with_session._process_in_background.call_count == 2
            
            # Check that each call included the batch context
            calls = bot_with_session._process_in_background.call_args_list
            for call in calls:
                call_args = call[0]
                call_kwargs = call[1]
                assert call_args[0] == bot_with_session.ai_generator.generate_facebook_post
                assert call_args[1] in ['# Test Post 1\n\nThis is test content 1.', '# Test Post 2\n\nThis is test content 2.']
                # Check keyword arguments
                assert call_kwargs['user_tone_preference'] == 'professional'
                assert call_kwargs['audience_type'] == 'business'
                assert call_kwargs['freeform_context'] == 'Focus on technical details'

    @pytest.mark.asyncio
    async def test_generate_batch_posts_no_context_still_works(self, bot_with_session, update, test_session):
        """Test that batch generation works without context."""
        # Arrange
        # No batch context set
        test_session['selected_tone'] = 'professional'
        
        # Mock the _process_in_background method
        bot_with_session._process_in_background = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Mock asyncio.gather to return successful results
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = [
                {'post_content': 'Generated post 1', 'tone_used': 'professional'},
                {'post_content': 'Generated post 2', 'tone_used': 'professional'}
            ]
            
            # Act
            await bot_with_session._generate_batch_posts(update, test_session)
            
            # Assert
            # Check that _process_in_background was called for each file
            assert bot_with_session._process_in_background.call_count == 2
            
            # Check that each call had empty context
            calls = bot_with_session._process_in_background.call_args_list
            for call in calls:
                call_kwargs = call[1]
                assert call_kwargs['freeform_context'] == ''  # freeform_context should be empty

    @pytest.mark.asyncio
    async def test_batch_context_preserved_across_generation(self, bot_with_session, update, test_session):
        """Test that batch context is preserved during generation."""
        # Arrange
        test_session['batch_context'] = 'Focus on technical details'
        test_session['selected_tone'] = 'professional'
        
        # Mock the _process_in_background method
        bot_with_session._process_in_background = AsyncMock()
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Mock asyncio.gather to return successful results
        with patch('asyncio.gather') as mock_gather:
            mock_gather.return_value = [
                {'post_content': 'Generated post 1', 'tone_used': 'professional'},
                {'post_content': 'Generated post 2', 'tone_used': 'professional'}
            ]
            
            # Act
            await bot_with_session._generate_batch_posts(update, test_session)
            
            # Assert
            # Check that batch context is still in session
            assert test_session['batch_context'] == 'Focus on technical details'

    @pytest.mark.asyncio
    async def test_batch_context_timeout_handling(self, bot_with_session, test_session):
        """Test that batch context timeout is handled correctly."""
        # Arrange - Set last activity to more than 5 minutes ago
        test_session['last_activity'] = (datetime.now() - timedelta(minutes=6)).isoformat()
        test_session['state'] = 'awaiting_batch_context'
        
        # Act
        result = bot_with_session._check_freeform_timeout(test_session)
        
        # Assert
        assert result is True  # Should indicate timeout

    @pytest.mark.asyncio
    async def test_batch_context_error_handling(self, bot_with_session, update, context, test_session):
        """Test that errors in batch context processing are handled gracefully."""
        # Arrange
        test_session['state'] = 'awaiting_batch_context'
        
        # Mock the _generate_batch_posts method to raise an exception
        bot_with_session._generate_batch_posts = AsyncMock(side_effect=Exception("Generation failed"))
        
        # Mock the _send_formatted_message method
        bot_with_session._send_formatted_message = AsyncMock()
        
        # Act
        await bot_with_session._handle_batch_context_input(update, context, "Focus on technical details")
        
        # Assert
        # Should be called multiple times: validation success, generation message, error message
        assert bot_with_session._send_formatted_message.call_count >= 2
        
        # Check that the error message was sent
        calls = bot_with_session._send_formatted_message.call_args_list
        error_call = calls[-1]  # Last call should be the error message
        assert "Error generating batch posts" in error_call[0][1]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 