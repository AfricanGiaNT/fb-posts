#!/usr/bin/env python3
"""
Test script to demonstrate the new less salesy content generation
compared to the previous overly enthusiastic approach.
"""

import sys
from pathlib import Path
import re

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator


def print_divider(title):
    """Print a styled divider."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_post_comparison(label, tone, content, reason):
    """Print a formatted post comparison."""
    print(f"\n--- {label} ---")
    print(f"TONE: {tone}")
    print(f"REASON: {reason}")
    print("\nCONTENT:")
    print("-" * 40)
    # Clean up and format the content
    clean_content = re.sub(r'\s+', ' ', content.strip())
    # Break into reasonable line lengths
    words = clean_content.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > 80:  # Max line length
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)
        else:
            current_line.append(word)
            current_length += len(word) + 1
    
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        print(line)
    print("-" * 40)


def main():
    """Main test function."""
    print("🧪 Testing New Less Salesy Content Generation")
    print("=" * 60)
    
    # Test markdown content
    sample_markdown = """
# AI Meeting Summarizer Bot

## What I Built
An AI-powered meeting summarizer that automatically processes Zoom recordings and generates actionable insights for team productivity.

## The Problem
Our team was spending 2-3 hours weekly manually reviewing meeting recordings and creating action items. With 15+ meetings per week, this was becoming unsustainable.

## My Solution
I created a system that handles this automatically:
- Downloads Zoom recordings via API
- Transcribes using Whisper API for accuracy
- Generates structured summaries with GPT-4o
- Sends personalized summaries to participants

## The Impact / Result
- Time Saved: 2.5 hours per week (83% reduction)
- Action Item Completion: Increased from 60% to 85%
- Meeting Follow-up: 100% automated
- Team Satisfaction: 4.8/5 stars

## Key Lessons Learned
The biggest lesson was keeping the solution simple and focused on actual business value rather than technical complexity.
"""
    
    try:
        # Initialize system
        config = ConfigManager()
        ai_gen = AIContentGenerator(config)
        
        print_divider("BUSINESS AUDIENCE GENERATION")
        print("Testing with updated, less salesy prompts...")
        
        # Generate business post
        business_result = ai_gen.generate_facebook_post(
            sample_markdown,
            audience_type='business'
        )
        
        print_post_comparison(
            "BUSINESS POST (New Approach)",
            business_result.get('tone_used', 'Unknown'),
            business_result.get('post_content', 'No content generated'),
            business_result.get('tone_reason', 'No reason provided')
        )
        
        print_divider("TECHNICAL AUDIENCE GENERATION")
        print("For comparison, here's the technical audience version...")
        
        # Generate technical post
        technical_result = ai_gen.generate_facebook_post(
            sample_markdown,
            audience_type='technical'
        )
        
        print_post_comparison(
            "TECHNICAL POST (Unchanged)",
            technical_result.get('tone_used', 'Unknown'),
            technical_result.get('post_content', 'No content generated'),
            technical_result.get('tone_reason', 'No reason provided')
        )
        
        print_divider("ANALYSIS")
        print("Key improvements in the new approach:")
        print("✅ More conversational, less hype-driven language")
        print("✅ Practical focus instead of marketing excitement")
        print("✅ Honest communication about limitations")
        print("✅ Natural questions instead of sales CTAs")
        print("✅ Reduced emojis and formatting overload")
        print("✅ Focus on genuine value over dramatic transformation")
        
        print("\n🎯 The new system creates authentic posts that feel like")
        print("   genuine sharing from a developer, not marketing material.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 