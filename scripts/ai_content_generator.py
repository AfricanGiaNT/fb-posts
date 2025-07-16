"""
AI Content Generator for Facebook Posts
"""

import openai
from typing import Dict, Optional, List
import re
from datetime import datetime
import json

# Handle both absolute and relative imports
try:
    from chichewa_integrator import ChichewaIntegrator
except ImportError:
    from .chichewa_integrator import ChichewaIntegrator

# Claude support
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

class AIContentGenerator:
    """Handles AI-powered content generation using OpenAI or Claude."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.prompt_template = self.config.get_prompt_template()
        self.chichewa_integrator = ChichewaIntegrator()
        
        # Initialize the appropriate client based on configuration
        self.provider = self.config.content_generation_provider
        
        if self.provider == 'openai':
            self.client = openai.OpenAI(api_key=self.config.openai_api_key)
            self.model = self.config.openai_model
        elif self.provider == 'claude':
            if not CLAUDE_AVAILABLE:
                raise ImportError("Claude support requires 'anthropic' package. Install with: pip install anthropic")
            self.client = anthropic.Anthropic(api_key=self.config.claude_api_key)
            self.model = self.config.claude_model
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        # Phase 2: Relationship types for context-aware generation
        self.relationship_types = {
            'different_aspects': '🔍 Different Aspects',
            'different_angles': '📐 Different Angles', 
            'series_continuation': '📚 Series Continuation',
            'thematic_connection': '🔗 Thematic Connection',
            'technical_deep_dive': '🔧 Technical Deep Dive',
            'sequential_story': '📖 Sequential Story'
        }
    
    def _generate_content(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2500) -> str:
        """Unified content generation method that works with both OpenAI and Claude."""
        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
            
            elif self.provider == 'claude':
                # Claude uses a different API format
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return response.content[0].text
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            raise Exception(f"Error generating content with {self.provider}: {str(e)}")
    
    def get_model_info(self) -> Dict:
        """Get information about the current model configuration."""
        return {
            'provider': self.provider,
            'model': self.model,
            'supports_streaming': self.provider == 'claude',
            'max_tokens_supported': 4096 if self.provider == 'openai' else 8192,
            'description': self._get_model_description()
        }
    
    def _get_model_description(self) -> str:
        """Get a description of the current model's capabilities."""
        descriptions = {
            'openai': {
                'gpt-4o': 'GPT-4o: Advanced reasoning, good for technical content',
                'gpt-4': 'GPT-4: Reliable, balanced performance',
                'gpt-3.5-turbo': 'GPT-3.5 Turbo: Fast, cost-effective'
            },
            'claude': {
                'claude-3-5-sonnet-20241022': 'Claude 3.5 Sonnet: Excellent creative writing, storytelling, and copywriting',
                'claude-3-opus-20240229': 'Claude 3 Opus: Highest quality reasoning and creativity',
                'claude-3-haiku-20240307': 'Claude 3 Haiku: Fast, efficient for simple tasks'
            }
        }
        
        provider_models = descriptions.get(self.provider, {})
        return provider_models.get(self.model, f'{self.provider} model: {self.model}')
    
    def generate_facebook_post(self, markdown_content: str, user_tone_preference: Optional[str] = None, 
                              session_context: Optional[str] = None, previous_posts: Optional[List[Dict]] = None,
                              relationship_type: Optional[str] = None, parent_post_id: Optional[str] = None,
                              audience_type: Optional[str] = None) -> Dict:
        """
        Generate a Facebook post from markdown content with context awareness.
        
        Args:
            markdown_content: The markdown content to transform
            user_tone_preference: Optional tone preference from user
            session_context: Context from previous posts in the series
            previous_posts: List of previous posts in the series
            relationship_type: How this post relates to previous posts
            parent_post_id: ID of the parent post to reference
            audience_type: The target audience ('business' or 'technical')
            
        Returns:
            Dict containing the generated post, tone used, and metadata
        """
        try:
            # Determine if this is a context-aware generation
            is_context_aware = session_context or previous_posts or relationship_type
            
            if is_context_aware:
                # Use context-aware prompt building
                full_prompt = self._build_context_aware_prompt(
                    markdown_content, user_tone_preference, session_context, 
                    previous_posts, relationship_type, parent_post_id, audience_type
                )
                system_prompt = self._get_context_aware_system_prompt(audience_type)
            else:
                # Use original single-post prompt
                full_prompt = self._build_full_prompt(markdown_content, user_tone_preference, audience_type)
                system_prompt = self._get_system_prompt(audience_type)
            
            # Generate content using OpenAI
            generated_content = self._generate_content(
                system_prompt, full_prompt, temperature=0.7, max_tokens=2500
            )
            
            # Parse the response
            parsed_response = self._parse_ai_response(generated_content)
            
            # Add metadata
            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', 'Unknown'),
                'tone_reason': parsed_response.get('reason', 'No reason provided'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model,
                'original_markdown': markdown_content,
                'is_context_aware': is_context_aware,
                'relationship_type': relationship_type,
                'parent_post_id': parent_post_id,
                'audience_type': audience_type
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error generating Facebook post: {str(e)}")
    
    def _build_full_prompt(self, markdown_content: str, user_tone_preference: Optional[str] = None, audience_type: Optional[str] = None) -> str:
        """Build the complete prompt for the AI."""
        prompt_parts = []
        
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)

        if user_tone_preference:
            prompt_parts.append(f"Please use the '{user_tone_preference}' tone style for this post.")
        
        prompt_parts.append("Here is the markdown content to transform:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _build_context_aware_prompt(self, markdown_content: str, user_tone_preference: Optional[str], 
                                   session_context: Optional[str], previous_posts: Optional[List[Dict]], 
                                   relationship_type: Optional[str], parent_post_id: Optional[str],
                                   audience_type: Optional[str] = None) -> str:
        """Build a context-aware prompt for multi-post generation."""
        prompt_parts = []
        
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)

        # Add relationship-specific instructions
        if relationship_type:
            relationship_instructions = self._get_relationship_instructions(relationship_type)
            prompt_parts.append(relationship_instructions)
        
        # Add session context if available
        if session_context:
            prompt_parts.append(f"SERIES CONTEXT:\n{session_context}")
        
        # Add previous posts context
        if previous_posts:
            prompt_parts.append("PREVIOUS POSTS IN THIS SERIES:")
            for i, post in enumerate(previous_posts[-3:], 1):  # Show last 3 posts for context
                prompt_parts.append(f"Post {i}: {post.get('tone_used', 'Unknown')} tone")
                content_preview = post.get('content', '')[:200] + "..." if len(post.get('content', '')) > 200 else post.get('content', '')
                prompt_parts.append(f"Content: {content_preview}")
                prompt_parts.append("")
        
        # Add tone preference if specified
        if user_tone_preference:
            prompt_parts.append(f"TONE PREFERENCE: Use the '{user_tone_preference}' tone style for this post.")
        
        # Add reference generation instructions
        if parent_post_id and previous_posts:
            parent_post = next((p for p in previous_posts if p.get('post_id') == parent_post_id), None)
            if parent_post:
                prompt_parts.append(f"REFERENCE POST: This post should naturally reference or build upon the previous post about {parent_post.get('tone_used', 'the topic')}. Use phrases like 'In my last post...', 'Building on what I shared...', or 'Following up on...'")
        
        # Add content variation strategy
        if relationship_type:
            variation_strategy = self._get_content_variation_strategy(relationship_type)
            prompt_parts.append(variation_strategy)
        
        # Add anti-repetition context
        if previous_posts and relationship_type:
            anti_repetition = self._add_anti_repetition_context(markdown_content, previous_posts, relationship_type)
            if anti_repetition:
                prompt_parts.append(anti_repetition)
        
        prompt_parts.append("MARKDOWN CONTENT TO TRANSFORM:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _get_relationship_instructions(self, relationship_type: str) -> str:
        """Get specific instructions for each relationship type."""
        instructions = {
            'different_aspects': """
RELATIONSHIP TYPE: Different Aspects
Focus on a different section, feature, or component of the same project. 
Avoid repeating what was already covered in previous posts.
Highlight a new aspect that adds value to the overall story.
            """,
            'different_angles': """
RELATIONSHIP TYPE: Different Angles  
Present the same information from a fresh perspective:
- Technical vs. Business vs. Personal angle
- Before/After vs. Process vs. Impact perspective
- Developer vs. User vs. Business owner viewpoint
            """,
            'series_continuation': """
RELATIONSHIP TYPE: Series Continuation
This is part of a sequential series (Part 1, 2, 3...).
Reference the previous post naturally and build upon it.
Use phrases like "In Part 1, I covered..." or "Now let's dive into..."
            """,
            'thematic_connection': """
RELATIONSHIP TYPE: Thematic Connection
Connect to broader themes, philosophies, or principles from previous posts.
Show how this project relates to overarching patterns or lessons.
Use phrases like "This connects to what I've been exploring..." or "Another example of..."
            """,
            'technical_deep_dive': """
RELATIONSHIP TYPE: Technical Deep Dive
Provide detailed technical explanation building on previous posts.
Focus on implementation details, architecture, or technical decisions.
Use phrases like "Here's how I actually built..." or "The technical side of..."
            """,
            'sequential_story': """
RELATIONSHIP TYPE: Sequential Story
Tell what happened next in the chronological story.
Use narrative progression: "Then I...", "Next thing I knew...", "The plot twist was..."
Maintain story flow and emotional continuity.
            """
        }
        return instructions.get(relationship_type, "")
    
    def _get_audience_instructions(self, audience_type: str) -> str:
        """Get audience-specific instructions."""
        if audience_type == 'business':
            return self._get_business_audience_instructions()
        elif audience_type == 'technical':
            return self._get_technical_audience_instructions()
        return ""

    def _get_business_audience_instructions(self) -> str:
        """Get specific instructions for business audience."""
        return """
AUDIENCE: Business Owner/General (like busy shop owners, service providers)

Content Guidelines:
- Use simple, clear language
- Focus on business impact: time saved, money made, problems solved
- Use relatable examples (running a shop, managing customers, handling inventory)
- Avoid technical jargon - explain in everyday terms
- Emphasize practical benefits and real-world results
- Make it sound like you're talking to a friend who owns a business

Examples of good language:
- "This saves me 3 hours every week"
- "My customers are happier because..."
- "I used to spend all day on paperwork, now..."
- "It's like having an assistant that never sleeps"
"""

    def _get_technical_audience_instructions(self) -> str:
        """Get specific instructions for technical audience."""
        return """
AUDIENCE: Developer/Technical (like software engineers, data scientists)

Content Guidelines:
- Use precise, technical language where appropriate
- Focus on the "how": architecture, algorithms, libraries, and tools used
- Include code snippets or pseudocode for illustration
- Explain technical challenges and trade-offs
- Emphasize innovation, efficiency, and elegant solutions

Examples of good language:
- "I refactored the data pipeline using..."
- "The key was to implement a caching layer with Redis..."
- "This microservice was built with FastAPI and containerized with Docker..."
- "We reduced query latency by 40% by adding an index to..."
"""

    def _get_content_variation_strategy(self, relationship_type: str) -> str:
        """Get content variation strategy based on relationship type."""
        # Base anti-repetition instructions
        base_instructions = """
CONTENT VARIATION STRATEGY:
- Avoid repeating exact phrases from previous posts
- Use different examples and analogies
- Vary sentence structure and opening statements
- Introduce new perspectives or angles
- Reference different aspects of the technical implementation
"""
        
        # Relationship-specific variation strategies
        variation_strategies = {
            'Different Aspects': base_instructions + """
- Focus on completely different features or components
- Highlight different user benefits or use cases
- Explore different technical challenges overcome
- Discuss different development phases or stages
""",
            
            'Different Angles': base_instructions + """
- Change perspective: technical vs business vs user experience
- Vary the narrative voice: builder vs user vs observer
- Focus on different emotional aspects: excitement vs challenge vs pride
- Alternate between problem-focused and solution-focused narratives
""",
            
            'Series Continuation': base_instructions + """
- Build chronologically on previous content
- Introduce new developments or improvements
- Show progression and evolution of ideas
- Reference 'what happened next' or 'building further'
- Avoid repeating the same accomplishments
""",
            
            'Technical Deep Dive': base_instructions + """
- Explore different technical layers (frontend, backend, database)
- Focus on different programming concepts or patterns
- Discuss different tools or technologies used
- Vary between high-level architecture and implementation details
""",
            
            'Thematic Connection': base_instructions + """
- Connect through underlying principles rather than surface details
- Explore different philosophical or strategic aspects
- Draw different life or business lessons
- Use different metaphors and analogies
""",
            
            'Sequential Story': base_instructions + """
- Focus on different timeline segments
- Introduce new characters or stakeholders
- Show different stages of problem-solving
- Highlight different obstacles and breakthroughs
""",
            
            'AI Decide': base_instructions + """
- Let AI determine the best variation approach
- Combine multiple strategies for maximum variety
- Ensure each post offers unique value and perspective
"""
        }
        
        return variation_strategies.get(relationship_type, base_instructions)
    
    def _add_anti_repetition_context(self, markdown_content: str, previous_posts: List[Dict], 
                                   relationship_type: str) -> str:
        """Add context to prevent content repetition."""
        if not previous_posts:
            return ""
        
        # Extract key phrases and topics from previous posts
        previous_content = []
        for post in previous_posts[-3:]:  # Look at last 3 posts
            content = post.get('content', '')
            if content:
                # Extract first sentences as key phrases
                sentences = content.split('.')[:3]
                previous_content.extend(sentences)
        
        if not previous_content:
            return ""
        
        # Create anti-repetition instructions
        anti_repetition = f"""
ANTI-REPETITION REQUIREMENTS:
- Previous posts used these opening approaches: {'; '.join(previous_content[:5])}
- Do NOT start with similar phrases or structures
- Introduce completely new examples and analogies
- Use different vocabulary and sentence patterns
- Bring fresh perspective while maintaining series coherence
- Focus on aspects NOT covered in previous posts
"""
        
        return anti_repetition
    
    def _get_context_aware_system_prompt(self, audience_type: Optional[str] = None) -> str:
        """Get enhanced system prompt for context-aware generation."""
        if audience_type == 'business':
            return self._get_business_context_aware_system_prompt()
        return self._get_base_system_prompt() # Fallback for technical or general

    def _get_business_context_aware_system_prompt(self) -> str:
        """Get business-focused context-aware system prompt."""
        business_prompt = self._get_business_system_prompt()
        
        # Add context-awareness instructions
        context_instructions = """

**MULTI-POST SERIES INSTRUCTIONS:**
- You are creating posts as part of a series for business owners
- Use the session context and previous posts to create natural continuity
- Reference previous posts naturally: "In my last post...", "Building on what I shared..."
- Ensure each post adds new business value while maintaining series coherence
- Keep the business-friendly language consistent across all posts in the series
- Focus on different business aspects or benefits in each post to avoid repetition
- Never mention time frames or duration across the series
- Present each milestone as a completed achievement that adds business value

**CONTENT PROCESSING FOR SERIES:**
- Each markdown file represents a completed development milestone
- Extract unique business value from each milestone
- Ignore any file naming patterns or dates
- Focus on different business benefits or use cases
- Present work as finished accomplishments that solve business problems

"""
        
        return business_prompt + context_instructions

    def _get_system_prompt(self, audience_type: Optional[str] = None) -> str:
        """Get system prompt based on audience type."""
        if audience_type == 'business':
            return self._get_business_system_prompt()
        elif audience_type == 'technical':
            return self._get_technical_system_prompt()
        return self._get_base_system_prompt() # Default

    def _get_base_system_prompt(self) -> str:
        """Base system prompt for general use."""
        return """You are a smart, helpful copywriter who turns project ideas and build summaries into engaging social media posts.

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

**Content Processing Instructions:**
- The markdown content represents a completed development milestone
- Extract the core problem, solution, and result
- Ignore any file naming patterns or dates
- Focus on the technical achievement and its impact
- Present the work as a finished accomplishment"""

    def _get_technical_system_prompt(self) -> str:
        """System prompt for a technical audience."""
        return self._get_base_system_prompt() + """

**TECHNICAL AUDIENCE FOCUS:**
You are writing for a technical audience of developers and engineers.
- Be precise and clear.
- Use correct terminology.
- Focus on the technical implementation, challenges, and solutions.
- Share code snippets and technical details when relevant.
- Explain your architectural decisions and trade-offs.
- Present technical work as completed achievements without time references.
- Focus on what was built, how it works, and the technical impact.
"""

    def _get_business_system_prompt(self) -> str:
        """Updated prompt for generating simple, clear Facebook posts for business owners."""
        return """You are a helpful copywriter who turns project notes into clear, practical Facebook posts for small business owners.

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

Your audience is busy business owners who want practical solutions. They may not be highly technical, but they understand business challenges. Your job is to explain solutions in clear, everyday language.

They want to know:
- What problem this solves  
- How it works (in simple terms)  
- Why it matters for their business  
- What realistic results they can expect

---

### ✍️ Your task:

Generate a conversational Facebook post from the content provided. Write it naturally, like you're explaining something useful to a business colleague.

**Use clear, everyday language.** Avoid technical jargon and replace complex terms with simple ones:
- Instead of "API integration" → say "connected systems"
- Instead of "database" → say "stored information"
- Instead of "automated workflow" → say "handles tasks automatically"

---

### ✏️ Format guidelines:

1. **Start naturally** – no dramatic hooks or greetings
2. **Use normal paragraphs** (2-4 sentences each)
3. **Include practical examples** when helpful
4. **Use simple language** that anyone can understand
5. **Be honest about limitations** – don't oversell
6. **End with a genuine question or observation**
7. **Minimal emojis** – only when they add clarity
8. **TARGET 400-600 WORDS** for optimal engagement and readability
9. **Extract the key narrative** – identify the most compelling business story or insight
10. **Choose the tone that best fits** – let the content guide your tone selection
11. **Never mention time frames or duration** – focus on the achievement and its business impact

**IMPORTANT LENGTH REQUIREMENT:**
Your post must be between 400-600 words to maximize Facebook engagement. This is a firm target, not a suggestion. If your first draft is too short, expand on:
- More detailed examples
- Additional context about the problem
- Specific implementation details (in simple terms)
- More comprehensive results or impact
- Personal insights and lessons learned

**Content Processing Instructions:**
- The markdown content represents a completed development milestone
- Extract the core problem, solution, and result
- Ignore any file naming patterns or dates
- Focus on the technical achievement and its impact
- Present the work as a finished accomplishment

---

### 🧠 Choose the most appropriate tone:

- 🧩 **Behind-the-Build** – "Here's what I worked on and why"
- 💡 **What Broke** – "Something didn't work as expected, here's what I learned"
- 🚀 **Finished & Proud** – "Got this working, here's what it does"
- 🎯 **Problem → Solution → Result** – "This addressed a real problem with practical results"
- 📓 **Mini Lesson** – "A simple insight from working on this"

---

**Output Format:**

TONE: [chosen tone name]
POST: [Facebook post content in clear, conversational language - aim for 400-600 words, no time references]
REASON: [brief explanation of tone choice and audience fit]

**IMPORTANT:** Keep the language natural and conversational. Avoid hype, excessive enthusiasm, or sales-like language. Focus on practical value and honest communication. Write as if YOU built this project yourself without mentioning when or how long it took."""

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
                # Unescape common markdown characters
                post_content = post_content.replace('\\*', '*').replace('\\_', '_').replace('\\`', '`').replace('\\#', '#').replace('\\.', '.').replace('\\!', '!').replace('\\-', '-').replace('\\(', '(').replace('\\)', ')').replace('\\[', '[').replace('\\]', ']')
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
    
    def regenerate_post(self, markdown_content: str, feedback: str = "", tone_preference: Optional[str] = None,
                       session_context: Optional[str] = None, previous_posts: Optional[List[Dict]] = None,
                       relationship_type: Optional[str] = None, parent_post_id: Optional[str] = None) -> Dict:
        """
        Regenerate a post with user feedback and context awareness.
        
        Args:
            markdown_content: Original markdown content
            feedback: User feedback on the previous version
            tone_preference: Specific tone to use for regeneration
            session_context: Context from previous posts in the series
            previous_posts: List of previous posts in the series
            relationship_type: How this post relates to previous posts
            parent_post_id: ID of the parent post to reference
            
        Returns:
            Dict containing the regenerated post and metadata
        """
        try:
            # Determine if this is a context-aware regeneration
            is_context_aware = session_context or previous_posts or relationship_type
            
            if is_context_aware:
                # Build context-aware regeneration prompt
                regeneration_prompt = self._build_context_aware_regeneration_prompt(
                    markdown_content, feedback, tone_preference, session_context, 
                    previous_posts, relationship_type, parent_post_id
                )
                system_prompt = self._get_context_aware_system_prompt()
            else:
                # Use original regeneration prompt
                regeneration_prompt = self._build_regeneration_prompt(markdown_content, feedback, tone_preference)
                system_prompt = self.prompt_template
            
            generated_content = self._generate_content(
                system_prompt, regeneration_prompt, temperature=0.8, max_tokens=2500
            )
            
            parsed_response = self._parse_ai_response(generated_content)
            
            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', 'Unknown'),
                'tone_reason': parsed_response.get('reason', 'No reason provided'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model,
                'original_markdown': markdown_content,
                'regenerated_with_feedback': feedback,
                'is_regeneration': True,
                'is_context_aware': is_context_aware,
                'relationship_type': relationship_type,
                'parent_post_id': parent_post_id
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
    
    def _build_context_aware_regeneration_prompt(self, markdown_content: str, feedback: str, 
                                               tone_preference: Optional[str], session_context: Optional[str],
                                               previous_posts: Optional[List[Dict]], relationship_type: Optional[str],
                                               parent_post_id: Optional[str]) -> str:
        """Build context-aware regeneration prompt."""
        prompt_parts = []
        
        prompt_parts.append("Please regenerate the Facebook post with the following feedback in mind:")
        prompt_parts.append(f"FEEDBACK: {feedback}")
        
        # Add relationship-specific instructions
        if relationship_type:
            relationship_instructions = self._get_relationship_instructions(relationship_type)
            prompt_parts.append(relationship_instructions)
        
        # Add session context if available
        if session_context:
            prompt_parts.append(f"SERIES CONTEXT:\n{session_context}")
        
        # Add previous posts context
        if previous_posts:
            prompt_parts.append("PREVIOUS POSTS IN THIS SERIES:")
            for i, post in enumerate(previous_posts[-3:], 1):
                prompt_parts.append(f"Post {i}: {post.get('tone_used', 'Unknown')} tone")
                content_preview = post.get('content', '')[:200] + "..." if len(post.get('content', '')) > 200 else post.get('content', '')
                prompt_parts.append(f"Content: {content_preview}")
                prompt_parts.append("")
        
        # Add tone preference if specified
        if tone_preference:
            prompt_parts.append(f"TONE PREFERENCE: Use the '{tone_preference}' tone style for this regeneration.")
        
        # Add reference generation instructions
        if parent_post_id and previous_posts:
            parent_post = next((p for p in previous_posts if p.get('post_id') == parent_post_id), None)
            if parent_post:
                prompt_parts.append(f"REFERENCE POST: This post should naturally reference or build upon the previous post about {parent_post.get('tone_used', 'the topic')}. Use phrases like 'In my last post...', 'Building on what I shared...', or 'Following up on...'")
        
        # Add content variation strategy
        if relationship_type:
            variation_strategy = self._get_content_variation_strategy(relationship_type)
            prompt_parts.append(variation_strategy)
        
        prompt_parts.append("ORIGINAL MARKDOWN CONTENT:")
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

    def generate_related_post(self, markdown_content: str, previous_posts: List[Dict], 
                             relationship_type: str, parent_post_id: Optional[str] = None,
                             user_tone_preference: Optional[str] = None) -> Dict:
        """
        Generate a related post based on a specific relationship to previous posts.
        
        Args:
            markdown_content: The original markdown content
            previous_posts: List of previous posts in the series
            relationship_type: Type of relationship to previous posts
            parent_post_id: Specific post to reference
            user_tone_preference: Optional tone preference from user
            
        Returns:
            Dict containing the generated post and metadata
        """
        # Create session context from previous posts
        session_context = self._create_session_context(previous_posts, markdown_content)
        
        return self.generate_facebook_post(
            markdown_content=markdown_content,
            user_tone_preference=user_tone_preference,
            session_context=session_context,
            previous_posts=previous_posts,
            relationship_type=relationship_type,
            parent_post_id=parent_post_id
        )
    
    def _create_session_context(self, previous_posts: List[Dict], original_markdown: str) -> str:
        """Create session context summary from previous posts."""
        if not previous_posts:
            return ""
        
        context_parts = [
            f"Series: {len(previous_posts)} posts created from project documentation",
            f"Original project: {original_markdown[:200]}...",
            ""
        ]
        
        for post in previous_posts:
            context_parts.append(f"Post {post.get('post_id', 'N/A')}: {post.get('tone_used', 'Unknown')} tone")
            content_summary = post.get('content', '')[:150] + "..." if len(post.get('content', '')) > 150 else post.get('content', '')
            context_parts.append(f"Content: {content_summary}")
            if post.get('relationship_type'):
                context_parts.append(f"Relationship: {post.get('relationship_type')}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def suggest_relationship_type(self, previous_posts: List[Dict], markdown_content: str) -> str:
        """
        Suggest the best relationship type for a new post based on previous posts.
        
        Args:
            previous_posts: List of previous posts in the series
            markdown_content: The original markdown content
            
        Returns:
            Suggested relationship type
        """
        if not previous_posts:
            return 'different_aspects'  # Default for first related post
        
        # Get tones of previous posts
        previous_tones = [post.get('tone_used', '') for post in previous_posts]
        
        # Simple rule-based suggestions
        if len(previous_posts) == 1:
            # Second post - suggest different angle
            return 'different_angles'
        elif len(previous_posts) == 2:
            # Third post - suggest technical deep dive or series continuation
            return 'technical_deep_dive'
        elif 'Behind-the-Build' in previous_tones and 'What Broke' not in previous_tones:
            # Haven't covered problems yet
            return 'different_aspects'
        elif all(tone != 'Mini Lesson' for tone in previous_tones):
            # Haven't done philosophical angle yet
            return 'thematic_connection'
        else:
            # Default to different aspects
            return 'different_aspects'
    
    def get_relationship_types(self) -> Dict[str, str]:
        """Get available relationship types."""
        return self.relationship_types.copy()
    
    def validate_relationship_type(self, relationship_type: str) -> bool:
        """Validate if relationship type is supported."""
        return relationship_type in self.relationship_types

    def generate_continuation_post(self, previous_post_text: str, add_chichewa_humor: bool = False) -> Dict:
        """
        Generate a follow-up Facebook post based on the text of a previous post.
        """
        try:
            system_prompt = self._get_system_prompt()
            full_prompt = self._build_continuation_prompt(previous_post_text)

            generated_content = self._generate_content(
                system_prompt, full_prompt, temperature=0.7, max_tokens=2500
            )

            parsed_response = self._parse_ai_response(generated_content)

            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', 'Unknown'),
                'tone_reason': parsed_response.get('reason', 'No reason provided'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model,
                'original_markdown': "Continuation from existing post",
                'is_context_aware': True,
                'relationship_type': 'continuation',
                'parent_post_id': None,
            }

            # Add Chichewa humor if requested
            if add_chichewa_humor:
                result['post_content'] = self.chichewa_integrator.integrate_phrases(result['post_content'])
            
            return result
        except Exception as e:
            raise Exception(f"Error generating continuation post: {str(e)}")

    def _build_continuation_prompt(self, previous_post_text: str) -> str:
        """Build the prompt for generating a continuation post."""
        prompt_parts = []

        prompt_parts.append(
            "You are a copywriter tasked with writing a follow-up to an existing Facebook post. "
            "Your goal is to create a new post that feels like a natural continuation of the story or topic."
        )
        prompt_parts.append(
            "INSTRUCTIONS:\\n"
            "1. **Analyze the Previous Post**: Carefully read the post provided below to understand its topic, tone, and style.\\n"
            "2. **Generate a Follow-Up**: Write a new, original post that builds on the previous one. Do NOT simply summarize or repeat it.\\n"
            "3. **Add New Value**: Introduce a new perspective, a deeper dive, a lesson learned, or the next step in the process.\\n"
            "4. **Use Transition Phrases**: Make the connection clear with phrases like 'In my last post...', 'Building on that idea...', 'To continue where I left off...', etc.\\n"
            "5. **Maintain Consistency**: Match the tone and voice of the previous post to ensure the series feels cohesive.\\n"
            "6. **Format Your Response**: Structure your entire output with the following tags: `[POST]`, `[TONE]`, and `[REASON]`."
        )
        prompt_parts.append("Here is the previous post to continue from:")
        prompt_parts.append("---")
        prompt_parts.append(previous_post_text)
        prompt_parts.append("---")
        
        return "\\n\\n".join(prompt_parts) 