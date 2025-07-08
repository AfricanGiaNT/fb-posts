#!/usr/bin/env python3
"""
Test script for AI Facebook Content Generator system
"""

import sys
import os
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator
from airtable_connector import AirtableConnector

def test_config_manager():
    """Test configuration manager."""
    print("🔧 Testing Configuration Manager...")
    
    try:
        config = ConfigManager()
        print("✅ ConfigManager initialized successfully")
        
        # Test prompt template loading
        prompt = config.get_prompt_template()
        if prompt and len(prompt) > 100:
            print("✅ Prompt template loaded successfully")
        else:
            print("⚠️  Prompt template seems short or missing")
        
        return config
        
    except Exception as e:
        print(f"❌ ConfigManager error: {e}")
        return None

def test_ai_generator(config):
    """Test AI content generator."""
    print("\n🤖 Testing AI Content Generator...")
    
    try:
        if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
            print("⚠️  OpenAI API key not configured - skipping AI tests")
            return None
        
        ai_gen = AIContentGenerator(config)
        print("✅ AI Content Generator initialized successfully")
        
        # Test with sample markdown
        sample_md = """
# Telegram Bot for Content Generation

I built a Telegram bot that converts markdown files into Facebook posts using AI.

## Features
- File upload handling
- AI-powered content generation
- Interactive review system
- Airtable integration

## Tech Stack
- Python
- OpenAI GPT-4o
- Telegram Bot API
- Airtable API

The bot processes markdown files and generates engaging Facebook posts using different tone styles.
        """
        
        print("🔄 Testing AI generation with sample content...")
        result = ai_gen.generate_facebook_post(sample_md)
        
        if result and result.get('post_content'):
            print("✅ AI generation successful")
            print(f"Generated tone: {result.get('tone_used', 'Unknown')}")
            print(f"Content length: {len(result.get('post_content', ''))}")
        else:
            print("❌ AI generation failed")
            
        return ai_gen
        
    except Exception as e:
        print(f"❌ AI Generator error: {e}")
        return None

def test_airtable_connector(config):
    """Test Airtable connector."""
    print("\n📊 Testing Airtable Connector...")
    
    try:
        if not config.airtable_api_key or config.airtable_api_key == "your_airtable_api_key_here":
            print("⚠️  Airtable API key not configured - skipping Airtable tests")
            return None
        
        airtable = AirtableConnector(config)
        print("✅ Airtable Connector initialized successfully")
        
        # Test connection
        if airtable.test_connection():
            print("✅ Airtable connection successful")
        else:
            print("❌ Airtable connection failed")
            
        return airtable
        
    except Exception as e:
        print(f"❌ Airtable Connector error: {e}")
        return None

def test_file_structure():
    """Test file structure."""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        "requirements.txt",
        "instructions.md",
        "README.md",
        "setup.py",
        "scripts/config_manager.py",
        "scripts/ai_content_generator.py",
        "scripts/airtable_connector.py",
        "scripts/telegram_bot.py",
        "rules/tone_guidelines.mdc",
        "rules/ai_prompt_structure.mdc"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_environment_variables():
    """Test environment variables setup."""
    print("\n🔑 Testing Environment Variables...")
    
    required_env_vars = [
        "TELEGRAM_BOT_TOKEN",
        "OPENAI_API_KEY", 
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID"
    ]
    
    missing_vars = []
    placeholder_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        elif value.startswith("your_") or value == "":
            placeholder_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
    
    if placeholder_vars:
        print(f"⚠️  Placeholder values found: {placeholder_vars}")
        print("   Please update these in your .env file")
    
    if not missing_vars and not placeholder_vars:
        print("✅ All environment variables configured")
        return True
    
    return False

def main():
    """Run all tests."""
    print("🧪 AI Facebook Content Generator - System Test")
    print("=" * 50)
    
    # Test file structure
    if not test_file_structure():
        print("\n❌ File structure test failed")
        return False
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test configuration manager
    config = test_config_manager()
    if not config:
        print("\n❌ Configuration test failed")
        return False
    
    # Test AI generator (if configured)
    ai_gen = test_ai_generator(config)
    
    # Test Airtable connector (if configured)
    airtable = test_airtable_connector(config)
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary")
    print("=" * 50)
    print("✅ File structure: OK")
    print("✅ Configuration: OK")
    print(f"{'✅' if env_ok else '⚠️ '} Environment: {'OK' if env_ok else 'Needs setup'}")
    print(f"{'✅' if ai_gen else '⚠️ '} AI Generator: {'OK' if ai_gen else 'Needs API key'}")
    print(f"{'✅' if airtable else '⚠️ '} Airtable: {'OK' if airtable else 'Needs API key'}")
    
    if env_ok and ai_gen and airtable:
        print("\n🚀 System ready for deployment!")
        print("Run: python scripts/telegram_bot.py")
    else:
        print("\n⚠️  System needs configuration:")
        print("1. Set up your .env file with API keys")
        print("2. Configure your Airtable base")
        print("3. Re-run this test")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 