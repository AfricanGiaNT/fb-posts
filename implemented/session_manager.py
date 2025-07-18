"""
Session Management for Multi-File Upload System
Handles session persistence, backup, and recovery.
"""

import json
import logging
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
import os
from pathlib import Path

class SessionManager:
    """Manages session persistence and recovery."""
    
    def __init__(self, backup_dir: str = "session_backups"):
        self.logger = logging.getLogger(__name__)
        self.backup_dir = backup_dir
        self._ensure_backup_dir()
        self._backup_task = None
        
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        try:
            Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating backup directory: {str(e)}")
            
    async def save_session(self, user_id: int, session: Dict) -> bool:
        """
        Save session to persistent storage.
        
        Args:
            user_id: User ID
            session: Session data dictionary
            
        Returns:
            Success status
        """
        try:
            # Add timestamp
            session['last_saved'] = datetime.now().isoformat()
            
            # Save to file
            file_path = os.path.join(self.backup_dir, f"session_{user_id}.json")
            with open(file_path, 'w') as f:
                json.dump(session, f, indent=2)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving session: {str(e)}")
            return False
            
    async def load_session(self, user_id: int) -> Optional[Dict]:
        """
        Load session from persistent storage.
        
        Args:
            user_id: User ID
            
        Returns:
            Session data dictionary or None if not found
        """
        try:
            file_path = os.path.join(self.backup_dir, f"session_{user_id}.json")
            
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r') as f:
                session = json.load(f)
                
            # Validate session timeout
            if self._is_session_expired(session):
                await self.clear_session(user_id)
                return None
                
            return session
            
        except Exception as e:
            self.logger.error(f"Error loading session: {str(e)}")
            return None
            
    async def create_backup(self, user_id: int, session: Dict) -> bool:
        """
        Create session backup.
        
        Args:
            user_id: User ID
            session: Session data dictionary
            
        Returns:
            Success status
        """
        try:
            # Get existing backups
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith(f"backup_{user_id}_")
            ])
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_file = os.path.join(
                self.backup_dir, 
                f"backup_{user_id}_{timestamp}.json"
            )
            
            # Save backup
            with open(backup_file, 'w') as f:
                json.dump(session, f, indent=2)
                
            # Get updated list of backups
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith(f"backup_{user_id}_")
            ])
            
            # Remove old backups if we have more than 5
            while len(backup_files) > 5:
                oldest_backup = backup_files[0]
                try:
                    os.remove(os.path.join(self.backup_dir, oldest_backup))
                    backup_files = backup_files[1:]
                except Exception as e:
                    self.logger.error(f"Error removing backup {oldest_backup}: {str(e)}")
                    break
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            return False
            
    async def restore_from_backup(self, user_id: int) -> Optional[Dict]:
        """
        Restore session from latest backup.
        
        Args:
            user_id: User ID
            
        Returns:
            Restored session data or None if no backup found
        """
        try:
            # Find latest backup
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith(f"backup_{user_id}_")
            ])
            
            if not backup_files:
                return None
                
            latest_backup = backup_files[-1]
            backup_path = os.path.join(self.backup_dir, latest_backup)
            
            # Load backup
            with open(backup_path, 'r') as f:
                session = json.load(f)
                
            return session
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {str(e)}")
            return None
            
    async def clear_session(self, user_id: int) -> bool:
        """
        Clear session data.
        
        Args:
            user_id: User ID
            
        Returns:
            Success status
        """
        try:
            # Remove session file
            session_file = os.path.join(self.backup_dir, f"session_{user_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing session: {str(e)}")
            return False
            
    async def start_backup_task(self, user_id: int, session: Dict):
        """Start periodic backup task."""
        if self._backup_task is None or self._backup_task.done():
            self._backup_task = asyncio.create_task(
                self._periodic_backup(user_id, session)
            )
            
    async def stop_backup_task(self):
        """Stop periodic backup task."""
        if self._backup_task and not self._backup_task.done():
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass
            
    async def _periodic_backup(self, user_id: int, session: Dict):
        """Periodic backup task."""
        try:
            while True:
                await asyncio.sleep(300)  # 5 minutes
                await self.create_backup(user_id, session)
                
        except asyncio.CancelledError:
            pass
            
    async def _cleanup_old_backups(self, user_id: int):
        """Clean up old backup files."""
        try:
            # Get all backup files for this user
            backup_files = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith(f"backup_{user_id}_")
            ])
            
            # Remove old backups if we have more than 5
            if len(backup_files) > 5:
                files_to_remove = backup_files[:-5]  # Keep the 5 most recent
                for old_backup in files_to_remove:
                    try:
                        os.remove(os.path.join(self.backup_dir, old_backup))
                    except Exception as e:
                        self.logger.error(f"Error removing backup {old_backup}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {str(e)}")
            
    def _is_session_expired(self, session: Dict) -> bool:
        """Check if session has expired."""
        try:
            session_start = datetime.fromisoformat(
                session.get('session_started', datetime.now().isoformat())
            )
            time_elapsed = datetime.now() - session_start
            
            return time_elapsed > timedelta(minutes=30)
            
        except Exception:
            return True  # Assume expired on error 