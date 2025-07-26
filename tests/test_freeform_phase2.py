"""
Test suite for Phase 2: File Upload Context
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime
import json

# Import the bot class
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from telegram_bot import FacebookContentBot
from ai_content_generator import AIContentGenerator


class TestFreeFormPhase2(unittest.TestCase):
    """Test cases for Phase 2 file upload context functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the config manager
        self.mock_config = Mock()
        self.mock_config.openai_api_key = "test_key"
        self.mock_config.telegram_bot_token = "test_telegram_token"
        self.mock_config.content_generation_provider = "openai"
        self.mock_config.openai_model = "gpt-4"
        self.mock_config.max_file_size_mb = 10
        self.mock_config.get_prompt_template.return_value = "Test template"
        
        # Mock the AI generator
        self.mock_ai_generator = Mock(spec=AIContentGenerator)
        self.mock_ai_generator.get_relationship_types.return_value = {
            'integration_expansion': '🔗 Integration Expansion',
            'implementation_evolution': '🔄 Implementation Evolution'
        }
        self.mock_ai_generator.get_tone_options.return_value = [
            'Behind-the-Build', 'What Broke', 'Problem → Solution → Result', 
            'Finished & Proud', 'Mini Lesson'
        ]
        
        # Mock the airtable connector
        self.mock_airtable = Mock()
        self.mock_airtable.save_draft.return_value = "test_record_id"
        
        # Create bot instance with mocked dependencies
        with patch('telegram_bot.ConfigManager', return_value=self.mock_config), \
             patch('telegram_bot.AIContentGenerator', return_value=self.mock_ai_generator), \
             patch('telegram_bot.AirtableConnector', return_value=self.mock_airtable), \
             patch('telegram_bot.Application'):
            self.bot = FacebookContentBot()
    
    def test_phase2_1_file_context_prompt(self):
        """Test Phase 2.1: File context prompt after upload."""
        # Test that file upload triggers context prompt
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test_file.md"
        
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        self.bot.user_sessions[user_id] = session
        
        # Mock the update and context
        mock_update = Mock()
        mock_update.effective_user.id = user_id
        mock_context = Mock()
        
        # Mock send_formatted_message
        self.bot._send_formatted_message = AsyncMock()
        
        # Test the context prompt
        asyncio.run(self.bot._ask_for_file_context(mock_update, mock_context, session))
        
        # Verify context prompt was sent
        self.bot._send_formatted_message.assert_called_once()
        call_args = self.bot._send_formatted_message.call_args
        message = call_args[0][1]
        
        # Check that the message contains context prompt elements
        self.assertIn("File Uploaded Successfully", message)
        self.assertIn("Would you like to provide any context", message)
        self.assertIn("Examples:", message)
        self.assertIn("5 minutes to respond", message)
        
        # Verify session state was set
        self.assertEqual(session['state'], 'awaiting_file_context')
    
    def test_phase2_1_skip_context_callback(self):
        """Test Phase 2.1: Skip context callback handling."""
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test_file.md"
        
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        session['state'] = 'awaiting_file_context'
        self.bot.user_sessions[user_id] = session
        
        # Mock the query
        mock_query = Mock()
        mock_query.from_user.id = user_id
        
        # Mock the tone selection method
        self.bot._show_initial_tone_selection_from_callback = AsyncMock()
        
        # Test skip context
        asyncio.run(self.bot._handle_skip_context(mock_query, session))
        
        # Verify state was reset and tone selection was called
        self.assertIsNone(session['state'])
        self.bot._show_initial_tone_selection_from_callback.assert_called_once_with(mock_query, session)
    
    def test_phase2_2_context_integration(self):
        """Test Phase 2.2: Context integration with AI generation."""
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test_file.md"
        
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        session['freeform_context'] = "focus on technical challenges and include code examples"
        self.bot.user_sessions[user_id] = session
        
        # Mock the query
        mock_query = Mock()
        mock_query.from_user.id = user_id
        
        # Mock AI generation
        self.mock_ai_generator.generate_facebook_post.return_value = {
            'post_content': 'Generated post with technical focus',
            'tone_used': 'Technical',
            'reasoning': 'Technical focus requested'
        }
        
        # Mock send_formatted_message
        self.bot._send_formatted_message = AsyncMock()
        
        # Test generation with context
        asyncio.run(self.bot._generate_with_initial_tone(mock_query, session, "Technical"))
        
        # Verify AI was called with free-form context
        self.mock_ai_generator.generate_facebook_post.assert_called_once()
        call_args = self.mock_ai_generator.generate_facebook_post.call_args
        self.assertEqual(call_args[1]['freeform_context'], "focus on technical challenges and include code examples")
    
    def test_phase2_2_ai_chosen_tone_with_context(self):
        """Test Phase 2.2: AI chosen tone with context integration."""
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test_file.md"
        
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        session['freeform_context'] = "emphasize business impact and ROI"
        self.bot.user_sessions[user_id] = session
        
        # Mock the query
        mock_query = Mock()
        mock_query.from_user.id = user_id
        
        # Mock AI generation
        self.mock_ai_generator.generate_facebook_post.return_value = {
            'post_content': 'Generated post with business focus',
            'tone_used': 'Professional',
            'reasoning': 'Business focus requested'
        }
        
        # Mock send_formatted_message
        self.bot._send_formatted_message = AsyncMock()
        
        # Test generation with context
        asyncio.run(self.bot._generate_with_ai_chosen_tone(mock_query, session))
        
        # Verify AI was called with free-form context
        self.mock_ai_generator.generate_facebook_post.assert_called_once()
        call_args = self.mock_ai_generator.generate_facebook_post.call_args
        self.assertEqual(call_args[1]['freeform_context'], "emphasize business impact and ROI")
    
    def test_phase2_3_document_upload_flow(self):
        """Test Phase 2.3: Complete document upload flow with context."""
        user_id = 12345
        
        # Mock document
        mock_document = Mock()
        mock_document.file_name = "test_file.md"
        mock_document.file_size = 1024  # 1KB
        
        # Mock update
        mock_update = Mock()
        mock_update.effective_user.id = user_id
        mock_update.message.document = mock_document
        
        # Mock file download
        mock_file = AsyncMock()
        mock_file.download_as_bytearray = AsyncMock(return_value=b"# Test Content\nThis is a test.")
        mock_document.get_file = AsyncMock(return_value=mock_file)
        
        # Mock context
        mock_context = Mock()
        
        # Mock send_formatted_message
        self.bot._send_formatted_message = AsyncMock()
        
        # Mock ask_for_file_context
        self.bot._ask_for_file_context = AsyncMock()
        
        # Test document upload
        asyncio.run(self.bot._handle_document(mock_update, mock_context))
        
        # Verify file context was requested
        self.bot._ask_for_file_context.assert_called_once()
        call_args = self.bot._ask_for_file_context.call_args
        session = call_args[0][2]
        
        # Verify session was created correctly
        self.assertEqual(session['original_markdown'], "# Test Content\nThis is a test.")
        self.assertEqual(session['filename'], "test_file.md")
    
    def test_phase2_3_context_processing_workflow(self):
        """Test Phase 2.3: Complete context processing workflow."""
        user_id = 12345
        markdown_content = "# Test Content\nThis is a test."
        filename = "test_file.md"
        
        session = self.bot._initialize_session(user_id, markdown_content, filename)
        session['state'] = 'awaiting_file_context'
        self.bot.user_sessions[user_id] = session
        
        # Mock the update and context
        mock_update = Mock()
        mock_update.effective_user.id = user_id
        mock_update.message.text = "focus on technical implementation details"
        mock_context = Mock()
        
        # Mock tone selection
        self.bot._show_initial_tone_selection = AsyncMock()
        
        # Test context processing
        asyncio.run(self.bot._handle_file_context_input(mock_update, mock_context, "focus on technical implementation details"))
        
        # Verify context was stored and state was reset
        self.assertEqual(session['freeform_context'], "focus on technical implementation details")
        self.assertIsNone(session['state'])
        
        # Verify tone selection was called
        self.bot._show_initial_tone_selection.assert_called_once_with(mock_update, mock_context, session)


if __name__ == '__main__':
    unittest.main() 