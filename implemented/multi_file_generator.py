"""
MultiFileContentGenerator: Handles content generation with cross-file awareness.

This class is responsible for generating content while maintaining awareness of multiple
input files, their relationships, and the overall narrative structure of the project.
"""

from typing import Dict, List, Optional
import logging
from datetime import datetime
from .ai_service import AIContentService

class MultiFileContentGenerator:
    """Generates content with full multi-file awareness."""
    
    def __init__(
        self,
        ai_service: Optional[AIContentService] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the MultiFileContentGenerator.
        
        Args:
            ai_service: Optional AIContentService instance
            logger: Optional logger instance for tracking operations
        """
        self.logger = logger or logging.getLogger(__name__)
        self.ai_service = ai_service or AIContentService()
        
    async def generate_with_multi_file_context(
        self, 
        target_file: Dict, 
        all_files: List[Dict], 
        strategy: Dict,
        narrative_position: int
    ) -> Dict:
        """Generate content with cross-file awareness.
        
        Args:
            target_file: Current file being processed
            all_files: List of all files in the project
            strategy: Content strategy configuration
            narrative_position: Position in the narrative sequence
            
        Returns:
            Dict containing generated content and metadata
        """
        try:
            # Build the context-aware prompt
            prompt = self.build_multi_file_prompt(
                target_file, 
                all_files, 
                strategy, 
                narrative_position
            )
            
            # Generate explicit references if not first post
            references = []
            if narrative_position > 0:
                previous_posts = self._get_previous_posts(all_files, narrative_position)
                references = self.generate_explicit_references(target_file, previous_posts)
            
            # Generate subtle connections
            connections = self.generate_subtle_connections(target_file, all_files)
            
            # Generate content using AI
            generated_content = await self._generate_ai_content(
                prompt,
                references,
                connections,
                target_file.get('file_phase', 'unknown')
            )
            
            # Ensure narrative continuity
            final_content = self.ensure_narrative_continuity(
                self._get_previous_posts(all_files, narrative_position),
                generated_content
            )
            
            return {
                "content": final_content,
                "references": references,
                "connections": connections,
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "narrative_position": narrative_position,
                    "source_file": target_file.get("file_id"),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            raise
            
    def build_multi_file_prompt(
        self, 
        target_file: Dict, 
        all_files: List[Dict], 
        strategy: Dict,
        narrative_position: int
    ) -> str:
        """Build context-aware prompt for multi-file generation.
        
        Args:
            target_file: Current file being processed
            all_files: List of all files in the project
            strategy: Content strategy configuration
            narrative_position: Position in the narrative sequence
            
        Returns:
            Constructed prompt string
        """
        # Extract key information
        project_theme = strategy.get('project_theme', '')
        narrative_arc = strategy.get('narrative_arc', '')
        content_threads = strategy.get('content_threads', [])
        recommended_tone = strategy.get('recommended_sequence', [])[narrative_position].get('tone', 'neutral')
        
        # Build context sections
        project_context = f"""
Project Overview:
- Theme: {project_theme}
- Narrative Arc: {narrative_arc}
- Current Position: {narrative_position + 1} of {len(strategy.get('recommended_sequence', []))}
"""

        file_context = f"""
Current File Context:
- Phase: {target_file.get('file_phase', 'unknown')}
- Key Themes: {', '.join(target_file.get('key_themes', []))}
- Technical Elements: {', '.join(target_file.get('technical_elements', []))}
- Business Impact: {', '.join(target_file.get('business_impact', []))}
"""

        # Build narrative context from previous posts
        previous_posts = self._get_previous_posts(all_files, narrative_position)
        narrative_context = "Previous Posts Context:\n"
        if previous_posts:
            for post in previous_posts:
                narrative_context += f"- {post.get('file_phase', 'unknown')}: {', '.join(post.get('key_themes', []))}\n"
        else:
            narrative_context += "- This is the first post in the series\n"

        # Build thematic connections
        thematic_context = "Thematic Connections:\n"
        for thread in content_threads:
            if any(theme in target_file.get('key_themes', []) for theme in thread.get('themes', [])):
                thematic_context += f"- {thread.get('description', '')}\n"

        # Combine all contexts into final prompt
        prompt = f"""
Generate a Facebook post about this development milestone with the following context:

{project_context}

{file_context}

{narrative_context}

{thematic_context}

Content Guidelines:
1. Use a {recommended_tone} tone
2. Focus on the current file's key themes while maintaining project context
3. Make natural references to previous posts where relevant
4. Maintain narrative flow within the larger project story
5. Include technical details balanced with business impact
6. Keep the content engaging and authentic

Content Structure:
1. Start with a hook that connects to the project theme
2. Explain the current development milestone
3. Share technical insights and challenges
4. Connect to the broader project narrative
5. End with engagement-focused conclusion

Generate the post now, maintaining authenticity and technical accuracy while engaging the audience.
"""
        
        return prompt
        
    def generate_explicit_references(
        self, 
        current_file: Dict, 
        previous_posts: List[Dict]
    ) -> List[str]:
        """Generate explicit references to previous posts.
        
        Args:
            current_file: Current file being processed
            previous_posts: List of previously generated posts
            
        Returns:
            List of reference strings
        """
        references = []
        current_themes = set(current_file.get('key_themes', []))
        current_technical = set(current_file.get('technical_elements', []))
        
        for prev_post in previous_posts:
            prev_themes = set(prev_post.get('key_themes', []))
            prev_technical = set(prev_post.get('technical_elements', []))
            
            # Find theme overlaps
            shared_themes = current_themes.intersection(prev_themes)
            shared_technical = current_technical.intersection(prev_technical)
            
            if shared_themes or shared_technical:
                reference = {
                    'post_id': prev_post.get('post_id'),
                    'phase': prev_post.get('file_phase'),
                    'connection_type': 'thematic' if shared_themes else 'technical',
                    'shared_elements': list(shared_themes) or list(shared_technical),
                    'reference_text': self._generate_reference_text(
                        prev_post,
                        shared_themes,
                        shared_technical,
                        current_file.get('file_phase')
                    )
                }
                references.append(reference)
        
        # Sort references by relevance (number of shared elements)
        references.sort(
            key=lambda x: len(x['shared_elements']),
            reverse=True
        )
        
        # Limit to most relevant references
        return references[:3]
    
    def _generate_reference_text(
        self,
        prev_post: Dict,
        shared_themes: set,
        shared_technical: set,
        current_phase: str
    ) -> str:
        """Generate natural reference text based on shared elements.
        
        Args:
            prev_post: Previous post data
            shared_themes: Set of shared themes
            shared_technical: Set of shared technical elements
            current_phase: Current development phase
            
        Returns:
            Natural language reference text
        """
        # Phase transition phrases
        phase_transitions = {
            'planning': {
                'implementation': "Moving from planning to implementation",
                'debugging': "From initial plan to debugging",
                'results': "From concept to results"
            },
            'implementation': {
                'debugging': "After implementation",
                'results': "From implementation to results"
            },
            'debugging': {
                'results': "After resolving those challenges"
            }
        }
        
        prev_phase = prev_post.get('file_phase')
        transition = phase_transitions.get(prev_phase, {}).get(current_phase, "Following up on")
        
        if shared_themes:
            themes_text = f"our work on {', '.join(shared_themes)}"
            return f"{transition} {themes_text}"
        elif shared_technical:
            tech_text = f"our use of {', '.join(shared_technical)}"
            return f"{transition} {tech_text}"
        
        return f"{transition} our previous milestone"
        
    def generate_subtle_connections(
        self, 
        current_file: Dict, 
        all_files: List[Dict]
    ) -> List[str]:
        """Generate subtle thematic connections.
        
        Args:
            current_file: Current file being processed
            all_files: List of all files in the project
            
        Returns:
            List of connection strings
        """
        connections = []
        current_themes = set(current_file.get('key_themes', []))
        current_technical = set(current_file.get('technical_elements', []))
        current_impact = set(current_file.get('business_impact', []))
        
        # Collect all themes and their frequencies
        theme_frequency = {}
        tech_frequency = {}
        impact_frequency = {}
        
        for file in all_files:
            for theme in file.get('key_themes', []):
                theme_frequency[theme] = theme_frequency.get(theme, 0) + 1
            for tech in file.get('technical_elements', []):
                tech_frequency[tech] = tech_frequency.get(tech, 0) + 1
            for impact in file.get('business_impact', []):
                impact_frequency[impact] = impact_frequency.get(impact, 0) + 1
        
        # Generate theme-based connections
        for theme in current_themes:
            if theme_frequency.get(theme, 0) > 1:
                connection = self._create_theme_connection(
                    theme,
                    theme_frequency[theme],
                    current_file.get('file_phase')
                )
                if connection:
                    connections.append({
                        'type': 'theme',
                        'element': theme,
                        'frequency': theme_frequency[theme],
                        'connection_text': connection
                    })
        
        # Generate technical connections
        for tech in current_technical:
            if tech_frequency.get(tech, 0) > 1:
                connection = self._create_technical_connection(
                    tech,
                    tech_frequency[tech],
                    current_file.get('file_phase')
                )
                if connection:
                    connections.append({
                        'type': 'technical',
                        'element': tech,
                        'frequency': tech_frequency[tech],
                        'connection_text': connection
                    })
        
        # Generate business impact connections
        for impact in current_impact:
            if impact_frequency.get(impact, 0) > 1:
                connection = self._create_impact_connection(
                    impact,
                    impact_frequency[impact],
                    current_file.get('file_phase')
                )
                if connection:
                    connections.append({
                        'type': 'impact',
                        'element': impact,
                        'frequency': impact_frequency[impact],
                        'connection_text': connection
                    })
        
        # Sort by frequency and limit
        connections.sort(key=lambda x: x['frequency'], reverse=True)
        return connections[:5]  # Limit to top 5 most relevant connections
    
    def _create_theme_connection(
        self,
        theme: str,
        frequency: int,
        phase: str
    ) -> str:
        """Create natural language connection for themes.
        
        Args:
            theme: The theme to create connection for
            frequency: How often this theme appears
            phase: Current development phase
            
        Returns:
            Natural language connection text
        """
        phase_phrases = {
            'planning': [
                f"This {theme} focus continues throughout our project",
                f"We'll see how {theme} evolves as we progress",
                f"{theme} is a key consideration in our design"
            ],
            'implementation': [
                f"Building upon our {theme} foundation",
                f"Implementing our vision for {theme}",
                f"Bringing {theme} to life in code"
            ],
            'debugging': [
                f"Ensuring {theme} works as intended",
                f"Fine-tuning our {theme} implementation",
                f"Optimizing {theme} performance"
            ],
            'results': [
                f"See how {theme} transformed our project",
                f"The impact of {theme} on our success",
                f"How {theme} shaped our solution"
            ]
        }
        
        options = phase_phrases.get(phase, [f"Continuing our work with {theme}"])
        return options[hash(theme) % len(options)]
    
    def _create_technical_connection(
        self,
        tech: str,
        frequency: int,
        phase: str
    ) -> str:
        """Create natural language connection for technical elements.
        
        Args:
            tech: The technical element to create connection for
            frequency: How often this element appears
            phase: Current development phase
            
        Returns:
            Natural language connection text
        """
        phase_phrases = {
            'planning': [
                f"We chose {tech} for its capabilities",
                f"{tech} will be central to our solution",
                f"Planning our {tech} architecture"
            ],
            'implementation': [
                f"Leveraging {tech} in our implementation",
                f"Building with {tech}",
                f"Integrating {tech} into our solution"
            ],
            'debugging': [
                f"Optimizing our {tech} implementation",
                f"Fine-tuning {tech} performance",
                f"Resolving {tech} challenges"
            ],
            'results': [
                f"The benefits of choosing {tech}",
                f"How {tech} delivered results",
                f"The impact of {tech} on our solution"
            ]
        }
        
        options = phase_phrases.get(phase, [f"Working with {tech}"])
        return options[hash(tech) % len(options)]
    
    def _create_impact_connection(
        self,
        impact: str,
        frequency: int,
        phase: str
    ) -> str:
        """Create natural language connection for business impacts.
        
        Args:
            impact: The business impact to create connection for
            frequency: How often this impact appears
            phase: Current development phase
            
        Returns:
            Natural language connection text
        """
        phase_phrases = {
            'planning': [
                f"Aiming to achieve {impact}",
                f"Designing for {impact}",
                f"Planning to deliver {impact}"
            ],
            'implementation': [
                f"Building towards {impact}",
                f"Implementing features for {impact}",
                f"Working to ensure {impact}"
            ],
            'debugging': [
                f"Optimizing for {impact}",
                f"Fine-tuning to maximize {impact}",
                f"Ensuring we deliver {impact}"
            ],
            'results': [
                f"Delivering on our promise of {impact}",
                f"Achieving {impact} through our solution",
                f"How we accomplished {impact}"
            ]
        }
        
        options = phase_phrases.get(phase, [f"Focusing on {impact}"])
        return options[hash(impact) % len(options)]
        
    def ensure_narrative_continuity(
        self, 
        previous_posts: List[Dict], 
        current_content: str
    ) -> str:
        """Ensure narrative flow across posts.
        
        Args:
            previous_posts: List of previously generated posts
            current_content: Currently generated content
            
        Returns:
            Modified content maintaining narrative flow
        """
        if not previous_posts:
            return current_content
            
        # Extract key information from previous posts
        prev_themes = set()
        prev_technical = set()
        prev_impacts = set()
        
        for post in previous_posts:
            prev_themes.update(post.get('key_themes', []))
            prev_technical.update(post.get('technical_elements', []))
            prev_impacts.update(post.get('business_impact', []))
            
        # Define transition patterns based on post position
        transitions = {
            'continuation': [
                "Building on our previous work",
                "As we continue our development journey",
                "Taking the next step in our project",
                "Moving forward with our implementation"
            ],
            'technical_bridge': [
                f"After working with {', '.join(list(prev_technical)[-2:])}",
                "Expanding our technical implementation",
                "Advancing our technical architecture"
            ],
            'theme_bridge': [
                f"Continuing our focus on {', '.join(list(prev_themes)[-2:])}",
                "Developing our core themes further",
                "Building upon our key concepts"
            ],
            'impact_bridge': [
                f"Working towards {', '.join(list(prev_impacts)[-2:])}",
                "Driving towards our business goals",
                "Advancing our project objectives"
            ]
        }
        
        # Select appropriate transition based on content overlap
        selected_transition = None
        content_lower = current_content.lower()
        
        # Check if content already starts with a transition
        common_starts = [
            "continuing", "building", "moving", "following",
            "after", "next", "now", "as we"
        ]
        
        content_words = content_lower.split()
        if any(content_words[0].startswith(start) for start in common_starts):
            return current_content
            
        # Select transition based on context
        if prev_technical and any(tech.lower() in content_lower for tech in prev_technical):
            selected_transition = transitions['technical_bridge']
        elif prev_themes and any(theme.lower() in content_lower for theme in prev_themes):
            selected_transition = transitions['theme_bridge']
        elif prev_impacts and any(impact.lower() in content_lower for impact in prev_impacts):
            selected_transition = transitions['impact_bridge']
        else:
            selected_transition = transitions['continuation']
            
        # Use hash of content to consistently select transition
        transition = selected_transition[hash(current_content) % len(selected_transition)]
        
        # Apply transition
        modified_content = f"{transition}. {current_content}"
        
        # Ensure proper capitalization and spacing
        modified_content = modified_content.strip()
        if not modified_content[0].isupper():
            modified_content = modified_content[0].upper() + modified_content[1:]
            
        return modified_content
        
    def _get_previous_posts(
        self, 
        all_files: List[Dict], 
        current_position: int
    ) -> List[Dict]:
        """Helper method to get previously generated posts.
        
        Args:
            all_files: List of all files in the project
            current_position: Current position in sequence
            
        Returns:
            List of previous posts
        """
        return [f for f in all_files if f.get("position", 0) < current_position] 

    async def _generate_ai_content(
        self,
        prompt: str,
        references: List[Dict],
        connections: List[Dict],
        phase: str
    ) -> str:
        """Generate content using AI with full context awareness.
        
        Args:
            prompt: The context-aware prompt
            references: List of explicit references to include
            connections: List of subtle connections to weave in
            phase: Current development phase
            
        Returns:
            Generated content string
        """
        try:
            # Enhance prompt with references and connections
            enhanced_prompt = self._build_enhanced_prompt(prompt, references, connections, phase)
            
            # Prepare context for AI service
            context = {
                'system_message': self._get_system_message(phase),
                'examples': self._get_phase_examples(phase)
            }
            
            # Generate content using AI service
            result = await self.ai_service.generate_content(
                enhanced_prompt,
                context=context,
                temperature=self._get_phase_temperature(phase)
            )
            
            return result['content']
            
        except Exception as e:
            self.logger.error(f"Error in AI content generation: {str(e)}")
            raise

    def _build_enhanced_prompt(
        self,
        base_prompt: str,
        references: List[Dict],
        connections: List[Dict],
        phase: str
    ) -> str:
        """Build enhanced prompt with references and connections.
        
        Args:
            base_prompt: Original context-aware prompt
            references: List of explicit references to include
            connections: List of subtle connections to weave in
            phase: Current development phase
            
        Returns:
            Enhanced prompt string
        """
        reference_section = "\nExplicit References to Include:\n"
        for ref in references:
            reference_section += f"- {ref['reference_text']}\n"
            
        connection_section = "\nThematic Connections to Weave In:\n"
        for conn in connections:
            connection_section += f"- {conn['connection_text']}\n"
            
        phase_guidance = f"""
Phase-Specific Guidance:
- This is a {phase} phase post
- Focus on {self._get_phase_focus(phase)}
- Maintain appropriate technical depth for {phase}
- Include relevant {phase} metrics or outcomes
"""
        
        return f"{base_prompt}\n{reference_section}\n{connection_section}\n{phase_guidance}"
        
    def _get_phase_focus(self, phase: str) -> str:
        """Get the main focus points for each development phase.
        
        Args:
            phase: Development phase
            
        Returns:
            Focus points for the phase
        """
        phase_focus = {
            'planning': "design decisions, architecture choices, and anticipated challenges",
            'implementation': "technical execution, code structure, and development progress",
            'debugging': "problem identification, solution approaches, and lessons learned",
            'results': "achievements, performance improvements, and business impact"
        }
        
        return phase_focus.get(phase, "development progress and technical details") 

    def _get_system_message(self, phase: str) -> str:
        """Get the system message for the AI based on phase.
        
        Args:
            phase: Development phase
            
        Returns:
            System message string
        """
        return f"""You are a technical developer sharing your development journey on Facebook.
Your current post is about a {phase} phase milestone.
Write in a personal, authentic voice while maintaining technical accuracy.
Focus on {self._get_phase_focus(phase)}.
Keep the content engaging and relatable for both technical and business audiences."""
        
    def _get_phase_examples(self, phase: str) -> List[Dict]:
        """Get example posts for the current phase.
        
        Args:
            phase: Development phase
            
        Returns:
            List of example input/output pairs
        """
        examples = {
            'planning': [{
                'input': 'Write about system architecture design decisions',
                'output': """🏗️ Diving deep into architecture decisions today!

After weeks of research, I've settled on a microservices approach for our new backend. Here's why:

The scalability requirements are intense - we're looking at handling 10x our current load. Microservices will let us scale individual components independently.

Tech stack:
• Go for high-performance services
• gRPC for inter-service communication
• Redis for caching

The most exciting part? Each service can evolve independently. No more monolithic deployment anxiety! 

Who else has tackled similar architectural challenges? Would love to hear your experiences! 💡"""
            }],
            'implementation': [{
                'input': 'Write about implementing a new feature',
                'output': """🚀 Just shipped something cool!

Remember that scalability challenge I mentioned last week? Well, I've just implemented our first microservice in Go.

The process was both exciting and challenging:
• Learned Go's concurrency patterns
• Set up gRPC endpoints
• Implemented circuit breakers for resilience

Most interesting discovery? Go's goroutines made handling concurrent requests a breeze! We're seeing response times under 100ms even under heavy load.

Next up: Adding metrics and tracing. Because if you can't measure it, you can't improve it! 📊

Drop a ❤️ if you're also passionate about performance optimization!"""
            }],
            'debugging': [{
                'input': 'Write about solving a complex bug',
                'output': """🐛 I broke something. And I loved it.

Spent the last 48 hours tracking down the most fascinating bug. Our microservices were playing ping-pong with requests, creating an infinite loop.

The culprit? A subtle race condition in our circuit breaker implementation. The fix involved:
• Adding distributed tracing
• Implementing proper backoff strategies
• Rethinking our retry logic

Key lesson: Distributed systems are hard, but the right observability tools make debugging them possible.

Has anyone else battled interesting distributed systems bugs? Share your war stories! 💪"""
            }],
            'results': [{
                'input': 'Write about project outcomes',
                'output': """📈 The numbers are in!

Remember that microservices migration I've been sharing about? Here's what we achieved:

• 95% reduction in response time
• 99.99% uptime last month
• 10x increase in throughput
• Zero downtime deployments

But the real win? Our team can now deploy services independently, multiple times a day!

Huge thanks to the Go community for all the amazing tools and support.

What's your biggest technical achievement this quarter? Let's celebrate wins together! 🎉"""
            }]
        }
        
        return examples.get(phase, examples['implementation'])
        
    def _get_phase_temperature(self, phase: str) -> float:
        """Get the AI temperature setting based on phase.
        
        Args:
            phase: Development phase
            
        Returns:
            Temperature value between 0 and 1
        """
        # Adjust creativity level based on phase
        temperatures = {
            'planning': 0.7,  # More creative for architectural discussions
            'implementation': 0.5,  # More focused for technical details
            'debugging': 0.6,  # Balance between technical and narrative
            'results': 0.8  # More creative for engagement
        }
        
        return temperatures.get(phase, 0.6) 