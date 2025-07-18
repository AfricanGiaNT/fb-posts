"""
Strategy Customization UI Components for Multi-File Upload System
Handles interactive interfaces for customizing content strategy.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

class StrategyCustomizationUI:
    """Manages UI components for strategy customization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def show_strategy_overview(self, strategy: Dict) -> str:
        """Generate strategy overview message."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            message = (
                f"📋 Content Strategy Overview\n\n"
                f"Project Theme: {strategy.get('project_theme', 'N/A')}\n"
                f"Estimated Posts: {len(strategy.get('recommended_sequence', []))}\n\n"
                f"Recommended Sequence:\n"
            )
            
            for i, post in enumerate(strategy.get('recommended_sequence', []), 1):
                message += (
                    f"{i}. {post.get('filename', 'Unknown')}\n"
                    f"   Theme: {post.get('theme', 'N/A')}\n"
                    f"   Tone: {post.get('tone', 'N/A')}\n"
                )
                
            message += "\nCross-References:\n"
            for ref in strategy.get('cross_references', []):
                message += (
                    f"• {ref.get('source_id', 'Unknown')} → "
                    f"{ref.get('target_id', 'Unknown')}: "
                    f"{ref.get('type', 'Unknown')}\n"
                )
                
            message += "\nCustomization Options:\n"
            message += "1. 🔄 Reorder sequence\n"
            message += "2. ➕ Add custom post\n"
            message += "3. ➖ Remove post\n"
            message += "4. 🎨 Change tone\n"
            message += "5. ✅ Confirm strategy"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing strategy overview: {str(e)}")
            return "⚠️ Error displaying strategy overview"
            
    def show_sequence_editor(self, strategy: Dict) -> str:
        """Generate sequence editor interface."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            message = (
                f"🔄 Sequence Editor\n\n"
                f"Current Sequence:\n"
            )
            
            for i, post in enumerate(strategy.get('recommended_sequence', []), 1):
                message += (
                    f"{i}. {post.get('filename', 'Unknown')}\n"
                    f"   Theme: {post.get('theme', 'N/A')}\n"
                )
                
            message += "\nTo reorder:"
            message += "\n1. Enter new sequence (e.g., '3,1,2,4')"
            message += "\n2. Type 'done' to finish"
            message += "\n3. Type 'cancel' to keep current order"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing sequence editor: {str(e)}")
            return "⚠️ Error displaying sequence editor"
            
    def show_tone_selector(self, file_id: str, strategy: Dict) -> str:
        """Generate tone selection interface."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            # Find current tone
            current_tone = "N/A"
            for post in strategy.get('recommended_sequence', []):
                if post.get('file_id') == file_id:
                    current_tone = post.get('tone', 'N/A')
                    break
                    
            message = (
                f"🎨 Tone Selector\n\n"
                f"File: {file_id}\n"
                f"Current Tone: {current_tone}\n\n"
                f"Available Tones:\n"
                f"1. 🏗️ Behind-the-Build\n"
                f"2. 💔 What Broke\n"
                f"3. 🎯 Problem → Solution\n"
                f"4. ✨ Finished & Proud\n"
                f"5. 📚 Mini Lesson\n\n"
                f"Select a number (1-5) or type 'cancel'"
            )
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing tone selector: {str(e)}")
            return "⚠️ Error displaying tone selector"
            
    def show_cross_reference_editor(self, strategy: Dict) -> str:
        """Generate cross-reference editor interface."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            message = (
                f"🔗 Cross-Reference Editor\n\n"
                f"Current References:\n"
            )
            
            for i, ref in enumerate(strategy.get('cross_references', []), 1):
                message += (
                    f"{i}. {ref.get('source_id', 'Unknown')} → "
                    f"{ref.get('target_id', 'Unknown')}\n"
                    f"   Type: {ref.get('type', 'Unknown')}\n"
                )
                
            message += "\nReference Types:\n"
            message += "• continuation - Sequential story flow\n"
            message += "• related - Similar themes or concepts\n"
            message += "• technical - Technical dependencies\n"
            message += "• contrast - Different perspectives\n\n"
            
            message += "To add: 'add source_id target_id type'\n"
            message += "To remove: 'remove #'\n"
            message += "Type 'done' when finished"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing reference editor: {str(e)}")
            return "⚠️ Error displaying reference editor"
            
    def show_custom_post_creator(self, strategy: Dict) -> str:
        """Generate custom post creation interface."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            message = (
                f"➕ Custom Post Creator\n\n"
                f"Available Files:\n"
            )
            
            # Show files not in sequence
            used_files = {post.get('file_id') for post in strategy.get('recommended_sequence', [])}
            all_files = strategy.get('available_files', [])
            
            for file in all_files:
                if file.get('file_id') not in used_files:
                    message += (
                        f"• {file.get('filename', 'Unknown')}\n"
                        f"  ID: {file.get('file_id', 'Unknown')}\n"
                        f"  Theme: {file.get('theme', 'N/A')}\n"
                    )
                    
            message += "\nTo create custom post:"
            message += "\n1. Enter file ID"
            message += "\n2. Choose tone (1-5)"
            message += "\n3. Set position (1-N or 'end')"
            message += "\nOr type 'cancel' to exit"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing custom post creator: {str(e)}")
            return "⚠️ Error displaying custom post creator"
            
    def show_confirmation_prompt(self, strategy: Dict) -> str:
        """Generate strategy confirmation prompt."""
        try:
            if not strategy:
                return "⚠️ Error: Invalid strategy data"
                
            message = (
                f"✅ Confirm Strategy\n\n"
                f"Final Sequence ({len(strategy.get('recommended_sequence', []))} posts):\n"
            )
            
            for i, post in enumerate(strategy.get('recommended_sequence', []), 1):
                message += (
                    f"{i}. {post.get('filename', 'Unknown')}\n"
                    f"   Theme: {post.get('theme', 'N/A')}\n"
                    f"   Tone: {post.get('tone', 'N/A')}\n"
                )
                
            message += f"\nCross-References: {len(strategy.get('cross_references', []))}\n"
            message += f"Custom Posts: {strategy.get('custom_post_count', 0)}\n\n"
            
            message += "Type 'confirm' to proceed with generation\n"
            message += "Type 'edit' to make more changes\n"
            message += "Type 'cancel' to start over"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing confirmation prompt: {str(e)}")
            return "⚠️ Error displaying confirmation prompt" 