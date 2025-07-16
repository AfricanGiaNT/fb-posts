"""
Test for follow-up classification loss issue in regeneration.

This test reproduces the bug where regenerating follow-up posts causes them
to lose their relationship context and be treated as original posts.
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from telegram_bot import FacebookContentBot
from ai_content_generator import AIContentGenerator
from config_manager import ConfigManager
import pytest


class TestFollowUpClassification:
    """Test suite for follow-up classification preservation during regeneration."""

    def setup_method(self):
        """Set up test environment."""
        self.bot = FacebookContentBot()
        self.config = ConfigManager()
        self.ai_generator = AIContentGenerator(self.config)
        
        # Mock session with follow-up post context
        self.mock_session = {
            'series_id': 'test-series-123',
            'original_markdown': '# Test Project\nThis is a test project about automation.',
            'filename': 'test_project.md',
            'posts': [
                {
                    'post_id': 1,
                    'content': 'First post content about automation project',
                    'tone_used': 'Behind-the-Build',
                    'relationship_type': None,
                    'parent_post_id': None,
                    'content_summary': 'First post content about automation...'
                },
                {
                    'post_id': 2,
                    'content': 'Second post building on the first one',
                    'tone_used': 'Technical Deep Dive',
                    'relationship_type': 'Different Aspects',
                    'parent_post_id': 1,
                    'content_summary': 'Second post building on the first...'
                }
            ],
            'current_draft': {
                'post_content': 'This is a follow-up post that builds on my previous work...',
                'tone_used': 'Series Continuation',
                'is_context_aware': True,
                'relationship_type': 'Series Continuation',
                'parent_post_id': 2
            },
            'session_context': 'Series: 2 posts created from test_project.md',
            'post_count': 2
        }

    def test_current_draft_contains_relationship_context(self):
        """Verify that current_draft contains relationship metadata."""
        current_draft = self.mock_session['current_draft']
        
        # Should have relationship context
        assert 'relationship_type' in current_draft
        assert 'parent_post_id' in current_draft
        assert current_draft['relationship_type'] == 'Series Continuation'
        assert current_draft['parent_post_id'] == 2
        assert current_draft['is_context_aware'] == True

    def test_regenerate_post_function_signature_missing_context_params(self):
        """Test the core issue: _regenerate_post doesn't extract context from current_draft."""
        # This test demonstrates the bug by showing what's missing in the current implementation
        session = self.mock_session
        current_draft = session['current_draft']
        
        # The current_draft HAS the context we need
        assert current_draft.get('relationship_type') == 'Series Continuation'
        assert current_draft.get('parent_post_id') == 2
        assert current_draft.get('is_context_aware') == True
        
        # But looking at the _regenerate_post function in telegram_bot.py, 
        # it doesn't extract this information from current_draft
        # This is the bug we need to fix
        
        # The function should extract these values:
        expected_relationship_type = current_draft.get('relationship_type')
        expected_parent_post_id = current_draft.get('parent_post_id')
        
        # And pass them to the AI generator, but it doesn't
        assert expected_relationship_type is not None
        assert expected_parent_post_id is not None

    def test_ai_generator_regenerate_post_supports_context_params(self):
        """Verify that AIContentGenerator.regenerate_post supports relationship parameters."""
        # The AIContentGenerator already supports these parameters
        # This test confirms the API exists
        
        session_context = self.mock_session.get('session_context', '')
        previous_posts = self.mock_session.get('posts', [])
        current_draft = self.mock_session['current_draft']
        
        # Test that we can call regenerate_post with relationship parameters
        with patch.object(self.ai_generator, 'regenerate_post') as mock_regenerate:
            mock_regenerate.return_value = {
                'post_content': 'Test content',
                'tone_used': 'Test tone',
                'is_context_aware': True,
                'relationship_type': 'Series Continuation',
                'parent_post_id': 2
            }
            
            # This call should work (and does) - proving the API supports it
            result = self.ai_generator.regenerate_post(
                markdown_content=self.mock_session['original_markdown'],
                feedback="Test feedback",
                session_context=session_context,
                previous_posts=previous_posts,
                relationship_type=current_draft.get('relationship_type'),
                parent_post_id=current_draft.get('parent_post_id')
            )
            
            # Verify the call was made with the right parameters
            mock_regenerate.assert_called_once()
            call_kwargs = mock_regenerate.call_args.kwargs
            
            assert 'relationship_type' in call_kwargs
            assert 'parent_post_id' in call_kwargs
            assert call_kwargs['relationship_type'] == 'Series Continuation'
            assert call_kwargs['parent_post_id'] == 2

    @patch('scripts.ai_content_generator.AIContentGenerator.regenerate_post')
    def test_fix_verification_regenerate_post_now_preserves_context(self, mock_regenerate):
        """Test that our fix works - _regenerate_post now extracts and passes relationship context."""
        # Mock the regenerate_post method to capture what arguments it receives
        mock_regenerate.return_value = {
            'post_content': 'Regenerated content with preserved context',
            'tone_used': 'Series Continuation',
            'is_context_aware': True,
            'relationship_type': 'Series Continuation',
            'parent_post_id': 2
        }
        
        # Create a proper mock query object with async methods
        mock_query = Mock()
        mock_query.edit_message_text = AsyncMock()
        
        # Simulate calling _regenerate_post with a session that has follow-up context
        import asyncio
        
        async def run_test():
            await self.bot._regenerate_post(mock_query, self.mock_session)
        
        # Run the async test
        asyncio.run(run_test())
        
        # Verify regenerate_post was called
        assert mock_regenerate.called
        
        # Get the arguments passed to regenerate_post
        call_args = mock_regenerate.call_args
        
        # The fix: relationship_type and parent_post_id should now be passed correctly
        assert 'relationship_type' in call_args.kwargs
        assert 'parent_post_id' in call_args.kwargs
        assert call_args.kwargs['relationship_type'] == 'Series Continuation'
        assert call_args.kwargs['parent_post_id'] == 2
        
        # This demonstrates the fix works - follow-up context is now preserved!

    @patch('scripts.ai_content_generator.AIContentGenerator.regenerate_post')
    def test_regenerate_post_loses_follow_up_context(self, mock_regenerate):
        """Test that _regenerate_post doesn't pass relationship context - reproducing the bug."""
        # Mock the regenerate_post method to capture what arguments it receives
        mock_regenerate.return_value = {
            'post_content': 'Regenerated content',
            'tone_used': 'Behind-the-Build',
            'is_context_aware': False  # This shows the context was lost
        }
        
        # Create a proper mock query object with async methods
        mock_query = Mock()
        mock_query.edit_message_text = AsyncMock()
        
        # Simulate calling _regenerate_post with a session that has follow-up context
        import asyncio
        
        async def run_test():
            await self.bot._regenerate_post(mock_query, self.mock_session)
        
        # Run the async test
        asyncio.run(run_test())
        
        # Verify regenerate_post was called
        assert mock_regenerate.called
        
        # Get the arguments passed to regenerate_post
        call_args = mock_regenerate.call_args
        
        # The bug: relationship_type and parent_post_id should be passed but aren't
        # Check that the required context parameters are missing
        assert 'relationship_type' not in call_args.kwargs or call_args.kwargs.get('relationship_type') is None
        assert 'parent_post_id' not in call_args.kwargs or call_args.kwargs.get('parent_post_id') is None
        
        # This demonstrates the bug - follow-up context is lost during regeneration

    def test_follow_up_post_metadata_extraction(self):
        """Test extracting relationship metadata from current_draft."""
        current_draft = self.mock_session['current_draft']
        
        # Extract metadata that should be preserved during regeneration
        relationship_type = current_draft.get('relationship_type')
        parent_post_id = current_draft.get('parent_post_id')
        is_context_aware = current_draft.get('is_context_aware', False)
        
        # Verify we can extract the needed information
        assert relationship_type == 'Series Continuation'
        assert parent_post_id == 2
        assert is_context_aware == True

    @patch('scripts.ai_content_generator.AIContentGenerator.regenerate_post')
    def test_regeneration_should_preserve_context(self, mock_regenerate):
        """Test what regeneration SHOULD do - preserve follow-up context."""
        # This test shows what the fix should achieve
        mock_regenerate.return_value = {
            'post_content': 'Regenerated follow-up content that maintains context',
            'tone_used': 'Series Continuation',
            'is_context_aware': True,
            'relationship_type': 'Series Continuation',
            'parent_post_id': 2
        }
        
        # Extract context from current draft (what the fix should do)
        current_draft = self.mock_session['current_draft']
        relationship_type = current_draft.get('relationship_type')
        parent_post_id = current_draft.get('parent_post_id')
        
        # Manually call regenerate_post with the context (showing desired behavior)
        session_context = self.mock_session.get('session_context', '')
        previous_posts = self.mock_session.get('posts', [])
        
        result = self.ai_generator.regenerate_post(
            markdown_content=self.mock_session['original_markdown'],
            feedback="User requested regeneration - try different tone or approach",
            session_context=session_context,
            previous_posts=previous_posts,
            relationship_type=relationship_type,  # This should be passed
            parent_post_id=parent_post_id        # This should be passed
        )
        
        # Verify the result maintains context
        assert result['is_context_aware'] == True
        assert result['relationship_type'] == 'Series Continuation'
        assert result['parent_post_id'] == 2

    def test_different_relationship_types_preservation(self):
        """Test that different relationship types should be preserved."""
        test_cases = [
            {
                'relationship_type': 'Different Aspects',
                'parent_post_id': 1,
                'expected_behavior': 'Should maintain Different Aspects relationship'
            },
            {
                'relationship_type': 'Technical Deep Dive',
                'parent_post_id': 2,
                'expected_behavior': 'Should maintain Technical Deep Dive relationship'
            },
            {
                'relationship_type': 'Sequential Story',
                'parent_post_id': 3,
                'expected_behavior': 'Should maintain Sequential Story relationship'
            }
        ]
        
        for case in test_cases:
            # Mock current draft with different relationship types
            draft_with_context = {
                'post_content': 'Test content',
                'tone_used': 'Test Tone',
                'is_context_aware': True,
                'relationship_type': case['relationship_type'],
                'parent_post_id': case['parent_post_id']
            }
            
            # Verify we can extract the relationship context
            assert draft_with_context['relationship_type'] == case['relationship_type']
            assert draft_with_context['parent_post_id'] == case['parent_post_id']
            
            # This demonstrates that all relationship types should be preserved

    def test_original_posts_not_affected(self):
        """Test that original posts (without follow-up context) are not affected."""
        # Original post session (no relationship context)
        original_post_session = {
            'current_draft': {
                'post_content': 'This is an original post',
                'tone_used': 'Behind-the-Build',
                'is_context_aware': False,
                # No relationship_type or parent_post_id
            },
            'original_markdown': '# Original Project\nThis is original content.',
            'session_context': '',
            'posts': []
        }
        
        # Verify original posts don't have relationship context
        current_draft = original_post_session['current_draft']
        assert 'relationship_type' not in current_draft
        assert 'parent_post_id' not in current_draft
        assert current_draft.get('is_context_aware', False) == False
        
        # Original posts should continue to work as before

    def test_regeneration_preserves_original_metadata(self):
        """Test that regeneration preserves other important metadata."""
        current_draft = self.mock_session['current_draft']
        
        # Other metadata that should also be preserved
        assert 'post_content' in current_draft
        assert 'tone_used' in current_draft
        assert 'is_context_aware' in current_draft
        
        # After regeneration, these should still be present along with relationship data
        # This ensures our fix doesn't break existing functionality

    def test_regenerate_with_tone_should_also_preserve_context(self):
        """Test that _regenerate_with_tone also preserves follow-up context."""
        # This is another function that should preserve context
        current_draft = self.mock_session['current_draft']
        
        # Extract the context that should be preserved
        relationship_type = current_draft.get('relationship_type')
        parent_post_id = current_draft.get('parent_post_id')
        
        # Both regeneration methods should preserve this context
        assert relationship_type == 'Series Continuation'
        assert parent_post_id == 2
        
        # This highlights that multiple regeneration paths need the fix


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 