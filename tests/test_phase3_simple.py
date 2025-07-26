"""
Simple test for Phase 3: Story Editing Implementation

This test verifies that the core functionality of Phase 3 works correctly.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
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
    return user


@pytest.fixture
def update(user):
    """Create a mock update."""
    update = Mock(spec=Update)
    update.effective_user = user
    update.message = Mock(spec=Message)
    update.message.text = "Test edit instructions"
    return update


@pytest.fixture
def callback_query(user):
    """Create a mock callback query."""
    callback_query = Mock(spec=CallbackQuery)
    callback_query.from_user = user
    callback_query.data = "edit_post"
    callback_query.message = Mock(spec=Message)
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


def test_edit_instructions_parsing(bot):
    """Test that edit instructions are parsed correctly."""
    # Test various edit instruction formats
    test_instructions = [
        "Expand on the technical challenges",
        "Make it more casual and relatable",
        "Add more details about deployment",
        "Focus on business impact instead of technical details"
    ]
    
    for instruction in test_instructions:
        parsed = bot._parse_edit_instructions(instruction)
        assert isinstance(parsed, dict)
        assert 'action' in parsed
        assert 'target' in parsed


def test_validate_freeform_input(bot):
    """Test that freeform input validation works."""
    # Test valid input
    assert bot._validate_freeform_input("Valid edit instructions")
    
    # Test invalid input (too long)
    long_input = "x" * 600  # Over 500 character limit
    assert not bot._validate_freeform_input(long_input)
    
    # Test invalid input (too short)
    assert not bot._validate_freeform_input("")


def test_check_freeform_timeout(bot):
    """Test that freeform timeout checking works."""
    # Test current session (should not timeout)
    current_session = {
        'last_activity': datetime.now().isoformat()
    }
    assert not bot._check_freeform_timeout(current_session)
    
    # Test old session (should timeout)
    old_session = {
        'last_activity': '2023-01-01T00:00:00'
    }
    assert bot._check_freeform_timeout(old_session)


@pytest.mark.asyncio
async def test_handle_edit_post_request(bot, callback_query, test_session):
    """Test the edit post request handler."""
    with patch.object(bot, '_send_formatted_message') as mock_send:
        # Call the edit post request handler
        await bot._handle_edit_post_request(callback_query, test_session)
        
        # Check that the session state was updated
        assert test_session['state'] == 'awaiting_story_edits'
        
        # Check that a message was sent
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_story_edit_input_handler(bot, update, context, test_session):
    """Test the story edit input handler."""
    # Set up session state
    test_session['state'] = 'awaiting_story_edits'
    bot.user_sessions[12345] = test_session
    
    # Mock the AI generator and _show_generated_post to avoid actual API calls
    with patch.object(bot.ai_generator, 'regenerate_post') as mock_ai, \
         patch.object(bot, '_show_generated_post') as mock_show:
        
        mock_ai.return_value = {
            'post_content': 'Updated post content with technical details.',
            'tone_used': 'Professional',
            'tone_reason': 'Updated with technical focus'
        }
        
        # Set up text input
        update.message.text = "Expand on the technical challenges"
        
        # Call the text handler
        await bot._handle_text(update, context)
        
        # Check that AI generator was called
        mock_ai.assert_called_once()
        
        # Check that session was updated
        assert test_session['edit_instructions'] == "Expand on the technical challenges"
        assert test_session['state'] is None


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 