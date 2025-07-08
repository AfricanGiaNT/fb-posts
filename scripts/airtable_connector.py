"""
Airtable Connector for Content Tracking
"""

from airtable import Airtable
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class AirtableConnector:
    """Handles Airtable integration for content tracking."""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.airtable = Airtable(
            base_id=self.config.airtable_base_id,
            table_name=self.config.airtable_table_name,
            api_key=self.config.airtable_api_key
        )
    
    def save_draft(self, post_data: Dict, title: str, review_status: str = "📝 To Review") -> str:
        """
        Save a generated draft to Airtable.
        
        Args:
            post_data: Dictionary containing post content and metadata
            title: Title for the post
            review_status: Initial review status
            
        Returns:
            Airtable record ID
        """
        try:
            # Extract post content
            post_content = post_data.get('post_content', '')
            
            # Map AI tone to Airtable tone options (exact values from screenshot)
            ai_tone = post_data.get('tone_used', '')
            tone_mapping = {
                'Behind-the-Build': '🧩 Behind-the-Build',
                'What Broke': '💡 What Broke',
                'Finished & Proud': '🚀 Finished & Proud', 
                'Problem → Solution → Result': '🎯 Problem → Solution → Result',
                'Mini Lesson': '📓 Mini Lesson'
            }
            
            # Find matching tone or default to Behind-the-Build
            airtable_tone = None
            for key, value in tone_mapping.items():
                if key.lower() in ai_tone.lower():
                    airtable_tone = value
                    break
            
            if not airtable_tone:
                airtable_tone = '🧩 Behind-the-Build'  # Default tone
            
            # Extract tags that match Airtable options exactly
            extracted_tags = self._extract_tags_from_content(post_data.get('original_markdown', ''))
            
            # Prepare the record data matching user's Airtable structure
            record_data = {
                'Post Title': title,
                'Markdown Source': post_data.get('original_markdown', ''),
                'Generated Draft': post_content,
                'Tone Used': airtable_tone,
                'Review Status': review_status,  # This should already be properly formatted
                'AI Notes or Edits': post_data.get('tone_reason', ''),
                'Tags / Categories': extracted_tags
            }
            
            # Add scheduled date if provided (optional)
            if 'scheduled_date' in post_data:
                record_data['Scheduled Date'] = post_data['scheduled_date']
            
            # Add regeneration info if applicable
            if post_data.get('is_regeneration'):
                record_data['AI Notes or Edits'] += f"\n\nRegenerated with feedback: {post_data.get('regenerated_with_feedback', '')}"
            
            # Save to Airtable
            created_record = self.airtable.insert(record_data)
            return created_record['id']
            
        except Exception as e:
            raise Exception(f"Error saving draft to Airtable: {str(e)}")
    
    def update_draft_status(self, record_id: str, status: str, reviewed_content: Optional[str] = None) -> bool:
        """
        Update the review status of a draft.
        
        Args:
            record_id: Airtable record ID
            status: New review status (should be one of: "📝 To Review", "✅ Approved", "📝 Needs Editing", "❌ Rejected")
            reviewed_content: Optional reviewed/edited content
            
        Returns:
            True if successful
        """
        try:
            # Map status to correct Airtable values if needed (exact from screenshot)
            status_mapping = {
                'To Review': '📝 To Review',
                'Approved': '✅ Approved',
                'Needs Editing': '📝 Needs Editing',
                'Rejected': '❌ Rejected'
            }
            
            # Use mapped status or original if already correct
            mapped_status = status_mapping.get(status, status)
            
            update_data = {
                'Review Status': mapped_status,
                'Review Completion': datetime.now().isoformat()
            }
            
            if reviewed_content:
                update_data['Reviewed Draft'] = reviewed_content
            
            # Calculate days until scheduled if scheduled date exists
            record = self.airtable.get(record_id)
            if record and 'fields' in record and 'Scheduled Date' in record['fields']:
                scheduled_date = record['fields']['Scheduled Date']
                if scheduled_date:
                    try:
                        scheduled = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
                        now = datetime.now()
                        days_until = (scheduled - now).days
                        update_data['Days Until Scheduled'] = days_until
                    except:
                        pass  # Skip if date parsing fails
            
            self.airtable.update(record_id, update_data)
            return True
            
        except Exception as e:
            raise Exception(f"Error updating draft status: {str(e)}")
    
    def get_draft_by_id(self, record_id: str) -> Optional[Dict]:
        """
        Get a draft by its Airtable record ID.
        
        Args:
            record_id: Airtable record ID
            
        Returns:
            Draft data or None if not found
        """
        try:
            record = self.airtable.get(record_id)
            return record
        except Exception as e:
            print(f"Error getting draft by ID: {e}")
            return None
    
    def get_recent_drafts(self, limit: int = 10) -> List[Dict]:
        """
        Get recent drafts from Airtable.
        
        Args:
            limit: Number of drafts to retrieve
            
        Returns:
            List of draft records
        """
        try:
            # Sort by creation time (Airtable's default created time)
            records = self.airtable.get_all(
                max_records=limit,
                sort=['-CREATED_TIME']
            )
            return records
        except Exception as e:
            print(f"Error getting recent drafts: {e}")
            return []
    
    def get_drafts_by_status(self, status: str, limit: int = 10) -> List[Dict]:
        """
        Get drafts by review status.
        
        Args:
            status: Review status to filter by (with or without emoji prefix)
            limit: Number of drafts to retrieve
            
        Returns:
            List of draft records
        """
        try:
            # Map status to correct Airtable values for filtering
            status_mapping = {
                'To Review': '📝 To Review',
                'Approved': '✅ Approved',
                'Needs Editing': '📝 Needs Editing',
                'Rejected': '❌ Rejected'
            }
            
            # Use mapped status or original if already correct
            mapped_status = status_mapping.get(status, status)
            
            records = self.airtable.get_all(
                formula=f"{{Review Status}} = '{mapped_status}'",
                max_records=limit,
                sort=['-CREATED_TIME']
            )
            return records
        except Exception as e:
            print(f"Error getting drafts by status: {e}")
            return []
    
    def _extract_tags_from_content(self, markdown_content: str) -> List[str]:
        """
        Extract relevant tags from markdown content.
        Only returns tags that match the exact Airtable options.
        
        Args:
            markdown_content: The markdown content to analyze
            
        Returns:
            List of extracted tags matching Airtable options
        """
        tags = []
        content_lower = markdown_content.lower()
        
        # EXACT tag options from user's Airtable (from screenshot)
        available_tags = {
            'Automation': ['automation', 'automated', 'automate', 'ai', 'bot'],
            'Telegram Bot': ['telegram', 'bot', 'chatbot'],
            'Business Tracker': ['business', 'tracker', 'tracking', 'analytics'],
            'Storytelling': ['story', 'narrative', 'storytelling', 'post', 'content'],
            'Reflection': ['reflection', 'lesson', 'insight', 'learning', 'philosophy']
        }
        
        for tag, keywords in available_tags.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(tag)
        
        # Return only tags that exist in Airtable (max 5)
        return tags[:5]
    
    def _generate_improvement_suggestions(self, post_data: Dict) -> str:
        """
        Generate improvement suggestions based on the post content.
        
        Args:
            post_data: Dictionary containing post content and metadata
            
        Returns:
            String with improvement suggestions
        """
        suggestions = []
        post_content = post_data.get('post_content', '')
        markdown_content = post_data.get('original_markdown', '')
        
        # Length-based suggestions
        if len(post_content) < 100:
            suggestions.append("Consider expanding the content for better engagement")
        elif len(post_content) > 1000:
            suggestions.append("Consider shortening for better readability")
        
        # Emoji suggestions
        if '🚀' not in post_content and '✨' not in post_content and '💡' not in post_content:
            suggestions.append("Consider adding relevant emojis for visual appeal")
        
        # CTA suggestions
        if 'dm me' not in post_content.lower() and 'comment' not in post_content.lower():
            suggestions.append("Consider adding a call-to-action for engagement")
        
        # Technical detail suggestions
        if 'automation' in markdown_content.lower() or 'ai' in markdown_content.lower():
            if 'time saved' not in post_content.lower() and 'problem solved' not in post_content.lower():
                suggestions.append("Consider quantifying the impact or results")
        
        return '; '.join(suggestions) if suggestions else "Content looks good!"
    
    def test_connection(self) -> bool:
        """
        Test the Airtable connection.
        
        Returns:
            True if connection successful
        """
        try:
            # Try to get one record to test connection
            self.airtable.get_all(max_records=1)
            return True
        except Exception as e:
            print(f"Airtable connection test failed: {e}")
            return False
    
    def create_content_tracker_fields(self) -> Dict:
        """
        Return the expected field structure for the Content Tracker table.
        This matches the user's actual Airtable structure.
        
        Returns:
            Dict describing the expected fields
        """
        return {
            'Markdown Source': 'Long text - Original markdown content',
            'Generated Draft': 'Long text - AI-generated Facebook post',
            'Tone Used': 'Single select (Behind-the-Build, What Broke, Finished & Proud, Problem → Solution → Result, Mini Lesson)',
            'Review Status': 'Single select (To Review, Approved, Needs Editing, Rejected)',
            'Scheduled Date': 'Date - When to publish the post',
            'Reviewed Draft': 'Long text - Final edited version',
            'AI Notes or Edits': 'Long text - AI reasoning and feedback',
            'Tags / Categories': 'Multiple select - Auto-generated tags',
            'Post URL (After Publishing)': 'URL - Link to published Facebook post',
            'Days Until Scheduled': 'Number - Calculated days until scheduled date',
            'Review Completion': 'Date - When review was completed',
            'Improvement Suggestions': 'Long text - AI-generated suggestions for improvement'
        } 