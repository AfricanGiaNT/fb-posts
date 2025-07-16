"""
Test for backslash accumulation issue in markdown escaping.

This test reproduces the bug where calling _escape_markdown multiple times
on the same content causes exponential backslash accumulation.
"""

import sys
import os
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from telegram_bot import FacebookContentBot
import pytest


class TestBackslashAccumulation:
    """Test suite for backslash accumulation bug."""

    def setup_method(self):
        """Set up test environment."""
        self.bot = FacebookContentBot()

    def test_escape_markdown_idempotent(self):
        """Test that _escape_markdown is idempotent (safe to call multiple times)."""
        # Test content with markdown characters
        original_content = "This is a *bold* text with [link](url) and `code`"
        
        # First escape
        escaped_once = self.bot._escape_markdown(original_content)
        
        # Second escape (should be idempotent)
        escaped_twice = self.bot._escape_markdown(escaped_once)
        
        # Third escape (should still be idempotent)
        escaped_thrice = self.bot._escape_markdown(escaped_twice)
        
        # All subsequent escapes should be identical
        assert escaped_once == escaped_twice == escaped_thrice, \
            f"Escaping not idempotent:\n" \
            f"First:  {escaped_once}\n" \
            f"Second: {escaped_twice}\n" \
            f"Third:  {escaped_thrice}"

    def test_backslash_accumulation_bug_reproduction(self):
        """Reproduce the backslash accumulation bug."""
        # Content that would be typical in a Facebook post
        content = "Here's my project: https://github.com/user/repo (check it out!)"
        
        # Simulate multiple regenerations (each calls _escape_markdown)
        escaped_content = content
        for i in range(5):  # Simulate 5 regenerations
            escaped_content = self.bot._escape_markdown(escaped_content)
        
        # Count backslashes - should not accumulate
        backslash_count = escaped_content.count('\\')
        expected_backslash_count = self.bot._escape_markdown(content).count('\\')
        
        assert backslash_count == expected_backslash_count, \
            f"Backslash accumulation detected:\n" \
            f"Expected {expected_backslash_count} backslashes, got {backslash_count}\n" \
            f"Final content: {escaped_content}"

    def test_complex_markdown_characters(self):
        """Test with complex markdown characters that commonly appear in posts."""
        test_cases = [
            "Check out my *amazing* project!",
            "Here's a [link](https://example.com) to my work",
            "Some `code` and **bold** text",
            "Bullet points:\n- Item 1\n- Item 2",
            "Math: 2 + 2 = 4",
            "Special chars: !@#$%^&*()",
            "Combined: *bold* `code` [link](url) - list item!"
        ]
        
        for original in test_cases:
            # Escape multiple times
            escaped = original
            for _ in range(3):
                escaped = self.bot._escape_markdown(escaped)
            
            # Should be same as single escape
            single_escaped = self.bot._escape_markdown(original)
            
            assert escaped == single_escaped, \
                f"Accumulation in: {original}\n" \
                f"Single escape: {single_escaped}\n" \
                f"Triple escape: {escaped}"

    def test_already_escaped_content(self):
        """Test with content that's already properly escaped."""
        # Content that looks like it's already escaped
        already_escaped = "This is \\*escaped\\* text with \\[brackets\\]"
        
        # Should not double-escape
        result = self.bot._escape_markdown(already_escaped)
        
        # Should be idempotent
        result_twice = self.bot._escape_markdown(result)
        
        assert result == result_twice, \
            f"Double-escaping detected:\n" \
            f"Original: {already_escaped}\n" \
            f"Once: {result}\n" \
            f"Twice: {result_twice}"

    def test_empty_and_none_input(self):
        """Test edge cases with empty or None input."""
        # Empty string
        assert self.bot._escape_markdown("") == ""
        
        # None input
        assert self.bot._escape_markdown(None) is None
        
        # Whitespace only
        assert self.bot._escape_markdown("   ") == "   "

    def test_real_world_post_content(self):
        """Test with realistic Facebook post content."""
        real_post = """
🚀 Exciting Update: Just launched my new project!

Check it out: https://github.com/user/awesome-project

Key features:
- Fast performance (50% faster!)
- Easy to use API
- Great documentation

Built with Python, using OpenAI's GPT-4 for *intelligent* processing.

#coding #python #ai #openai
        """
        
        # Simulate multiple regenerations
        escaped = real_post
        for _ in range(4):
            escaped = self.bot._escape_markdown(escaped)
        
        # Should be same as single escape
        single_escaped = self.bot._escape_markdown(real_post)
        
        assert escaped == single_escaped, \
            f"Real-world content accumulation:\n" \
            f"Single: {single_escaped}\n" \
            f"Multiple: {escaped}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 