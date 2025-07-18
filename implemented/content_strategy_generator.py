from typing import Dict, List, Optional, Set
import json
from datetime import datetime
import re
from collections import defaultdict

class ContentStrategyGenerator:
    """Generates optimal content strategies from project analysis."""
    
    def __init__(self):
        self.audience_types = {
            "technical": ["implementation", "debugging", "architecture", "testing", "performance", "security"],
            "business": ["planning", "results", "impact", "metrics", "roi", "strategy"]
        }
        
        # Enhanced theme detection patterns
        self.theme_patterns = {
            "architecture": [
                r"architect(?:ure|ural)",
                r"system design",
                r"infrastructure",
                r"scalability"
            ],
            "implementation": [
                r"implement(?:ation|ed|ing)",
                r"develop(?:ment|ed|ing)",
                r"build(?:ing)?",
                r"code"
            ],
            "testing": [
                r"test(?:ing|ed)",
                r"quality assurance",
                r"qa",
                r"unit test",
                r"integration test"
            ],
            "debugging": [
                r"debug(?:ging|ged)",
                r"fix(?:ing|ed)",
                r"issue",
                r"problem",
                r"error"
            ],
            "performance": [
                r"performance",
                r"optimize",
                r"efficiency",
                r"speed",
                r"latency"
            ],
            "security": [
                r"security",
                r"auth(?:entication|orization)",
                r"encrypt(?:ion)?",
                r"protect(?:ion)?"
            ],
            "planning": [
                r"plan(?:ning)?",
                r"design",
                r"strategy",
                r"roadmap"
            ],
            "results": [
                r"result",
                r"outcome",
                r"achievement",
                r"success"
            ]
        }
        
        # Connection type patterns for cross-references
        self.connection_patterns = {
            "continuation": {
                "patterns": [r"next", r"continue", r"following", r"subsequent"],
                "template": "Building on {previous_theme} from earlier..."
            },
            "dependency": {
                "patterns": [r"require", r"depend", r"need", r"prerequisite"],
                "template": "This relies on the {previous_theme} we discussed..."
            },
            "improvement": {
                "patterns": [r"improve", r"enhance", r"optimize", r"better"],
                "template": "We improved upon the {previous_theme} approach..."
            },
            "comparison": {
                "patterns": [r"compare", r"versus", r"alternative", r"different"],
                "template": "Comparing this with our {previous_theme} approach..."
            }
        }

    def generate_optimal_strategy(self, project_analysis: Dict, customization: Optional[Dict] = None) -> Dict:
        """Create AI-recommended content strategy with optional customization."""
        try:
            # Apply customization if provided
            if customization:
                project_analysis = self._apply_customization(project_analysis, customization)
            
            # Generate sequence first
            recommended_sequence = self.suggest_posting_sequence(
                project_analysis.get("source_files", []),
                project_analysis
            )
            
            # Generate cross-references using the sequence
            cross_references = self.generate_cross_references(
                project_analysis.get("source_files", []),
                recommended_sequence
            )
            
            strategy = {
                "project_theme": project_analysis.get("project_theme", ""),
                "estimated_posts": len(project_analysis.get("source_files", [])),
                "narrative_flow": self._generate_narrative_flow(project_analysis),
                "recommended_sequence": recommended_sequence,
                "content_themes": self._extract_content_themes(project_analysis),
                "audience_split": self._analyze_audience_split(project_analysis),
                "cross_references": cross_references,
                "tone_suggestions": self._generate_tone_suggestions(project_analysis),
                "posting_timeline": self._generate_posting_timeline(
                    len(project_analysis.get("source_files", []))
                ),
                "theme_strength": self._analyze_theme_strength(project_analysis),
                "customization_applied": bool(customization)
            }
            return strategy
        except Exception as e:
            raise Exception(f"Error generating content strategy: {str(e)}")

    def _apply_customization(self, analysis: Dict, customization: Dict) -> Dict:
        """Apply user customizations to the analysis."""
        # Store customization in analysis for use in other methods
        analysis["customization"] = customization
        
        if "excluded_themes" in customization:
            # Remove excluded themes from existing key_themes
            for file in analysis["source_files"]:
                file["key_themes"] = [
                    theme for theme in file.get("key_themes", [])
                    if theme not in customization["excluded_themes"]
                ]
        
        if "preferred_sequence" in customization:
            # Add preferred sequence to analysis for use in suggest_posting_sequence
            analysis["preferred_sequence"] = customization["preferred_sequence"]
        
        if "audience_preference" in customization:
            # Adjust audience types based on preference
            if customization["audience_preference"] == "technical":
                self.audience_types["technical"].extend(
                    ["planning", "results"]
                )
            elif customization["audience_preference"] == "business":
                self.audience_types["business"].extend(
                    ["implementation", "architecture"]
                )
        
        return analysis

    def suggest_posting_sequence(self, files: List[Dict], analysis: Dict) -> List[Dict]:
        """Recommend optimal posting order based on narrative flow."""
        try:
            # Check if there's a preferred sequence in the analysis
            if hasattr(analysis, 'get') and analysis.get('preferred_sequence'):
                # Use preferred sequence
                files_dict = {f["file_id"]: f for f in files}
                sorted_files = [
                    files_dict[file_id] 
                    for file_id in analysis['preferred_sequence']
                    if file_id in files_dict
                ]
            else:
                # Sort files by phase importance
                phase_order = ["planning", "implementation", "debugging", "results"]
                sorted_files = sorted(
                    files,
                    key=lambda x: phase_order.index(x.get("file_phase", ""))
                )
            
            sequence = []
            for idx, file in enumerate(sorted_files):
                post = {
                    "file_id": file.get("file_id"),
                    "filename": file.get("filename"),
                    "position": idx + 1,
                    "theme": file.get("key_themes", [])[0] if file.get("key_themes") else "",
                    "recommended_tone": self._determine_tone(file),
                    "target_audience": self._determine_audience(file)
                }
                sequence.append(post)
            
            return sequence
        except Exception as e:
            raise Exception(f"Error suggesting posting sequence: {str(e)}")

    def generate_cross_references(self, files: List[Dict], sequence: List[Dict]) -> List[Dict]:
        """Create cross-reference suggestions between posts."""
        try:
            references = []
            for i, current_file in enumerate(sequence):
                # Look for references to previous posts
                if i > 0:
                    # Try to find at least one reference to a previous post
                    found_ref = False
                    for j in range(i):
                        prev_file = sequence[j]
                        ref = self._find_connection(
                            current_file,
                            prev_file,
                            files
                        )
                        if ref:
                            references.append(ref)
                            found_ref = True
                    
                    # If no reference found, create a default continuation reference
                    if not found_ref:
                        references.append({
                            "from_file": sequence[i-1]["file_id"],
                            "to_file": current_file["file_id"],
                            "connection_type": "continuation",
                            "reference_text": f"Building on our previous work...",
                            "strength": 1
                        })
            
            return references
        except Exception as e:
            raise Exception(f"Error generating cross references: {str(e)}")

    def _generate_narrative_flow(self, analysis: Dict) -> str:
        """Generate narrative flow description."""
        phases = [f["file_phase"] for f in analysis.get("source_files", [])]
        if "planning" in phases and "results" in phases:
            return "Complete project journey from planning to results"
        elif "implementation" in phases and "debugging" in phases:
            return "Technical deep-dive with problem-solving focus"
        return "Project implementation highlights"

    def _extract_content_themes(self, analysis: Dict) -> List[str]:
        """Extract main content themes using enhanced pattern matching."""
        themes = set()
        theme_counts = defaultdict(int)
        
        # Get excluded themes from analysis if present
        excluded_themes = set()
        if hasattr(analysis, 'get') and isinstance(analysis.get('customization', {}), dict):
            excluded_themes = set(analysis.get('customization', {}).get('excluded_themes', []))
        
        for file in analysis.get("source_files", []):
            content = file.get("content", "").lower()
            file_themes = set()
            
            # Check each theme pattern
            for theme, patterns in self.theme_patterns.items():
                # Skip excluded themes
                if theme in excluded_themes:
                    continue
                    
                matches = 0
                for pattern in patterns:
                    matches += len(re.findall(pattern, content))
                if matches > 0:
                    file_themes.add(theme)
                    theme_counts[theme] += matches
            
            # Update file themes
            file["key_themes"] = list(file_themes)
            themes.update(file_themes)
        
        # Sort themes by frequency
        sorted_themes = sorted(
            themes,
            key=lambda t: theme_counts[t],
            reverse=True
        )
        return sorted_themes

    def _analyze_theme_strength(self, analysis: Dict) -> Dict:
        """Analyze the strength of each theme in the content."""
        theme_strength = defaultdict(int)
        total_files = len(analysis.get("source_files", []))
        
        for file in analysis.get("source_files", []):
            content = file.get("content", "").lower()
            for theme, patterns in self.theme_patterns.items():
                matches = sum(len(re.findall(pattern, content)) for pattern in patterns)
                theme_strength[theme] += matches
        
        # Normalize strengths to percentages
        max_strength = max(theme_strength.values()) if theme_strength else 1
        return {
            theme: round((strength / max_strength) * 100)
            for theme, strength in theme_strength.items()
            if strength > 0
        }

    def _analyze_audience_split(self, analysis: Dict) -> Dict:
        """Analyze content split between technical and business audiences."""
        technical_count = 0
        business_count = 0
        
        for file in analysis.get("source_files", []):
            if any(theme in self.audience_types["technical"] 
                  for theme in file.get("key_themes", [])):
                technical_count += 1
            if any(theme in self.audience_types["business"] 
                  for theme in file.get("key_themes", [])):
                business_count += 1
                
        return {
            "technical": technical_count,
            "business": business_count
        }

    def _determine_tone(self, file: Dict) -> str:
        """Determine appropriate tone for the file content."""
        phase = file.get("file_phase", "")
        if phase == "debugging":
            return "What Broke"
        elif phase == "implementation":
            return "Behind-the-Build"
        elif phase == "results":
            return "Finished & Proud"
        elif phase == "planning":
            return "Problem → Solution"
        return "Technical Deep Dive"

    def _determine_audience(self, file: Dict) -> str:
        """Determine target audience based on file content."""
        themes = file.get("key_themes", [])
        if any(theme in self.audience_types["technical"] for theme in themes):
            return "technical"
        return "business"

    def _find_connection(self, current: Dict, previous: Dict, files: List[Dict]) -> Optional[Dict]:
        """Find meaningful connection between two posts using enhanced pattern matching."""
        current_content = next(
            (f.get("content", "") for f in files if f["file_id"] == current["file_id"]),
            ""
        ).lower()
        
        previous_content = next(
            (f.get("content", "") for f in files if f["file_id"] == previous["file_id"]),
            ""
        ).lower()
        
        # Find the strongest connection type
        best_connection = None
        max_matches = 0
        
        for conn_type, config in self.connection_patterns.items():
            matches = 0
            for pattern in config["patterns"]:
                matches += len(re.findall(pattern, current_content))
                matches += len(re.findall(pattern, previous_content))
            
            if matches > max_matches:
                max_matches = matches
                best_connection = {
                    "from_file": previous["file_id"],
                    "to_file": current["file_id"],
                    "connection_type": conn_type,
                    "reference_text": config["template"].format(
                        previous_theme=previous.get("theme", "approach")
                    ),
                    "strength": matches
                }
        
        return best_connection if max_matches > 0 else None

    def _generate_tone_suggestions(self, analysis: Dict) -> List[str]:
        """Generate tone suggestions for the content series."""
        tones = []
        for file in analysis.get("source_files", []):
            tones.append(self._determine_tone(file))
        return list(set(tones))

    def _generate_posting_timeline(self, post_count: int) -> Dict:
        """Generate suggested posting timeline."""
        return {
            "frequency": "2-3 posts per week",
            "duration": f"{post_count // 2} weeks",
            "best_times": ["Tuesday 10am", "Thursday 2pm", "Friday 11am"]
        } 