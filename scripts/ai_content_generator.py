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
            'integration_expansion': '🔗 Integration Expansion',
            'implementation_evolution': '🔄 Implementation Evolution',
            'system_enhancement': '⚡ System Enhancement',
            'problem_solution_chain': '🎯 Problem-Solution Chain',
            'feature_milestone': '🚀 Feature Milestone',
            'deployment_experience': '📦 Deployment Experience'
        }
    
    def _generate_content(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
        """Unified content generation method that works with both OpenAI and Claude."""
        import time
        import random
        
        # Enhanced retry logic for Claude overload errors
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
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
                error_str = str(e)
                
                # Check if it's a Claude overload error
                if "overloaded" in error_str.lower() or "529" in error_str:
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Claude overloaded, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Claude API overloaded after {max_retries} attempts. Please try again in a few minutes.")
                else:
                    # For other errors, fail immediately
                    raise Exception(f"Error generating content with {self.provider}: {error_str}")
        
        # Should not reach here
        raise Exception(f"Unexpected error after {max_retries} attempts")
    
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
                              audience_type: Optional[str] = None, freeform_context: Optional[str] = None,
                              length_preference: Optional[str] = None) -> Dict:
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
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        try:
            # Determine if this is a context-aware generation
            is_context_aware = session_context or previous_posts or relationship_type
            
            if is_context_aware:
                # Use context-aware prompt building
                full_prompt = self._build_context_aware_prompt(
                    markdown_content, user_tone_preference, session_context, 
                    previous_posts, relationship_type, parent_post_id, audience_type, freeform_context, length_preference
                )
                system_prompt = self._get_context_aware_system_prompt(audience_type)
            else:
                # Use original single-post prompt
                full_prompt = self._build_full_prompt(markdown_content, user_tone_preference, audience_type, freeform_context, length_preference)
                system_prompt = self._get_system_prompt(audience_type)
            
            # Generate content using OpenAI
            generated_content = self._generate_content(
                system_prompt, full_prompt, temperature=0.7, max_tokens=4000
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
    
    def _build_full_prompt(self, markdown_content: str, user_tone_preference: Optional[str] = None, audience_type: Optional[str] = None, freeform_context: Optional[str] = None, length_preference: Optional[str] = None) -> str:
        """Build the complete prompt for the AI."""
        prompt_parts = []
        
        # Simple, direct user prompt
        prompt_parts.append("You are an AI assistant tasked with generating a Facebook post for a small business owner based on project notes. Your goal is to create an engaging, conversational post that explains a technical accomplishment in simple terms.")
        
        # Add tone preference if provided
        if user_tone_preference:
            prompt_parts.append(f"Please use the '{user_tone_preference}' tone style for this post.")
        
        # Add length preference if provided
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("Please create a SHORT-FORM post (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("Please create a LONG-FORM post (4-6 paragraphs, detailed and comprehensive).")
        
        # Add free-form context if provided
        if freeform_context:
            prompt_parts.append(f"Additional Context/Instructions: {freeform_context}")
        
        prompt_parts.append("Here is the markdown content to transform:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _build_context_aware_prompt(self, markdown_content: str, user_tone_preference: Optional[str], 
                                   session_context: Optional[str], previous_posts: Optional[List[Dict]], 
                                   relationship_type: Optional[str], parent_post_id: Optional[str],
                                   audience_type: Optional[str] = None, freeform_context: Optional[str] = None,
                                   length_preference: Optional[str] = None) -> str:
        """Build a context-aware prompt for multi-post generation."""
        prompt_parts = []
        
        # Simple, direct user prompt
        prompt_parts.append("You are an AI assistant tasked with generating a Facebook post for a small business owner based on project notes. Your goal is to create an engaging, conversational post that explains a technical accomplishment in simple terms.")

        # Add relationship-specific instructions
        if relationship_type:
            relationship_instructions = self._get_relationship_instructions(relationship_type)
            prompt_parts.append(relationship_instructions)
        
        # Add session context if available
        if session_context:
            prompt_parts.append(f"SERIES CONTEXT:\n{session_context}")
        
        # Add previous posts context with detailed information
        if previous_posts:
            prompt_parts.append("PREVIOUS POSTS IN THIS SERIES:")
            for i, post in enumerate(previous_posts[-3:], 1):  # Show last 3 posts for context
                prompt_parts.append(f"Post {i}: {post.get('tone_used', 'Unknown')} tone")
                
                # Extract key details from previous posts
                content = post.get('content', '')
                if content:
                    # Extract the main topics/themes
                    sentences = content.split('.')[:5]  # First 5 sentences
                    key_topics = []
                    for sentence in sentences:
                        if len(sentence.strip()) > 20:  # Skip very short sentences
                            key_topics.append(sentence.strip())
                    
                    prompt_parts.append(f"Key Topics Covered: {'; '.join(key_topics[:3])}")
                    
                    # Extract specific details that can be referenced
                    specific_details = []
                    for sentence in content.split('.'):
                        if any(word in sentence.lower() for word in ['built', 'created', 'implemented', 'solved', 'fixed', 'improved']):
                            specific_details.append(sentence.strip())
                    
                    if specific_details:
                        prompt_parts.append(f"Specific Details to Reference: {'; '.join(specific_details[:2])}")
                    
                    # Extract problems mentioned
                    problems = []
                    for sentence in content.split('.'):
                        if any(word in sentence.lower() for word in ['problem', 'issue', 'challenge', 'frustrating', 'broken']):
                            problems.append(sentence.strip())
                    
                    if problems:
                        prompt_parts.append(f"Problems Mentioned: {'; '.join(problems[:2])}")
                    
                    # Extract results/benefits
                    results = []
                    for sentence in content.split('.'):
                        if any(word in sentence.lower() for word in ['result', 'now', 'improvement', 'better', 'difference']):
                            results.append(sentence.strip())
                    
                    if results:
                        prompt_parts.append(f"Results/Benefits Shared: {'; '.join(results[:2])}")
                
                prompt_parts.append("")
        
        # Add tone preference if specified
        if user_tone_preference:
            prompt_parts.append(f"TONE PREFERENCE: Use the '{user_tone_preference}' tone style for this post.")
        
        # Add length preference if specified
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("LENGTH PREFERENCE: Create a SHORT-FORM post (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("LENGTH PREFERENCE: Create a LONG-FORM post (4-6 paragraphs, detailed and comprehensive).")
        
        # Add reference generation instructions
        if parent_post_id and previous_posts:
            parent_post = next((p for p in previous_posts if p.get('post_id') == parent_post_id), None)
            if parent_post:
                prompt_parts.append(f"REFERENCE POST: This post should naturally reference or build upon the previous post about {parent_post.get('tone_used', 'the topic')}. Use phrases like 'In my last post...', 'Building on what I shared...', or 'Following up on...'")
        
        # Add mandatory referencing requirements for follow-up posts
        if previous_posts:
            prompt_parts.append("""
MANDATORY FOLLOW-UP POST REQUIREMENTS:

1. **MUST Reference Previous Posts**: Start your post by specifically referencing what you shared in your previous post. This is NOT optional.

2. **Use Specific Details**: Don't just say "In my last post" - reference specific details, problems, or solutions you mentioned before.

3. **Show Progression**: Demonstrate how this new content builds upon, extends, or relates to what you previously shared.

4. **Natural Integration**: Weave the reference into your opening naturally, not as an afterthought.

5. **Avoid Repetition**: Reference previous content but don't repeat it - use it as a foundation to share something new.

Example Openings:
- "In my last post, I shared how I solved [specific problem]. Now I want to dive into [new aspect]..."
- "Building on the [specific solution] I posted about, I discovered something interesting..."
- "After sharing about [specific improvement], I realized there's another layer to this..."
- "Following up on my post about [specific feature], let me show you what happened when..."

CRITICAL: This post must clearly connect to your previous post while offering completely new value.
            """)
        
        # Add content variation strategy
        if relationship_type:
            variation_strategy = self._get_content_variation_strategy(relationship_type)
            prompt_parts.append(variation_strategy)
        
        # Add anti-repetition context
        if previous_posts and relationship_type:
            anti_repetition = self._add_anti_repetition_context(markdown_content, previous_posts, relationship_type)
            if anti_repetition:
                prompt_parts.append(anti_repetition)
        
        # Add enhanced documentation format understanding
        prompt_parts.append("""
ENHANCED DOCUMENTATION FORMAT UNDERSTANDING:

The markdown content follows an enhanced documentation structure with these sections:
- **🎯 What I Built**: Core feature/solution description
- **⚡ The Problem**: Specific pain points and challenges
- **🔧 My Solution**: Implementation approach and key features
- **🏆 The Impact/Result**: Measurable outcomes and benefits
- **🏗️ Architecture & Design**: Technical implementation details
- **💻 Code Implementation**: Specific technical choices and patterns
- **🔗 Integration Points**: System connections and dependencies
- **🎨 What Makes This Special**: Unique differentiators
- **🔄 How This Connects to Previous Work**: Context and progression
- **📊 Specific Use Cases & Scenarios**: Real-world applications
- **💡 Key Lessons Learned**: Insights and discoveries
- **🚧 Challenges & Solutions**: Problems overcome
- **🔮 Future Implications**: What this enables next

DYNAMIC CONTENT EXTRACTION BASED ON RELATIONSHIP TYPE:
""")
        
        # Add relationship-specific content extraction guidance
        content_extraction_guidance = self._get_content_extraction_guidance(relationship_type)
        if content_extraction_guidance:
            prompt_parts.append(content_extraction_guidance)
        
        # Add free-form context if provided
        if freeform_context:
            prompt_parts.append(f"ADDITIONAL CONTEXT/INSTRUCTIONS: {freeform_context}")
            prompt_parts.append("Please incorporate these instructions while maintaining the core content and requested tone.")
        
        prompt_parts.append("MARKDOWN CONTENT TO TRANSFORM:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _get_relationship_instructions(self, relationship_type: str) -> str:
        """Get specific instructions for each relationship type."""
        instructions = {
            'integration_expansion': """
RELATIONSHIP TYPE: Integration Expansion
Reference your previous post and expand on integration or connection aspects.
Build upon what you shared before about connecting systems or APIs.
Use phrases like "In my last post about..." or "Building on what I shared about integrations..."
            """,
            'implementation_evolution': """
RELATIONSHIP TYPE: Implementation Evolution
Reference your previous post and show how implementation evolved or improved.
Build upon what you shared before about the building process.
Use phrases like "After sharing about the initial build..." or "Following up on my implementation post..."
            """,
            'system_enhancement': """
RELATIONSHIP TYPE: System Enhancement
Reference your previous post and focus on performance or capability improvements.
Build upon what you shared before about system capabilities.
Use phrases like "In my previous post, I mentioned..." or "Building on the system I shared..."
            """,
            'problem_solution_chain': """
RELATIONSHIP TYPE: Problem-Solution Chain
Reference your previous post and connect to related problems or solutions.
Build upon problems or solutions you mentioned in your last post.
Use phrases like "The issue I mentioned in my last post..." or "Following up on the problem I shared..."
            """,
            'feature_milestone': """
RELATIONSHIP TYPE: Feature Milestone
Reference your previous post and present this as the next milestone or completion.
Build upon the feature work you shared before.
Use phrases like "After completing what I shared..." or "The next milestone from my last post..."
            """,
            'deployment_experience': """
RELATIONSHIP TYPE: Deployment Experience
Reference your previous post and share real-world deployment or usage experience.
Build upon what you shared before about building or testing.
Use phrases like "After deploying what I shared..." or "In production, the system I posted about..."
            """
        }
        return instructions.get(relationship_type, "")
    
    def _get_content_extraction_guidance(self, relationship_type: str) -> str:
        """Get specific guidance for extracting content based on relationship type."""
        guidance = {
            'integration_expansion': """
FOR INTEGRATION EXPANSION POSTS:
- Primary focus: **🔗 Integration Points** section
- Secondary focus: **🏗️ Architecture & Design** section
- Supporting details: **💻 Code Implementation** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Specific APIs or services integrated
- Data flow and connection patterns
- System architecture decisions
- Technical integration challenges solved
- How this connects to or extends previous integrations

Create content that shows how systems connect and communicate, focusing on the technical architecture and data flow aspects.
            """,
            'implementation_evolution': """
FOR IMPLEMENTATION EVOLUTION POSTS:
- Primary focus: **🔧 My Solution** section
- Secondary focus: **💻 Code Implementation** section
- Supporting details: **🎨 What Makes This Special** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Evolution of implementation approach
- Technical decisions and trade-offs made
- Code patterns and architectural improvements
- Lessons learned from previous implementations
- How the approach refined over time

Create content that shows the journey of implementation improvement, focusing on technical evolution and learning.
            """,
            'system_enhancement': """
FOR SYSTEM ENHANCEMENT POSTS:
- Primary focus: **🏆 The Impact/Result** section
- Secondary focus: **🎨 What Makes This Special** section
- Supporting details: **💻 Code Implementation** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Specific performance improvements achieved
- Scalability or capability enhancements
- Measurable optimization results
- Unique performance-focused innovations
- How this builds upon previous system capabilities

Create content that emphasizes improvements, optimizations, and enhanced capabilities with concrete metrics.
            """,
            'problem_solution_chain': """
FOR PROBLEM-SOLUTION CHAIN POSTS:
- Primary focus: **⚡ The Problem** section
- Secondary focus: **🔧 My Solution** section
- Supporting details: **🚧 Challenges & Solutions** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Specific problems identified and addressed
- Root cause analysis and investigation
- Solution approach and methodology
- Challenges overcome during implementation
- How this problem relates to previous issues solved

Create content that shows logical problem-solving progression, focusing on the analytical and solution-building process.
            """,
            'feature_milestone': """
FOR FEATURE MILESTONE POSTS:
- Primary focus: **🎯 What I Built** section
- Secondary focus: **📊 Specific Use Cases & Scenarios** section
- Supporting details: **🏆 The Impact/Result** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Complete feature description and capabilities
- Real-world use cases and applications
- User impact and practical benefits
- Feature completion and milestone achievement
- How this feature builds upon previous work

Create content that celebrates feature completion and demonstrates practical value and real-world impact.
            """,
            'deployment_experience': """
FOR DEPLOYMENT EXPERIENCE POSTS:
- Primary focus: **🔮 Future Implications** section
- Secondary focus: **📊 Specific Use Cases & Scenarios** section
- Supporting details: **💡 Key Lessons Learned** section
- Reference: **🔄 How This Connects to Previous Work** section

Extract and combine:
- Real-world deployment insights and outcomes
- User feedback and usage patterns
- Operational lessons learned
- Production performance and reliability
- Future possibilities enabled by deployment

Create content that shares real-world deployment insights, user feedback, and operational learning experiences.
            """
        }
        return guidance.get(relationship_type, "")
    
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
AUDIENCE: Business Owner/General (people who might be interested in or benefit from automation and tech solutions)

FEATURE-FIRST STORYTELLING:
- Focus your post on the specific feature you implemented. If you mention any tools, always explain them in relation to the feature and its impact. Do not make the tool the main subject.

FORMATTING GUIDELINES:
- Use 2-4 relevant emojis to enhance readability and engagement.
- Format your post for Facebook:
    - Start with an engaging hook
    - Use line breaks for readability
    - Keep paragraphs short (2-3 sentences)
    - Use bullet points or numbered lists if helpful
- Do not include fictional or imaginary scenarios—stick to real features and outcomes.
- Use authentic, real-world examples from your actual implementation.

TECHNICAL LANGUAGE BALANCE:
- You may use up to 3 technical terms per post, but each must be immediately explained in simple, everyday language. For example:
    - "API (a way for different software to talk to each other)"
    - "Database (where all the information is stored)"
    - "Machine learning (where the computer learns patterns)"
- Avoid technical jargon without explanation.

CONTENT GUIDELINES:
- Write from YOUR perspective about YOUR own projects and the features you are implementing.
- Share what YOU built for YOUR own use, not for others.
- Focus on what the feature does and why YOU needed it.
- Mention the practical benefits YOU get from it.
- Keep it conversational but professional.
- Avoid excessive examples or analogies.

LANGUAGE STYLE:
- "I built this feature to help me..."
- "This saves me time because..."
- "I needed something that could..."
- "Now I can..."
- "The result is..."

OUTPUT FORMAT:
TONE: [chosen tone, e.g., 🎉 Finished & Proud]
POST: [the Facebook post content]
REASON: [briefly explain why you chose this tone and how it fits the content/audience]

End your post with a genuine question or prompt to encourage engagement.

Remember: You're sharing YOUR development journey and achievements, not selling services to others.
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
ENHANCED CONTENT VARIATION STRATEGY:
- Create FUNDAMENTALLY different content, not just rephrased versions
- Use completely different narrative structures and approaches
- Introduce new technical details, business benefits, or use cases
- Focus on aspects that haven't been covered in previous posts
- Use different examples, analogies, and metaphors
- Vary writing style: problem-focused vs solution-focused vs result-focused
"""
        
        # Relationship-specific variation strategies
        variation_strategies = {
            'Integration Expansion': base_instructions + """
INTEGRATION EXPANSION FOCUS:
- Reference your previous post and expand on API connections or data flows
- Discuss how systems connect differently than what you shared before
- Focus on integration challenges or solutions not mentioned in previous post
- Explore different connection patterns or communication methods
- Show how this feature integrates with other systems you've built
""",
            
            'Implementation Evolution': base_instructions + """
IMPLEMENTATION EVOLUTION FOCUS:
- Reference your previous post and show how the approach evolved
- Discuss refinements or optimizations made since your last post
- Focus on architectural improvements or code changes
- Show lessons learned from the implementation you shared before
- Reveal different challenges encountered after your initial post
""",
            
            'System Enhancement': base_instructions + """
SYSTEM ENHANCEMENT FOCUS:
- Reference your previous post and focus on performance improvements
- Discuss scalability or capability enhancements since your last post
- Show measurable improvements or optimizations made
- Focus on system upgrades or enhanced functionality
- Reveal performance insights discovered after your previous post
""",
            
            'Problem-Solution Chain': base_instructions + """
PROBLEM-SOLUTION CHAIN FOCUS:
- Reference problems or solutions mentioned in your previous post
- Connect this new solution to issues you identified before
- Show logical progression from your previous post's challenges
- Focus on related problems that emerged from your last solution
- Reveal solutions that address concerns raised in your previous post
""",
            
            'Feature Milestone': base_instructions + """
FEATURE MILESTONE FOCUS:
- Reference your previous post and present this as the next milestone
- Show completion or advancement from what you shared before
- Focus on capabilities enabled by completing your previous feature
- Discuss what this milestone makes possible beyond your last post
- Reveal outcomes or results from implementing your previous feature
""",
            
            'Deployment Experience': base_instructions + """
DEPLOYMENT EXPERIENCE FOCUS:
- Reference your previous post and share real-world deployment insights
- Discuss production experience with what you shared before
- Focus on user feedback or operational insights from your previous feature
- Show how the deployed system performs differently than expected
- Reveal lessons learned from using the system you posted about
""",
            
            'AI Decide': base_instructions + """
AI DECIDE FOCUS:
- Let AI determine the most different and complementary approach
- Combine multiple strategies for maximum content variation
- Ensure the new post offers completely unique value and perspective
- Focus on the most unexplored aspects of the project or topic
- Create content that fills gaps left by previous posts
"""
        }
        
        return variation_strategies.get(relationship_type, base_instructions)
    
    def _add_anti_repetition_context(self, markdown_content: str, previous_posts: List[Dict], 
                                   relationship_type: str) -> str:
        """Add enhanced context to prevent content repetition."""
        if not previous_posts:
            return ""
        
        # Extract comprehensive elements from previous posts
        previous_content = []
        previous_openings = []
        previous_examples = []
        previous_conclusions = []
        previous_metaphors = []
        previous_questions = []
        previous_problems = []
        previous_solutions = []
        previous_benefits = []
        
        for post in previous_posts[-3:]:  # Look at last 3 posts
            content = post.get('content', '')
            if content:
                # Split into sentences and paragraphs
                sentences = content.split('.')
                paragraphs = content.split('\n\n')
                
                # Get opening sentences (first 3 sentences)
                if len(sentences) >= 3:
                    opening = '. '.join(sentences[:3])
                    previous_openings.append(opening.strip())
                
                # Get conclusions (last 3 sentences)
                if len(sentences) >= 3:
                    conclusion = '. '.join(sentences[-3:])
                    previous_conclusions.append(conclusion.strip())
                
                # Extract examples and analogies
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['example', 'like', 'such as', 'instance', 'similar to', 'it\'s like']):
                        previous_examples.append(sentence.strip())
                    if any(word in sentence.lower() for word in ['like having', 'imagine', 'think of', 'picture']):
                        previous_metaphors.append(sentence.strip())
                
                # Extract questions
                for sentence in sentences:
                    if sentence.strip().endswith('?'):
                        previous_questions.append(sentence.strip())
                
                # Extract problem statements
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['problem', 'issue', 'challenge', 'frustrating', 'broken']):
                        previous_problems.append(sentence.strip())
                
                # Extract solution statements
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['solution', 'fixed', 'solved', 'built', 'created']):
                        previous_solutions.append(sentence.strip())
                
                # Extract benefit statements
                for sentence in sentences:
                    if any(word in sentence.lower() for word in ['now', 'result', 'benefit', 'improvement', 'better']):
                        previous_benefits.append(sentence.strip())
                
                # Extract key phrases (first 8 sentences for general context)
                previous_content.extend(sentences[:8])
        
        if not any([previous_content, previous_openings, previous_examples, previous_metaphors, previous_questions, previous_problems, previous_solutions, previous_benefits]):
            return ""
        
        # Create enhanced anti-repetition instructions
        anti_repetition = f"""
STRICT ANTI-REPETITION REQUIREMENTS:

**COMPLETELY AVOID THESE PREVIOUS OPENINGS:**
{'; '.join(previous_openings[:3]) if previous_openings else 'None'}

**NEVER REPEAT THESE EXAMPLES/ANALOGIES:**
{'; '.join(previous_examples[:3]) if previous_examples else 'None'}

**AVOID THESE METAPHORS:**
{'; '.join(previous_metaphors[:3]) if previous_metaphors else 'None'}

**DON'T REPEAT THESE QUESTIONS:**
{'; '.join(previous_questions[:3]) if previous_questions else 'None'}

**AVOID THESE PROBLEM STATEMENTS:**
{'; '.join(previous_problems[:3]) if previous_problems else 'None'}

**DON'T REPEAT THESE SOLUTION APPROACHES:**
{'; '.join(previous_solutions[:3]) if previous_solutions else 'None'}

**AVOID THESE BENEFIT STATEMENTS:**
{'; '.join(previous_benefits[:3]) if previous_benefits else 'None'}

**FORBIDDEN PHRASES AND PATTERNS:**
{'; '.join([content.strip() for content in previous_content[:8]]) if previous_content else 'None'}

**MANDATORY VARIATION RULES:**
1. Use COMPLETELY different opening sentences and hooks - NO SIMILAR PATTERNS
2. Introduce ENTIRELY NEW examples, analogies, and metaphors  
3. Focus on DIFFERENT aspects/features/benefits not previously mentioned
4. Use DIFFERENT vocabulary, sentence structures, and writing patterns
5. Provide NEW insights, perspectives, or angles not covered before
6. Reference different technical implementations or business impacts
7. DO NOT repeat the same accomplishments, features, or outcomes
8. DO NOT use similar success metrics, results, or comparisons
9. Start with a completely different narrative approach and voice
10. If building on previous posts, ADD NEW VALUE, don't repeat existing value
11. Use different types of questions than previously asked
12. Employ different storytelling techniques and structures
13. Focus on different emotions or motivations
14. Use completely different examples from different industries/contexts
15. Avoid similar conclusions or calls-to-action

**FOLLOW-UP POST REQUIREMENTS:**
- Reference your own previously generated and approved posts naturally
- Build upon what YOU shared in your previous post, not assumed prior knowledge
- Use phrases like "In my last post, I shared..." or "Building on what I posted about..."
- Connect this content to the specific things you mentioned in your previous post
- Show progression from your previous post's content
- Reference specific details from your previous post to create genuine continuity

**CONTENT FOCUS STRATEGY - FIND COMPLETELY NEW ANGLES:**
Instead of repeating what was already shared about this project, focus on:
- Different technical components or modules not previously discussed
- Alternative use cases, applications, or scenarios
- Deeper technical details or architectural decisions
- Different user perspectives, stakeholder benefits, or business impacts
- Related insights, lessons learned, or unexpected discoveries
- Future developments, improvements, or planned enhancements
- Broader industry context, trends, or implications
- Different problem-solving approaches or methodologies
- Unique challenges encountered or overcome
- Different success metrics or measurable outcomes
- Alternative implementation strategies or technical choices
- Different user feedback or real-world usage patterns
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
- Ensure each post adds new personal value while maintaining series coherence
- Keep the business-friendly language consistent across all posts in the series
- Focus on different practical benefits or use cases in each post to avoid repetition
- Never mention time frames or duration across the series
- Present each feature as a completed achievement that adds personal value

**CONTENT PROCESSING FOR SERIES:**
- Each markdown file represents a completed feature implementation
- Extract unique practical value from each feature
- Ignore any file naming patterns or dates
- Focus on different practical benefits or use cases of each feature
- Present features as finished accomplishments that solve specific personal problems

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
- You are processing enhanced development documentation from individual .mdc files
- Each file follows a structured format with specific sections (🎯 What I Built, ⚡ The Problem, etc.)
- Files contain rich technical and contextual information across multiple sections
- Focus on extracting and combining information from relevant sections based on the relationship type
- These are feature implementations with comprehensive documentation for varied content creation
- Content represents completed features with detailed context for multiple content angles

**CRITICAL PERSONAL PROJECT PERSPECTIVE:**
These are PERSONAL features that I built to solve MY OWN problems. I am sharing specific features and improvements I implemented for myself, not creating services for others.

✅ CORRECT PERSPECTIVE:
- "I built this tool to solve my own problem with..."
- "I needed a way to handle my own..."
- "This helps me manage my own..."
- "I created this for my own use because..."

❌ INCORRECT PERSPECTIVE:
- "I built this for farmers to..."
- "This helps farmers with..."
- "Farmers can now..."
- "This system serves farmers by..."

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

This is YOUR personal feature update that YOU worked on YOURSELF. Share it authentically in first person without time frames.

**CRITICAL FEATURE SHARING APPROACH:**
- Focus on what the feature does and why it's useful
- Share the specific improvement or capability you built
- Explain the problem it solves and the benefits it provides
- Avoid making it sound like you're documenting an entire project journey
- Present it as "I built this feature..." not "I'm working on this project..."

**FEATURE-FIRST STORYTELLING:**
- Focus primarily on FEATURES you implemented, not the tools benefiting from these features
- When mentioning tools, always contextualize them within the feature discussion
- Lead with what the feature does and accomplishes, not what technology it uses
- Share the problem the feature solves and the impact it has

**FORMATTING GUIDELINES:**
- Use strategic emojis (2-4 per post) to enhance readability and engagement
- Format for Facebook algorithm optimization:
  - Use line breaks for readability
  - Include engaging hooks in the first line
  - Use bullet points or numbered lists when appropriate
  - Keep paragraphs short (2-3 sentences max)
- NO fictional scenarios or imaginary stories - stick to what was actually built
- Use authentic, real-world examples from your actual implementation

**TECHNICAL LANGUAGE BALANCE:**
- Maximum 3 technical terms per post
- Always explain technical terms in simple, layman's terms immediately after use
- Good examples:
  - "I built an API (a way for different software to talk to each other) that..."
  - "The database (where all the information is stored) now..."
  - "I used machine learning (where the computer learns patterns) to..."
- Avoid technical jargon without explanation

**Content Processing Instructions:**
- The markdown content represents a completed feature implementation with rich documentation
- Extract information from specific sections based on relationship type and content focus
- Combine information from multiple sections to create unique content angles
- Ignore any file naming patterns or dates
- Focus on the relevant aspects (technical, business, user impact) as guided by relationship type
- Present the feature as a finished accomplishment with specific details from appropriate sections"""

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
- You are processing enhanced development documentation from individual .mdc files
- Each file follows a structured format with specific sections (🎯 What I Built, ⚡ The Problem, etc.)
- Files contain rich technical and contextual information across multiple sections
- Focus on extracting and combining information from relevant sections based on the relationship type
- These are feature implementations with comprehensive documentation for varied content creation
- Content represents completed features with detailed context for multiple content angles

**CRITICAL PERSONAL PROJECT PERSPECTIVE:**
These are PERSONAL features that I built to solve MY OWN problems. I am sharing specific features and improvements I implemented for myself, not creating services for others.

✅ CORRECT PERSPECTIVE:
- "I built this tool to solve my own problem with..."
- "I needed a way to handle my own..."
- "This helps me manage my own..."
- "I created this for my own use because..."

❌ INCORRECT PERSPECTIVE:
- "I built this for farmers to..."
- "This helps farmers with..."
- "Farmers can now..."
- "This system serves farmers by..."

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

This is YOUR personal feature that YOU built for YOURSELF. Share it authentically in first person without time frames.

**CRITICAL FEATURE SHARING APPROACH:**
- Focus on what the feature does and why it's useful
- Share the specific improvement or capability you built
- Explain the problem it solves and the benefits it provides
- Avoid making it sound like you're documenting an entire project journey
- Present it as "I built this feature..." not "I'm working on this project..."

**FEATURE-FIRST STORYTELLING:**
- Focus primarily on FEATURES you implemented, not the tools benefiting from these features
- When mentioning tools, always contextualize them within the feature discussion
- Lead with what the feature does and accomplishes, not what technology it uses
- Share the problem the feature solves and the impact it has

**FORMATTING GUIDELINES:**
- Use strategic emojis (2-4 per post) to enhance readability and engagement
- Format for Facebook algorithm optimization:
  - Use line breaks for readability
  - Include engaging hooks in the first line
  - Use bullet points or numbered lists when appropriate
  - Keep paragraphs short (2-3 sentences max)
- NO fictional scenarios or imaginary stories - stick to what was actually built
- Use authentic, real-world examples from your actual implementation

**TECHNICAL LANGUAGE BALANCE:**
- Maximum 3 technical terms per post
- Always explain technical terms in simple, layman's terms immediately after use
- Good examples:
  - "I built an API (a way for different software to talk to each other) that..."
  - "The database (where all the information is stored) now..."
  - "I used machine learning (where the computer learns patterns) to..."
- Avoid technical jargon without explanation

---

**CRITICAL LANGUAGE REQUIREMENT:**
Your audience includes busy business owners who may not be technical. Write at a 15-year-old reading level using ONLY everyday language that anyone can understand.

**MANDATORY LANGUAGE SIMPLIFICATION:**
Replace ALL technical terms with simple, everyday words:
- "API integration" → "connecting different apps"
- "database" → "digital filing cabinet" or "stored information"
- "automated workflow" → "tasks that run by themselves"
- "authentication" → "login system" or "security check"
- "backend" → "behind-the-scenes part"
- "frontend" → "the part users see"
- "cloud hosting" → "storing files online"
- "algorithm" → "step-by-step process"
- "optimization" → "making it work better"
- "deployment" → "putting it online"
- "server" → "computer that stores the website"
- "repository" → "project folder"
- "framework" → "pre-built tools"
- "library" → "collection of pre-written code"
- "configuration" → "settings"
- "implementation" → "building it"
- "functionality" → "what it does"
- "integration" → "connecting"
- "interface" → "how you interact with it"
- "module" → "part of the system"
- "protocol" → "set of rules"
- "infrastructure" → "the foundation"
- "scalability" → "ability to grow"
- "migration" → "moving from one system to another"
- "validation" → "checking"
- "synchronization" → "keeping things updated"
- "cache" → "temporary storage"
- "webhook" → "automatic notification"
- "endpoint" → "connection point"

**ADDITIONAL SIMPLIFICATION RULES:**
- Use "app" instead of "application" or "software"
- Use "code" instead of "codebase" or "source code"
- Use "fix" instead of "debug" or "troubleshoot"
- Use "test" instead of "validate" or "verify"
- Use "update" instead of "refactor" or "optimize"
- Use "connect" instead of "integrate" or "sync"
- Use "store" instead of "persist" or "cache"
- Use "send" instead of "transmit" or "deploy"
- Use "check" instead of "validate" or "authenticate"
- Use "run" instead of "execute" or "process"

They want to know:
- What problem this solves (in simple terms)
- How it works (explained like talking to a friend)
- Why it matters for their business
- What realistic results they can expect

---

### ✍️ Your task:

Generate a conversational Facebook post from the content provided. Write it naturally, like you're explaining something useful to a friend who runs a small business but isn't tech-savvy.

**Use ONLY simple, everyday language that a 15-year-old would understand.**

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
- More detailed examples (in simple terms)
- Additional context about the problem
- Specific implementation details (explained simply)
- More comprehensive results or impact
- Personal insights and lessons learned

**Content Processing Instructions:**
- The markdown content represents a completed feature implementation with rich documentation
- Extract information from specific sections based on relationship type and content focus
- Combine information from multiple sections to create unique content angles
- Ignore any file naming patterns or dates
- Focus on the relevant aspects (technical, business, user impact) as guided by relationship type
- Present the feature as a finished accomplishment with specific details from appropriate sections

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

**IMPORTANT:** Keep the language natural and conversational. Avoid hype, excessive enthusiasm, or sales-like language. Focus on practical value and honest communication. Write as if YOU built this project yourself without mentioning when or how long it took. Remember: if a 15-year-old can't understand it, rewrite it in simpler terms."""

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
                       relationship_type: Optional[str] = None, parent_post_id: Optional[str] = None,
                       audience_type: Optional[str] = None, length_preference: Optional[str] = None) -> Dict:
        """
        Regenerate a Facebook post with feedback and context awareness.
        
        Args:
            markdown_content: The markdown content to transform
            feedback: Feedback to consider for regeneration
            tone_preference: Optional tone preference from user
            session_context: Context from previous posts in the series
            previous_posts: List of previous posts in the series
            relationship_type: How this post relates to previous posts
            parent_post_id: ID of the parent post to reference
            audience_type: The target audience ('business' or 'technical')
            
        Returns:
            Dict containing the regenerated post, tone used, and metadata
        """
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        try:
            # Determine if this is a context-aware regeneration
            is_context_aware = session_context or previous_posts or relationship_type
            
            if is_context_aware:
                # Build context-aware regeneration prompt
                regeneration_prompt = self._build_context_aware_regeneration_prompt(
                    markdown_content, feedback, tone_preference, session_context, 
                    previous_posts, relationship_type, parent_post_id, audience_type, length_preference
                )
                system_prompt = self._get_context_aware_system_prompt(audience_type)
            else:
                # Use original regeneration prompt
                regeneration_prompt = self._build_regeneration_prompt(markdown_content, feedback, tone_preference, audience_type, length_preference)
                system_prompt = self._get_system_prompt(audience_type)
            
            generated_content = self._generate_content(
                system_prompt, regeneration_prompt, temperature=0.8, max_tokens=4000
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
                'parent_post_id': parent_post_id,
                'audience_type': audience_type
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error regenerating Facebook post: {str(e)}")
    
    def _build_regeneration_prompt(self, markdown_content: str, feedback: str, tone_preference: Optional[str] = None, audience_type: Optional[str] = None, length_preference: Optional[str] = None) -> str:
        """Build prompt for regeneration with feedback."""
        prompt_parts = []
        
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)
        
        prompt_parts.append("Please regenerate the Facebook post with the following feedback in mind:")
        prompt_parts.append(f"FEEDBACK: {feedback}")
        
        if tone_preference:
            prompt_parts.append(f"Please use the '{tone_preference}' tone style for this regeneration.")
        
        # Add length preference if provided
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("Please create a SHORT-FORM post (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("Please create a LONG-FORM post (4-6 paragraphs, detailed and comprehensive).")
        
        prompt_parts.append("Here is the original markdown content:")
        prompt_parts.append("---")
        prompt_parts.append(markdown_content)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts)
    
    def _build_context_aware_regeneration_prompt(self, markdown_content: str, feedback: str, 
                                               tone_preference: Optional[str], session_context: Optional[str],
                                               previous_posts: Optional[List[Dict]], relationship_type: Optional[str],
                                               parent_post_id: Optional[str], audience_type: Optional[str] = None,
                                               length_preference: Optional[str] = None) -> str:
        """Build context-aware regeneration prompt."""
        prompt_parts = []
        
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)
        
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
        
        # Add length preference if specified
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("LENGTH PREFERENCE: Create a SHORT-FORM post (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("LENGTH PREFERENCE: Create a LONG-FORM post (4-6 paragraphs, detailed and comprehensive).")
        
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

    def generate_continuation_post(self, previous_post_text: str, add_chichewa_humor: bool = False, audience_type: Optional[str] = None) -> Dict:
        """
        Generate a follow-up Facebook post based on the text of a previous post.
        """
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        try:
            # Use the same system prompt as regular posts for consistent format
            system_prompt = self._get_system_prompt(audience_type)
            
            # Build a continuation prompt that maintains the same format
            full_prompt = self._build_continuation_prompt(previous_post_text, audience_type)

            generated_content = self._generate_content(
                system_prompt, full_prompt, temperature=0.7, max_tokens=4000
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
                'audience_type': audience_type
            }

            # Add Chichewa humor if requested
            if add_chichewa_humor:
                result['post_content'] = self.chichewa_integrator.integrate_phrases(result['post_content'])
            
            return result
        except Exception as e:
            raise Exception(f"Error generating continuation post: {str(e)}")

    def _build_continuation_prompt(self, previous_post_text: str, audience_type: Optional[str] = None) -> str:
        """Build the prompt for generating a continuation post."""
        prompt_parts = []
        
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        # Add audience instructions for consistency
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)

        prompt_parts.append(
            "You are creating a follow-up Facebook post that builds naturally on a previous post. "
            "Your goal is to create a new, original post that feels like the next chapter in the story."
        )
        
        prompt_parts.append(
            "FOLLOW-UP POST INSTRUCTIONS:\n"
            "1. **Analyze the Previous Post**: Understand the topic, tone, and style of the previous post.\n"
            "2. **Generate a Natural Follow-Up**: Write a new post that builds on the previous one - do NOT summarize or repeat it.\n"
            "3. **Add New Value**: Introduce a new perspective, deeper insight, lesson learned, or next step.\n"
            "4. **Use Connection Phrases**: Reference the previous post naturally with phrases like:\n"
            "   - 'In my last post...'\n"
            "   - 'Building on what I shared...'\n"
            "   - 'Following up on...'\n"
            "   - 'After sharing about...'\n"
            "5. **Maintain Consistency**: Match the tone and voice for series coherence.\n"
            "6. **Keep Same Format**: Use the same 400-600 word structure as the original post.\n"
            "7. **Same Language Level**: Use the same simple, clear language as the previous post."
        )
        
        prompt_parts.append("PREVIOUS POST TO BUILD ON:")
        prompt_parts.append("---")
        prompt_parts.append(previous_post_text)
        prompt_parts.append("---")
        
        return "\n\n".join(prompt_parts) 

    def edit_post(self, original_post_content: str, edit_instructions: str, 
                  original_tone: str = None, original_markdown: str = None,
                  session_context: Optional[str] = None, previous_posts: Optional[List[Dict]] = None,
                  relationship_type: Optional[str] = None, parent_post_id: Optional[str] = None,
                  audience_type: Optional[str] = None, length_preference: Optional[str] = None) -> Dict:
        """
        Edit an existing Facebook post with specific instructions.
        
        Args:
            original_post_content: The existing post content to edit
            edit_instructions: Specific instructions for what to change
            original_tone: The tone used in the original post
            original_markdown: The original markdown content (for context)
            session_context: Context from previous posts in the series
            previous_posts: List of previous posts in the series
            relationship_type: How this post relates to previous posts
            parent_post_id: ID of the parent post to reference
            audience_type: The target audience ('business' or 'technical')
            length_preference: Length preference for the edited post
            
        Returns:
            Dict containing the edited post, tone used, and metadata
        """
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        try:
            # Determine if this is a context-aware edit
            is_context_aware = bool(session_context or previous_posts or relationship_type)
            
            if is_context_aware:
                # Build context-aware edit prompt
                edit_prompt = self._build_context_aware_edit_prompt(
                    original_post_content, edit_instructions, original_tone, original_markdown,
                    session_context, previous_posts, relationship_type, parent_post_id, 
                    audience_type, length_preference
                )
                system_prompt = self._get_context_aware_system_prompt(audience_type)
            else:
                # Use simple edit prompt
                edit_prompt = self._build_edit_prompt(
                    original_post_content, edit_instructions, original_tone, original_markdown,
                    audience_type, length_preference
                )
                system_prompt = self._get_system_prompt(audience_type)
            
            generated_content = self._generate_content(
                system_prompt, edit_prompt, temperature=0.7, max_tokens=4000
            )
            
            parsed_response = self._parse_ai_response(generated_content)
            
            result = {
                'post_content': parsed_response.get('post', generated_content),
                'tone_used': parsed_response.get('tone', original_tone or 'Unknown'),
                'tone_reason': parsed_response.get('reason', f'Edited from {original_tone or "Unknown"} tone'),
                'generated_at': datetime.now().isoformat(),
                'model_used': self.model,
                'original_markdown': original_markdown,
                'edited_from_content': original_post_content,
                'edit_instructions': edit_instructions,
                'is_edit': True,
                'is_context_aware': is_context_aware,
                'relationship_type': relationship_type,
                'parent_post_id': parent_post_id,
                'audience_type': audience_type
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Error editing Facebook post: {str(e)}")
    
    def _build_edit_prompt(self, original_post_content: str, edit_instructions: str, 
                          original_tone: str = None, original_markdown: str = None,
                          audience_type: Optional[str] = None, length_preference: Optional[str] = None) -> str:
        """Build prompt for editing an existing post."""
        prompt_parts = []
        
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)
        
        prompt_parts.append("You are editing an existing Facebook post. Please make the requested changes while maintaining the overall structure and quality.")
        
        # Add the original post content
        prompt_parts.append("ORIGINAL POST CONTENT:")
        prompt_parts.append("---")
        prompt_parts.append(original_post_content)
        prompt_parts.append("---")
        
        # Add edit instructions
        prompt_parts.append("EDIT INSTRUCTIONS:")
        prompt_parts.append(f"{edit_instructions}")
        
        # Add original tone information if available
        if original_tone:
            prompt_parts.append(f"ORIGINAL TONE: {original_tone}")
            prompt_parts.append("Please maintain this tone unless the edit instructions specifically request a tone change.")
        
        # Add length preference if provided
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("LENGTH PREFERENCE: Make the edited post SHORT-FORM (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("LENGTH PREFERENCE: Make the edited post LONG-FORM (4-6 paragraphs, detailed and comprehensive).")
        
        # Add original markdown context if available
        if original_markdown:
            prompt_parts.append("ORIGINAL MARKDOWN CONTEXT:")
            prompt_parts.append("---")
            prompt_parts.append(original_markdown)
            prompt_parts.append("---")
        
        prompt_parts.append("""
EDITING GUIDELINES:
1. Make ONLY the changes requested in the edit instructions
2. Preserve the overall structure and flow of the original post
3. Maintain the same tone and voice unless specifically asked to change
4. Keep the same level of detail and engagement
5. Ensure the edited post flows naturally and reads well
6. Preserve any specific examples, analogies, or technical details that weren't mentioned in the edit instructions
7. Make targeted, surgical edits rather than rewriting the entire post

Please provide the edited post content:""")
        
        return "\n\n".join(prompt_parts)
    
    def _build_context_aware_edit_prompt(self, original_post_content: str, edit_instructions: str,
                                       original_tone: str = None, original_markdown: str = None,
                                       session_context: Optional[str] = None, previous_posts: Optional[List[Dict]] = None, 
                                       relationship_type: Optional[str] = None, parent_post_id: Optional[str] = None,
                                       audience_type: Optional[str] = None, length_preference: Optional[str] = None) -> str:
        """Build context-aware edit prompt."""
        prompt_parts = []
        
        # Default to business audience for better language simplification
        if audience_type is None:
            audience_type = 'business'
            
        if audience_type:
            audience_instructions = self._get_audience_instructions(audience_type)
            prompt_parts.append(audience_instructions)
        
        prompt_parts.append("You are editing an existing Facebook post within a series. Please make the requested changes while maintaining series coherence and context.")
        
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
        
        # Add the original post content
        prompt_parts.append("ORIGINAL POST CONTENT TO EDIT:")
        prompt_parts.append("---")
        prompt_parts.append(original_post_content)
        prompt_parts.append("---")
        
        # Add edit instructions
        prompt_parts.append("EDIT INSTRUCTIONS:")
        prompt_parts.append(f"{edit_instructions}")
        
        # Add original tone information if available
        if original_tone:
            prompt_parts.append(f"ORIGINAL TONE: {original_tone}")
            prompt_parts.append("Please maintain this tone unless the edit instructions specifically request a tone change.")
        
        # Add length preference if provided
        if length_preference:
            if length_preference == 'short':
                prompt_parts.append("LENGTH PREFERENCE: Make the edited post SHORT-FORM (2-3 paragraphs maximum, concise and to the point).")
            elif length_preference == 'long':
                prompt_parts.append("LENGTH PREFERENCE: Make the edited post LONG-FORM (4-6 paragraphs, detailed and comprehensive).")
        
        # Add original markdown context if available
        if original_markdown:
            prompt_parts.append("ORIGINAL MARKDOWN CONTEXT:")
            prompt_parts.append("---")
            prompt_parts.append(original_markdown)
            prompt_parts.append("---")
        
        # Add content variation strategy for series
        if relationship_type:
            variation_strategy = self._get_content_variation_strategy(relationship_type)
            prompt_parts.append(variation_strategy)
        
        prompt_parts.append("""
CONTEXT-AWARE EDITING GUIDELINES:
1. Make ONLY the changes requested in the edit instructions
2. Preserve the overall structure and flow of the original post
3. Maintain series coherence with previous posts
4. Keep the same tone and voice unless specifically asked to change
5. Ensure the edited post maintains its relationship to other posts in the series
6. Preserve any specific examples, analogies, or technical details that weren't mentioned in the edit instructions
7. Make targeted, surgical edits rather than rewriting the entire post
8. Consider how the edited post fits within the broader series narrative

Please provide the edited post content:""")
        
        return "\n\n".join(prompt_parts) 