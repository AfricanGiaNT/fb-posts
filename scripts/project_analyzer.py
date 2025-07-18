"""
Project Analyzer for Multi-File Upload System
Handles intelligent file categorization and cross-file relationship mapping
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import uuid

try:
    from ai_content_generator import AIContentGenerator
except ImportError:
    from .ai_content_generator import AIContentGenerator

@dataclass
class FileAnalysis:
    """Structured analysis of a single file."""
    file_id: str
    filename: str
    content: str
    upload_timestamp: datetime
    file_phase: str
    content_summary: str
    key_themes: List[str]
    technical_elements: List[str]
    business_impact: List[str]
    word_count: int
    processing_status: str
    challenges_identified: List[str]
    solutions_presented: List[str]
    complexity_score: float  # 0-1 scale

@dataclass
class ProjectAnalysis:
    """Comprehensive analysis of multiple files."""
    project_theme: str
    narrative_arc: str
    key_challenges: List[str]
    solutions_implemented: List[str]
    technical_stack: List[str]
    business_outcomes: List[str]
    content_threads: List[Dict]
    estimated_posts: int
    completeness_score: float  # 0-1 scale
    cohesion_score: float  # 0-1 scale

class ProjectAnalyzer:
    """Analyzes multiple dev journal files to extract project narrative."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.ai_generator = AIContentGenerator(config_manager)
        
        # File phase patterns for classification
        self.phase_patterns = {
            'planning': [
                r'plan(?:ning)?', r'design', r'architecture', r'requirements?',
                r'specification', r'wireframe', r'mockup', r'research',
                r'analysis', r'strategy', r'roadmap', r'scope'
            ],
            'implementation': [
                r'implement(?:ation)?', r'develop(?:ment)?', r'build(?:ing)?',
                r'code', r'coding', r'program(?:ming)?', r'creation',
                r'feature', r'component', r'module', r'system'
            ],
            'debugging': [
                r'debug(?:ging)?', r'fix(?:ing)?', r'bug', r'error', r'issue',
                r'problem', r'troubleshoot(?:ing)?', r'resolve', r'repair',
                r'patch', r'hotfix', r'maintenance'
            ],
            'results': [
                r'result(?:s)?', r'outcome', r'finish(?:ed)?', r'complete(?:d)?',
                r'deploy(?:ment)?', r'launch(?:ing)?', r'release', r'optimize',
                r'performance', r'metrics', r'evaluation', r'success'
            ]
        }
        
        # Technical elements to identify
        self.technical_keywords = [
            'api', 'database', 'server', 'client', 'framework', 'library',
            'algorithm', 'architecture', 'deployment', 'authentication',
            'authorization', 'optimization', 'performance', 'scalability',
            'security', 'integration', 'microservice', 'container',
            'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'ci/cd'
        ]
        
        # Business impact keywords
        self.business_keywords = [
            'revenue', 'cost', 'efficiency', 'productivity', 'automation',
            'user experience', 'customer', 'client', 'business', 'roi',
            'profit', 'growth', 'scaling', 'competitive', 'market',
            'value', 'benefit', 'impact', 'solution', 'opportunity'
        ]
    
    def categorize_file(self, content: str, filename: str) -> Dict:
        """
        Categorize file into project phase and extract metadata.
        
        Args:
            content: The file content
            filename: The filename
            
        Returns:
            Dict containing file analysis data
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Basic metrics
        word_count = len(content.split())
        
        # Determine file phase using multiple methods
        phase_scores = self._calculate_phase_scores(content, filename)
        file_phase = max(phase_scores, key=phase_scores.get)
        
        # Extract content summary using AI
        content_summary = self._generate_content_summary(content)
        
        # Extract themes and elements
        key_themes = self._extract_key_themes(content)
        technical_elements = self._extract_technical_elements(content)
        business_impact = self._extract_business_impact(content)
        
        # Identify challenges and solutions
        challenges_identified = self._identify_challenges(content)
        solutions_presented = self._identify_solutions(content)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(content, technical_elements)
        
        return {
            'file_id': file_id,
            'filename': filename,
            'content': content,
            'upload_timestamp': datetime.now(),
            'file_phase': file_phase,
            'content_summary': content_summary,
            'key_themes': key_themes,
            'technical_elements': technical_elements,
            'business_impact': business_impact,
            'word_count': word_count,
            'processing_status': 'analyzed',
            'challenges_identified': challenges_identified,
            'solutions_presented': solutions_presented,
            'complexity_score': complexity_score,
            'phase_scores': phase_scores  # For debugging
        }
    
    def analyze_project_narrative(self, files: List[Dict]) -> Dict:
        """
        Analyze multiple files to extract comprehensive project story.
        
        Args:
            files: List of file analysis dictionaries
            
        Returns:
            Dict containing project analysis
        """
        if not files:
            return self._empty_project_analysis()
        
        # Combine all content for analysis
        combined_content = "\n\n".join([f"FILE: {f['filename']}\n{f['content']}" for f in files])
        
        # Extract project theme using AI
        project_theme = self._extract_project_theme(files)
        
        # Determine narrative arc
        narrative_arc = self._determine_narrative_arc(files)
        
        # Aggregate challenges and solutions
        key_challenges = self._aggregate_challenges(files)
        solutions_implemented = self._aggregate_solutions(files)
        
        # Extract technical stack
        technical_stack = self._extract_technical_stack(files)
        
        # Identify business outcomes
        business_outcomes = self._identify_business_outcomes(files)
        
        # Map content threads
        content_threads = self._map_content_threads(files)
        
        # Estimate post count
        estimated_posts = self._estimate_post_count(files)
        
        # Calculate quality scores
        completeness_score = self._calculate_completeness_score(files)
        cohesion_score = self._calculate_cohesion_score(files)
        
        return {
            'project_theme': project_theme,
            'narrative_arc': narrative_arc,
            'key_challenges': key_challenges,
            'solutions_implemented': solutions_implemented,
            'technical_stack': technical_stack,
            'business_outcomes': business_outcomes,
            'content_threads': content_threads,
            'estimated_posts': estimated_posts,
            'completeness_score': completeness_score,
            'cohesion_score': cohesion_score,
            'files_analyzed': len(files),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def identify_cross_file_relationships(self, files: List[Dict]) -> List[Dict]:
        """
        Map relationships and connections between files.
        
        Args:
            files: List of file analysis dictionaries
            
        Returns:
            List of relationship mappings
        """
        relationships = []
        
        for i, file1 in enumerate(files):
            for j, file2 in enumerate(files):
                if i >= j:  # Skip self and already compared pairs
                    continue
                
                relationship = self._analyze_file_relationship(file1, file2)
                if relationship['strength'] > 0.3:  # Only significant relationships
                    relationships.append(relationship)
        
        return sorted(relationships, key=lambda x: x['strength'], reverse=True)
    
    def extract_narrative_threads(self, files: List[Dict]) -> List[Dict]:
        """
        Identify story threads that connect multiple files.
        
        Args:
            files: List of file analysis dictionaries
            
        Returns:
            List of narrative thread dictionaries
        """
        threads = []
        
        # Group files by common themes
        theme_groups = self._group_files_by_themes(files)
        
        # Identify technical progression threads
        technical_threads = self._identify_technical_threads(files)
        
        # Identify problem-solution threads
        problem_solution_threads = self._identify_problem_solution_threads(files)
        
        # Identify learning threads
        learning_threads = self._identify_learning_threads(files)
        
        threads.extend(technical_threads)
        threads.extend(problem_solution_threads)
        threads.extend(learning_threads)
        
        return threads
    
    def assess_content_completeness(self, files: List[Dict]) -> Dict:
        """
        Evaluate how well files cover the project story.
        
        Args:
            files: List of file analysis dictionaries
            
        Returns:
            Dict containing completeness assessment
        """
        # Check for all phases
        phases_present = set(f['file_phase'] for f in files)
        required_phases = {'planning', 'implementation', 'debugging', 'results'}
        phase_completeness = len(phases_present.intersection(required_phases)) / len(required_phases)
        
        # Check for narrative elements
        has_problem_statement = any('problem' in f['content_summary'].lower() for f in files)
        has_solution_description = any('solution' in f['content_summary'].lower() for f in files)
        has_technical_details = any(f['technical_elements'] for f in files)
        has_business_impact = any(f['business_impact'] for f in files)
        
        narrative_completeness = sum([
            has_problem_statement,
            has_solution_description,
            has_technical_details,
            has_business_impact
        ]) / 4
        
        # Overall completeness score
        overall_score = (phase_completeness + narrative_completeness) / 2
        
        return {
            'overall_score': overall_score,
            'phase_completeness': phase_completeness,
            'narrative_completeness': narrative_completeness,
            'phases_present': list(phases_present),
            'missing_phases': list(required_phases - phases_present),
            'narrative_elements': {
                'has_problem_statement': has_problem_statement,
                'has_solution_description': has_solution_description,
                'has_technical_details': has_technical_details,
                'has_business_impact': has_business_impact
            },
            'recommendations': self._generate_completeness_recommendations(files, phases_present)
        }
    
    # Private helper methods
    
    def _calculate_phase_scores(self, content: str, filename: str) -> Dict[str, float]:
        """Calculate probability scores for each phase."""
        content_lower = content.lower()
        filename_lower = filename.lower()
        
        scores = {}
        for phase, patterns in self.phase_patterns.items():
            score = 0
            for pattern in patterns:
                # Content matches (weighted higher)
                content_matches = len(re.findall(pattern, content_lower))
                score += content_matches * 0.7
                
                # Filename matches (weighted lower)
                filename_matches = len(re.findall(pattern, filename_lower))
                score += filename_matches * 0.3
            
            scores[phase] = min(score, 10)  # Cap at 10
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {k: v/total for k, v in scores.items()}
        
        return scores
    
    def _generate_content_summary(self, content: str) -> str:
        """Generate AI-powered content summary."""
        try:
            prompt = f"""Analyze this development journal entry and provide a concise 2-3 sentence summary focusing on:
1. What was built or worked on
2. The main challenge or objective
3. The key outcome or result

Content:
{content[:2000]}...

Provide a clear, professional summary:"""
            
            summary = self.ai_generator._generate_content(
                "You are a technical writing assistant that creates clear, concise summaries of development work.",
                prompt,
                temperature=0.3,
                max_tokens=150
            )
            
            return summary.strip()
        except Exception as e:
            # Fallback to simple extraction
            lines = content.split('\n')
            summary_lines = []
            for line in lines[:10]:  # First 10 lines
                if line.strip() and not line.startswith('#'):
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= 3:
                        break
            
            return ' '.join(summary_lines)[:300]
    
    def _extract_key_themes(self, content: str) -> List[str]:
        """Extract key themes from content."""
        content_lower = content.lower()
        themes = []
        
        # Theme categories
        theme_patterns = {
            'authentication': r'auth|login|password|security|token',
            'database': r'database|sql|nosql|mongodb|postgresql|mysql',
            'api': r'api|rest|graphql|endpoint|service',
            'frontend': r'frontend|ui|interface|react|vue|angular',
            'backend': r'backend|server|express|django|flask',
            'testing': r'test|testing|unit|integration|qa',
            'deployment': r'deploy|deployment|production|hosting|cloud',
            'performance': r'performance|optimization|speed|caching',
            'automation': r'automation|scripting|workflow|pipeline',
            'integration': r'integration|connect|sync|webhook'
        }
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, content_lower):
                themes.append(theme)
        
        return themes[:5]  # Limit to top 5 themes
    
    def _extract_technical_elements(self, content: str) -> List[str]:
        """Extract technical elements from content."""
        content_lower = content.lower()
        elements = []
        
        for keyword in self.technical_keywords:
            if keyword in content_lower:
                elements.append(keyword)
        
        return list(set(elements))[:10]  # Limit to 10 unique elements
    
    def _extract_business_impact(self, content: str) -> List[str]:
        """Extract business impact statements."""
        content_lower = content.lower()
        impacts = []
        
        for keyword in self.business_keywords:
            if keyword in content_lower:
                impacts.append(keyword)
        
        return list(set(impacts))[:5]  # Limit to 5 unique impacts
    
    def _identify_challenges(self, content: str) -> List[str]:
        """Identify challenges mentioned in content."""
        challenge_patterns = [
            r'challenge', r'problem', r'issue', r'difficult', r'struggle',
            r'obstacle', r'barrier', r'limitation', r'constraint', r'bug'
        ]
        
        challenges = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            for pattern in challenge_patterns:
                if pattern in line_lower and len(line.strip()) > 20:
                    challenges.append(line.strip())
                    break
        
        return challenges[:5]  # Limit to 5 challenges
    
    def _identify_solutions(self, content: str) -> List[str]:
        """Identify solutions mentioned in content."""
        solution_patterns = [
            r'solution', r'solve', r'fix', r'resolve', r'implement',
            r'address', r'overcome', r'handle', r'approach', r'method'
        ]
        
        solutions = []
        lines = content.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            for pattern in solution_patterns:
                if pattern in line_lower and len(line.strip()) > 20:
                    solutions.append(line.strip())
                    break
        
        return solutions[:5]  # Limit to 5 solutions
    
    def _calculate_complexity_score(self, content: str, technical_elements: List[str]) -> float:
        """Calculate complexity score (0-1)."""
        # Base score on technical elements
        tech_score = min(len(technical_elements) / 10, 1.0)
        
        # Adjust for content length
        length_score = min(len(content) / 5000, 1.0)
        
        # Adjust for technical depth indicators
        depth_indicators = ['algorithm', 'architecture', 'optimization', 'scalability']
        depth_score = sum(1 for indicator in depth_indicators if indicator in content.lower()) / len(depth_indicators)
        
        return (tech_score + length_score + depth_score) / 3
    
    def _extract_project_theme(self, files: List[Dict]) -> str:
        """Extract overall project theme using AI."""
        try:
            # Combine summaries
            summaries = [f['content_summary'] for f in files]
            combined_summary = '\n'.join(summaries)
            
            prompt = f"""Based on these development journal summaries, identify the main project theme in 1-2 sentences:

{combined_summary}

Theme:"""
            
            theme = self.ai_generator._generate_content(
                "You are a project analyst that identifies main themes from development work.",
                prompt,
                temperature=0.3,
                max_tokens=100
            )
            
            return theme.strip()
        except Exception:
            return "Development project with multiple phases"
    
    def _determine_narrative_arc(self, files: List[Dict]) -> str:
        """Determine the narrative progression."""
        phases = [f['file_phase'] for f in files]
        phase_order = ['planning', 'implementation', 'debugging', 'results']
        
        # Check if phases follow logical order
        ordered_phases = []
        for phase in phase_order:
            if phase in phases:
                ordered_phases.append(phase)
        
        if len(ordered_phases) >= 3:
            return f"Complete development journey: {' → '.join(ordered_phases)}"
        elif 'planning' in phases and 'implementation' in phases:
            return "Design to implementation"
        elif 'implementation' in phases and 'debugging' in phases:
            return "Development and problem-solving"
        elif 'debugging' in phases and 'results' in phases:
            return "Problem resolution and outcomes"
        else:
            return "Development milestone documentation"
    
    def _aggregate_challenges(self, files: List[Dict]) -> List[str]:
        """Aggregate challenges from all files."""
        all_challenges = []
        for file in files:
            all_challenges.extend(file.get('challenges_identified', []))
        
        # Remove duplicates and limit
        unique_challenges = list(dict.fromkeys(all_challenges))
        return unique_challenges[:10]
    
    def _aggregate_solutions(self, files: List[Dict]) -> List[str]:
        """Aggregate solutions from all files."""
        all_solutions = []
        for file in files:
            all_solutions.extend(file.get('solutions_presented', []))
        
        # Remove duplicates and limit
        unique_solutions = list(dict.fromkeys(all_solutions))
        return unique_solutions[:10]
    
    def _extract_technical_stack(self, files: List[Dict]) -> List[str]:
        """Extract technical stack from all files."""
        all_tech = []
        for file in files:
            all_tech.extend(file.get('technical_elements', []))
        
        # Remove duplicates and sort by frequency
        tech_count = {}
        for tech in all_tech:
            tech_count[tech] = tech_count.get(tech, 0) + 1
        
        sorted_tech = sorted(tech_count.items(), key=lambda x: x[1], reverse=True)
        return [tech for tech, count in sorted_tech[:15]]
    
    def _identify_business_outcomes(self, files: List[Dict]) -> List[str]:
        """Identify business outcomes from all files."""
        all_outcomes = []
        for file in files:
            all_outcomes.extend(file.get('business_impact', []))
        
        # Remove duplicates and limit
        unique_outcomes = list(dict.fromkeys(all_outcomes))
        return unique_outcomes[:8]
    
    def _map_content_threads(self, files: List[Dict]) -> List[Dict]:
        """Map content threads that connect files."""
        threads = []
        
        # Common theme threads
        all_themes = []
        for file in files:
            all_themes.extend(file.get('key_themes', []))
        
        theme_count = {}
        for theme in all_themes:
            theme_count[theme] = theme_count.get(theme, 0) + 1
        
        # Create threads for themes that appear in multiple files
        for theme, count in theme_count.items():
            if count > 1:
                thread_files = [f['filename'] for f in files if theme in f.get('key_themes', [])]
                threads.append({
                    'type': 'theme',
                    'name': theme,
                    'files': thread_files,
                    'strength': min(count / len(files), 1.0)
                })
        
        return threads[:10]
    
    def _estimate_post_count(self, files: List[Dict]) -> int:
        """Estimate optimal number of posts."""
        # Base: 1 post per file
        base_posts = len(files)
        
        # Adjust for content richness
        avg_complexity = sum(f.get('complexity_score', 0.5) for f in files) / len(files)
        
        # Adjust for technical depth
        avg_tech_elements = sum(len(f.get('technical_elements', [])) for f in files) / len(files)
        
        # Calculate multiplier
        multiplier = 1.0
        if avg_complexity > 0.7:
            multiplier += 0.3
        if avg_tech_elements > 5:
            multiplier += 0.2
        
        return min(int(base_posts * multiplier), 12)  # Cap at 12 posts
    
    def _calculate_completeness_score(self, files: List[Dict]) -> float:
        """Calculate how complete the project documentation is."""
        return self.assess_content_completeness(files)['overall_score']
    
    def _calculate_cohesion_score(self, files: List[Dict]) -> float:
        """Calculate how well files connect to each other."""
        if len(files) < 2:
            return 1.0
        
        relationships = self.identify_cross_file_relationships(files)
        if not relationships:
            return 0.3
        
        avg_strength = sum(r['strength'] for r in relationships) / len(relationships)
        return min(avg_strength, 1.0)
    
    def _analyze_file_relationship(self, file1: Dict, file2: Dict) -> Dict:
        """Analyze relationship between two files."""
        # Theme overlap
        themes1 = set(file1.get('key_themes', []))
        themes2 = set(file2.get('key_themes', []))
        theme_overlap = len(themes1.intersection(themes2)) / max(len(themes1.union(themes2)), 1)
        
        # Technical overlap
        tech1 = set(file1.get('technical_elements', []))
        tech2 = set(file2.get('technical_elements', []))
        tech_overlap = len(tech1.intersection(tech2)) / max(len(tech1.union(tech2)), 1)
        
        # Phase relationship
        phase1 = file1.get('file_phase', '')
        phase2 = file2.get('file_phase', '')
        phase_relationships = {
            ('planning', 'implementation'): 0.8,
            ('implementation', 'debugging'): 0.7,
            ('debugging', 'results'): 0.6,
            ('planning', 'results'): 0.5
        }
        phase_strength = phase_relationships.get((phase1, phase2), 0.0)
        phase_strength = max(phase_strength, phase_relationships.get((phase2, phase1), 0.0))
        
        # Overall relationship strength
        overall_strength = (theme_overlap + tech_overlap + phase_strength) / 3
        
        return {
            'file1': file1['filename'],
            'file2': file2['filename'],
            'strength': overall_strength,
            'type': self._determine_relationship_type(file1, file2, overall_strength),
            'theme_overlap': theme_overlap,
            'tech_overlap': tech_overlap,
            'phase_relationship': phase_strength
        }
    
    def _determine_relationship_type(self, file1: Dict, file2: Dict, strength: float) -> str:
        """Determine the type of relationship between files."""
        if strength > 0.7:
            return 'sequential'
        elif strength > 0.5:
            return 'thematic'
        elif strength > 0.3:
            return 'technical'
        else:
            return 'weak'
    
    def _group_files_by_themes(self, files: List[Dict]) -> Dict:
        """Group files by common themes."""
        theme_groups = {}
        for file in files:
            for theme in file.get('key_themes', []):
                if theme not in theme_groups:
                    theme_groups[theme] = []
                theme_groups[theme].append(file)
        
        return theme_groups
    
    def _identify_technical_threads(self, files: List[Dict]) -> List[Dict]:
        """Identify technical progression threads."""
        threads = []
        
        # Sort files by phase for logical progression
        phase_order = ['planning', 'implementation', 'debugging', 'results']
        sorted_files = sorted(files, key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
        
        # Look for technical evolution
        tech_evolution = []
        for file in sorted_files:
            tech_elements = file.get('technical_elements', [])
            if tech_elements:
                tech_evolution.append({
                    'file': file['filename'],
                    'phase': file.get('file_phase', ''),
                    'elements': tech_elements
                })
        
        if len(tech_evolution) >= 2:
            threads.append({
                'type': 'technical_progression',
                'name': 'Technical Evolution',
                'files': [t['file'] for t in tech_evolution],
                'strength': 0.8,
                'description': 'Technical implementation progression'
            })
        
        return threads
    
    def _identify_problem_solution_threads(self, files: List[Dict]) -> List[Dict]:
        """Identify problem-solution threads."""
        threads = []
        
        problem_files = [f for f in files if f.get('challenges_identified')]
        solution_files = [f for f in files if f.get('solutions_presented')]
        
        if problem_files and solution_files:
            threads.append({
                'type': 'problem_solution',
                'name': 'Problem-Solution Arc',
                'files': list(set([f['filename'] for f in problem_files + solution_files])),
                'strength': 0.7,
                'description': 'Problem identification and resolution'
            })
        
        return threads
    
    def _identify_learning_threads(self, files: List[Dict]) -> List[Dict]:
        """Identify learning and insight threads."""
        threads = []
        
        # Look for learning indicators
        learning_files = []
        for file in files:
            content_lower = file.get('content', '').lower()
            if any(keyword in content_lower for keyword in ['learn', 'discover', 'realize', 'insight', 'lesson']):
                learning_files.append(file)
        
        if len(learning_files) >= 2:
            threads.append({
                'type': 'learning',
                'name': 'Learning Journey',
                'files': [f['filename'] for f in learning_files],
                'strength': 0.6,
                'description': 'Development insights and learnings'
            })
        
        return threads
    
    def _generate_completeness_recommendations(self, files: List[Dict], phases_present: set) -> List[str]:
        """Generate recommendations for improving completeness."""
        recommendations = []
        
        required_phases = {'planning', 'implementation', 'debugging', 'results'}
        missing_phases = required_phases - phases_present
        
        if 'planning' in missing_phases:
            recommendations.append("Consider adding documentation about project planning and initial design decisions")
        
        if 'implementation' in missing_phases:
            recommendations.append("Add details about the actual implementation process and technical decisions")
        
        if 'debugging' in missing_phases:
            recommendations.append("Include information about challenges faced and how they were resolved")
        
        if 'results' in missing_phases:
            recommendations.append("Document the final outcomes, performance metrics, and lessons learned")
        
        # Check for narrative elements
        has_business_impact = any(f.get('business_impact') for f in files)
        if not has_business_impact:
            recommendations.append("Consider adding more context about business impact and user benefits")
        
        return recommendations
    
    def _empty_project_analysis(self) -> Dict:
        """Return empty project analysis structure."""
        return {
            'project_theme': 'No files analyzed',
            'narrative_arc': 'No narrative identified',
            'key_challenges': [],
            'solutions_implemented': [],
            'technical_stack': [],
            'business_outcomes': [],
            'content_threads': [],
            'estimated_posts': 0,
            'completeness_score': 0.0,
            'cohesion_score': 0.0,
            'files_analyzed': 0,
            'analysis_timestamp': datetime.now().isoformat()
        } 