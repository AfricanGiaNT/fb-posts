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
        
        # Claude Configuration (NEW)
        self.claude_api_key = os.getenv('CLAUDE_API_KEY')
        self.claude_model = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
        
        # Content Generation Configuration (NEW)
        self.content_generation_provider = os.getenv('CONTENT_GENERATION_PROVIDER', 'claude')  # 'openai' or 'claude'
        
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
        
        # Validate content generation provider
        if self.content_generation_provider not in ['openai', 'claude']:
            missing_vars.append('CONTENT_GENERATION_PROVIDER (must be "openai" or "claude")')
        
        # Validate based on selected provider
        if self.content_generation_provider == 'openai':
            if not self.openai_api_key:
                missing_vars.append('OPENAI_API_KEY (required for OpenAI provider)')
        elif self.content_generation_provider == 'claude':
            if not self.claude_api_key:
                missing_vars.append('CLAUDE_API_KEY (required for Claude provider)')
        
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

**CRITICAL UNDERSTANDING:**
- You are processing developer journal entries from `content/dev_journal/`
- Files follow the format: `milestone-name-001.md` (sequential numbering, no dates)
- Content describes development work but contains NO TIME REFERENCES
- Focus on the Problem → Solution → Result narrative, not duration
- Content represents completed work, not ongoing projects

**CRITICAL VOICE ENFORCEMENT:**
You are writing as a solo developer sharing personal projects. Use ONLY first-person language:
✅ ALWAYS use "I" language:
- "I built this system..."
- "I discovered that..."
- "I learned..."
- "I struggled with..."
- "I found a solution..."

❌ NEVER use "WE" language:
- Never: "We built", "Our system", "Our solution"
- Never: "We discovered", "We learned", "We found"
- Never: "Our integrated", "Our smart", "Our advanced"

❌ NEVER add time references:
- Never: "took 3 days", "spent hours", "after a week"
- Never: "recently", "yesterday", "last month"
- Never: "over the weekend", "in the evening"

This is YOUR personal project that YOU built. Share it authentically in first person without time frames.

---

Your task is to:
1. Analyze the Markdown content I provide from the developer journal.
2. Choose one of the 5 brand tones below to structure the post.
3. Rewrite the content as a story-driven, engaging Facebook post with proper grammar and formatting.
4. Include emojis, short paragraphs, and strong line breaks for readability.
5. Always maintain a personal, relatable voice (as if I'm building in public).
6. End with an optional insight, CTA, or reflection.
7. Target 400-600 words for optimal engagement.
8. **Extract the key narrative** - identify the most compelling story or insight from the content.
9. **Choose the tone that best fits** - let the content guide your tone selection, not a predetermined structure.
10. **Never mention time frames or duration** - present work as completed achievements.

Keep tone casual, reflective, builder-focused. Do not oversell or sound corporate. Show the human side of the work.

**Content Processing Instructions:**
- The markdown content represents a completed development milestone
- Extract the core problem, solution, and result
- Ignore any file naming patterns or dates
- Focus on the technical achievement and its impact
- Present the work as a finished accomplishment

Please format your response as:
TONE: [chosen tone]
POST: [Facebook post content - aim for 400-600 words, no time references]
REASON: [brief explanation of tone choice]""" 

    def get_active_model_info(self):
        """Get information about the active model configuration."""
        if self.content_generation_provider == 'openai':
            return {
                'provider': 'OpenAI',
                'model': self.openai_model,
                'api_key_configured': bool(self.openai_api_key)
            }
        elif self.content_generation_provider == 'claude':
            return {
                'provider': 'Claude',
                'model': self.claude_model,
                'api_key_configured': bool(self.claude_api_key)
            }
        else:
            return {
                'provider': 'Unknown',
                'model': 'Unknown',
                'api_key_configured': False
            } 