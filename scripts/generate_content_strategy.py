#!/usr/bin/env python3
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

# Add parent directory to path to import from implemented/
sys.path.append(str(Path(__file__).parent.parent))
from implemented.content_strategy_generator import ContentStrategyGenerator

def load_markdown_files(directory: str) -> List[Dict]:
    """Load and analyze markdown files from directory."""
    files = []
    for idx, file_path in enumerate(Path(directory).glob("*.md")):
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Simple phase detection based on filename
            phase = "implementation"
            if "planning" in file_path.name:
                phase = "planning"
            elif "debug" in file_path.name:
                phase = "debugging"
            elif "result" in file_path.name:
                phase = "results"
            
            # Simple theme extraction (in real implementation, this would be more sophisticated)
            themes = []
            if "architecture" in content.lower():
                themes.append("architecture")
            if "implementation" in content.lower():
                themes.append("implementation")
            if "debug" in content.lower():
                themes.append("debugging")
            if "result" in content.lower():
                themes.append("results")
            
            files.append({
                "file_id": f"file{idx + 1}",
                "filename": file_path.name,
                "file_phase": phase,
                "key_themes": themes,
                "content": content
            })
    return files

def main():
    parser = argparse.ArgumentParser(description='Generate content strategy from markdown files')
    parser.add_argument('directory', help='Directory containing markdown files')
    parser.add_argument('--output', '-o', help='Output JSON file', default='content_strategy.json')
    
    args = parser.parse_args()
    
    try:
        # Load and analyze files
        files = load_markdown_files(args.directory)
        if not files:
            print("No markdown files found in directory")
            return
        
        # Create project analysis
        project_analysis = {
            "project_theme": "Project Development",  # This would be extracted in real implementation
            "source_files": files
        }
        
        # Generate strategy
        generator = ContentStrategyGenerator()
        strategy = generator.generate_optimal_strategy(project_analysis)
        
        # Save strategy to file
        with open(args.output, 'w') as f:
            json.dump(strategy, f, indent=2)
            
        print(f"\nContent strategy generated successfully!")
        print(f"Strategy saved to: {args.output}")
        
        # Print summary
        print("\nStrategy Summary:")
        print(f"- Number of posts: {strategy['estimated_posts']}")
        print(f"- Narrative flow: {strategy['narrative_flow']}")
        print(f"- Content themes: {', '.join(strategy['content_themes'])}")
        print("\nAudience split:")
        print(f"- Technical: {strategy['audience_split']['technical']} posts")
        print(f"- Business: {strategy['audience_split']['business']} posts")
        print("\nRecommended posting timeline:")
        print(f"- Frequency: {strategy['posting_timeline']['frequency']}")
        print(f"- Duration: {strategy['posting_timeline']['duration']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 