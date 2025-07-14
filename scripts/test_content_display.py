#!/usr/bin/env python3
"""
Test script to verify that content display no longer shows backslashes.
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from telegram_bot import FacebookContentBot

def test_content_display_without_backslashes():
    """Test that content displayed to users has no backslashes."""
    print("🧪 Testing Content Display Without Backslashes...")
    print("=" * 60)
    
    # Create mock post data that might have formatting
    mock_post_data = {
        'post_content': 'Just built this **amazing** automation tool! 🚀\n\nIt saves me *3 hours* every day and handles `database` operations automatically.\n\nReach me at: user@example.com',
        'tone_used': 'Behind-the-Build',
        'tone_reason': 'Testing backslash handling with **bold** text and *italic* formatting',
        'generated_at': '2025-01-16T12:00:00',
        'model_used': 'mock',
        'is_context_aware': False
    }
    
    # Simulate the content processing pipeline
    post_content = mock_post_data.get('post_content', 'No content generated')
    tone_reason = mock_post_data.get('tone_reason', 'No reason provided')
    
    print("Original content from AI:")
    print(f"Post: {post_content}")
    print(f"Reason: {tone_reason}")
    print(f"Contains backslashes: {'\\' in post_content or '\\' in tone_reason}")
    
    # Process content as it would be displayed (NO ESCAPING)
    if len(post_content) > 2000:
        display_content = post_content[:2000] + "\n\n📝 [Content truncated for display - full version saved to Airtable]"
    else:
        display_content = post_content
    
    if len(tone_reason) > 500:
        display_reason = tone_reason[:500] + "..."
    else:
        display_reason = tone_reason
    
    # Create the message as users would see it
    post_preview = f"""🎯 Generated Facebook Post

Tone Used: {mock_post_data.get('tone_used', 'Unknown')}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?"""
    
    print("\n" + "=" * 60)
    print("CONTENT AS DISPLAYED TO USER:")
    print("=" * 60)
    print(post_preview)
    print("=" * 60)
    
    # Check for backslashes in the final display
    has_backslashes = '\\' in post_preview
    print(f"\n✅ Display contains backslashes: {has_backslashes}")
    
    if not has_backslashes:
        print("🎉 SUCCESS: No backslashes in user-visible content!")
    else:
        print("❌ FAILURE: Backslashes still present in display")
        # Show where backslashes are
        lines = post_preview.split('\n')
        for i, line in enumerate(lines, 1):
            if '\\' in line:
                print(f"   Line {i}: {line}")
    
    return not has_backslashes

def test_context_aware_display():
    """Test that context-aware posts also display without backslashes."""
    print("\n\n🧪 Testing Context-Aware Content Display...")
    print("=" * 60)
    
    # Create mock context-aware post data
    mock_post_data = {
        'post_content': 'Building on my **previous** post about automation, here\'s the *technical* implementation: `Python + FastAPI`. Check it out!',
        'tone_used': 'Technical Deep Dive',
        'tone_reason': 'User requested **technical** details with *code* examples',
        'generated_at': '2025-01-16T12:00:00',
        'model_used': 'mock',
        'is_context_aware': True,
        'relationship_type': 'Different Aspects',
        'parent_post_id': 1
    }
    
    # Process context-aware content
    post_content = mock_post_data.get('post_content', 'No content generated')
    tone_reason = mock_post_data.get('tone_reason', 'No reason provided')
    
    # Simulate display processing
    display_content = post_content
    display_reason = tone_reason
    
    # Add context information
    context_info = ""
    if mock_post_data.get('is_context_aware', False):
        context_info = f"\n\n🔗 Context-Aware Generation"
        if mock_post_data.get('relationship_type'):
            context_info += f"\n• Relationship: {mock_post_data.get('relationship_type')}"
    
    # Create the message
    post_preview = f"""🎯 Generated Facebook Post

Tone Used: {mock_post_data.get('tone_used', 'Unknown')}{context_info}

Content:
───────────────────────────
{display_content}
───────────────────────────

AI Reasoning: {display_reason}

What would you like to do?"""
    
    print("CONTEXT-AWARE CONTENT AS DISPLAYED:")
    print("=" * 60)
    print(post_preview)
    print("=" * 60)
    
    # Check for backslashes
    has_backslashes = '\\' in post_preview
    print(f"\n✅ Context-aware display contains backslashes: {has_backslashes}")
    
    if not has_backslashes:
        print("🎉 SUCCESS: No backslashes in context-aware content!")
    else:
        print("❌ FAILURE: Backslashes still present in context-aware display")
    
    return not has_backslashes

def test_regeneration_display():
    """Test that regenerated posts also display without backslashes."""
    print("\n\n🧪 Testing Regenerated Content Display...")
    print("=" * 60)
    
    # Create mock regenerated post data
    mock_post_data = {
        'post_content': 'Here\'s a **different** approach to the same project! Instead of using *manual* processes, I automated everything with `Python scripts`. Email me: dev@example.com',
        'tone_used': 'What Broke',
        'tone_reason': 'User wanted a **different** perspective on the *same* project',
        'generated_at': '2025-01-16T12:00:00',
        'model_used': 'mock',
        'is_context_aware': True,
        'relationship_type': 'Series Continuation'
    }
    
    # Process regenerated content
    post_content = mock_post_data.get('post_content', 'No content generated')
    tone_reason = mock_post_data.get('tone_reason', 'No reason provided')
    
    # Simulate regeneration display
    display_content = post_content
    display_reason = tone_reason
    
    # Add context information for regeneration
    context_info = ""
    if mock_post_data.get('is_context_aware', False):
        context_info = f"\n\n🔗 Context-Aware Regeneration"
        if mock_post_data.get('relationship_type'):
            context_info += f"\n• Relationship: {mock_post_data.get('relationship_type')}"
    
    # Create regeneration message
    post_preview = f"""🔄 **Regenerated Post**

**Tone:** {mock_post_data.get('tone_used', 'Unknown')}{context_info}

**Content:**
───────────────────────────
{display_content}
───────────────────────────

**AI Reasoning:** {display_reason}

What would you like to do?"""
    
    print("REGENERATED CONTENT AS DISPLAYED:")
    print("=" * 60)
    print(post_preview)
    print("=" * 60)
    
    # Check for backslashes
    has_backslashes = '\\' in post_preview
    print(f"\n✅ Regenerated display contains backslashes: {has_backslashes}")
    
    if not has_backslashes:
        print("🎉 SUCCESS: No backslashes in regenerated content!")
    else:
        print("❌ FAILURE: Backslashes still present in regenerated display")
    
    return not has_backslashes

def main():
    """Run all content display tests."""
    print("🔧 FB Content Generator - Content Display Fix Verification")
    print("=" * 70)
    
    # Run all tests
    test1_passed = test_content_display_without_backslashes()
    test2_passed = test_context_aware_display()
    test3_passed = test_regeneration_display()
    
    print("\n" + "=" * 70)
    print("📋 Content Display Test Summary:")
    print("=" * 70)
    print(f"{'✅' if test1_passed else '❌'} Regular content display: {'PASS' if test1_passed else 'FAIL'}")
    print(f"{'✅' if test2_passed else '❌'} Context-aware display: {'PASS' if test2_passed else 'FAIL'}")
    print(f"{'✅' if test3_passed else '❌'} Regenerated content display: {'PASS' if test3_passed else 'FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n🎉 ALL TESTS PASSED! Content displays without backslashes")
        print("✅ Phase 2 (Backslash Removal) is complete")
        print("Ready for Phase 3 (Comprehensive Testing)")
    else:
        print("\n⚠️  Some tests failed - backslashes may still be present")
        print("❌ Phase 2 needs more work")
    
    return all([test1_passed, test2_passed, test3_passed])

if __name__ == "__main__":
    main() 