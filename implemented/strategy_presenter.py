from typing import Dict, List, Optional
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import track

class StrategyPresenter:
    """Handles the presentation and interaction with content strategies."""
    
    def __init__(self):
        self.console = Console()
    
    def present_strategy(self, strategy: Dict):
        """Present the complete content strategy in a visually appealing way."""
        self._print_header(strategy)
        self._print_themes(strategy)
        self._print_sequence(strategy)
        self._print_cross_references(strategy)
        self._print_audience_split(strategy)
        self._print_timeline(strategy)
    
    def _print_header(self, strategy: Dict):
        """Print strategy header with key information."""
        self.console.print("\n")
        self.console.print(Panel.fit(
            f"[bold blue]Content Strategy: {strategy['project_theme']}[/]\n"
            f"Posts: {strategy['estimated_posts']} | "
            f"Flow: {strategy['narrative_flow']}",
            title="Strategy Overview"
        ))
    
    def _print_themes(self, strategy: Dict):
        """Print content themes and their strengths."""
        theme_table = Table(show_header=True, header_style="bold magenta")
        theme_table.add_column("Theme")
        theme_table.add_column("Strength", justify="right")
        
        for theme, strength in strategy.get('theme_strength', {}).items():
            bar = "█" * (strength // 10)
            theme_table.add_row(
                theme.title(),
                f"{bar} {strength}%"
            )
        
        self.console.print("\n")
        self.console.print(Panel(theme_table, title="Content Themes"))
    
    def _print_sequence(self, strategy: Dict):
        """Print recommended posting sequence."""
        sequence_table = Table(show_header=True, header_style="bold green")
        sequence_table.add_column("#")
        sequence_table.add_column("File")
        sequence_table.add_column("Theme")
        sequence_table.add_column("Tone")
        sequence_table.add_column("Audience")
        
        for post in strategy.get('recommended_sequence', []):
            sequence_table.add_row(
                str(post['position']),
                post['filename'],
                post.get('theme', '').title(),
                post['recommended_tone'],
                post['target_audience'].title()
            )
        
        self.console.print("\n")
        self.console.print(Panel(sequence_table, title="Posting Sequence"))
    
    def _print_cross_references(self, strategy: Dict):
        """Print cross-references between posts."""
        refs_tree = Tree("[bold]Cross References")
        
        # Group references by source file
        refs_by_source = {}
        for ref in strategy.get('cross_references', []):
            if ref['from_file'] not in refs_by_source:
                refs_by_source[ref['from_file']] = []
            refs_by_source[ref['from_file']].append(ref)
        
        # Create tree structure
        for from_file, refs in refs_by_source.items():
            file_node = refs_tree.add(f"[cyan]{from_file}")
            for ref in refs:
                file_node.add(
                    f"→ {ref['to_file']}: "
                    f"[italic]{ref['reference_text']}[/] "
                    f"({ref.get('strength', 0)})"
                )
        
        self.console.print("\n")
        self.console.print(Panel(refs_tree, title="Content Connections"))
    
    def _print_audience_split(self, strategy: Dict):
        """Print audience distribution analysis."""
        split = strategy.get('audience_split', {})
        total = split.get('technical', 0) + split.get('business', 0)
        
        if total > 0:
            tech_percent = (split.get('technical', 0) / total) * 100
            biz_percent = (split.get('business', 0) / total) * 100
            
            split_table = Table(show_header=False)
            split_table.add_column("Audience")
            split_table.add_column("Distribution")
            
            split_table.add_row(
                "Technical",
                f"{'█' * int(tech_percent/5)} {tech_percent:.1f}%"
            )
            split_table.add_row(
                "Business",
                f"{'█' * int(biz_percent/5)} {biz_percent:.1f}%"
            )
            
            self.console.print("\n")
            self.console.print(Panel(split_table, title="Audience Distribution"))
    
    def _print_timeline(self, strategy: Dict):
        """Print posting timeline recommendations."""
        timeline = strategy.get('posting_timeline', {})
        
        timeline_table = Table(show_header=False)
        timeline_table.add_column("Metric")
        timeline_table.add_column("Value")
        
        timeline_table.add_row("Frequency", timeline.get('frequency', ''))
        timeline_table.add_row("Duration", timeline.get('duration', ''))
        timeline_table.add_row(
            "Best Times",
            "\n".join(timeline.get('best_times', []))
        )
        
        self.console.print("\n")
        self.console.print(Panel(timeline_table, title="Posting Timeline"))
    
    def edit_sequence(self, strategy: Dict) -> Dict:
        """Interactive sequence editor."""
        sequence = strategy.get('recommended_sequence', [])
        
        self.console.print("\n[bold]Current Sequence:[/]")
        for i, post in enumerate(sequence):
            self.console.print(f"{i+1}. {post['filename']}")
        
        while True:
            action = self.console.input(
                "\n[bold]Edit Actions:[/]\n"
                "1. Move post\n"
                "2. Remove post\n"
                "3. Done\n"
                "Choose action (1-3): "
            )
            
            if action == "1":
                # Move post
                from_idx = int(self.console.input("Move from position: ")) - 1
                to_idx = int(self.console.input("Move to position: ")) - 1
                
                if 0 <= from_idx < len(sequence) and 0 <= to_idx < len(sequence):
                    post = sequence.pop(from_idx)
                    sequence.insert(to_idx, post)
                    
                    # Update positions
                    for i, p in enumerate(sequence):
                        p['position'] = i + 1
            
            elif action == "2":
                # Remove post
                idx = int(self.console.input("Remove position: ")) - 1
                if 0 <= idx < len(sequence):
                    sequence.pop(idx)
                    
                    # Update positions
                    for i, p in enumerate(sequence):
                        p['position'] = i + 1
            
            elif action == "3":
                break
            
            # Show updated sequence
            self.console.print("\n[bold]Updated Sequence:[/]")
            for i, post in enumerate(sequence):
                self.console.print(f"{i+1}. {post['filename']}")
        
        strategy['recommended_sequence'] = sequence
        return strategy
    
    def customize_themes(self, strategy: Dict) -> Dict:
        """Interactive theme customization."""
        themes = strategy.get('content_themes', [])
        excluded = []
        
        self.console.print("\n[bold]Current Themes:[/]")
        for theme in themes:
            self.console.print(f"- {theme}")
        
        while True:
            theme = self.console.input(
                "\nEnter theme to exclude (or 'done' to finish): "
            ).lower()
            
            if theme == 'done':
                break
            
            if theme in themes:
                excluded.append(theme)
                self.console.print(f"Excluded: {theme}")
            else:
                self.console.print("[red]Theme not found[/]")
        
        if excluded:
            if 'customization' not in strategy:
                strategy['customization'] = {}
            strategy['customization']['excluded_themes'] = excluded
        
        return strategy
    
    def set_audience_preference(self, strategy: Dict) -> Dict:
        """Set audience preference for content."""
        self.console.print("\n[bold]Set Audience Preference:[/]")
        self.console.print("1. Technical focus")
        self.console.print("2. Business focus")
        self.console.print("3. Balanced (default)")
        
        choice = self.console.input("Choose preference (1-3): ")
        
        if choice in ["1", "2"]:
            if 'customization' not in strategy:
                strategy['customization'] = {}
            strategy['customization']['audience_preference'] = (
                "technical" if choice == "1" else "business"
            )
        
        return strategy 