"""
Configuration manager for AI Facebook Content Generator
"""

import os
from dotenv import load_dotenv
from pathlib import Path

class ConfigManager:
    """Manages environment variables and system configuration."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Telegram Configuration
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # OpenAI Configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        # Airtable Configuration
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        self.airtable_table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Content Tracker')
        
        # System Configuration
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
        self.processing_timeout = int(os.getenv('PROCESSING_TIMEOUT_SECONDS', '60'))
        
        # Project paths
        self.project_root = Path(__file__).parent.parent
        self.rules_dir = self.project_root / 'rules'
        self.content_dir = self.project_root / 'content'
        
        # Ensure directories exist
        self.content_dir.mkdir(exist_ok=True)
        (self.content_dir / 'markdown_logs').mkdir(exist_ok=True)
        (self.content_dir / 'generated_drafts').mkdir(exist_ok=True)
        (self.content_dir / 'reviewed_drafts').mkdir(exist_ok=True)
    
    def validate_config(self):
        """Validate that all required configuration is present."""
        missing_vars = []
        
        if not self.telegram_bot_token:
            missing_vars.append('TELEGRAM_BOT_TOKEN')
        
        if not self.openai_api_key:
            missing_vars.append('OPENAI_API_KEY')
        
        if not self.airtable_api_key:
            missing_vars.append('AIRTABLE_API_KEY')
        
        if not self.airtable_base_id:
            missing_vars.append('AIRTABLE_BASE_ID')
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_prompt_template(self):
        """Load the AI prompt template from rules directory."""
        try:
            prompt_file = self.rules_dir / 'ai_prompt_structure.mdc'
            if prompt_file.exists():
                return prompt_file.read_text(encoding='utf-8')
            else:
                # Fallback to embedded template
                return self._get_default_prompt_template()
        except Exception as e:
            print(f"Error loading prompt template: {e}")
            return self._get_default_prompt_template()
    
    def _get_default_prompt_template(self):
        """Default prompt template as fallback."""
        return """You are a copywriting assistant helping me turn Markdown documents about my AI/automation builds into engaging Facebook posts.

Your task is to:
1. Analyze the Markdown content I provide.
2. Choose one of the 5 brand tones below to structure the post.
3. Rewrite the content as a story-driven, engaging Facebook post with proper grammar and formatting.
4. Include emojis, short paragraphs, and strong line breaks for readability.
5. Always maintain a personal, relatable voice (as if I'm building in public).
6. End with an optional insight, CTA, or reflection.

Keep tone casual, reflective, builder-focused. Do not oversell or sound corporate. Show the human side of the work.

Please format your response as:
TONE: [chosen tone]
POST: [Facebook post content]
REASON: [brief explanation of tone choice]""" 