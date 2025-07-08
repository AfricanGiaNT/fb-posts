"""
AI Content Generator for Facebook Posts
"""

import openai
from typing import Dict, Optional
import re
from datetime import datetime
import json

class AIContentGenerator:
    """Handles AI-powered content generation using OpenAI."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.client = openai.OpenAI(api_key=self.config.openai_api_key)
        self.prompt_template = self.config.get_prompt_template()
    
    def generate_facebook_post(self, markdown_content: str, user_tone_preference: Optional[str] = None) -> Dict:
        """
        Generate a Facebook post from markdown content.
        
        Args:
            markdown_content: The markdown content to transform
            user_tone_preference: Optional tone preference from user
            
        Returns:
            Dict containing the generated post, tone used, and metadata
        """
        try:
            # Prepare the full prompt
            full_prompt = self._build_full_prompt(markdown_content, user_tone_preference)
            
            # Generate content using OpenAI
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse the response
            generated_content = response.choices[0].message.content
            parsed_response = self._parse_ai_response(generated_content)
            
            # Add metadata
            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', 'Unknown'),
                'tone_reason': parsed_response.get('reason', 'No reason provided'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.config.openai_model,
                'original_markdown': markdown_content
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating Facebook post: {str(e)}")
    
    def _build_full_prompt(self, markdown_content: str, user_tone_preference: Optional[str] = None) -> str:
        """Build the complete prompt for the AI."""
        prompt_parts = []
        
        if user_tone_preference:
            prompt_parts.append(f"Please use the '{user_tone_preference}' tone style for this post.")
        
        prompt_parts.append("Here is the markdown content to transform:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse the AI response to extract tone, post content, and reason."""
        result = {}
        
        # Try to extract structured response with more flexible patterns
        tone_patterns = [
            r'TONE:\s*(.+?)(?=\n|POST:|$)',
            r'Tone Used?:\s*(.+?)(?=\n|POST:|$)',
            r'Brand Tone:\s*(.+?)(?=\n|POST:|$)'
        ]
        
        for pattern in tone_patterns:
            tone_match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if tone_match:
                tone_text = tone_match.group(1).strip()
                # Clean up the tone text to match our standard format
                if 'behind' in tone_text.lower() and 'build' in tone_text.lower():
                    result['tone'] = 'Behind-the-Build'
                elif 'broke' in tone_text.lower() or 'break' in tone_text.lower():
                    result['tone'] = 'What Broke'
                elif 'finished' in tone_text.lower() or 'proud' in tone_text.lower():
                    result['tone'] = 'Finished & Proud'
                elif 'problem' in tone_text.lower() and 'solution' in tone_text.lower():
                    result['tone'] = 'Problem → Solution → Result'
                elif 'lesson' in tone_text.lower() or 'mini' in tone_text.lower():
                    result['tone'] = 'Mini Lesson'
                else:
                    result['tone'] = tone_text  # Use as-is if no match
                break
        
        # Try to extract post content with more flexible patterns
        post_patterns = [
            r'POST:\s*(.+?)(?=REASON:|$)',
            r'Content:\s*(.+?)(?=REASON:|$)',
            r'Facebook Post:\s*(.+?)(?=REASON:|$)'
        ]
        
        for pattern in post_patterns:
            post_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if post_match:
                post_content = post_match.group(1).strip()
                # Clean up the post content
                post_content = post_content.replace('```', '').strip()
                result['post'] = post_content
                break
        
        # Try to extract reason
        reason_patterns = [
            r'REASON:\s*(.+)',
            r'Explanation:\s*(.+)',
            r'Why this tone:\s*(.+)'
        ]
        
        for pattern in reason_patterns:
            reason_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if reason_match:
                result['reason'] = reason_match.group(1).strip()
                break
        
        # If no structured POST found, check if the response looks like raw markdown
        if not result.get('post'):
            # Check if the response contains markdown headers or lists (indicating it's not transformed)
            if re.search(r'^#{1,6}\s', response, re.MULTILINE) or re.search(r'^[-*+]\s', response, re.MULTILINE):
                # Try to extract a meaningful portion or use fallback
                lines = response.split('\n')
                # Skip markdown headers and find content
                content_lines = []
                for line in lines:
                    if not line.strip().startswith('#') and not line.strip().startswith('-') and not line.strip().startswith('*'):
                        if line.strip():
                            content_lines.append(line.strip())
                
                if content_lines:
                    result['post'] = '\n\n'.join(content_lines[:5])  # Take first 5 meaningful lines
                else:
                    result['post'] = "I need to transform this content better. Let me regenerate this post."
            else:
                result['post'] = response
            
        # If no tone was detected, try to infer from content
        if not result.get('tone'):
            result['tone'] = self._infer_tone_from_content(response)
        
        # If no reason provided, create a default one
        if not result.get('reason'):
            result['reason'] = f"Chose {result.get('tone', 'this tone')} to best match the content and engage the audience."
        
        return result
    
    def _infer_tone_from_content(self, content: str) -> str:
        """Infer tone from content when not explicitly stated."""
        content_lower = content.lower()
        
        if 'built' in content_lower and ('cursor' in content_lower or 'ai' in content_lower):
            return 'Behind-the-Build'
        elif 'broke' in content_lower or 'failed' in content_lower or 'error' in content_lower:
            return 'What Broke'
        elif 'shipped' in content_lower or 'completed' in content_lower or 'finished' in content_lower:
            return 'Finished & Proud'
        elif 'problem' in content_lower and 'solution' in content_lower:
            return 'Problem → Solution → Result'
        elif 'lesson' in content_lower or 'principle' in content_lower or 'insight' in content_lower:
            return 'Mini Lesson'
        else:
            return 'Behind-the-Build'  # Default fallback
    
    def regenerate_post(self, markdown_content: str, feedback: str = "", tone_preference: Optional[str] = None) -> Dict:
        """
        Regenerate a post with user feedback.
        
        Args:
            markdown_content: Original markdown content
            feedback: User feedback on the previous version
            tone_preference: Specific tone to use for regeneration
            
        Returns:
            Dict containing the regenerated post and metadata
        """
        try:
            # Build prompt with feedback
            regeneration_prompt = self._build_regeneration_prompt(markdown_content, feedback, tone_preference)
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {"role": "system", "content": self.prompt_template},
                    {"role": "user", "content": regeneration_prompt}
                ],
                max_tokens=1000,
                temperature=0.8  # Slightly higher temperature for more variation
            )
            
            generated_content = response.choices[0].message.content
            parsed_response = self._parse_ai_response(generated_content)
            
            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', 'Unknown'),
                'tone_reason': parsed_response.get('reason', 'No reason provided'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.config.openai_model,
                'original_markdown': markdown_content,
                'regenerated_with_feedback': feedback,
                'is_regeneration': True
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error regenerating Facebook post: {str(e)}")
    
    def _build_regeneration_prompt(self, markdown_content: str, feedback: str, tone_preference: Optional[str] = None) -> str:
        """Build prompt for regeneration with feedback."""
        prompt_parts = []
        
        prompt_parts.append("Please regenerate the Facebook post with the following feedback in mind:")
        prompt_parts.append(f"FEEDBACK: {feedback}")
        
        if tone_preference:
            prompt_parts.append(f"Please use the '{tone_preference}' tone style for this regeneration.")
        
        prompt_parts.append("Here is the original markdown content:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def get_tone_options(self) -> list:
        """Get list of available tone options."""
        return [
            "Behind-the-Build",
            "What Broke", 
            "Finished & Proud",
            "Problem → Solution → Result",
            "Mini Lesson"
        ] 