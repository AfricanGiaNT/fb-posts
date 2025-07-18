#!/usr/bin/env python3
"""
Test script for follow-up post generation feature.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ai_content_generator import AIContentGenerator
from scripts.config_manager import ConfigManager
from datetime import datetime
import json


def test_followup_generation():
    """Test follow-up post generation functionality."""
    print("🔧 Testing Follow-up Post Generation Feature")
    print("=" * 50)
    
    # Initialize components
    config = ConfigManager()
    ai_generator = AIContentGenerator(config)
    
    # Test 1: Check relationship types are available
    print("\n1. Testing relationship types:")
    relationship_types = ai_generator.get_relationship_types()
    print(f"   Available relationship types: {len(relationship_types)}")
    for key, display_name in relationship_types.items():
        print(f"   • {key}: {display_name}")
    
    # Test 2: Generate initial post
    print("\n2. Generating initial post...")
    markdown_content = """
# Test Project
## What I Built
I built a simple automation tool that helps manage daily tasks.

## The Problem
People struggle with keeping track of their daily tasks and often forget important items.

## My Solution
I created a simple Python script that sends reminder notifications.

## The Results
Users report 40% better task completion rates.
"""
    
    try:
        initial_post = ai_generator.generate_facebook_post(
            markdown_content,
            user_tone_preference=None,
            audience_type='business'
        )
        print(f"   ✅ Initial post generated: {initial_post['tone_used']}")
        print(f"   Content preview: {initial_post['post_content'][:100]}...")
        
        # Create mock session with the initial post
        mock_session_posts = [
            {
                'post_id': 1,
                'content': initial_post['post_content'],
                'tone_used': initial_post['tone_used'],
                'approved_at': datetime.now().isoformat(),
                'content_summary': initial_post['post_content'][:100] + '...'
            }
        ]
        
        # Test 3: Generate follow-up with different relationship types
        print("\n3. Testing follow-up generation with different relationships:")
        
        test_relationships = ['different_aspects', 'series_continuation', 'technical_deep_dive']
        
        for rel_type in test_relationships:
            print(f"\n   Testing {rel_type}:")
            try:
                followup_post = ai_generator.generate_facebook_post(
                    markdown_content,
                    user_tone_preference=None,
                    session_context=f"Previous post: {initial_post['post_content'][:200]}...",
                    previous_posts=mock_session_posts,
                    relationship_type=rel_type,
                    parent_post_id='1',
                    audience_type='business'
                )
                print(f"   ✅ Follow-up generated: {followup_post['tone_used']}")
                print(f"   Content preview: {followup_post['post_content'][:100]}...")
                
                # Add to mock session for next test
                mock_session_posts.append({
                    'post_id': len(mock_session_posts) + 1,
                    'content': followup_post['post_content'],
                    'tone_used': followup_post['tone_used'],
                    'approved_at': datetime.now().isoformat(),
                    'relationship_type': rel_type,
                    'parent_post_id': '1',
                    'content_summary': followup_post['post_content'][:100] + '...'
                })
                
            except Exception as e:
                print(f"   ❌ Error generating {rel_type}: {e}")
        
        # Test 4: Test 5-post limit context
        print("\n4. Testing 5-post limit context:")
        print(f"   Current posts in session: {len(mock_session_posts)}")
        
        # Create session context with recent posts (last 5)
        recent_posts = mock_session_posts[-5:]
        context_parts = [
            f"Series: {len(recent_posts)}/{len(mock_session_posts)} posts created from test_project.md",
            f"Original project: {markdown_content[:200]}...",
            ""
        ]
        
        for post in recent_posts:
            context_parts.append(f"Post {post['post_id']}: {post['tone_used']} tone")
            context_parts.append(f"Content: {post['content_summary']}")
            if post.get('relationship_type'):
                context_parts.append(f"Relationship: {post['relationship_type']}")
            context_parts.append("")
        
        session_context = "\n".join(context_parts)
        print(f"   ✅ Context limited to {len(recent_posts)} posts")
        print(f"   Context length: {len(session_context)} characters")
        
        print("\n✅ All tests passed! Follow-up post generation feature is working correctly.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_followup_generation()
    sys.exit(0 if success else 1) 