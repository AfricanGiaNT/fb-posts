"""
Test Phase 2: Smart Context Prioritization
Tests the implementation of intelligent context scoring, selection, and optimization.
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from context_prioritizer import ContextPrioritizer
from telegram_bot import FacebookContentBot

class TestPhase2ContextPrioritization(unittest.TestCase):
    """Test Phase 2: Smart Context Prioritization implementation."""
    
    def setUp(self):
        """Set up test environment."""
        self.prioritizer = ContextPrioritizer()
        self.bot = FacebookContentBot()
        self.user_id = 12345
        
        # Sample chat history for testing
        self.sample_chat_history = [
            {
                'timestamp': datetime.now().isoformat(),
                'user_message': 'Uploaded file: project.md',
                'bot_response': 'File processed successfully',
                'message_type': 'file_upload',
                'context': {'filename': 'project.md', 'file_size': 1024},
                'satisfaction_score': 0.9
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                'user_message': 'Generate post with technical tone',
                'bot_response': 'Post generated successfully',
                'message_type': 'post_generation',
                'context': {'tone_used': 'technical', 'audience_type': 'business'},
                'satisfaction_score': 0.8
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                'user_message': 'Regenerate with different approach',
                'bot_response': 'Post regenerated',
                'message_type': 'post_regeneration',
                'context': {'reason': 'user requested different approach'},
                'satisfaction_score': 0.6
            }
        ]
    
    def test_phase2_01_context_prioritizer_initialization(self):
        """Test ContextPrioritizer initialization and configuration."""
        self.assertIsNotNone(self.prioritizer)
        self.assertIsInstance(self.prioritizer.relevance_weights, dict)
        self.assertIsInstance(self.prioritizer.message_type_importance, dict)
        self.assertIsInstance(self.prioritizer.request_type_keywords, dict)
        
        # Check that weights sum to reasonable values
        total_weight = sum(self.prioritizer.relevance_weights.values())
        self.assertGreater(total_weight, 0.5)
        self.assertLess(total_weight, 1.5)
    
    def test_phase2_02_recency_scoring(self):
        """Test recency scoring algorithm."""
        # Test recent timestamp
        recent_timestamp = datetime.now().isoformat()
        recent_score = self.prioritizer._calculate_recency_score(recent_timestamp)
        self.assertGreater(recent_score, 0.8)
        
        # Test old timestamp
        old_timestamp = (datetime.now() - timedelta(days=7)).isoformat()
        old_score = self.prioritizer._calculate_recency_score(old_timestamp)
        self.assertLess(old_score, 0.3)
        
        # Test invalid timestamp
        invalid_score = self.prioritizer._calculate_recency_score("invalid")
        self.assertEqual(invalid_score, 0.5)
    
    def test_phase2_03_similarity_scoring(self):
        """Test content similarity scoring."""
        context_item = {
            'user_message': 'Generate technical post about AI',
            'bot_response': 'Post generated with technical details',
            'context': {'tone_used': 'technical'}
        }
        
        current_request = {
            'type': 'post_generation',
            'content': 'Create technical content about machine learning'
        }
        
        similarity_score = self.prioritizer._calculate_similarity_score(context_item, current_request)
        self.assertGreater(similarity_score, 0.3)  # Should have some similarity
        self.assertLessEqual(similarity_score, 1.0)
    
    def test_phase2_04_importance_scoring(self):
        """Test importance scoring based on message type and content."""
        # High importance interaction
        high_importance = {
            'message_type': 'post_approval',
            'satisfaction_score': 0.9,
            'context': {'tone_used': 'technical', 'audience_type': 'business'}
        }
        high_score = self.prioritizer._calculate_importance_score(high_importance)
        self.assertGreater(high_score, 0.8)
        
        # Low importance interaction
        low_importance = {
            'message_type': 'button_click',
            'satisfaction_score': 0.5,
            'context': {}
        }
        low_score = self.prioritizer._calculate_importance_score(low_importance)
        self.assertLess(low_score, 0.6)
    
    def test_phase2_05_context_relevance_scoring(self):
        """Test overall context relevance scoring."""
        context_item = {
            'timestamp': datetime.now().isoformat(),
            'user_message': 'Generate technical post',
            'bot_response': 'Post generated',
            'message_type': 'post_generation',
            'context': {'tone_used': 'technical'},
            'satisfaction_score': 0.8
        }
        
        current_request = {
            'type': 'post_generation',
            'content': 'Create technical content'
        }
        
        relevance_score = self.prioritizer.score_context_relevance(context_item, current_request)
        self.assertGreater(relevance_score, 0.5)
        self.assertLessEqual(relevance_score, 1.0)
    
    def test_phase2_06_optimal_context_selection(self):
        """Test optimal context selection with token limits."""
        session = {'chat_history': self.sample_chat_history}
        current_request = {
            'type': 'post_generation',
            'content': 'Generate new post'
        }
        
        optimized_context = self.prioritizer.select_optimal_context(
            session=session,
            current_request=current_request,
            max_tokens=1000
        )
        
        self.assertIsInstance(optimized_context, str)
        self.assertIn("Previous Interactions Context", optimized_context)
    
    def test_phase2_07_context_statistics(self):
        """Test context statistics generation."""
        session = {'chat_history': self.sample_chat_history}
        stats = self.prioritizer.get_context_statistics(session)
        
        self.assertEqual(stats['total_interactions'], 3)
        self.assertGreater(stats['average_satisfaction'], 0.7)
        self.assertIn('file_upload', stats['message_types'])
        self.assertIn('post_generation', stats['message_types'])
    
    def test_phase2_08_bot_integration(self):
        """Test ContextPrioritizer integration with bot."""
        self.assertIsNotNone(self.bot.context_prioritizer)
        # Check that it's a ContextPrioritizer instance (accounting for import path differences)
        self.assertIn('ContextPrioritizer', str(type(self.bot.context_prioritizer)))
    
    def test_phase2_09_optimized_context_retrieval(self):
        """Test optimized context retrieval from bot."""
        # Initialize session with chat history
        session = self.bot._initialize_session(self.user_id, "# Test\nContent", "test.md")
        session['chat_history'] = self.sample_chat_history
        self.bot.user_sessions[self.user_id] = session
        
        current_request = {
            'type': 'post_generation',
            'content': 'Generate new post'
        }
        
        optimized_context = self.bot._get_optimized_context_for_prompt(
            user_id=self.user_id,
            current_request=current_request,
            max_tokens=1000
        )
        
        self.assertIsInstance(optimized_context, str)
    
    def test_phase2_10_context_statistics_retrieval(self):
        """Test context statistics retrieval from bot."""
        # Initialize session with chat history
        session = self.bot._initialize_session(self.user_id, "# Test\nContent", "test.md")
        session['chat_history'] = self.sample_chat_history
        self.bot.user_sessions[self.user_id] = session
        
        stats = self.bot._get_context_statistics(self.user_id)
        
        self.assertEqual(stats['total_interactions'], 3)
        self.assertIsInstance(stats['message_types'], dict)
    
    def test_phase2_11_smart_chat_history_retrieval(self):
        """Test smart chat history retrieval with prioritization."""
        # Initialize session with chat history
        session = self.bot._initialize_session(self.user_id, "# Test\nContent", "test.md")
        session['chat_history'] = self.sample_chat_history
        self.bot.user_sessions[self.user_id] = session
        
        current_request = {
            'type': 'post_generation',
            'content': 'Generate technical post'
        }
        
        relevant_history = self.bot._get_relevant_chat_history(
            user_id=self.user_id,
            current_request=current_request,
            max_entries=2
        )
        
        self.assertLessEqual(len(relevant_history), 2)
        # Should return the most relevant entries (likely the recent ones with high satisfaction)
    
    def test_phase2_12_token_estimation(self):
        """Test token estimation for context selection."""
        text = "This is a test text with multiple words for token estimation"
        estimated_tokens = self.prioritizer._estimate_tokens(text)
        
        self.assertIsInstance(estimated_tokens, int)
        self.assertGreater(estimated_tokens, 0)
    
    def test_phase2_13_text_content_extraction(self):
        """Test text content extraction from context items."""
        context_item = {
            'user_message': 'Generate post',
            'bot_response': 'Post created',
            'context': {'tone_used': 'technical', 'reason': 'user request'}
        }
        
        extracted_text = self.prioritizer._extract_text_content(context_item)
        
        self.assertIn('Generate post', extracted_text)
        self.assertIn('Post created', extracted_text)
        self.assertIn('technical', extracted_text)
    
    def test_phase2_14_user_preferences_summary(self):
        """Test user preferences summary generation."""
        context_items = [
            {
                'context': {'tone_used': 'technical', 'audience_type': 'business'},
                'satisfaction_score': 0.9
            },
            {
                'context': {'tone_used': 'casual', 'audience_type': 'technical'},
                'satisfaction_score': 0.3
            }
        ]
        
        summary = self.prioritizer._format_user_preferences_summary(context_items)
        
        self.assertIn('User Preferences Summary', summary)
        self.assertIn('technical', summary)
        self.assertIn('casual', summary)
    
    def test_phase2_15_error_handling(self):
        """Test error handling in context prioritization."""
        # Test with invalid session
        empty_context = self.prioritizer.select_optimal_context({}, {}, 1000)
        self.assertEqual(empty_context, "")
        
        # Test with invalid request
        context_item = {'timestamp': 'invalid', 'message_type': 'unknown'}
        score = self.prioritizer.score_context_relevance(context_item, {})
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

if __name__ == '__main__':
    unittest.main() 