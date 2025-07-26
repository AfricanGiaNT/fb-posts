import pytest
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch, AsyncMock
from scripts.telegram_bot import FacebookContentBot
from scripts.ai_content_generator import AIContentGenerator
from scripts.config_manager import ConfigManager

class TestLengthControl:
    """Test the length control feature for post generation."""
    
    @pytest.fixture
    def bot(self):
        """Create a bot instance for testing."""
        config_manager = ConfigManager()
        bot = FacebookContentBot()
        return bot
    
    @pytest.fixture
    def ai_generator(self):
        """Create an AI generator instance for testing."""
        config_manager = ConfigManager()
        return AIContentGenerator(config_manager)
    
    def test_parse_edit_instructions_length_short(self, bot):
        """Test parsing edit instructions for short length."""
        edit_text = "make it short and concise"
        parsed = bot._parse_edit_instructions(edit_text)
        
        assert parsed['length_change'] == 'short'
        assert parsed['action'] == 'shorten'
    
    def test_parse_edit_instructions_length_long(self, bot):
        """Test parsing edit instructions for long length."""
        edit_text = "make it long and detailed"
        parsed = bot._parse_edit_instructions(edit_text)
        
        assert parsed['length_change'] == 'long'
        assert parsed['action'] == 'expand'
    
    def test_parse_edit_instructions_no_length(self, bot):
        """Test parsing edit instructions without length change."""
        edit_text = "change the tone to casual"
        parsed = bot._parse_edit_instructions(edit_text)
        
        assert parsed['length_change'] is None
        assert parsed['tone_change'] == 'casual'
    
    def test_get_length_preference_from_edit(self, bot):
        """Test extracting length preference from edit instructions."""
        # Test short length
        edit_text = "make it short"
        length = bot._get_length_preference_from_edit(edit_text)
        assert length == 'short'
        
        # Test long length
        edit_text = "make it long"
        length = bot._get_length_preference_from_edit(edit_text)
        assert length == 'long'
        
        # Test no length preference
        edit_text = "change the tone"
        length = bot._get_length_preference_from_edit(edit_text)
        assert length is None
    
    def test_build_full_prompt_with_length_short(self, ai_generator):
        """Test building prompt with short length preference."""
        markdown_content = "# Test Content\n\nThis is test content."
        prompt = ai_generator._build_full_prompt(
            markdown_content, 
            user_tone_preference="Behind-the-Build",
            length_preference="short"
        )
        
        assert "SHORT-FORM post (2-3 paragraphs maximum" in prompt
        assert "concise and to the point" in prompt
    
    def test_build_full_prompt_with_length_long(self, ai_generator):
        """Test building prompt with long length preference."""
        markdown_content = "# Test Content\n\nThis is test content."
        prompt = ai_generator._build_full_prompt(
            markdown_content, 
            user_tone_preference="Behind-the-Build",
            length_preference="long"
        )
        
        assert "LONG-FORM post (4-6 paragraphs" in prompt
        assert "detailed and comprehensive" in prompt
    
    def test_build_full_prompt_without_length(self, ai_generator):
        """Test building prompt without length preference."""
        markdown_content = "# Test Content\n\nThis is test content."
        prompt = ai_generator._build_full_prompt(
            markdown_content, 
            user_tone_preference="Behind-the-Build"
        )
        
        assert "SHORT-FORM post" not in prompt
        assert "LONG-FORM post" not in prompt
    
    def test_build_context_aware_prompt_with_length(self, ai_generator):
        """Test building context-aware prompt with length preference."""
        markdown_content = "# Test Content\n\nThis is test content."
        prompt = ai_generator._build_context_aware_prompt(
            markdown_content,
            user_tone_preference="Behind-the-Build",
            session_context="Test context",
            previous_posts=[],
            relationship_type="continuation",
            parent_post_id="123",
            length_preference="short"
        )
        
        assert "LENGTH PREFERENCE: Create a SHORT-FORM post" in prompt
    
    def test_generate_facebook_post_with_length_parameter(self, ai_generator):
        """Test that generate_facebook_post accepts length_preference parameter."""
        markdown_content = "# Test Content\n\nThis is test content."
        
        # Mock the _generate_content method
        with patch.object(ai_generator, '_generate_content', return_value="Test post content"):
            with patch.object(ai_generator, '_parse_ai_response', return_value={
                'post': 'Test post content',
                'tone': 'Behind-the-Build',
                'reason': 'Test reason'
            }):
                result = ai_generator.generate_facebook_post(
                    markdown_content,
                    user_tone_preference="Behind-the-Build",
                    length_preference="short"
                )
                
                assert result['post_content'] == 'Test post content'
                assert result['tone_used'] == 'Behind-the-Build'
    
    def test_regenerate_post_with_length_parameter(self, ai_generator):
        """Test that regenerate_post accepts length_preference parameter."""
        markdown_content = "# Test Content\n\nThis is test content."
        feedback = "make it shorter"
        
        # Mock the _generate_content method
        with patch.object(ai_generator, '_generate_content', return_value="Test regenerated content"):
            with patch.object(ai_generator, '_parse_ai_response', return_value={
                'post': 'Test regenerated content',
                'tone': 'Behind-the-Build',
                'reason': 'Test reason'
            }):
                result = ai_generator.regenerate_post(
                    markdown_content,
                    feedback=feedback,
                    length_preference="short"
                )
                
                assert result['post_content'] == 'Test regenerated content'
                assert result['is_regeneration'] is True

if __name__ == "__main__":
    pytest.main([__file__]) 