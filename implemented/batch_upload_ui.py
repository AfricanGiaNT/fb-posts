"""
Batch Upload UI Components for Multi-File Upload System
Handles UI elements and progress indicators for batch file uploads.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class BatchUploadUI:
    """Manages UI components for batch file upload workflow."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    async def show_upload_progress(self, file_data: Dict) -> str:
        """
        Generate upload progress message for a file.
        
        Args:
            file_data: Dictionary containing file metadata
            
        Returns:
            Formatted progress message
        """
        try:
            status_emoji = self._get_status_emoji(file_data['processing_status'])
            
            message = (
                f"{status_emoji} {file_data['filename']}\n"
                f"   Phase: {file_data['file_phase']}\n"
                f"   Words: {file_data.get('word_count', 'Calculating...')}\n"
                f"   Status: {self._format_status(file_data['processing_status'])}\n"
            )
            
            if file_data.get('key_themes'):
                message += f"   Themes: {', '.join(file_data['key_themes'])}\n"
                
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing upload progress: {str(e)}")
            return "⚠️ Error displaying progress"
            
    async def show_batch_status(self, session: Dict) -> str:
        """
        Generate overall batch upload status message.
        
        Args:
            session: Current session dictionary
            
        Returns:
            Formatted status message
        """
        try:
            total_files = len(session['source_files'])
            processed = sum(1 for f in session['source_files'] 
                          if f['processing_status'] == 'analyzed')
            
            time_remaining = self._calculate_time_remaining(session)
            
            message = (
                f"📚 Batch Upload Status ({processed}/{total_files})\n\n"
                f"Time Remaining: {time_remaining}\n\n"
            )
            
            for file_data in session['source_files']:
                progress = await self.show_upload_progress(file_data)
                message += progress + "\n"
                
            message += "\nCommands:\n"
            message += "• /project - Generate project overview\n"
            message += "• /strategy - Show content strategy\n"
            message += "• /done - Finish uploading\n"
            message += "• /cancel - Exit batch mode"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing batch status: {str(e)}")
            return "⚠️ Error displaying batch status"
            
    def show_timeout_warning(self, session: Dict) -> Optional[str]:
        """
        Generate timeout warning message if needed.
        
        Args:
            session: Current session dictionary
            
        Returns:
            Warning message if timeout is approaching, None otherwise
        """
        try:
            session_start = session['session_started']
            time_elapsed = datetime.now() - session_start
            
            # 30-minute timeout
            if time_elapsed > timedelta(minutes=25):
                remaining = timedelta(minutes=30) - time_elapsed
                return (
                    f"⚠️ Session Timeout Warning\n\n"
                    f"Session will expire in {remaining.seconds // 60} minutes.\n"
                    f"Please complete your uploads or use /done to finish."
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking timeout: {str(e)}")
            return None
            
    def show_completion_summary(self, session: Dict) -> str:
        """
        Generate batch upload completion summary.
        
        Args:
            session: Current session dictionary
            
        Returns:
            Formatted completion summary
        """
        try:
            total_files = len(session['source_files'])
            total_words = sum(f.get('word_count', 0) for f in session['source_files'])
            
            message = (
                f"✅ Batch Upload Complete\n\n"
                f"Files Processed: {total_files}\n"
                f"Total Words: {total_words}\n\n"
                f"Project Overview:\n"
            )
            
            if 'project_overview' in session:
                overview = session['project_overview']
                message += f"• Theme: {overview.get('project_theme', 'N/A')}\n"
                message += f"• Technical Stack: {', '.join(overview.get('technical_stack', ['N/A']))}\n"
                message += f"• Key Challenges: {len(overview.get('key_challenges', []))}\n"
            else:
                message += "• Theme: N/A\n"
                message += "• Technical Stack: N/A\n"
                message += "• Key Challenges: N/A\n"
                
            message += "\nNext Steps:\n"
            message += "1. Review project analysis (/project)\n"
            message += "2. Generate content strategy (/strategy)\n"
            message += "3. Begin content generation"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error showing completion summary: {str(e)}")
            return "⚠️ Error displaying completion summary"
            
    def _get_status_emoji(self, status: str) -> str:
        """Get appropriate emoji for file status."""
        status_emojis = {
            'pending': '⏳',
            'processing': '🔄',
            'analyzed': '✅',
            'error': '❌'
        }
        return status_emojis.get(status, '❓')
        
    def _format_status(self, status: str) -> str:
        """Format status string for display."""
        return status.replace('_', ' ').title()
        
    def _calculate_time_remaining(self, session: Dict) -> str:
        """Calculate and format remaining session time."""
        try:
            session_start = session['session_started']
            time_elapsed = datetime.now() - session_start
            time_remaining = timedelta(minutes=30) - time_elapsed
            
            if time_remaining.total_seconds() <= 0:
                return "Session expired"
                
            minutes = time_remaining.seconds // 60
            return f"{minutes} minutes"
            
        except Exception:
            return "Unknown" 