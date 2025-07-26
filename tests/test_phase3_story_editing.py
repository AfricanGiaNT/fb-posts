"""
Test Phase 3: Story Editing Implementation

This test file verifies the implementation of Phase 3 of the free-form bot improvement plan,
specifically the story editing functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from datetime import datetime

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot
from telegram import Update, CallbackQuery, User, Message, Chat
from telegram.ext import ContextTypes


@pytest.fixture
def bot():
    """Create a bot instance for testing."""
    return FacebookContentBot()

@pytest.fixture
def user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = 12345
    user.first_name = "Test"
    user.username = "testuser"
    return user

@pytest.fixture
def chat():
    """Create a mock chat."""
    chat = Mock(spec=Chat)
    chat.id = 12345
    chat.type = "private"
    return chat

@pytest.fixture
def message(user, chat):
    """Create a mock message."""
    message = Mock(spec=Message)
    message.chat = chat
    message.from_user = user
    message.text = "Test message"
    return message

@pytest.fixture
def update(user, message):
    """Create a mock update."""
    update = Mock(spec=Update)
    update.effective_user = user
    update.message = message
    return update

@pytest.fixture
def callback_query(user, message):
    """Create a mock callback query."""
    callback_query = Mock(spec=CallbackQuery)
    callback_query.from_user = user
    callback_query.data = "edit_post"
    callback_query.message = message
    return callback_query

@pytest.fixture
def context():
    """Create a mock context."""
    return Mock(spec=ContextTypes.DEFAULT_TYPE)

@pytest.fixture
def test_session():
    """Create a test session."""
    return {
        'user_id': 12345,
        'original_markdown': '# Test Post\n\nThis is a test post content.',
        'filename': 'test.md',
        'current_draft': {
            'post_content': 'This is a test Facebook post content.',
            'tone_used': 'Professional',
            'tone_reason': 'Content is technical and business-focused'
        },
        'state': None,
        'last_activity': datetime.now().isoformat(),
        'posts': [],
        'post_count': 0
    }

@pytest.fixture
def bot_with_session(bot, test_session):
    """Create a bot with a test session."""
    bot.user_sessions[12345] = test_session
    return bot

@pytest.mark.asyncio
class TestPhase3StoryEditing:
    """Test Phase 3 Story Editing functionality."""

    @pytest.mark.asyncio
    async def test_edit_post_button_in_keyboard(self, bot_with_session, callback_query, test_session):
        """Test that Edit Post button is present in the keyboard."""
        # Mock the _show_generated_post method to capture the keyboard
        with patch.object(bot_with_session, '_send_formatted_message') as mock_send:
            # Call _show_generated_post
            await bot_with_session._show_generated_post(
                callback_query, 
                test_session['current_draft'], 
                test_session
            )
            
            # Get the keyboard from the call
            call_args = mock_send.call_args
            if call_args and len(call_args) > 1 and 'reply_markup' in call_args[1]:
                reply_markup = call_args[1]['reply_markup']
                keyboard = reply_markup.inline_keyboard
                
                # Check that Edit Post button exists
                edit_button_found = False
                for row in keyboard:
                    for button in row:
                        if button.text == "✏️ Edit Post" and button.callback_data == "edit_post":
                            edit_button_found = True
                            break
                    if edit_button_found:
                        break
                
                assert edit_button_found, "Edit Post button not found in keyboard"
            else:
                pytest.fail("No reply_markup found in the call")

    @pytest.mark.asyncio
    async def test_edit_post_callback_handler(self):
        """Test that edit_post action is handled correctly."""
        # Mock the _handle_edit_post_request method
        with patch.object(self.bot, '_handle_edit_post_request') as mock_handler:
            # Set up callback data
            self.callback_query.data = "edit_post"
            
            # Call the callback handler
            await self.bot._handle_callback(self.update, self.context)
            
            # Check that the handler was called
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_edit_post_request(self):
        """Test the edit post request handler."""
        with patch.object(self.bot, '_send_formatted_message') as mock_send:
            # Call the edit post request handler
            await self.bot._handle_edit_post_request(self.callback_query, self.test_session)
            
            # Check that the session state was updated
            assert self.test_session['state'] == 'awaiting_story_edits'
            
            # Check that a message was sent
            mock_send.assert_called_once()
            
            # Check that the message contains edit instructions
            call_args = mock_send.call_args
            if call_args and len(call_args[0]) > 1:
                message_text = call_args[0][1]
                assert "Edit Post" in message_text
                assert "What would you like to change" in message_text
                assert "Examples:" in message_text
            else:
                pytest.fail("No message text found in the call")

    @pytest.mark.asyncio
    async def test_story_edit_input_handler(self):
        """Test the story edit input handler."""
        # Set up session state
        self.test_session['state'] = 'awaiting_story_edits'
        
        # Mock the _regenerate_post_with_edits method
        with patch.object(self.bot, '_regenerate_post_with_edits') as mock_regenerate:
            # Set up text input
            self.update.message.text = "Expand on the technical challenges"
            
            # Call the text handler
            await self.bot._handle_text(self.update, self.context)
            
            # Check that regeneration was called
            mock_regenerate.assert_called_once()
            
            # Check that session was updated
            assert self.test_session['edit_instructions'] == "Expand on the technical challenges"
            assert self.test_session['state'] is None

    @pytest.mark.asyncio
    async def test_edit_input_validation(self):
        """Test that edit input is properly validated."""
        # Set up session state
        self.test_session['state'] = 'awaiting_story_edits'
        
        # Test with invalid input (too long)
        long_input = "x" * 600  # Over 500 character limit
        
        with patch.object(self.bot, '_send_formatted_message') as mock_send:
            self.update.message.text = long_input
            await self.bot._handle_text(self.update, self.context)
            
            # Check that error message was sent
            call_args = mock_send.call_args
            if call_args and len(call_args[0]) > 1:
                message_text = call_args[0][1]
                assert "Invalid input" in message_text
                assert "500 characters" in message_text
            else:
                pytest.fail("No error message sent")

    @pytest.mark.asyncio
    async def test_edit_input_timeout(self):
        """Test that edit input timeout is handled."""
        # Set up session state with old timestamp
        self.test_session['state'] = 'awaiting_story_edits'
        self.test_session['last_activity'] = '2023-01-01T00:00:00'  # Old timestamp
        
        with patch.object(self.bot, '_send_formatted_message') as mock_send:
            self.update.message.text = "Some edit instructions"
            await self.bot._handle_text(self.update, self.context)
            
            # Check that timeout message was sent
            call_args = mock_send.call_args
            if call_args and len(call_args[0]) > 1:
                message_text = call_args[0][1]
                assert "timeout" in message_text.lower()
            else:
                pytest.fail("No timeout message sent")

    @pytest.mark.asyncio
    async def test_regenerate_post_with_edits(self):
        """Test the regenerate post with edits functionality."""
        # Mock the AI generator
        with patch.object(self.bot.ai_generator, 'regenerate_post') as mock_ai:
            mock_ai.return_value = {
                'post_content': 'Updated post content with technical details.',
                'tone_used': 'Professional',
                'tone_reason': 'Updated with technical focus'
            }
            
            # Mock the _show_generated_post method
            with patch.object(self.bot, '_show_generated_post') as mock_show:
                # Call regenerate with edits
                await self.bot._regenerate_post_with_edits(
                    self.update, 
                    self.context, 
                    self.test_session['original_markdown'],
                    "Expand on technical challenges"
                )
                
                # Check that AI generator was called
                mock_ai.assert_called_once()
                
                # Check that session was updated
                assert self.test_session['state'] is None
                assert 'current_draft' in self.test_session
                
                # Check that the post was shown
                mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_interface_cancel_button(self):
        """Test that cancel button works in edit interface."""
        with patch.object(self.bot, '_handle_edit_post_request') as mock_edit:
            # Set up callback data for cancel
            self.callback_query.data = "cancel"
            
            # Call the callback handler
            await self.bot._handle_callback(self.update, self.context)
            
            # Check that cancel was handled (should call _cancel_session)
            # This would be handled by the existing cancel action

    def test_edit_instructions_parsing(self):
        """Test that edit instructions are parsed correctly."""
        # Test various edit instruction formats
        test_instructions = [
            "Expand on the technical challenges",
            "Make it more casual and relatable",
            "Add more details about deployment",
            "Focus on business impact instead of technical details"
        ]
        
        for instruction in test_instructions:
            parsed = self.bot._parse_edit_instructions(instruction)
            assert isinstance(parsed, dict)
            assert 'action' in parsed
            assert 'target' in parsed

    @pytest.mark.asyncio
    async def test_edit_flow_integration(self):
        """Test the complete edit flow integration."""
        # 1. User clicks Edit Post
        with patch.object(self.bot, '_handle_edit_post_request') as mock_edit:
            self.callback_query.data = "edit_post"
            await self.bot._handle_callback(self.update, self.context)
            mock_edit.assert_called_once()
        
        # 2. User provides edit instructions
        self.test_session['state'] = 'awaiting_story_edits'
        
        with patch.object(self.bot, '_regenerate_post_with_edits') as mock_regenerate:
            self.update.message.text = "Make it more technical"
            await self.bot._handle_text(self.update, self.context)
            mock_regenerate.assert_called_once()
        
        # 3. Verify final state
        assert self.test_session['state'] is None
        assert 'edit_instructions' in self.test_session


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 