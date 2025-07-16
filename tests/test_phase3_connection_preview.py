"""
Test Phase 3: Connection Preview Generation
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot

class TestConnectionPreviewGeneration:
    """Test the connection preview generation functionality."""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing."""
        with patch('telegram_bot.ConfigManager'), \
             patch('telegram_bot.AIContentGenerator'), \
             patch('telegram_bot.AirtableConnector'):
            bot = FacebookContentBot()
            return bot
    
    @pytest.fixture
    def mock_session_with_series(self):
        """Create a mock session with a series of posts."""
        return {
            'series_id': 'test-series-789',
            'original_markdown': 'Test markdown content about building an automation system',
            'filename': 'automation_system.md',
            'posts': [
                {
                    'post_id': 1,
                    'content': 'Building an automated workflow system using Python and APIs. Started with the basic architecture and planning phase.',
                    'tone_used': 'Behind-the-Build',
                    'approved': True,
                    'content_summary': 'Building an automated workflow system using Python and APIs. Started with the basic architecture...',
                    'relationship_type': None,
                    'parent_post_id': None
                },
                {
                    'post_id': 2,
                    'content': 'Encountered several challenges during implementation including API rate limits and authentication issues.',
                    'tone_used': 'What Broke',
                    'approved': True,
                    'content_summary': 'Encountered several challenges during implementation including API rate limits and authentication...',
                    'relationship_type': 'Different Aspects',
                    'parent_post_id': 1
                },
                {
                    'post_id': 3,
                    'content': 'Successfully deployed the automation system with 95% uptime and processing 1000+ requests daily.',
                    'tone_used': 'Finished & Proud',
                    'approved': True,
                    'content_summary': 'Successfully deployed the automation system with 95% uptime and processing 1000+ requests daily.',
                    'relationship_type': 'Sequential Story',
                    'parent_post_id': 2
                }
            ],
            'post_count': 3,
            'session_context': 'Test context for automation system project',
            'pending_generation': {
                'relationship_type': 'Technical Deep Dive',
                'parent_post_id': 2,
                'connection_preview': None,
                'user_confirmed': False
            },
            'workflow_state': 'awaiting_generation_confirmation'
        }
    
    @pytest.fixture
    def mock_callback_query(self):
        """Create a mock callback query."""
        query = Mock(spec=CallbackQuery)
        query.from_user.id = 12345
        query.data = "connection_preview"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()
        return query
    
    @pytest.mark.asyncio
    async def test_generate_connection_preview_basic(self, bot, mock_session_with_series):
        """Test basic connection preview generation."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_series
        session = bot.user_sessions[user_id]
        
        selected_post = session['posts'][1]  # Post 2
        relationship_type = 'Technical Deep Dive'
        
        # Act
        preview = bot._generate_connection_preview(selected_post, relationship_type, session['posts'])
        
        # Assert
        assert preview is not None
        assert 'Technical Deep Dive' in preview
        assert 'Post 2' in preview or '2' in preview
        assert 'What Broke' in preview  # Should mention the tone of the parent post
    
    @pytest.mark.asyncio
    async def test_calculate_connection_strength_strong(self, bot, mock_session_with_series):
        """Test connection strength calculation for strong connections."""
        # Setup
        session = mock_session_with_series
        posts = session['posts']
        
        # Act - Sequential story should be strong connection
        strength = bot._calculate_connection_strength('Sequential Story', posts[1], posts)
        
        # Assert
        assert strength in ['Strong', 'Medium', 'Weak']
        assert strength == 'Strong'  # Sequential stories are strong connections
    
    @pytest.mark.asyncio
    async def test_calculate_connection_strength_medium(self, bot, mock_session_with_series):
        """Test connection strength calculation for medium connections."""
        # Setup
        session = mock_session_with_series
        posts = session['posts']
        
        # Act - Different aspects should be medium connection
        strength = bot._calculate_connection_strength('Different Aspects', posts[0], posts)
        
        # Assert
        assert strength in ['Strong', 'Medium', 'Weak']
        assert strength == 'Medium'  # Different aspects are medium connections
    
    @pytest.mark.asyncio
    async def test_calculate_connection_strength_weak(self, bot, mock_session_with_series):
        """Test connection strength calculation for weak connections."""
        # Setup
        session = mock_session_with_series
        posts = session['posts']
        
        # Act - Thematic connection should be weak connection
        strength = bot._calculate_connection_strength('Thematic Connection', posts[0], posts)
        
        # Assert
        assert strength in ['Strong', 'Medium', 'Weak']
        assert strength == 'Weak'  # Thematic connections are weak connections
    
    @pytest.mark.asyncio
    async def test_get_relationship_emoji(self, bot):
        """Test relationship type emoji generation."""
        # Test all relationship types have emojis
        relationship_types = [
            'Different Aspects',
            'Different Angles', 
            'Series Continuation',
            'Thematic Connection',
            'Technical Deep Dive',
            'Sequential Story',
            'AI Decide'
        ]
        
        for rel_type in relationship_types:
            emoji = bot._get_relationship_emoji(rel_type)
            assert emoji is not None
            assert len(emoji) > 0
            # Should be an actual emoji character
            assert any(ord(char) > 127 for char in emoji)  # Contains non-ASCII (emoji) characters
    
    @pytest.mark.asyncio
    async def test_enhanced_generation_confirmation_display(self, bot, mock_session_with_series, mock_callback_query):
        """Test enhanced generation confirmation with connection preview."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_series
        selected_post = mock_session_with_series['posts'][1]  # Post 2
        
        # Act
        await bot._show_generation_confirmation(mock_callback_query, user_id, selected_post)
        
        # Assert
        mock_callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Check for enhanced preview elements
        assert "Ready to Generate Post" in message_text
        assert "Technical Deep Dive" in message_text  # Relationship type
        assert "Connection Strength:" in message_text  # Connection strength indicator
        assert "📊" in message_text or "🔗" in message_text  # Should have emoji indicators
        assert "Post 2" in message_text  # Building on specific post
    
    @pytest.mark.asyncio
    async def test_reading_sequence_estimation(self, bot, mock_session_with_series):
        """Test reading sequence estimation for posts."""
        # Setup
        session = mock_session_with_series
        posts = session['posts']
        
        # Act
        sequence = bot._estimate_reading_sequence(posts, 2)  # Building on post 2
        
        # Assert
        assert sequence is not None
        assert isinstance(sequence, str)
        assert "Post 1" in sequence  # Should include the sequence
        assert "Post 2" in sequence
        assert "→" in sequence or "->" in sequence  # Should show flow
    
    @pytest.mark.asyncio
    async def test_connection_preview_with_different_relationship_types(self, bot, mock_session_with_series):
        """Test connection preview generation with different relationship types."""
        # Setup
        session = mock_session_with_series
        selected_post = session['posts'][0]  # Post 1
        posts = session['posts']
        
        relationship_types = [
            'Different Aspects',
            'Technical Deep Dive',
            'Sequential Story',
            'Thematic Connection'
        ]
        
        for rel_type in relationship_types:
            # Act
            preview = bot._generate_connection_preview(selected_post, rel_type, posts)
            
            # Assert
            assert preview is not None
            assert rel_type in preview
            assert len(preview) > 50  # Should be a substantial preview
            # Should contain relationship-specific language
            if rel_type == 'Technical Deep Dive':
                assert 'technical' in preview.lower() or 'detail' in preview.lower()
            elif rel_type == 'Sequential Story':
                assert 'continues' in preview.lower() or 'next' in preview.lower()
    
    @pytest.mark.asyncio
    async def test_connection_preview_storage_in_session(self, bot, mock_session_with_series, mock_callback_query):
        """Test that connection preview is stored in session for later use."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_series
        selected_post = mock_session_with_series['posts'][1]
        
        # Act
        await bot._show_generation_confirmation(mock_callback_query, user_id, selected_post)
        
        # Assert
        session = bot.user_sessions[user_id]
        assert 'pending_generation' in session
        assert session['pending_generation']['connection_preview'] is not None
        assert len(session['pending_generation']['connection_preview']) > 0
    
    @pytest.mark.asyncio
    async def test_connection_strength_indicator_display(self, bot, mock_session_with_series, mock_callback_query):
        """Test that connection strength indicator is properly displayed."""
        # Setup
        user_id = 12345
        bot.user_sessions[user_id] = mock_session_with_series
        selected_post = mock_session_with_series['posts'][1]
        
        # Act
        await bot._show_generation_confirmation(mock_callback_query, user_id, selected_post)
        
        # Assert
        call_args = mock_callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        
        # Should have connection strength indicators
        strength_indicators = ['Strong', 'Medium', 'Weak']
        assert any(indicator in message_text for indicator in strength_indicators)
        
        # Should have visual indicators
        visual_indicators = ['🟢', '🟡', '🔴', '💪', '⚖️', '🔗']
        assert any(indicator in message_text for indicator in visual_indicators) 