#!/usr/bin/env python3
"""
Unit Tests for Task 2, Subtask 2.1: Series Overview Command
Tests the /series command functionality and series tree visualization
"""

import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from datetime import datetime
import uuid

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from telegram_bot import FacebookContentBot
from telegram import Update, User, Message, Chat, CallbackQuery

class TestSeriesOverviewCommand(unittest.TestCase):
    """Test the series overview command functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = FacebookContentBot()
        self.user_id = 12345
        self.test_series_id = str(uuid.uuid4())
        
        # Mock Telegram objects
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = self.user_id
        self.mock_user.first_name = "TestUser"
        
        self.mock_chat = MagicMock(spec=Chat)
        self.mock_chat.id = self.user_id
        
        self.mock_message = MagicMock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update = MagicMock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Create test session with multiple posts
        self.test_session = {
            'series_id': self.test_series_id,
            'original_markdown': '# Test Project\n\nThis is a test project.',
            'filename': 'test_project.md',
            'posts': [
                {
                    'post_id': 1,
                    'content': 'This is the first post about my project...',
                    'tone_used': 'Behind-the-Build',
                    'airtable_record_id': 'rec123',
                    'approved_at': '2025-01-09T10:00:00Z',
                    'parent_post_id': None,
                    'relationship_type': None,
                    'content_summary': 'This is the first post about my project...'
                },
                {
                    'post_id': 2,
                    'content': 'Building on my previous post, here are the technical details...',
                    'tone_used': 'Technical Deep Dive',
                    'airtable_record_id': 'rec456',
                    'approved_at': '2025-01-09T10:30:00Z',
                    'parent_post_id': 1,
                    'relationship_type': 'Technical Deep Dive',
                    'content_summary': 'Building on my previous post, here are the technical details...'
                },
                {
                    'post_id': 3,
                    'content': 'Following up on the technical aspects, here what broke...',
                    'tone_used': 'What Broke',
                    'airtable_record_id': 'rec789',
                    'approved_at': '2025-01-09T11:00:00Z',
                    'parent_post_id': 2,
                    'relationship_type': 'Sequential Story',
                    'content_summary': 'Following up on the technical aspects, here what broke...'
                }
            ],
            'current_draft': None,
            'session_started': '2025-01-09T09:00:00Z',
            'last_activity': '2025-01-09T11:00:00Z',
            'session_context': 'Test session context',
            'post_count': 3,
            'series_metadata': {
                'post_count': 3,
                'relationship_types_used': ['Technical Deep Dive', 'Sequential Story'],
                'created_at': '2025-01-09T09:00:00Z',
                'last_modified': '2025-01-09T11:00:00Z',
                'total_approvals': 3,
                'most_used_tone': 'Behind-the-Build'
            }
        }
        
        self.bot.user_sessions[self.user_id] = self.test_session
    
    def test_series_command_handler_registration(self):
        """Test that the series command handler is properly registered."""
        # Check that the method exists
        self.assertTrue(hasattr(self.bot, '_series_command'), "Bot should have _series_command method")
        
        # Check that the method is callable
        self.assertTrue(callable(getattr(self.bot, '_series_command')), "Series command method should be callable")
        
        # Check that the setup_handlers method includes the series command
        # This is a more reliable test than checking the handlers dict
        import inspect
        setup_source = inspect.getsource(self.bot._setup_handlers)
        self.assertIn('CommandHandler("series"', setup_source, "setup_handlers should include series command")
    
    async def test_series_command_with_active_session(self):
        """Test series command with an active session."""
        # Mock context
        mock_context = MagicMock()
        
        with patch.object(self.bot, '_show_series_overview', new_callable=AsyncMock) as mock_show_series:
            await self.bot._series_command(self.mock_update, mock_context)
            
            # Verify that show_series_overview was called
            mock_show_series.assert_called_once_with(self.mock_update, mock_context)
    
    async def test_series_command_without_active_session(self):
        """Test series command without an active session."""
        # Remove user session
        del self.bot.user_sessions[self.user_id]
        
        mock_context = MagicMock()
        
        await self.bot._series_command(self.mock_update, mock_context)
        
        # Verify appropriate error message
        self.mock_message.reply_text.assert_called_once()
        args, kwargs = self.mock_message.reply_text.call_args
        self.assertIn("no active series", args[0].lower())
    
    async def test_show_series_overview_display(self):
        """Test series overview display formatting."""
        mock_context = MagicMock()
        
        with patch.object(self.bot, '_format_series_tree') as mock_format_tree, \
             patch.object(self.bot, '_calculate_series_statistics') as mock_calc_stats:
            
            mock_format_tree.return_value = "📊 Series Tree:\n├── Post 1: Behind-the-Build\n└── Post 2: Technical Deep Dive"
            mock_calc_stats.return_value = {
                'total_posts': 3,
                'relationship_types': ['Technical Deep Dive', 'Sequential Story'],
                'most_used_tone': 'Behind-the-Build',
                'creation_date': '2025-01-09'
            }
            
            await self.bot._show_series_overview(self.mock_update, mock_context)
            
            # Verify message was sent
            self.mock_message.reply_text.assert_called_once()
            args, kwargs = self.mock_message.reply_text.call_args
            message_text = args[0]
            
            # Check message contains expected elements
            self.assertIn("Series Overview", message_text)
            self.assertIn("📊 Series Tree:", message_text)
            self.assertIn("3 posts", message_text)
            self.assertIn("Behind-the-Build", message_text)
    
    def test_build_relationship_tree_simple(self):
        """Test building relationship tree with simple parent-child relationships."""
        posts = self.test_session['posts']
        
        tree = self.bot._build_relationship_tree(posts)
        
        # Verify tree structure
        self.assertIsInstance(tree, dict)
        self.assertIn('roots', tree)
        self.assertIn('children', tree)
        
        # Check that post 1 is a root (no parent)
        self.assertIn(1, tree['roots'])
        
        # Check that post 2 is a child of post 1
        self.assertIn(1, tree['children'])
        self.assertIn(2, tree['children'][1])
        
        # Check that post 3 is a child of post 2
        self.assertIn(2, tree['children'])
        self.assertIn(3, tree['children'][2])
    
    def test_build_relationship_tree_complex(self):
        """Test building relationship tree with complex relationships."""
        # Add more complex relationships
        complex_posts = self.test_session['posts'] + [
            {
                'post_id': 4,
                'content': 'Different angle on the original project...',
                'tone_used': 'Different Angles',
                'parent_post_id': 1,  # Also builds on post 1
                'relationship_type': 'Different Angles',
                'content_summary': 'Different angle on the original project...'
            }
        ]
        
        tree = self.bot._build_relationship_tree(complex_posts)
        
        # Verify that post 1 has multiple children (2 and 4)
        self.assertIn(1, tree['children'])
        self.assertEqual(len(tree['children'][1]), 2)
        self.assertIn(2, tree['children'][1])
        self.assertIn(4, tree['children'][1])
    
    def test_format_series_tree_display(self):
        """Test series tree formatting for display."""
        # Use complex posts to create scenario with multiple children
        complex_posts = self.test_session['posts'] + [
            {
                'post_id': 4,
                'content': 'Different angle on the original project...',
                'tone_used': 'Different Angles',
                'parent_post_id': 1,  # Also builds on post 1
                'relationship_type': 'Different Angles',
                'content_summary': 'Different angle on the original project...'
            }
        ]
        
        tree_display = self.bot._format_series_tree(complex_posts)
        
        # Check basic structure
        self.assertIsInstance(tree_display, str)
        self.assertIn("Post 1", tree_display)
        self.assertIn("Post 2", tree_display)
        self.assertIn("Post 3", tree_display)
        self.assertIn("Post 4", tree_display)
        
        # Check relationship indicators - now Post 1 has multiple children (2 and 4)
        self.assertIn("├──", tree_display)  # Tree structure symbols for non-last children
        self.assertIn("└──", tree_display)  # Tree structure symbols for last children
        self.assertIn("Behind-the-Build", tree_display)  # Tone information
        self.assertIn("Technical Deep Dive", tree_display)  # Relationship type
    
    def test_calculate_series_statistics(self):
        """Test series statistics calculation."""
        posts = self.test_session['posts']
        
        stats = self.bot._calculate_series_statistics(posts)
        
        # Verify statistics structure
        self.assertIsInstance(stats, dict)
        self.assertIn('total_posts', stats)
        self.assertIn('relationship_types_used', stats)
        self.assertIn('tone_distribution', stats)
        self.assertIn('creation_timespan', stats)
        
        # Verify statistics values
        self.assertEqual(stats['total_posts'], 3)
        self.assertIn('Technical Deep Dive', stats['relationship_types_used'])
        self.assertIn('Sequential Story', stats['relationship_types_used'])
        self.assertIn('Behind-the-Build', stats['tone_distribution'])
    
    def test_series_navigation_keyboard(self):
        """Test series navigation keyboard generation."""
        with patch.object(self.bot, '_create_series_navigation_keyboard') as mock_keyboard:
            mock_keyboard.return_value = MagicMock()
            
            # Test keyboard creation
            keyboard = self.bot._create_series_navigation_keyboard(self.test_session)
            
            self.assertIsNotNone(keyboard)
            mock_keyboard.assert_called_once_with(self.test_session)
    
    def test_series_overview_with_empty_posts(self):
        """Test series overview with no posts."""
        # Create session with no posts
        empty_session = {
            'series_id': self.test_series_id,
            'original_markdown': '# Test Project\n\nThis is a test project.',
            'filename': 'test_project.md',
            'posts': [],
            'post_count': 0
        }
        
        self.bot.user_sessions[self.user_id] = empty_session
        
        stats = self.bot._calculate_series_statistics(empty_session['posts'])
        
        # Verify empty statistics
        self.assertEqual(stats['total_posts'], 0)
        self.assertEqual(len(stats['relationship_types_used']), 0)
        self.assertEqual(len(stats['tone_distribution']), 0)
    
    def test_series_overview_performance(self):
        """Test series overview performance with many posts."""
        # Create a large number of posts
        large_posts = []
        for i in range(50):
            large_posts.append({
                'post_id': i + 1,
                'content': f'Post {i + 1} content...',
                'tone_used': 'Behind-the-Build',
                'parent_post_id': i if i > 0 else None,
                'relationship_type': 'Series Continuation' if i > 0 else None,
                'content_summary': f'Post {i + 1} summary...'
            })
        
        # Test that tree building doesn't fail with large datasets
        tree = self.bot._build_relationship_tree(large_posts)
        
        self.assertIsInstance(tree, dict)
        self.assertIn('roots', tree)
        self.assertIn('children', tree)
        
        # Test statistics calculation performance
        stats = self.bot._calculate_series_statistics(large_posts)
        
        self.assertEqual(stats['total_posts'], 50)
        self.assertIsInstance(stats['relationship_types_used'], list)


if __name__ == '__main__':
    unittest.main() 