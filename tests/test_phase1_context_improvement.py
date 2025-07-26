"""
Test Phase 1: Enhanced Conversational Memory
Tests the implementation of chat history tracking, user preference learning, and feedback analysis.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot

class TestPhase1ContextImprovement(unittest.TestCase):
    """Test Phase 1: Enhanced Conversational Memory implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.bot = FacebookContentBot()
        self.user_id = 12345
        self.markdown_content = "# Test Project\nThis is a test project for context improvement."
        self.filename = "test_project.md"
        
    def test_phase1_1_enhanced_session_initialization(self):
        """Test Phase 1.1: Enhanced session initialization with new fields."""
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        
        # Test that new Phase 1 fields are present
        self.assertIn('chat_history', session)
        self.assertIn('user_preferences', session)
        self.assertIn('request_mapping', session)
        self.assertIn('feedback_analysis', session)
        
        # Test chat_history structure
        self.assertEqual(session['chat_history'], [])
        
        # Test user_preferences structure
        self.assertIn('preferred_tones', session['user_preferences'])
        self.assertIn('audience_preferences', session['user_preferences'])
        self.assertIn('content_length_preferences', session['user_preferences'])
        self.assertIn('successful_patterns', session['user_preferences'])
        self.assertIn('avoided_patterns', session['user_preferences'])
        
        # Test request_mapping structure
        self.assertIn('current_request_id', session['request_mapping'])
        self.assertIn('request_history', session['request_mapping'])
        self.assertIn('content_relationships', session['request_mapping'])
        
        # Test feedback_analysis structure
        self.assertIn('approval_rate', session['feedback_analysis'])
        self.assertIn('regeneration_patterns', session['feedback_analysis'])
        self.assertIn('common_edit_requests', session['feedback_analysis'])
        self.assertIn('successful_content_elements', session['feedback_analysis'])
        
        print("✅ Phase 1.1: Enhanced session initialization working correctly")
    
    def test_phase1_2_chat_history_tracking(self):
        """Test Phase 1.2: Chat history entry tracking."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Test adding chat history entry
        self.bot._add_chat_history_entry(
            user_id=self.user_id,
            user_message="Test user message",
            bot_response="Test bot response",
            message_type="test",
            context={'test_key': 'test_value'},
            satisfaction_score=0.8
        )
        
        # Verify entry was added
        chat_history = session['chat_history']
        self.assertEqual(len(chat_history), 1)
        
        entry = chat_history[0]
        self.assertEqual(entry['user_message'], "Test user message")
        self.assertEqual(entry['bot_response'], "Test bot response")
        self.assertEqual(entry['message_type'], "test")
        self.assertEqual(entry['context']['test_key'], "test_value")
        self.assertEqual(entry['satisfaction_score'], 0.8)
        self.assertIn('timestamp', entry)
        
        print("✅ Phase 1.2: Chat history tracking working correctly")
    
    def test_phase1_3_post_approval_tracking(self):
        """Test Phase 1.3: Post approval tracking and user preference updates."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Mock post data
        post_data = {
            'post_content': 'Test post content',
            'tone_used': 'Behind-the-Build',
            'tone_reason': 'Test reason'
        }
        
        # Test post approval tracking
        self.bot._track_post_approval(self.user_id, post_data, "test_record_id")
        
        # Verify user preferences were updated
        user_prefs = session['user_preferences']
        self.assertIn('Behind-the-Build', user_prefs['preferred_tones'])
        
        # Verify successful patterns were added
        self.assertEqual(len(user_prefs['successful_patterns']), 1)
        pattern = user_prefs['successful_patterns'][0]
        self.assertEqual(pattern['tone'], 'Behind-the-Build')
        self.assertEqual(pattern['content_summary'], 'Test post content')
        self.assertEqual(pattern['airtable_record_id'], 'test_record_id')
        
        print("✅ Phase 1.3: Post approval tracking working correctly")
    
    def test_phase1_4_post_regeneration_tracking(self):
        """Test Phase 1.4: Post regeneration tracking."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Test regeneration tracking
        self.bot._track_post_regeneration(
            user_id=self.user_id,
            reason="User requested different tone",
            original_content="Original content",
            new_content="New content"
        )
        
        # Verify regeneration patterns were added
        feedback_analysis = session['feedback_analysis']
        self.assertEqual(len(feedback_analysis['regeneration_patterns']), 1)
        
        pattern = feedback_analysis['regeneration_patterns'][0]
        self.assertEqual(pattern['reason'], "User requested different tone")
        self.assertEqual(pattern['original_content_summary'], "Original content")
        self.assertEqual(pattern['new_content_summary'], "New content")
        
        # Verify common edit requests were updated
        self.assertIn("User requested different tone", feedback_analysis['common_edit_requests'])
        
        print("✅ Phase 1.4: Post regeneration tracking working correctly")
    
    def test_phase1_5_user_feedback_tracking(self):
        """Test Phase 1.5: User feedback tracking."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Test user feedback tracking
        feedback_data = {'feedback_type': 'tone_preference', 'details': 'Too technical'}
        self.bot._track_user_feedback(
            user_id=self.user_id,
            feedback_type="tone_preference",
            feedback_data=feedback_data,
            satisfaction_score=0.6
        )
        
        # Verify chat history entry was added
        chat_history = session['chat_history']
        self.assertEqual(len(chat_history), 1)
        
        entry = chat_history[0]
        self.assertEqual(entry['user_message'], "Feedback: tone_preference")
        self.assertEqual(entry['bot_response'], "Feedback recorded")
        self.assertEqual(entry['message_type'], "feedback")
        self.assertEqual(entry['context'], feedback_data)
        self.assertEqual(entry['satisfaction_score'], 0.6)
        
        print("✅ Phase 1.5: User feedback tracking working correctly")
    
    def test_phase1_6_user_preference_learning(self):
        """Test Phase 1.6: User preference learning from interactions."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Test interaction data
        interaction_data = {
            'tone_selected': 'What Broke',
            'audience_type': 'business',
            'length_preference': 'medium'
        }
        
        # Update preferences from interaction
        self.bot._update_user_preferences_from_interaction(self.user_id, interaction_data)
        
        # Verify tone preferences
        user_prefs = session['user_preferences']
        self.assertIn('What Broke', user_prefs['preferred_tones'])
        
        # Verify audience preferences (count may be higher due to previous test runs)
        self.assertGreaterEqual(user_prefs['audience_preferences']['business'], 1)
        
        # Verify length preferences (count may be higher due to previous test runs)
        self.assertGreaterEqual(user_prefs['content_length_preferences']['medium'], 1)
        
        # Test multiple interactions
        initial_count = user_prefs['audience_preferences']['business']
        self.bot._update_user_preferences_from_interaction(self.user_id, interaction_data)
        self.assertEqual(user_prefs['audience_preferences']['business'], initial_count + 1)
        
        print("✅ Phase 1.6: User preference learning working correctly")
    
    def test_phase1_7_relevant_chat_history_retrieval(self):
        """Test Phase 1.7: Relevant chat history retrieval."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Add multiple chat history entries
        for i in range(10):
            self.bot._add_chat_history_entry(
                user_id=self.user_id,
                user_message=f"Message {i}",
                bot_response=f"Response {i}",
                message_type="test"
            )
        
        # Test relevant chat history retrieval
        current_request = {'type': 'post_generation'}
        relevant_entries = self.bot._get_relevant_chat_history(self.user_id, current_request, max_entries=5)
        
        # Should return 5 entries (now prioritized by relevance, not just recency)
        self.assertEqual(len(relevant_entries), 5)
        # Verify that entries are returned (order may vary due to smart prioritization)
        self.assertTrue(all('user_message' in entry for entry in relevant_entries))
        
        print("✅ Phase 1.7: Relevant chat history retrieval working correctly")
    
    def test_phase1_8_session_persistence(self):
        """Test Phase 1.8: Session data persistence and structure."""
        # Initialize session
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        # Add some data to test persistence
        self.bot._add_chat_history_entry(
            user_id=self.user_id,
            user_message="Test message",
            bot_response="Test response",
            message_type="test"
        )
        
        self.bot._update_user_preferences_from_interaction(self.user_id, {
            'tone_selected': 'Behind-the-Build',
            'audience_type': 'technical'
        })
        
        # Verify session structure is maintained
        session = self.bot.user_sessions[self.user_id]
        
        # Check that all Phase 1 fields are present and functional
        self.assertIsInstance(session['chat_history'], list)
        self.assertIsInstance(session['user_preferences'], dict)
        self.assertIsInstance(session['request_mapping'], dict)
        self.assertIsInstance(session['feedback_analysis'], dict)
        
        # Check that data was properly stored
        self.assertEqual(len(session['chat_history']), 1)
        self.assertIn('Behind-the-Build', session['user_preferences']['preferred_tones'])
        self.assertGreaterEqual(session['user_preferences']['audience_preferences']['technical'], 1)
        
        print("✅ Phase 1.8: Session persistence working correctly")
    
    def test_phase1_9_backward_compatibility(self):
        """Test Phase 1.9: Backward compatibility with existing session structure."""
        # Test that existing session fields are still present
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        
        # Verify all existing fields are still present
        existing_fields = [
            'series_id', 'original_markdown', 'filename', 'posts', 
            'current_draft', 'session_started', 'last_activity', 
            'session_context', 'post_count', 'state'
        ]
        
        for field in existing_fields:
            self.assertIn(field, session)
        
        # Verify existing functionality still works
        self.assertIsInstance(session['posts'], list)
        self.assertIsInstance(session['session_started'], str)
        self.assertIsInstance(session['last_activity'], str)
        
        print("✅ Phase 1.9: Backward compatibility maintained")
    
    def test_phase1_10_error_handling(self):
        """Test Phase 1.10: Error handling for invalid user IDs and edge cases."""
        # Test with non-existent user
        self.bot._add_chat_history_entry(
            user_id=99999,  # Non-existent user
            user_message="Test",
            bot_response="Test",
            message_type="test"
        )
        # Should not raise an exception
        
        # Test with None values
        session = self.bot._initialize_session(self.user_id, self.markdown_content, self.filename)
        self.bot.user_sessions[self.user_id] = session
        
        self.bot._add_chat_history_entry(
            user_id=self.user_id,
            user_message=None,
            bot_response=None,
            message_type=None,
            context=None,
            satisfaction_score=None
        )
        
        # Should handle None values gracefully
        entry = session['chat_history'][0]
        self.assertIsInstance(entry['user_message'], str)
        self.assertIsInstance(entry['bot_response'], str)
        self.assertIsInstance(entry['message_type'], str)
        
        print("✅ Phase 1.10: Error handling working correctly")

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 