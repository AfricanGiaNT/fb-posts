#!/usr/bin/env python3
"""
Phase 1 Tests: Core Free-Form Infrastructure
Tests for enhanced session state management, text handler routing, input validation, 
timeout handling, and AI integration enhancement.
"""

import unittest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add scripts directory to path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot

class TestFreeFormPhase1(unittest.TestCase):
    """Test Phase 1: Core Free-Form Infrastructure."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_config = Mock()
        self.mock_config.telegram_bot_token = "test_telegram_token"  # Add telegram token
        self.mock_config.openai_api_key = "test_openai_key"
        self.mock_config.airtable_api_key = "test_airtable_key"
        self.mock_config.airtable_base_id = "test_base_id"
        self.mock_config.airtable_table_name = "test_table"
        
        self.mock_ai_generator = Mock()
        self.mock_airtable = Mock()
        
        # Mock the Application to avoid real bot creation
        with patch('telegram_bot.ConfigManager', return_value=self.mock_config), \
             patch('telegram_bot.AIContentGenerator', return_value=self.mock_ai_generator), \
             patch('telegram_bot.AirtableConnector', return_value=self.mock_airtable), \
             patch('telegram_bot.Application'):  # Mock the Application to avoid real bot creation
            self.bot = FacebookContentBot()
    
    def test_phase1_1_session_state_management(self):
        """Test Phase 1.1: Enhanced session state management."""
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test.md"
        
        # Initialize session
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        
        # Verify state field is added
        self.assertIn('state', session)
        self.assertIsNone(session['state'])
        
        # Test state transitions
        session['state'] = 'awaiting_file_context'
        self.assertEqual(session['state'], 'awaiting_file_context')
        
        session['state'] = 'awaiting_story_edits'
        self.assertEqual(session['state'], 'awaiting_story_edits')
        
        print("✅ Phase 1.1: Session state management working correctly")
    
    def test_phase1_2_timeout_handling(self):
        """Test Phase 1.2: Timeout handling for free-form states."""
        user_id = 12345
        session = {
            'last_activity': datetime.now().isoformat(),
            'state': 'awaiting_file_context'
        }
        self.bot.user_sessions[user_id] = session
        
        # Test no timeout (recent activity)
        self.assertFalse(self.bot._check_freeform_timeout(session))
        
        # Test timeout (old activity)
        old_time = (datetime.now() - timedelta(minutes=6)).isoformat()
        session['last_activity'] = old_time
        self.assertTrue(self.bot._check_freeform_timeout(session))
        
        # Test invalid session
        self.assertTrue(self.bot._check_freeform_timeout(None))
        self.assertTrue(self.bot._check_freeform_timeout({}))
        
        print("✅ Phase 1.2: Timeout handling working correctly")
    
    def test_phase1_2_input_validation(self):
        """Test Phase 1.2: Input validation."""
        # Test valid input
        valid_input = "This is a valid input"
        self.assertTrue(self.bot._validate_freeform_input(valid_input))
        
        # Test empty input
        self.assertFalse(self.bot._validate_freeform_input(""))
        self.assertFalse(self.bot._validate_freeform_input("   "))
        self.assertFalse(self.bot._validate_freeform_input(None))
        
        # Test too long input
        long_input = "a" * 501
        self.assertFalse(self.bot._validate_freeform_input(long_input))
        
        # Test exactly at limit
        limit_input = "a" * 500
        self.assertTrue(self.bot._validate_freeform_input(limit_input))
        
        print("✅ Phase 1.2: Input validation working correctly")
    
    def test_phase1_2_error_handling(self):
        """Test Phase 1.2: Error handling with clear messages."""
        # Mock update and context
        mock_update = Mock()
        mock_update.effective_user.id = 12345
        mock_update.message.text = "a" * 501  # Too long
        mock_context = Mock()
        
        # Mock send_formatted_message
        self.bot._send_formatted_message = AsyncMock()
        
        # Set up session
        session = {
            'state': 'awaiting_file_context',
            'last_activity': datetime.now().isoformat()
        }
        self.bot.user_sessions[12345] = session
        
        # Test error handling
        asyncio.run(self.bot._handle_file_context_input(mock_update, mock_context, "a" * 501))
        
        # Verify error message was sent
        call_args = self.bot._send_formatted_message.call_args
        self.assertIn("invalid input", call_args[0][1].lower())
        
        print("✅ Phase 1.2: Error handling working correctly")
    
    def test_phase1_3_edit_instruction_parsing(self):
        """Test Phase 1.3: Edit instruction parsing."""
        # Test basic parsing
        edit_text = "expand on implementation details"
        parsed = self.bot._parse_edit_instructions(edit_text)
        
        self.assertEqual(parsed['action'], 'expand')
        self.assertEqual(parsed['target'], 'content')
        self.assertEqual(parsed['specific_instructions'], edit_text)
        self.assertIsNone(parsed['tone_change'])
        
        # Test tone change detection
        edit_text_with_tone = "make it more casual and friendly"
        parsed = self.bot._parse_edit_instructions(edit_text_with_tone)
        
        self.assertEqual(parsed['tone_change'], 'casual')
        
        # Test different actions
        actions = {
            'restructure to focus on business impact': 'restructure',
            'add more details about deployment': 'expand',
            'shorten the technical section': 'shorten',
            'focus on the key points': 'focus'
        }
        
        for edit_text, expected_action in actions.items():
            parsed = self.bot._parse_edit_instructions(edit_text)
            self.assertEqual(parsed['action'], expected_action)
        
        print("✅ Phase 1.3: Edit instruction parsing working correctly")
    
    def test_phase1_3_tone_preservation(self):
        """Test Phase 1.3: Tone preservation unless explicitly changed."""
        original_tone = "Technical"
        
        # Test tone preservation
        edit_text = "add more details about the implementation"
        preserved_tone = self.bot._preserve_tone_unless_changed(original_tone, edit_text)
        self.assertEqual(preserved_tone, original_tone)
        
        # Test tone change
        edit_text_with_tone = "make it more casual and relatable"
        changed_tone = self.bot._preserve_tone_unless_changed(original_tone, edit_text_with_tone)
        self.assertEqual(changed_tone, "Casual")
        
        # Test different tone changes
        tone_changes = {
            'make it professional': 'Professional',
            'add technical details': 'Technical',
            'make it inspirational': 'Inspirational'
        }
        
        for edit_text, expected_tone in tone_changes.items():
            result_tone = self.bot._preserve_tone_unless_changed(original_tone, edit_text)
            self.assertEqual(result_tone, expected_tone)
        
        print("✅ Phase 1.3: Tone preservation working correctly")
    
    def test_phase1_3_enhanced_prompt_building(self):
        """Test Phase 1.3: Enhanced prompt building with free-form context."""
        markdown_content = "# Test Content\nThis is a test."
        freeform_context = "Focus on technical challenges"
        tone_preference = "Technical"
        
        enhanced_prompt = self.bot._build_context_aware_prompt_with_freeform(
            markdown_content, freeform_context, tone_preference
        )
        
        # Verify context is included
        self.assertIn(freeform_context, enhanced_prompt)
        self.assertIn(markdown_content, enhanced_prompt)
        self.assertIn(tone_preference, enhanced_prompt)
        
        # Test without tone preference
        enhanced_prompt_no_tone = self.bot._build_context_aware_prompt_with_freeform(
            markdown_content, freeform_context, None
        )
        
        self.assertIn("AI-chosen", enhanced_prompt_no_tone)
        
        print("✅ Phase 1.3: Enhanced prompt building working correctly")
    
    def test_phase1_integration_workflow(self):
        """Test Phase 1: Complete integration workflow."""
        user_id = 12345
        mock_update = Mock()
        mock_update.effective_user.id = user_id
        mock_update.message.text = "Focus on technical implementation details"
        mock_context = Mock()
        
        # Mock dependencies
        self.bot._send_formatted_message = AsyncMock()
        self.bot._show_initial_tone_selection = AsyncMock()
        
        # Initialize session
        session = {
            'state': 'awaiting_file_context',
            'last_activity': datetime.now().isoformat()
        }
        self.bot.user_sessions[user_id] = session
        
        # Test file context input handling
        asyncio.run(self.bot._handle_file_context_input(mock_update, mock_context, "Focus on technical implementation details"))
        
        # Verify context was stored
        self.assertEqual(session['freeform_context'], "Focus on technical implementation details")
        
        # Verify state was reset
        self.assertIsNone(session['state'])
        
        # Verify tone selection was called
        self.bot._show_initial_tone_selection.assert_called_once()
        
        print("✅ Phase 1: Complete integration workflow working correctly")

if __name__ == '__main__':
    unittest.main() 