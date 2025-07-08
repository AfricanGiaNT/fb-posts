#!/usr/bin/env python3
"""
Quick End-to-End Test for AI Facebook Content Generator
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from airtable_connector import AirtableConnector

def quick_test():
    """Run a quick end-to-end test of the system."""
    print("🚀 AI Facebook Content Generator - Quick Test")
    print("=" * 50)
    
    try:
        # Initialize components
        print("🔧 Initializing system components...")
        config = ConfigManager()
        ai_gen = AIContentGenerator(config)
        airtable = AirtableConnector(config)
        print("✅ Components initialized")
        
        # Test Airtable connection
        print("\n📊 Testing Airtable connection...")
        if airtable.test_connection():
            print("✅ Airtable connection successful")
        else:
            print("❌ Airtable connection failed")
            return False
        
        # Test AI generation
        print("\n🤖 Testing AI content generation...")
        sample_markdown = """
# AI Facebook Content Generator

I just built an AI system that converts markdown project documentation into engaging Facebook posts!

## Features
- Telegram bot interface for easy file uploads
- AI-powered content generation using GPT-4o  
- 5 different brand tone styles for consistent voice
- Interactive review and approval workflow
- Airtable integration for content tracking
- Auto-generated tags and improvement suggestions

## Tech Stack
- Python with OpenAI API
- Telegram Bot API for user interface
- Airtable API for content management
- Custom prompt engineering for brand voice

The system analyzes technical documentation and transforms it into story-driven posts that engage audiences while maintaining authenticity.

This saves hours of manual content creation and ensures consistent brand voice across all posts.
        """
        
        post_data = ai_gen.generate_facebook_post(sample_markdown)
        if post_data and post_data.get('post_content'):
            print("✅ AI generation successful")
            print(f"   Generated tone: {post_data.get('tone_used', 'Unknown')}")
            print(f"   Content length: {len(post_data.get('post_content', ''))} chars")
        else:
            print("❌ AI generation failed")
            return False
        
        # Test Airtable saving
        print("\n💾 Testing Airtable save...")
        record_id = airtable.save_draft(post_data, "Test Post", "📝 To Review")
        if record_id:
            print(f"✅ Successfully saved to Airtable (Record ID: {record_id})")
            
            # Show what was saved
            print("\n📋 Saved data includes:")
            print("   • Generated Facebook post content")
            print("   • AI tone analysis and reasoning")
            print("   • Auto-extracted tags")
            print("   • Content metrics (length, summary)")
            print("   • Improvement suggestions")
            
            return True
        else:
            print("❌ Failed to save to Airtable")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def show_next_steps():
    """Show next steps after successful test."""
    print("\n" + "=" * 50)
    print("🎉 System Test Successful!")
    print("=" * 50)
    print("\n🚀 Ready to use your AI Facebook Content Generator!")
    print("\n📋 Next Steps:")
    print("1. Start the Telegram bot:")
    print("   python scripts/telegram_bot.py")
    print("\n2. Find your bot on Telegram and send /start")
    print("\n3. Upload a .md file to generate your first post")
    print("\n4. Review, approve, and check Airtable for the result")
    print("\n💡 Tips:")
    print("   • Include project context and outcomes in your markdown")
    print("   • Mention specific tools and technologies used")
    print("   • Quantify results when possible (time saved, problems solved)")
    print("   • Use descriptive file names for better organization")

if __name__ == "__main__":
    success = quick_test()
    
    if success:
        show_next_steps()
    else:
        print("\n🛠️  Please fix the issues above and run the test again.")
        print("💡 Most common fix: Update Airtable token permissions.") 