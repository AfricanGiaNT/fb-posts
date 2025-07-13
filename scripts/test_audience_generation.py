import os
import sys
from pathlib import Path

# Add scripts directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from ai_content_generator import AIContentGenerator

def main():
    """
    Tests the audience-aware content generation feature.
    It generates two versions of a Facebook post from the same markdown file:
    1. For a 'business' audience.
    2. For a 'technical' audience.
    The results are printed to the console for comparison.
    """
    print("🧪 Testing Audience-Aware Content Generation...")
    print("=" * 50)

    try:
        # 1. Initialize Config and AI Generator
        config = ConfigManager()
        ai_gen = AIContentGenerator(config)

        # Check for API key
        if not config.openai_api_key or config.openai_api_key == "your_openai_api_key_here":
            print("❌ OpenAI API key not configured in .env file. Aborting.")
            sys.exit(1)

        # 2. Load Markdown Content
        markdown_file = "content/test_markdown_for_phase2.md"
        print(f"📖 Loading markdown from: {markdown_file}")
        with open(markdown_file, 'r') as f:
            sample_md = f.read()
        
        print("✅ Markdown loaded successfully.")
        print("-" * 50)

        # 3. Generate for Business Audience
        print("🏢 Generating for 'Business Owner' audience...")
        business_result = ai_gen.generate_facebook_post(
            sample_md, 
            audience_type='business'
        )
        if business_result and business_result.get('post_content'):
            print("✅ Business post generated successfully.")
            print("\n--- 🏢 BUSINESS POST ---")
            print(f"TONE: {business_result.get('tone_used')}")
            print(f"REASON: {business_result.get('tone_reason')}")
            print("---\n")
            print(business_result.get('post_content'))
            print("\n" + "-" * 25)
        else:
            print("❌ Failed to generate business post.")

        # 4. Generate for Technical Audience
        print("\n💻 Generating for 'Technical' audience...")
        technical_result = ai_gen.generate_facebook_post(
            sample_md,
            audience_type='technical'
        )
        if technical_result and technical_result.get('post_content'):
            print("✅ Technical post generated successfully.")
            print("\n--- 💻 TECHNICAL POST ---")
            print(f"TONE: {technical_result.get('tone_used')}")
            print(f"REASON: {technical_result.get('tone_reason')}")
            print("---\n")
            print(technical_result.get('post_content'))
            print("\n" + "-" * 25)
        else:
            print("❌ Failed to generate technical post.")

        print("\n✅ Test complete.")

    except FileNotFoundError:
        print(f"❌ Error: Markdown file not found at {markdown_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 