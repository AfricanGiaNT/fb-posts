"""
Strategy Customization Interface for Multi-File Upload System
Handles user customization of content strategy including sequence, references, and tones.
"""

from typing import Dict, List, Optional
import logging

class StrategyCustomizer:
    """Handles customization of content strategy for multi-file uploads."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def customize_sequence(self, strategy: Dict, sequence: List[Dict]) -> Dict:
        """
        Customize the posting sequence of files.
        
        Args:
            strategy: Current content strategy
            sequence: New sequence of file IDs and metadata
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # Validate sequence
            if not self._validate_sequence(sequence, strategy):
                raise ValueError("Invalid sequence configuration")
                
            # Update sequence
            strategy['recommended_sequence'] = sequence
            
            # Recalculate cross-references
            strategy['cross_references'] = self._recalculate_references(sequence)
            
            # Update narrative flow
            strategy['narrative_flow'] = self._analyze_narrative_flow(sequence)
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Sequence customization error: {str(e)}")
            raise
            
    def customize_references(self, strategy: Dict, references: List[Dict]) -> Dict:
        """
        Customize cross-references between posts.
        
        Args:
            strategy: Current content strategy
            references: List of custom reference configurations
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # Validate references
            if not self._validate_references(references, strategy):
                raise ValueError("Invalid reference configuration")
                
            # Update cross-references
            strategy['cross_references'] = references
            
            # Update narrative flow
            strategy['narrative_flow'] = self._analyze_narrative_flow(
                strategy['recommended_sequence'],
                references
            )
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Reference customization error: {str(e)}")
            raise
            
    def customize_tones(self, strategy: Dict, tones: Dict) -> Dict:
        """
        Customize tone settings for specific posts.
        
        Args:
            strategy: Current content strategy
            tones: Dictionary mapping file IDs to tone settings
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # Validate tones
            if not self._validate_tones(tones):
                raise ValueError("Invalid tone configuration")
                
            # Update tone suggestions
            strategy['tone_suggestions'] = self._merge_tone_settings(
                strategy['tone_suggestions'],
                tones
            )
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Tone customization error: {str(e)}")
            raise
            
    def exclude_files(self, strategy: Dict, excluded_files: List[str]) -> Dict:
        """
        Update strategy to exclude specific files.
        
        Args:
            strategy: Current content strategy
            excluded_files: List of file IDs to exclude
            
        Returns:
            Updated strategy dictionary
        """
        try:
            # Remove excluded files from sequence
            strategy['recommended_sequence'] = [
                item for item in strategy['recommended_sequence']
                if item['file_id'] not in excluded_files
            ]
            
            # Update cross-references
            strategy['cross_references'] = [
                ref for ref in strategy['cross_references']
                if ref['source_id'] not in excluded_files
                and ref['target_id'] not in excluded_files
            ]
            
            # Recalculate narrative flow
            strategy['narrative_flow'] = self._analyze_narrative_flow(
                strategy['recommended_sequence']
            )
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"File exclusion error: {str(e)}")
            raise
            
    def _validate_sequence(self, sequence: List[Dict], strategy: Dict) -> bool:
        """Validate sequence configuration."""
        if not sequence:
            return False
            
        # Check all files are accounted for
        strategy_files = {item['file_id'] for item in strategy['recommended_sequence']}
        sequence_files = {item['file_id'] for item in sequence}
        
        return sequence_files.issubset(strategy_files)
        
    def _validate_references(self, references: List[Dict], strategy: Dict) -> bool:
        """Validate reference configuration."""
        if not references:
            return True  # Empty references are valid
            
        # Check reference structure
        required_keys = {'source_id', 'target_id', 'type'}
        return all(all(key in ref for key in required_keys) for ref in references)
        
    def _validate_tones(self, tones: Dict) -> bool:
        """Validate tone configuration."""
        valid_tones = {
            'behind-the-build',
            'what-broke',
            'technical-deep-dive',
            'finished-and-proud',
            'mini-lesson'
        }
        
        return all(tone in valid_tones for tone in tones.values())
        
    def _recalculate_references(self, sequence: List[Dict]) -> List[Dict]:
        """Recalculate cross-references based on new sequence."""
        references = []
        
        # Generate references between consecutive files
        for i in range(len(sequence) - 1):
            current_file = sequence[i]
            next_file = sequence[i + 1]
            
            # Add forward reference
            references.append({
                'source_id': current_file['file_id'],
                'target_id': next_file['file_id'],
                'type': 'continuation'
            })
            
            # Add backward reference if themes are related
            if current_file.get('theme') == next_file.get('theme'):
                references.append({
                    'source_id': next_file['file_id'],
                    'target_id': current_file['file_id'],
                    'type': 'related'
                })
        
        return references
        
    def _analyze_narrative_flow(self, sequence: List[Dict],
                              references: Optional[List[Dict]] = None) -> str:
        """Analyze and describe narrative flow of the sequence."""
        # Implementation would analyze sequence and generate flow description
        
        return "Sequential project progression"
        
    def _merge_tone_settings(self, original_tones: Dict, new_tones: Dict) -> Dict:
        """Merge original and new tone settings."""
        merged = original_tones.copy()
        merged.update(new_tones)
        return merged 