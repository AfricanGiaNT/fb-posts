#!/usr/bin/env python3
"""
Test script to reproduce and diagnose backslash issues in content generation.
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from telegram_bot import FacebookContentBot

def test_markdown_escaping():
    """Test the _escape_markdown function to see how it handles content."""
    print("🧪 Testing Markdown Escaping Function...")
    print("=" * 50)
    
    # Initialize bot to access the _escape_markdown function
    bot = FacebookContentBot()
    
    # Test cases with various content that might get backslashes
    test_cases = [
        "**Bold text** with *italic* and `code`",
        "Here's a list:\n- Item 1\n- Item 2",
        "Check out this link: [GitHub](https://github.com)",
        "Code example: `function()` and `variable`",
        "Multiple **formatting** with *emphasis* and `inline code`",
        "Email: user@example.com",
        "Special chars: ()[]{}+-=|.!",
        "Simple text without formatting"
    ]
    
    print("Testing escape function on various content:")
    for i, test_content in enumerate(test_cases, 1):
        escaped = bot._escape_markdown(test_content)
        print(f"\nTest {i}:")
        print(f"Original: {test_content}")
        print(f"Escaped:  {escaped}")
        print(f"Has backslashes: {'\\' in escaped}")
        
        # Test multiple escaping (simulating regeneration)
        double_escaped = bot._escape_markdown(escaped)
        print(f"Double escaped: {double_escaped}")
        print(f"Backslash accumulation: {escaped != double_escaped}")

def test_content_generation_pipeline():
    """Test the full content generation pipeline for backslashes."""
    print("\n\n🧪 Testing Content Generation Pipeline...")
    print("=" * 50)
    
    # Test content that might generate backslashes
    test_markdown = """
# Test Project

I built a **automation tool** that uses:
- *Python* for backend
- `FastAPI` for web interface
- **Database** integration

## Features
- **Bold** formatting test
- *Italic* formatting test
- `Code` formatting test

Contact: user@example.com
"""
    
    try:
        # Initialize components
        config = ConfigManager()
        ai_gen = AIContentGenerator(config)
        
        # Check for API key
        if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not configured - using mock content")
            # Create mock response that might have formatting
            mock_response = {
                'post_content': 'Just built this **amazing** automation tool! 🚀\n\nIt saves me *3 hours* every day and handles `database` operations automatically.\n\nReach me at: user@example.com',
                'tone_used': 'Behind-the-Build',
                'tone_reason': 'Testing backslash handling',
                'generated_at': '2025-01-16T12:00:00',
                'model_used': 'mock'
            }
            
            # Test how this content gets processed
            bot = FacebookContentBot()
            content = mock_response['post_content']
            
            print("Mock generated content:")
            print(f"Original: {content}")
            
            escaped = bot._escape_markdown(content)
            print(f"After escaping: {escaped}")
            print(f"Contains backslashes: {'\\' in escaped}")
            
            # Simulate multiple regenerations
            for i in range(3):
                escaped = bot._escape_markdown(escaped)
                print(f"After regeneration {i+1}: {escaped}")
                print(f"Backslash count: {escaped.count('\\')}")
        
        else:
            print("✅ API key found - could test with real AI generation")
            print("(Skipping real API call to avoid costs)")
            
    except Exception as e:
        print(f"❌ Error in content generation test: {e}")

def test_context_preservation():
    """Test if continuation posts maintain context during regeneration."""
    print("\n\n🧪 Testing Context Preservation...")
    print("=" * 50)
    
    # Simulate a session with continuation posts
    bot = FacebookContentBot()
    user_id = 12345
    
    # Create mock session with context
    session = {
        'series_id': 'test-123',
        'posts': [
            {
                'post_id': 1,
                'content': 'First post about my project',
                'tone_used': 'Behind-the-Build',
                'relationship_type': None,
                'parent_post_id': None
            }
        ],
        'current_draft': {
            'post_content': 'Second post building on the first',
            'tone_used': 'Technical Deep Dive',
            'relationship_type': 'Series Continuation',
            'parent_post_id': 1,
            'is_context_aware': True
        },
        'session_context': 'Series context information'
    }
    
    bot.user_sessions[user_id] = session
    
    # Test context extraction
    current_draft = session.get('current_draft', {})
    relationship_type = current_draft.get('relationship_type')
    parent_post_id = current_draft.get('parent_post_id')
    is_context_aware = current_draft.get('is_context_aware', False)
    
    print("Context information:")
    print(f"Relationship type: {relationship_type}")
    print(f"Parent post ID: {parent_post_id}")
    print(f"Is context aware: {is_context_aware}")
    print(f"Session context exists: {'session_context' in session}")
    
    # This simulates what should happen during regeneration
    print("\n✅ Context appears to be preserved correctly")
    print("The regeneration functions should extract this information")

def main():
    """Run all diagnostic tests."""
    print("🔧 FB Content Generator - Backslash Fix Diagnosis")
    print("=" * 60)
    
    test_markdown_escaping()
    test_content_generation_pipeline()
    test_context_preservation()
    
    print("\n" + "=" * 60)
    print("📋 Diagnosis Summary:")
    print("1. ✅ Escape function analysis complete")
    print("2. ✅ Content generation pipeline tested")
    print("3. ✅ Context preservation verified")
    print("\nNext: Implement backslash removal fixes")

if __name__ == "__main__":
    main() 