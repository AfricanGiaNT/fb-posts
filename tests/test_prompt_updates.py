#!/usr/bin/env python3
"""
Test script to verify the updated system and user prompts are working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ai_content_generator import AIContentGenerator
from scripts.config_manager import ConfigManager

def test_prompt_structure():
    """Test that the system and user prompts have the correct structure."""
    
    # Initialize the AI content generator
    config_manager = ConfigManager()
    ai_generator = AIContentGenerator(config_manager)
    
    print("=== Testing System Prompt Structure ===")
    
    # Test the business system prompt
    system_prompt = ai_generator._get_system_prompt('business')
    
    # Check for key sections
    required_sections = [
        "CRITICAL PERSONAL PROJECT PERSPECTIVE",
        "CRITICAL VOICE ENFORCEMENT", 
        "**FEATURE-FIRST STORYTELLING:**",
        "**FORMATTING GUIDELINES:**",
        "**TECHNICAL LANGUAGE BALANCE:**",
        "MANDATORY LANGUAGE SIMPLIFICATION"
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in system_prompt:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"❌ Missing sections in system prompt: {missing_sections}")
        return False
    else:
        print("✅ All required sections found in system prompt")
    
    # Check for specific guidelines
    specific_checks = [
        ("Maximum 3 technical terms per post", "Technical language limit"),
        ("2-4 per post", "Emoji guidelines"),
        ("NO fictional scenarios", "No fake stories rule"),
        ("Use ONLY first-person language", "Voice enforcement")
    ]
    
    for check_text, description in specific_checks:
        if check_text in system_prompt:
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: Missing")
            return False
    
    print("\n=== Testing User Prompt Structure ===")
    
    # Test the user prompt
    markdown_content = """
# Test Content

## What I Built
A simple test feature for demonstration.

## The Problem
Testing the prompt structure.

## My Solution
Created a test to verify everything works.
"""
    
    user_prompt = ai_generator._build_full_prompt(markdown_content)
    
    # Check that user prompt is simple and direct
    if "You are an AI assistant tasked with generating a Facebook post" in user_prompt:
        print("✅ User prompt has correct opening")
    else:
        print("❌ User prompt missing correct opening")
        return False
    
    # Check that it doesn't contain detailed instructions (those should be in system prompt)
    if "FEATURE-FIRST STORYTELLING" not in user_prompt:
        print("✅ User prompt doesn't contain detailed instructions (good)")
    else:
        print("❌ User prompt contains detailed instructions (should be in system prompt)")
        return False
    
    if "TECHNICAL LANGUAGE BALANCE" not in user_prompt:
        print("✅ User prompt doesn't contain technical guidelines (good)")
    else:
        print("❌ User prompt contains technical guidelines (should be in system prompt)")
        return False
    
    print("\n=== Testing Context-Aware Prompt ===")
    
    # Test context-aware prompt
    context_prompt = ai_generator._build_context_aware_prompt(
        markdown_content=markdown_content,
        user_tone_preference="Behind-the-Build",
        session_context="Previous session context",
        previous_posts=[{"tone_used": "Finished & Proud", "content": "Previous post content"}],
        relationship_type="Implementation Evolution",
        parent_post_id="test_parent_id"
    )
    
    if "You are an AI assistant tasked with generating a Facebook post" in context_prompt:
        print("✅ Context-aware prompt has correct opening")
    else:
        print("❌ Context-aware prompt missing correct opening")
        return False
    
    if "Previous session context" in context_prompt:
        print("✅ Context-aware prompt includes session context")
    else:
        print("❌ Context-aware prompt missing session context")
        return False
    
    print("\n=== All Tests Passed! ===")
    return True

def test_prompt_length():
    """Test that prompts are reasonable length."""
    
    config_manager = ConfigManager()
    ai_generator = AIContentGenerator(config_manager)
    
    system_prompt = ai_generator._get_system_prompt('business')
    
    # System prompt should be substantial but not excessive
    if 2000 < len(system_prompt) < 10000:
        print(f"✅ System prompt length is reasonable: {len(system_prompt)} characters")
    else:
        print(f"❌ System prompt length may be problematic: {len(system_prompt)} characters")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing Updated Prompt Structure...\n")
    
    success = True
    success &= test_prompt_structure()
    success &= test_prompt_length()
    
    if success:
        print("\n🎉 All tests passed! The prompt updates are working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the prompt updates.")
        sys.exit(1) 