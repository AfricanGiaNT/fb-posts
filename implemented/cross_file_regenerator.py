"""
Cross-File Content Regeneration for Multi-File Upload System
Handles regeneration of content while maintaining context awareness and references.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

class CrossFileRegenerator:
    """Manages content regeneration with cross-file awareness."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def regenerate_content(self, target_file: Dict, all_files: List[Dict], 
                               strategy: Dict, feedback: str) -> Dict:
        """
        Regenerate content for a specific file while maintaining context.
        
        Args:
            target_file: File to regenerate content for
            all_files: List of all files in the project
            strategy: Content strategy dictionary
            feedback: User feedback for regeneration
            
        Returns:
            Updated file data with regenerated content
        """
        try:
            # Extract context from related files
            context = self._build_regeneration_context(target_file, all_files, strategy)
            
            # Preserve existing references
            references = self._extract_existing_references(target_file, strategy)
            
            # Update file data with context
            target_file['regeneration_context'] = context
            target_file['preserved_references'] = references
            target_file['user_feedback'] = feedback
            target_file['last_regenerated'] = datetime.now().isoformat()
            
            return target_file
            
        except Exception as e:
            self.logger.error(f"Error regenerating content: {str(e)}")
            return target_file
            
    def _build_regeneration_context(self, target_file: Dict, 
                                  all_files: List[Dict], 
                                  strategy: Dict) -> Dict:
        """Build comprehensive context for regeneration."""
        try:
            if not target_file or not all_files or not strategy:
                return {}
                
            # Find position in sequence
            sequence = strategy.get('recommended_sequence', [])
            current_position = next(
                (i for i, post in enumerate(sequence) 
                 if post.get('file_id') == target_file.get('file_id')),
                -1
            )
            
            # Get previous and next posts
            previous_posts = sequence[:current_position] if current_position > 0 else []
            next_posts = sequence[current_position + 1:] if current_position < len(sequence) - 1 else []
            
            # Build context
            context = {
                'narrative_position': current_position + 1,
                'total_posts': len(sequence),
                'previous_posts': [
                    {
                        'file_id': post.get('file_id'),
                        'theme': post.get('theme'),
                        'key_points': self._extract_key_points(post)
                    }
                    for post in previous_posts
                ],
                'next_posts': [
                    {
                        'file_id': post.get('file_id'),
                        'theme': post.get('theme')
                    }
                    for post in next_posts
                ],
                'project_theme': strategy.get('project_theme'),
                'narrative_flow': strategy.get('narrative_flow'),
                'technical_elements': self._extract_technical_elements(target_file, all_files)
            }
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error building regeneration context: {str(e)}")
            return {}
            
    def _extract_existing_references(self, target_file: Dict, strategy: Dict) -> List[Dict]:
        """Extract and preserve existing cross-references."""
        try:
            references = []
            file_id = target_file.get('file_id')
            
            # Find references where this file is source or target
            for ref in strategy.get('cross_references', []):
                if ref.get('source_id') == file_id or ref.get('target_id') == file_id:
                    references.append(ref)
                    
            return references
            
        except Exception as e:
            self.logger.error(f"Error extracting references: {str(e)}")
            return []
            
    def _extract_key_points(self, post: Dict) -> List[str]:
        """Extract key points from a post for context."""
        try:
            # Extract from content summary if available
            if 'content_summary' in post:
                return post['content_summary'].get('key_points', [])
                
            # Extract from technical elements
            if 'technical_elements' in post:
                return post['technical_elements']
                
            return []
            
        except Exception as e:
            self.logger.error(f"Error extracting key points: {str(e)}")
            return []
            
    def _extract_technical_elements(self, target_file: Dict, all_files: List[Dict]) -> List[str]:
        """Extract technical elements with dependencies."""
        try:
            elements = set()
            
            # Add target file elements
            if 'technical_elements' in target_file:
                elements.update(target_file['technical_elements'])
                
            # Add related elements from other files
            for file in all_files:
                if file.get('file_id') != target_file.get('file_id'):
                    if 'technical_elements' in file:
                        file_elements = set(file['technical_elements'])
                        # Add elements that share common technology with target file
                        if any(tech in target_file.get('technical_elements', []) 
                              for tech in file_elements):
                            elements.update(file_elements)
                        
            return sorted(list(elements))  # Sort for consistent ordering
            
        except Exception as e:
            self.logger.error(f"Error extracting technical elements: {str(e)}")
            return [] 