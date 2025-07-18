"""
AI Service for content generation with OpenAI integration.
"""

import os
import openai
from typing import Dict, Optional, Any
import logging
from datetime import datetime

class AIContentService:
    """Service for generating content using OpenAI's GPT models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the AI Content Service.
        
        Args:
            api_key: OpenAI API key. If None, will look for OPENAI_API_KEY env var
            model: OpenAI model to use (default: gpt-4)
            temperature: Creativity level (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            logger: Optional logger instance
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
            
        openai.api_key = self.api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = logger or logging.getLogger(__name__)
        
    async def generate_content(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate content using the OpenAI API.
        
        Args:
            prompt: The main content generation prompt
            context: Additional context dictionary
            **kwargs: Additional parameters for the API call
            
        Returns:
            Dict containing generated content and metadata
        """
        try:
            # Merge default parameters with any overrides
            params = {
                'model': kwargs.get('model', self.model),
                'temperature': kwargs.get('temperature', self.temperature),
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'messages': self._build_messages(prompt, context)
            }
            
            # Make the API call
            self.logger.debug(f"Calling OpenAI API with params: {params}")
            response = await openai.ChatCompletion.acreate(**params)
            
            # Extract and process the response
            content = response.choices[0].message.content
            
            return {
                'content': content,
                'metadata': {
                    'model': params['model'],
                    'temperature': params['temperature'],
                    'generated_at': datetime.utcnow().isoformat(),
                    'tokens_used': response.usage.total_tokens,
                    'finish_reason': response.choices[0].finish_reason
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            raise
            
    def _build_messages(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> list:
        """Build the messages array for the API call.
        
        Args:
            prompt: Main generation prompt
            context: Additional context dictionary
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system context if provided
        if context and context.get('system_message'):
            messages.append({
                'role': 'system',
                'content': context['system_message']
            })
            
        # Add any example messages if provided
        if context and context.get('examples'):
            for example in context['examples']:
                messages.extend([
                    {'role': 'user', 'content': example['input']},
                    {'role': 'assistant', 'content': example['output']}
                ])
                
        # Add the main prompt
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        return messages
        
    def _validate_response(self, response: Dict) -> bool:
        """Validate the API response.
        
        Args:
            response: Response from the API
            
        Returns:
            bool indicating if response is valid
        """
        required_fields = ['choices', 'usage']
        if not all(field in response for field in required_fields):
            return False
            
        if not response['choices']:
            return False
            
        choice = response['choices'][0]
        if not choice.get('message') or not choice['message'].get('content'):
            return False
            
        return True 