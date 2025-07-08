#!/usr/bin/env python3
"""
Setup script for AI Facebook Content Generator
"""

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required Python packages."""
    print("🔧 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    return True

def create_env_file():
    """Create environment file from template."""
    print("📝 Creating environment configuration...")
    
    env_content = """# AI Facebook Content Generator - Environment Configuration
# Copy this file to .env and fill in your actual values

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI API Configuration  
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Airtable Configuration
AIRTABLE_API_KEY=your_airtable_api_key_here
AIRTABLE_BASE_ID=your_airtable_base_id_here
AIRTABLE_TABLE_NAME=Content Tracker

# System Configuration
DEBUG=False
MAX_FILE_SIZE_MB=10
PROCESSING_TIMEOUT_SECONDS=60
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping creation.")
    else:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file - please fill in your API keys!")
    
    return True

def create_directories():
    """Create required directories."""
    print("📁 Creating directory structure...")
    
    directories = [
        "content",
        "content/markdown_logs",
        "content/generated_drafts", 
        "content/reviewed_drafts",
        "scripts",
        "rules",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directory structure created!")
    return True

def show_setup_instructions():
    """Show post-setup instructions."""
    print("\n" + "="*50)
    print("🚀 Setup Complete!")
    print("="*50)
    print()
    print("📋 Next Steps:")
    print("1. Edit the .env file with your API keys:")
    print("   - Get Telegram Bot Token: @BotFather on Telegram")
    print("   - Get OpenAI API Key: https://platform.openai.com/")
    print("   - Get Airtable API Key: https://airtable.com/developers/")
    print()
    print("2. Set up your Airtable base with these fields:")
    print("   - Post Title (Single line text)")
    print("   - Generated Draft (Long text)")
    print("   - Tone Used (Single select)")
    print("   - Review Status (Single select)")
    print("   - And other fields as specified in the docs")
    print()
    print("3. Run the bot:")
    print("   python scripts/telegram_bot.py")
    print()
    print("4. Send /start to your bot on Telegram to begin!")
    print()
    print("📚 For detailed setup instructions, see instructions.md")
    print("="*50)

def main():
    """Main setup function."""
    print("🤖 AI Facebook Content Generator Setup")
    print("="*40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create environment file
    if not create_env_file():
        return False
    
    # Show instructions
    show_setup_instructions()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 