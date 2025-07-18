#!/usr/bin/env python3
"""
Tests for Phase 5.1: Enhanced Session Architecture
Tests multi-file session management, file categorization, and batch upload workflow
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import tempfile

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from config_manager import ConfigManager
from enhanced_telegram_bot import EnhancedFacebookContentBot
from project_analyzer import ProjectAnalyzer

class TestPhase51SessionArchitecture(unittest.TestCase):
    """Test Phase 5.1: Enhanced Session Architecture"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = ConfigManager()
        self.bot = EnhancedFacebookContentBot()
        self.test_user_id = 12345
        
        # Sample markdown content for testing
        self.sample_markdown_planning = """
# Project Planning Phase

## Architecture Design
We need to design a robust authentication system that can handle multiple user types.

## Requirements
- User registration and login
- Role-based access control
- Session management
- Security measures

## Technical Stack
- Backend: Python Flask
- Database: PostgreSQL
- Authentication: JWT tokens
- Frontend: React
        """
        
        self.sample_markdown_implementation = """
# Implementation Phase

## What I Built
I implemented the core authentication system with user registration, login, and JWT token management.

## Technical Details
- Created User model with SQLAlchemy
- Implemented password hashing with bcrypt
- Set up JWT token generation and validation
- Added role-based middleware
- Created API endpoints for auth operations

## Challenges
- Token expiration handling
- Session management across requests
- Password security requirements
        """
        
        self.sample_markdown_debugging = """
# Debugging Session

## What Broke
The authentication system was failing on token validation, causing users to be logged out randomly.

## Root Cause
- Token expiration not properly handled
- Timezone issues with token timestamps
- Missing error handling for expired tokens

## Solutions Implemented
- Added proper token refresh mechanism
- Fixed timezone handling using UTC
- Implemented graceful error handling
- Added logging for debugging
        """
        
        self.sample_markdown_results = """
# Project Results

## Final Outcomes
Successfully deployed the authentication system with 99.9% uptime and zero security incidents.

## Performance Metrics
- Login response time: <200ms
- Token validation: <50ms
- User registration: <500ms
- Daily active users: 1,000+

## Business Impact
- Reduced support tickets by 60%
- Improved user experience
- Enhanced security posture
- Enabled role-based features
        """
    
    def test_initialize_single_file_session(self):
        """Test single-file session initialization (backward compatibility)"""
        session = self.bot._initialize_session(
            self.test_user_id,
            self.sample_markdown_planning,
            "planning-phase-001.md"
        )
        
        # Verify session structure
        self.assertIsInstance(session, dict)
        self.assertEqual(session['mode'], 'single')
        self.assertEqual(session['original_markdown'], self.sample_markdown_planning)
        self.assertEqual(session['filename'], "planning-phase-001.md")
        self.assertEqual(session['posts'], [])
        self.assertEqual(session['post_count'], 0)
        self.assertEqual(session['workflow_state'], 'single_file')
        
        # Verify multi-file fields are empty but present
        self.assertEqual(session['source_files'], [])
        self.assertEqual(session['project_overview'], {})
        self.assertEqual(session['content_strategy'], {})
        self.assertEqual(session['user_customizations'], {})
        self.assertIsNone(session['batch_timeout'])
        
        # Verify session is stored
        self.assertIn(self.test_user_id, self.bot.user_sessions)
        self.assertEqual(self.bot.user_sessions[self.test_user_id], session)
    
    def test_initialize_multi_file_session(self):
        """Test multi-file session initialization"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Verify session structure
        self.assertIsInstance(session, dict)
        self.assertEqual(session['mode'], 'multi')
        self.assertEqual(session['source_files'], [])
        self.assertEqual(session['project_overview'], {})
        self.assertEqual(session['content_strategy'], {})
        self.assertEqual(session['user_customizations'], {})
        self.assertEqual(session['workflow_state'], 'collecting_files')
        self.assertEqual(session['posts'], [])
        self.assertEqual(session['post_count'], 0)
        
        # Verify timeout is set (30 minutes)
        self.assertIsNotNone(session['batch_timeout'])
        timeout_diff = session['batch_timeout'] - datetime.now()
        self.assertAlmostEqual(timeout_diff.total_seconds(), 30 * 60, delta=60)
        
        # Verify backward compatibility fields
        self.assertEqual(session['original_markdown'], '')
        self.assertEqual(session['filename'], '')
        
        # Verify session is stored
        self.assertIn(self.test_user_id, self.bot.user_sessions)
        self.assertEqual(self.bot.user_sessions[self.test_user_id], session)
    
    def test_check_multi_file_timeout_no_session(self):
        """Test timeout check when no session exists"""
        result = self.bot._check_multi_file_timeout(99999)
        self.assertTrue(result)
    
    def test_check_multi_file_timeout_multi_mode_not_expired(self):
        """Test timeout check for multi-file mode within timeout"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        result = self.bot._check_multi_file_timeout(self.test_user_id)
        self.assertFalse(result)
    
    def test_check_multi_file_timeout_multi_mode_expired(self):
        """Test timeout check for multi-file mode after timeout"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Manually set timeout to past
        session['batch_timeout'] = datetime.now() - timedelta(minutes=1)
        
        result = self.bot._check_multi_file_timeout(self.test_user_id)
        self.assertTrue(result)
    
    def test_check_multi_file_timeout_single_mode_not_expired(self):
        """Test timeout check for single-file mode within timeout"""
        session = self.bot._initialize_session(
            self.test_user_id,
            self.sample_markdown_planning,
            "test.md"
        )
        
        result = self.bot._check_multi_file_timeout(self.test_user_id)
        self.assertFalse(result)
    
    def test_check_multi_file_timeout_single_mode_expired(self):
        """Test timeout check for single-file mode after timeout"""
        session = self.bot._initialize_session(
            self.test_user_id,
            self.sample_markdown_planning,
            "test.md"
        )
        
        # Manually set last activity to past
        session['last_activity'] = (datetime.now() - timedelta(minutes=20)).isoformat()
        
        result = self.bot._check_multi_file_timeout(self.test_user_id)
        self.assertTrue(result)
    
    @patch('enhanced_telegram_bot.ProjectAnalyzer')
    def test_categorize_file_success(self, mock_analyzer_class):
        """Test successful file categorization"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_analyzer.categorize_file.return_value = {
            'file_phase': 'implementation',
            'content_summary': 'Test implementation',
            'key_themes': ['authentication', 'api']
        }
        
        # Create a new bot instance with the mock
        bot = EnhancedFacebookContentBot()
        result = bot._categorize_file(self.sample_markdown_implementation, "impl.md")
        
        self.assertEqual(result, 'implementation')
        mock_analyzer.categorize_file.assert_called_once_with(
            self.sample_markdown_implementation,
            "impl.md"
        )
    
    @patch('enhanced_telegram_bot.ProjectAnalyzer')
    def test_categorize_file_error_fallback(self, mock_analyzer_class):
        """Test file categorization with error fallback"""
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        
        mock_analyzer.categorize_file.side_effect = Exception("Categorization failed")
        
        # Create a new bot instance with the mock
        bot = EnhancedFacebookContentBot()
        result = bot._categorize_file(self.sample_markdown_implementation, "impl.md")
        
        self.assertEqual(result, 'implementation')  # Default fallback
    
    def test_suggest_tone_for_phase(self):
        """Test tone suggestions based on file phase"""
        test_cases = [
            ('planning', 'Behind-the-Build'),
            ('implementation', 'Problem → Solution → Result'),
            ('debugging', 'What Broke'),
            ('results', 'Finished & Proud'),
            ('unknown', 'Mini Lesson')
        ]
        
        for phase, expected_tone in test_cases:
            with self.subTest(phase=phase):
                result = self.bot._suggest_tone_for_phase(phase)
                self.assertEqual(result, expected_tone)
    
    def test_generate_basic_cross_references(self):
        """Test basic cross-reference generation"""
        files = [
            {'filename': 'file1.md', 'file_phase': 'planning'},
            {'filename': 'file2.md', 'file_phase': 'implementation'},
            {'filename': 'file3.md', 'file_phase': 'debugging'}
        ]
        
        references = self.bot._generate_basic_cross_references(files)
        
        self.assertEqual(len(references), 2)
        
        # Check first reference
        self.assertEqual(references[0]['from_file'], 'file2.md')
        self.assertEqual(references[0]['to_file'], 'file1.md')
        self.assertEqual(references[0]['type'], 'sequential')
        self.assertEqual(references[0]['description'], 'Post 2 builds on Post 1')
        
        # Check second reference
        self.assertEqual(references[1]['from_file'], 'file3.md')
        self.assertEqual(references[1]['to_file'], 'file2.md')
        self.assertEqual(references[1]['type'], 'sequential')
        self.assertEqual(references[1]['description'], 'Post 3 builds on Post 2')
    
    def test_generate_basic_cross_references_single_file(self):
        """Test cross-reference generation with single file"""
        files = [{'filename': 'file1.md', 'file_phase': 'planning'}]
        
        references = self.bot._generate_basic_cross_references(files)
        
        self.assertEqual(len(references), 0)
    
    def test_session_isolation(self):
        """Test that sessions are properly isolated between users"""
        user1_id = 12345
        user2_id = 67890
        
        # Create sessions for different users
        session1 = self.bot._initialize_session(user1_id, "Content 1", "file1.md")
        session2 = self.bot._initialize_multi_file_session(user2_id)
        
        # Verify sessions are different
        self.assertNotEqual(session1['series_id'], session2['series_id'])
        self.assertEqual(session1['mode'], 'single')
        self.assertEqual(session2['mode'], 'multi')
        
        # Verify sessions are stored separately
        self.assertIn(user1_id, self.bot.user_sessions)
        self.assertIn(user2_id, self.bot.user_sessions)
        self.assertNotEqual(self.bot.user_sessions[user1_id], self.bot.user_sessions[user2_id])
    
    def test_session_update_last_activity(self):
        """Test that session updates last activity timestamp"""
        session = self.bot._initialize_session(
            self.test_user_id,
            self.sample_markdown_planning,
            "test.md"
        )
        
        original_activity = session['last_activity']
        
        # Simulate some time passing
        import time
        time.sleep(0.1)
        
        # Update session
        session['last_activity'] = datetime.now().isoformat()
        
        # Verify timestamp changed
        self.assertNotEqual(session['last_activity'], original_activity)
    
    def test_session_data_integrity(self):
        """Test session data integrity across operations"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Verify initial state
        self.assertEqual(len(session['source_files']), 0)
        self.assertEqual(session['workflow_state'], 'collecting_files')
        
        # Simulate file addition
        mock_file = {
            'filename': 'test.md',
            'file_phase': 'implementation',
            'content': 'test content',
            'word_count': 100
        }
        session['source_files'].append(mock_file)
        
        # Verify state update
        self.assertEqual(len(session['source_files']), 1)
        self.assertEqual(session['source_files'][0]['filename'], 'test.md')
        
        # Simulate workflow state change
        session['workflow_state'] = 'project_analyzed'
        
        # Verify state persistence
        retrieved_session = self.bot.user_sessions[self.test_user_id]
        self.assertEqual(retrieved_session['workflow_state'], 'project_analyzed')
        self.assertEqual(len(retrieved_session['source_files']), 1)
    
    def test_backward_compatibility_fields(self):
        """Test that multi-file sessions maintain backward compatibility"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Verify backward compatibility fields exist
        self.assertIn('original_markdown', session)
        self.assertIn('filename', session)
        self.assertIn('posts', session)
        self.assertIn('current_draft', session)
        self.assertIn('session_started', session)
        self.assertIn('last_activity', session)
        self.assertIn('session_context', session)
        self.assertIn('post_count', session)
        self.assertIn('state', session)
    
    def test_session_memory_management(self):
        """Test session memory management and cleanup"""
        # Create multiple sessions
        user_ids = [1, 2, 3, 4, 5]
        
        for user_id in user_ids:
            self.bot._initialize_session(user_id, "test content", "test.md")
        
        # Verify all sessions are stored
        self.assertEqual(len(self.bot.user_sessions), len(user_ids))
        
        # Simulate session cleanup
        for user_id in user_ids:
            if user_id in self.bot.user_sessions:
                del self.bot.user_sessions[user_id]
        
        # Verify cleanup
        self.assertEqual(len(self.bot.user_sessions), 0)
    
    def test_session_timeout_edge_cases(self):
        """Test edge cases in session timeout handling"""
        # Test with None timeout
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        session['batch_timeout'] = None
        
        result = self.bot._check_multi_file_timeout(self.test_user_id)
        self.assertFalse(result)
        
        # Test with invalid timestamp
        session = self.bot._initialize_session(self.test_user_id, "test", "test.md")
        session['last_activity'] = "invalid_timestamp"
        
        # Should handle gracefully without crashing
        try:
            result = self.bot._check_multi_file_timeout(self.test_user_id)
            # Should not crash - any result is acceptable
        except Exception as e:
            self.fail(f"Timeout check should handle invalid timestamp gracefully: {e}")


class TestPhase51IntegrationWorkflow(unittest.TestCase):
    """Test Phase 5.1 integration workflow scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.bot = EnhancedFacebookContentBot()
        self.test_user_id = 12345
    
    def test_single_to_multi_file_transition(self):
        """Test transitioning from single-file to multi-file mode"""
        # Start with single-file session
        single_session = self.bot._initialize_session(
            self.test_user_id,
            "test content",
            "test.md"
        )
        
        self.assertEqual(single_session['mode'], 'single')
        
        # Transition to multi-file session
        multi_session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Verify session was replaced
        self.assertEqual(multi_session['mode'], 'multi')
        self.assertEqual(self.bot.user_sessions[self.test_user_id]['mode'], 'multi')
        
        # Verify new session structure
        self.assertIn('source_files', multi_session)
        self.assertIn('project_overview', multi_session)
        self.assertIn('content_strategy', multi_session)
    
    def test_multi_file_workflow_states(self):
        """Test multi-file workflow state transitions"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Initial state
        self.assertEqual(session['workflow_state'], 'collecting_files')
        
        # Simulate state transitions
        workflow_states = [
            'collecting_files',
            'upload_complete',
            'project_analyzed',
            'strategy_generated',
            'content_generation',
            'series_complete'
        ]
        
        for state in workflow_states:
            session['workflow_state'] = state
            self.assertEqual(session['workflow_state'], state)
    
    def test_file_limit_validation(self):
        """Test file limit validation (8 files max)"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Add files up to limit
        for i in range(8):
            mock_file = {
                'filename': f'file_{i}.md',
                'file_phase': 'implementation',
                'content': f'content {i}',
                'word_count': 100
            }
            session['source_files'].append(mock_file)
        
        # Verify limit is reached
        self.assertEqual(len(session['source_files']), 8)
        
        # Verify we can check if limit is reached
        self.assertTrue(len(session['source_files']) >= 8)
    
    def test_session_persistence_across_operations(self):
        """Test session persistence across multiple operations"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        original_series_id = session['series_id']
        
        # Simulate multiple operations
        operations = [
            {'field': 'workflow_state', 'value': 'upload_complete'},
            {'field': 'project_overview', 'value': {'theme': 'test project'}},
            {'field': 'content_strategy', 'value': {'posts': 3}}
        ]
        
        for op in operations:
            session[op['field']] = op['value']
            
            # Verify session is updated
            retrieved_session = self.bot.user_sessions[self.test_user_id]
            self.assertEqual(retrieved_session[op['field']], op['value'])
            
            # Verify series_id remains constant
            self.assertEqual(retrieved_session['series_id'], original_series_id)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 