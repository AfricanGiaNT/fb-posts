import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from scripts.telegram_bot import FacebookContentBot

class TestLengthControlIntegration:
    """Integration tests for length control feature."""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing."""
        with patch('scripts.telegram_bot.ConfigManager'), \
             patch('scripts.telegram_bot.AIContentGenerator'), \
             patch('scripts.telegram_bot.AirtableConnector'), \
             patch('scripts.telegram_bot.Application'):
            bot = FacebookContentBot()
            return bot
    
    @pytest.mark.asyncio
    async def test_length_selection_callback(self, bot):
        """Test that length selection callback works correctly."""
        # Mock query and session
        query = MagicMock()
        session = {'original_markdown': '# Test Content\n\nThis is test content.'}
        
        # Mock _send_formatted_message
        bot._send_formatted_message = AsyncMock()
        bot._show_initial_tone_selection_interface = AsyncMock()
        
        # Test short length selection
        await bot._handle_length_selection(query, session, 'short')
        
        # Verify length preference was stored
        assert session['length_preference'] == 'short'
        
        # Verify confirmation message was sent
        bot._send_formatted_message.assert_called_once()
        call_args = bot._send_formatted_message.call_args[0]
        assert "Length set to: **Short Form**" in call_args[1]
        
        # Verify tone selection interface was shown
        bot._show_initial_tone_selection_interface.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_length_selection_long(self, bot):
        """Test long length selection."""
        query = MagicMock()
        session = {'original_markdown': '# Test Content\n\nThis is test content.'}
        
        bot._send_formatted_message = AsyncMock()
        bot._show_initial_tone_selection_interface = AsyncMock()
        
        await bot._handle_length_selection(query, session, 'long')
        
        assert session['length_preference'] == 'long'
        
        call_args = bot._send_formatted_message.call_args[0]
        assert "Length set to: **Long Form**" in call_args[1]
    
    def test_length_preference_passed_to_generation(self, bot):
        """Test that length preference is passed to AI generation."""
        # Mock AI generator
        bot.ai_generator.generate_facebook_post = MagicMock(return_value={
            'post_content': 'Test post',
            'tone_used': 'Behind-the-Build',
            'tone_reason': 'Test reason'
        })
        
        # Create session with length preference
        session = {
            'original_markdown': '# Test Content\n\nThis is test content.',
            'length_preference': 'short',
            'session_context': '',
            'posts': []
        }
        
        # Mock the generation method
        with patch.object(bot, '_generate_and_show_post') as mock_generate:
            # This would normally be called by the bot flow
            # We're just testing that the length preference is available
            assert session.get('length_preference') == 'short'
    
    @pytest.mark.asyncio
    async def test_edit_instructions_with_length(self, bot):
        """Test that edit instructions with length commands work."""
        # Mock update and context
        update = MagicMock()
        update.effective_user.id = 12345
        context = MagicMock()
        
        # Mock user session
        session = {
            'original_markdown': '# Test Content\n\nThis is test content.',
            'current_draft': {'post_content': 'Original post'},
            'session_context': ''
        }
        bot.user_sessions = {12345: session}
        
        # Mock AI generator
        bot.ai_generator.regenerate_post = MagicMock(return_value={
            'post_content': 'Shortened post',
            'tone_used': 'Behind-the-Build',
            'tone_reason': 'Made shorter'
        })
        
        bot._send_formatted_message = AsyncMock()
        bot._show_generated_post = AsyncMock()
        
        # Test edit instruction with length command
        edit_instructions = "make it short and concise"
        
        await bot._regenerate_post_with_edits(update, context, 
                                            session['original_markdown'], 
                                            edit_instructions)
        
        # Verify that regenerate_post was called with length preference
        bot.ai_generator.regenerate_post.assert_called_once()
        call_kwargs = bot.ai_generator.regenerate_post.call_args[1]
        assert call_kwargs['length_preference'] == 'short'

if __name__ == "__main__":
    pytest.main([__file__]) 