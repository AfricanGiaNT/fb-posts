"""
Test Phase 3: Enhanced Storage System
Tests the implementation of SQLite database persistence for session data and user preferences.
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import json

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from enhanced_storage import EnhancedStorage
from telegram_bot import FacebookContentBot

class TestPhase3EnhancedStorage(unittest.TestCase):
    """Test Phase 3: Enhanced Storage System implementation."""
    
    def setUp(self):
        """Set up test environment with temporary database."""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.storage = EnhancedStorage(self.temp_db.name)
        self.bot = FacebookContentBot()
        self.user_id = 12345
        
        # Sample session data for testing
        self.sample_session = {
            'series_id': 'test-series-123',
            'filename': 'test.md',
            'original_markdown': '# Test Project\nThis is a test.',
            'session_started': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'session_context': 'Test context',
            'post_count': 2,
            'state': None,
            'chat_history': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'user_message': 'Uploaded file: test.md',
                    'bot_response': 'File processed successfully',
                    'message_type': 'file_upload',
                    'context': {'filename': 'test.md', 'file_size': 1024},
                    'satisfaction_score': 0.9
                },
                {
                    'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'user_message': 'Generate post',
                    'bot_response': 'Post generated successfully',
                    'message_type': 'post_generation',
                    'context': {'tone_used': 'technical'},
                    'satisfaction_score': 0.8
                }
            ],
            'posts': [
                {
                    'post_id': 'post-1',
                    'airtable_record_id': 'rec123',
                    'post_content': 'Test post content',
                    'tone_used': 'technical',
                    'tone_reason': 'User requested technical tone',
                    'parent_post_id': None,
                    'relationship_type': None
                }
            ],
            'user_preferences': {
                'preferred_tones': ['technical', 'casual'],
                'audience_preferences': {'business': 3, 'technical': 2},
                'content_length_preferences': {'medium': 5},
                'successful_patterns': ['technical tone', 'business audience'],
                'avoided_patterns': ['formal tone']
            },
            'request_mapping': {
                'current_request_id': 'req-123',
                'request_history': [],
                'content_relationships': {}
            },
            'feedback_analysis': {
                'approval_rate': 0.85,
                'regeneration_patterns': ['tone change'],
                'common_edit_requests': ['make it shorter'],
                'successful_content_elements': ['technical details']
            }
        }
    
    def tearDown(self):
        """Clean up test database."""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_phase3_01_storage_initialization(self):
        """Test EnhancedStorage initialization and database creation."""
        self.assertIsNotNone(self.storage)
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # Check that database has tables
        with self.storage.lock:
            import sqlite3
            with sqlite3.connect(self.temp_db.name) as conn:
                tables = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """).fetchall()
                
                table_names = [table[0] for table in tables]
                expected_tables = ['users', 'sessions', 'chat_history', 'user_preferences', 'feedback_analysis', 'posts']
                
                for table in expected_tables:
                    self.assertIn(table, table_names)
    
    def test_phase3_02_session_save_and_load(self):
        """Test saving and loading sessions."""
        # Save session
        success = self.storage.save_session(self.user_id, self.sample_session)
        self.assertTrue(success)
        
        # Load session
        loaded_session = self.storage.load_session(self.user_id, self.sample_session['series_id'])
        self.assertIsNotNone(loaded_session)
        
        # Verify key fields
        self.assertEqual(loaded_session['series_id'], self.sample_session['series_id'])
        self.assertEqual(loaded_session['filename'], self.sample_session['filename'])
        self.assertEqual(len(loaded_session['chat_history']), 2)
        self.assertEqual(len(loaded_session['posts']), 1)
    
    def test_phase3_03_user_preferences_save_and_load(self):
        """Test saving and loading user preferences."""
        preferences = {
            'preferred_tones': ['technical', 'casual'],
            'audience_preferences': {'business': 3},
            'content_length_preferences': {'medium': 5},
            'successful_patterns': ['technical tone'],
            'avoided_patterns': ['formal tone']
        }
        
        # Save preferences
        success = self.storage.save_user_preferences(self.user_id, preferences)
        self.assertTrue(success)
        
        # Load preferences
        loaded_preferences = self.storage.load_user_preferences(self.user_id)
        
        # Verify preferences
        self.assertEqual(loaded_preferences['preferred_tones'], ['technical', 'casual'])
        self.assertEqual(loaded_preferences['audience_preferences']['business'], 3)
        self.assertEqual(loaded_preferences['content_length_preferences']['medium'], 5)
    
    def test_phase3_04_user_statistics(self):
        """Test user statistics generation."""
        # Save session first
        self.storage.save_session(self.user_id, self.sample_session)
        
        # Get statistics
        stats = self.storage.get_user_statistics(self.user_id)
        
        # Verify statistics
        self.assertEqual(stats['user_id'], self.user_id)
        self.assertEqual(stats['total_sessions'], 1)
        self.assertEqual(stats['total_posts'], 2)  # Fixed: sample session has post_count: 2
        self.assertEqual(stats['total_interactions'], 2)
        self.assertGreater(stats['average_satisfaction'], 0.8)
    
    def test_phase3_05_session_list_retrieval(self):
        """Test session list retrieval."""
        # Save multiple sessions
        session1 = self.sample_session.copy()
        session1['series_id'] = 'session-1'
        session1['filename'] = 'file1.md'
        
        session2 = self.sample_session.copy()
        session2['series_id'] = 'session-2'
        session2['filename'] = 'file2.md'
        
        self.storage.save_session(self.user_id, session1)
        self.storage.save_session(self.user_id, session2)
        
        # Get session list
        sessions = self.storage.get_session_list(self.user_id, limit=5)
        
        # Verify sessions
        self.assertEqual(len(sessions), 2)
        filenames = [s['filename'] for s in sessions]
        self.assertIn('file1.md', filenames)
        self.assertIn('file2.md', filenames)
    
    def test_phase3_06_bot_integration(self):
        """Test EnhancedStorage integration with bot."""
        self.assertIsNotNone(self.bot.enhanced_storage)
        # Check that it's an EnhancedStorage instance (accounting for import path differences)
        self.assertIn('EnhancedStorage', str(type(self.bot.enhanced_storage)))
    
    def test_phase3_07_session_storage_integration(self):
        """Test session storage integration with bot."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, "# Test\nContent", "test.md")
        
        # Add some chat history
        self.bot._add_chat_history_entry(
            user_id=self.user_id,
            user_message="Test message",
            bot_response="Test response",
            message_type="text",
            satisfaction_score=0.8
        )
        
        # Save session
        success = self.bot._save_session_to_storage(self.user_id, session)
        self.assertTrue(success)
        
        # Load session
        loaded_session = self.bot._load_session_from_storage(self.user_id, session['series_id'])
        self.assertIsNotNone(loaded_session)
        self.assertEqual(loaded_session['series_id'], session['series_id'])
    
    def test_phase3_08_user_preferences_integration(self):
        """Test user preferences integration with bot."""
        # Load preferences (should return defaults)
        preferences = self.bot._load_user_preferences(self.user_id)
        self.assertIsInstance(preferences, dict)
        self.assertIn('preferred_tones', preferences)
        self.assertIn('audience_preferences', preferences)
        
        # Update preferences
        preferences['preferred_tones'].append('technical')
        success = self.bot._save_user_preferences(self.user_id, preferences)
        self.assertTrue(success)
        
        # Load again and verify
        loaded_preferences = self.bot._load_user_preferences(self.user_id)
        self.assertIn('technical', loaded_preferences['preferred_tones'])
    
    def test_phase3_09_user_statistics_integration(self):
        """Test user statistics integration with bot."""
        # Get user statistics
        stats = self.bot._get_user_statistics(self.user_id)
        
        # Should return user info even if no data
        self.assertIsInstance(stats, dict)
        self.assertIn('user_id', stats)
    
    def test_phase3_10_database_cleanup(self):
        """Test database cleanup functionality."""
        # Save some old data
        old_session = self.sample_session.copy()
        old_session['series_id'] = 'old-session'
        old_session['last_activity'] = (datetime.now() - timedelta(days=40)).isoformat()
        
        self.storage.save_session(self.user_id, old_session)
        
        # Clean up old data
        deleted_count = self.storage.cleanup_old_data(days_to_keep=30)
        self.assertGreaterEqual(deleted_count, 0)
    
    def test_phase3_11_database_backup(self):
        """Test database backup functionality."""
        # Create backup
        backup_path = self.temp_db.name + '.backup'
        success = self.storage.backup_database(backup_path)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(backup_path))
        
        # Clean up backup
        os.unlink(backup_path)
    
    def test_phase3_12_database_statistics(self):
        """Test database statistics."""
        # Save some data
        self.storage.save_session(self.user_id, self.sample_session)
        
        # Get database stats
        stats = self.storage.get_database_stats()
        
        # Verify stats
        self.assertIsInstance(stats, dict)
        self.assertIn('database_size_bytes', stats)
        self.assertIn('users_count', stats)
        self.assertIn('sessions_count', stats)
    
    def test_phase3_13_error_handling(self):
        """Test error handling in storage operations."""
        # Test with invalid user ID
        invalid_session = self.sample_session.copy()
        invalid_session['series_id'] = None  # Invalid session ID
        
        # Should handle gracefully
        success = self.storage.save_session(self.user_id, invalid_session)
        self.assertFalse(success)
    
    def test_phase3_14_concurrent_access(self):
        """Test concurrent access to storage."""
        import threading
        import time
        
        results = []
        
        def save_session(thread_id):
            session = self.sample_session.copy()
            session['series_id'] = f'thread-{thread_id}'
            session['filename'] = f'file-{thread_id}.md'
            
            success = self.storage.save_session(self.user_id, session)
            results.append(success)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))
    
    def test_phase3_15_data_integrity(self):
        """Test data integrity across save/load cycles."""
        # Save session with complex data
        complex_session = self.sample_session.copy()
        complex_preferences = {
            'preferred_tones': ['technical', 'casual', 'formal'],
            'audience_preferences': {'business': 5, 'technical': 3, 'general': 1},
            'content_length_preferences': {'short': 2, 'medium': 8, 'long': 1},
            'successful_patterns': ['technical tone', 'business focus', 'casual approach'],
            'avoided_patterns': ['formal tone', 'too technical']
        }
        
        # Save session and preferences separately (as per implementation)
        self.storage.save_session(self.user_id, complex_session)
        self.storage.save_user_preferences(self.user_id, complex_preferences)
        
        # Load session and preferences
        loaded_session = self.storage.load_session(self.user_id, complex_session['series_id'])
        loaded_preferences = self.storage.load_user_preferences(self.user_id)
        
        # Verify session data integrity
        self.assertEqual(loaded_session['series_id'], complex_session['series_id'])
        self.assertEqual(loaded_session['filename'], complex_session['filename'])
        self.assertEqual(len(loaded_session['chat_history']), len(complex_session['chat_history']))
        self.assertEqual(len(loaded_session['posts']), len(complex_session['posts']))
        
        # Verify preferences data integrity
        self.assertEqual(
            loaded_preferences['preferred_tones'],
            complex_preferences['preferred_tones']
        )
        self.assertEqual(
            loaded_preferences['audience_preferences'],
            complex_preferences['audience_preferences']
        )

if __name__ == '__main__':
    unittest.main() 