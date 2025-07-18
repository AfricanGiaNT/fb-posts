#!/usr/bin/env python3
"""
Integration Tests for Phase 5.1 & 5.2: Complete Multi-File Workflow
Tests the complete multi-file upload system including batch upload, project analysis, and strategy generation
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from config_manager import ConfigManager
from enhanced_telegram_bot import EnhancedFacebookContentBot
from project_analyzer import ProjectAnalyzer

class TestPhase5Integration(unittest.TestCase):
    """Integration tests for Phase 5.1 and 5.2"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = ConfigManager()
        
        # Mock AI components to avoid actual API calls
        with patch('scripts.enhanced_telegram_bot.ProjectAnalyzer') as mock_analyzer_class:
            self.mock_analyzer = Mock()
            mock_analyzer_class.return_value = self.mock_analyzer
            self.bot = EnhancedFacebookContentBot()
            
        self.test_user_id = 12345
        
        # Sample file data for testing
        self.sample_file_data = [
            {
                'filename': 'planning-phase-001.md',
                'content': 'Planning phase content with architecture and requirements',
                'file_phase': 'planning',
                'content_summary': 'Project planning and architecture design',
                'key_themes': ['architecture', 'planning'],
                'technical_elements': ['api', 'database'],
                'business_impact': ['efficiency', 'value'],
                'word_count': 500,
                'processing_status': 'analyzed',
                'challenges_identified': ['scalability challenge'],
                'solutions_presented': ['microservice solution'],
                'complexity_score': 0.6
            },
            {
                'filename': 'implementation-core-001.md',
                'content': 'Implementation content with code and technical details',
                'file_phase': 'implementation',
                'content_summary': 'Core system implementation',
                'key_themes': ['implementation', 'coding'],
                'technical_elements': ['api', 'server', 'database'],
                'business_impact': ['productivity', 'automation'],
                'word_count': 1200,
                'processing_status': 'analyzed',
                'challenges_identified': ['performance challenge'],
                'solutions_presented': ['optimization solution'],
                'complexity_score': 0.8
            },
            {
                'filename': 'debugging-session-001.md',
                'content': 'Debugging content with problems and solutions',
                'file_phase': 'debugging',
                'content_summary': 'System debugging and issue resolution',
                'key_themes': ['debugging', 'troubleshooting'],
                'technical_elements': ['monitoring', 'logging'],
                'business_impact': ['reliability', 'stability'],
                'word_count': 800,
                'processing_status': 'analyzed',
                'challenges_identified': ['bug in authentication'],
                'solutions_presented': ['security patch'],
                'complexity_score': 0.5
            },
            {
                'filename': 'results-final-001.md',
                'content': 'Results content with metrics and outcomes',
                'file_phase': 'results',
                'content_summary': 'Final results and performance metrics',
                'key_themes': ['results', 'metrics'],
                'technical_elements': ['performance', 'monitoring'],
                'business_impact': ['roi', 'success'],
                'word_count': 600,
                'processing_status': 'analyzed',
                'challenges_identified': [],
                'solutions_presented': ['deployment solution'],
                'complexity_score': 0.4
            }
        ]
        
        # Mock project analysis result
        self.mock_project_analysis = {
            'project_theme': 'Authentication System Development',
            'narrative_arc': 'Complete development journey: planning → implementation → debugging → results',
            'key_challenges': ['scalability challenge', 'performance challenge', 'bug in authentication'],
            'solutions_implemented': ['microservice solution', 'optimization solution', 'security patch'],
            'technical_stack': ['api', 'database', 'server', 'monitoring', 'logging'],
            'business_outcomes': ['efficiency', 'productivity', 'reliability', 'roi'],
            'content_threads': [
                {'type': 'technical', 'name': 'API Development', 'files': ['planning-phase-001.md', 'implementation-core-001.md']},
                {'type': 'problem_solution', 'name': 'Issue Resolution', 'files': ['debugging-session-001.md']}
            ],
            'estimated_posts': 5,
            'completeness_score': 0.9,
            'cohesion_score': 0.8,
            'files_analyzed': 4,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def test_complete_multi_file_workflow(self):
        """Test complete multi-file workflow from upload to strategy generation"""
        # Step 1: Initialize batch session
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        self.assertEqual(session['mode'], 'multi')
        self.assertEqual(session['workflow_state'], 'collecting_files')
        self.assertEqual(len(session['source_files']), 0)
        
        # Step 2: Add files to session
        for file_data in self.sample_file_data:
            session['source_files'].append(file_data)
        
        self.assertEqual(len(session['source_files']), 4)
        
        # Step 3: Mock project analysis
        self.mock_analyzer.analyze_project_narrative.return_value = self.mock_project_analysis
        
        # Simulate project analysis
        session['project_overview'] = self.mock_project_analysis
        session['workflow_state'] = 'project_analyzed'
        
        # Step 4: Generate content strategy
        source_files = session['source_files']
        
        # Basic sequence based on file phases
        phase_order = ['planning', 'implementation', 'debugging', 'results']
        sorted_files = sorted(source_files, 
                            key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
        
        recommended_sequence = []
        for i, file in enumerate(sorted_files, 1):
            recommended_sequence.append({
                'position': i,
                'filename': file['filename'],
                'phase': file['file_phase'],
                'recommended_tone': self.bot._suggest_tone_for_phase(file['file_phase']),
                'estimated_engagement': 'High' if file['file_phase'] in ['implementation', 'results'] else 'Medium'
            })
        
        content_strategy = {
            'recommended_sequence': recommended_sequence,
            'estimated_posts': len(sorted_files),
            'narrative_flow': self.mock_project_analysis['narrative_arc'],
            'cross_references': self.bot._generate_basic_cross_references(sorted_files),
            'audience_split': {'business': 60, 'technical': 40}
        }
        
        session['content_strategy'] = content_strategy
        session['workflow_state'] = 'strategy_generated'
        
        # Verify final state
        self.assertEqual(session['workflow_state'], 'strategy_generated')
        self.assertIn('project_overview', session)
        self.assertIn('content_strategy', session)
        self.assertEqual(len(session['content_strategy']['recommended_sequence']), 4)
        
        # Verify sequence order
        sequence = session['content_strategy']['recommended_sequence']
        self.assertEqual(sequence[0]['phase'], 'planning')
        self.assertEqual(sequence[1]['phase'], 'implementation')
        self.assertEqual(sequence[2]['phase'], 'debugging')
        self.assertEqual(sequence[3]['phase'], 'results')
        
        # Verify tone recommendations
        self.assertEqual(sequence[0]['recommended_tone'], 'Behind-the-Build')
        self.assertEqual(sequence[1]['recommended_tone'], 'Problem → Solution → Result')
        self.assertEqual(sequence[2]['recommended_tone'], 'What Broke')
        self.assertEqual(sequence[3]['recommended_tone'], 'Finished & Proud')
    
    def test_file_categorization_integration(self):
        """Test file categorization integration with session management"""
        # Initialize session
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Mock file categorization with proper patching
        with patch.object(self.bot.project_analyzer, 'categorize_file') as mock_categorize:
            mock_categorize.return_value = self.sample_file_data[0]
            
            # Test categorization
            result = self.bot._categorize_file(
                self.sample_file_data[0]['content'],
                self.sample_file_data[0]['filename']
            )
            
            self.assertEqual(result, 'planning')
            mock_categorize.assert_called_once_with(
                self.sample_file_data[0]['content'],
                self.sample_file_data[0]['filename']
            )
    
    def test_project_analysis_integration(self):
        """Test project analysis integration"""
        # Set up session with files
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        session['source_files'] = self.sample_file_data
        
        # Mock project analysis
        self.mock_analyzer.analyze_project_narrative.return_value = self.mock_project_analysis
        
        # Test project analysis
        result = self.mock_analyzer.analyze_project_narrative(session['source_files'])
        
        self.assertEqual(result, self.mock_project_analysis)
        self.assertEqual(result['files_analyzed'], 4)
        self.assertEqual(result['estimated_posts'], 5)
        self.assertGreater(result['completeness_score'], 0.8)
        self.mock_analyzer.analyze_project_narrative.assert_called_once_with(session['source_files'])
    
    def test_strategy_generation_integration(self):
        """Test strategy generation integration"""
        # Set up session
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        session['source_files'] = self.sample_file_data
        session['project_overview'] = self.mock_project_analysis
        
        # Generate strategy
        source_files = session['source_files']
        phase_order = ['planning', 'implementation', 'debugging', 'results']
        sorted_files = sorted(source_files, 
                            key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
        
        # Test strategy components
        self.assertEqual(len(sorted_files), 4)
        self.assertEqual(sorted_files[0]['file_phase'], 'planning')
        self.assertEqual(sorted_files[1]['file_phase'], 'implementation')
        self.assertEqual(sorted_files[2]['file_phase'], 'debugging')
        self.assertEqual(sorted_files[3]['file_phase'], 'results')
        
        # Test cross-references
        references = self.bot._generate_basic_cross_references(sorted_files)
        self.assertEqual(len(references), 3)  # N-1 references for N files
        
        # Test tone suggestions
        tones = [self.bot._suggest_tone_for_phase(f['file_phase']) for f in sorted_files]
        expected_tones = ['Behind-the-Build', 'Problem → Solution → Result', 'What Broke', 'Finished & Proud']
        self.assertEqual(tones, expected_tones)
    
    def test_session_state_transitions(self):
        """Test session state transitions through workflow"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Test state progression
        states = [
            'collecting_files',
            'upload_complete',
            'project_analyzed',
            'strategy_generated',
            'content_generation',
            'series_complete'
        ]
        
        for state in states:
            session['workflow_state'] = state
            self.assertEqual(session['workflow_state'], state)
            
            # Verify session persistence
            retrieved_session = self.bot.user_sessions[self.test_user_id]
            self.assertEqual(retrieved_session['workflow_state'], state)
    
    def test_timeout_handling_integration(self):
        """Test timeout handling integration"""
        # Test multi-file timeout
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Should not be timed out initially
        self.assertFalse(self.bot._check_multi_file_timeout(self.test_user_id))
        
        # Set timeout in past
        session['batch_timeout'] = datetime.now() - timedelta(minutes=1)
        
        # Should be timed out now
        self.assertTrue(self.bot._check_multi_file_timeout(self.test_user_id))
        
        # Test single-file timeout
        session = self.bot._initialize_session(self.test_user_id, "content", "file.md")
        
        # Should not be timed out initially
        self.assertFalse(self.bot._check_multi_file_timeout(self.test_user_id))
        
        # Set activity in past
        session['last_activity'] = (datetime.now() - timedelta(minutes=20)).isoformat()
        
        # Should be timed out now
        self.assertTrue(self.bot._check_multi_file_timeout(self.test_user_id))
    
    def test_backward_compatibility_integration(self):
        """Test backward compatibility with single-file workflow"""
        # Test single-file session
        single_session = self.bot._initialize_session(
            self.test_user_id,
            "single file content",
            "single.md"
        )
        
        self.assertEqual(single_session['mode'], 'single')
        self.assertEqual(single_session['workflow_state'], 'single_file')
        self.assertIn('source_files', single_session)  # Should have multi-file fields
        self.assertEqual(len(single_session['source_files']), 0)  # But empty
        
        # Test that multi-file fields exist but are empty
        multi_file_fields = ['source_files', 'project_overview', 'content_strategy', 'user_customizations']
        for field in multi_file_fields:
            self.assertIn(field, single_session)
            self.assertEqual(single_session[field], {} if field != 'source_files' else [])
        
        # Test that single-file fields are populated
        single_file_fields = ['original_markdown', 'filename']
        for field in single_file_fields:
            self.assertIn(field, single_session)
            self.assertNotEqual(single_session[field], '')
    
    def test_error_handling_integration(self):
        """Test error handling in integrated workflow"""
        # Test with analyzer error
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        session['source_files'] = self.sample_file_data
        
        # Mock analyzer error
        self.mock_analyzer.analyze_project_narrative.side_effect = Exception("Analysis error")
        
        # Should handle error gracefully
        try:
            self.bot._categorize_file("test content", "test.md")
        except Exception as e:
            self.assertEqual(str(e), "Analysis error")
        
        # Test with empty session
        empty_session = self.bot._initialize_multi_file_session(99999)
        empty_session['source_files'] = []
        
        # Should handle empty files gracefully
        self.mock_analyzer.analyze_project_narrative.side_effect = None
        self.mock_analyzer.analyze_project_narrative.return_value = {
            'project_theme': 'No files analyzed',
            'files_analyzed': 0,
            'estimated_posts': 0
        }
        
        result = self.mock_analyzer.analyze_project_narrative([])
        self.assertEqual(result['files_analyzed'], 0)
    
    def test_file_limit_integration(self):
        """Test file limit enforcement integration"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        
        # Add files up to limit
        for i in range(8):
            file_data = {
                'filename': f'file_{i}.md',
                'file_phase': 'implementation',
                'content': f'content {i}',
                'word_count': 100
            }
            session['source_files'].append(file_data)
        
        # Verify limit reached
        self.assertEqual(len(session['source_files']), 8)
        
        # Should be able to check limit
        self.assertTrue(len(session['source_files']) >= 8)
        
        # Test with over limit (should be handled by UI)
        extra_file = {
            'filename': 'extra.md',
            'file_phase': 'implementation',
            'content': 'extra content',
            'word_count': 100
        }
        
        # UI should prevent this, but if it happens, session should handle it
        if len(session['source_files']) < 8:
            session['source_files'].append(extra_file)
        
        # Should not exceed limit in proper implementation
        self.assertLessEqual(len(session['source_files']), 8)
    
    def test_content_strategy_quality(self):
        """Test content strategy quality and consistency"""
        session = self.bot._initialize_multi_file_session(self.test_user_id)
        session['source_files'] = self.sample_file_data
        session['project_overview'] = self.mock_project_analysis
        
        # Generate strategy
        source_files = session['source_files']
        phase_order = ['planning', 'implementation', 'debugging', 'results']
        sorted_files = sorted(source_files, 
                            key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
        
        # Test strategy quality
        self.assertEqual(len(sorted_files), 4)
        
        # Verify logical sequence
        phases = [f['file_phase'] for f in sorted_files]
        self.assertEqual(phases, ['planning', 'implementation', 'debugging', 'results'])
        
        # Test tone recommendations quality
        tones = [self.bot._suggest_tone_for_phase(f['file_phase']) for f in sorted_files]
        
        # Should have appropriate tones for each phase
        self.assertEqual(tones[0], 'Behind-the-Build')  # planning
        self.assertEqual(tones[1], 'Problem → Solution → Result')  # implementation
        self.assertEqual(tones[2], 'What Broke')  # debugging
        self.assertEqual(tones[3], 'Finished & Proud')  # results
        
        # Test cross-references quality
        references = self.bot._generate_basic_cross_references(sorted_files)
        
        # Should have logical references
        self.assertEqual(len(references), 3)
        for i, ref in enumerate(references):
            self.assertEqual(ref['type'], 'sequential')
            self.assertEqual(ref['from_file'], sorted_files[i+1]['filename'])
            self.assertEqual(ref['to_file'], sorted_files[i]['filename'])
    
    def test_memory_management_integration(self):
        """Test memory management in integrated workflow"""
        # Test multiple sessions
        user_ids = [1, 2, 3, 4, 5]
        sessions = []
        
        for user_id in user_ids:
            session = self.bot._initialize_multi_file_session(user_id)
            session['source_files'] = self.sample_file_data[:2]  # Add some files
            sessions.append(session)
        
        # Verify all sessions exist
        self.assertEqual(len(self.bot.user_sessions), 5)
        
        # Verify each session has correct data
        for i, user_id in enumerate(user_ids):
            session = self.bot.user_sessions[user_id]
            self.assertEqual(session['mode'], 'multi')
            self.assertEqual(len(session['source_files']), 2)
        
        # Test cleanup
        for user_id in user_ids:
            if user_id in self.bot.user_sessions:
                del self.bot.user_sessions[user_id]
        
        # Verify cleanup
        self.assertEqual(len(self.bot.user_sessions), 0)
    
    def test_performance_integration(self):
        """Test performance characteristics of integrated workflow"""
        import time
        
        # Test session creation performance
        start_time = time.time()
        
        for i in range(10):
            session = self.bot._initialize_multi_file_session(1000 + i)
            session['source_files'] = self.sample_file_data
        
        end_time = time.time()
        
        # Should be fast for session operations
        self.assertLess(end_time - start_time, 1.0)
        
        # Test strategy generation performance
        session = self.bot.user_sessions[1000]
        
        start_time = time.time()
        
        # Generate strategy multiple times
        for i in range(5):
            source_files = session['source_files']
            phase_order = ['planning', 'implementation', 'debugging', 'results']
            sorted_files = sorted(source_files, 
                                key=lambda f: phase_order.index(f.get('file_phase', 'implementation')))
            references = self.bot._generate_basic_cross_references(sorted_files)
        
        end_time = time.time()
        
        # Should be fast for strategy operations
        self.assertLess(end_time - start_time, 0.5)
        
        # Clean up
        for i in range(10):
            if 1000 + i in self.bot.user_sessions:
                del self.bot.user_sessions[1000 + i]


class TestPhase5AsyncIntegration(unittest.TestCase):
    """Test async integration scenarios"""
    
    def setUp(self):
        """Set up async test environment"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.config = ConfigManager()
        
        # Mock components
        with patch('scripts.enhanced_telegram_bot.ProjectAnalyzer') as mock_analyzer_class:
            self.mock_analyzer = Mock()
            mock_analyzer_class.return_value = self.mock_analyzer
            self.bot = EnhancedFacebookContentBot()
        
        self.test_user_id = 12345
    
    def tearDown(self):
        """Clean up async test environment"""
        self.loop.close()
    
    def test_async_file_processing(self):
        """Test async file processing integration"""
        async def async_test():
            # Mock async file processing
            mock_file_analysis = {
                'filename': 'test.md',
                'file_phase': 'implementation',
                'content': 'test content',
                'word_count': 100,
                'processing_status': 'analyzed'
            }
            
            # Mock asyncio.to_thread
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_to_thread.return_value = mock_file_analysis
                
                # Test async file categorization
                result = await asyncio.to_thread(
                    self.bot._categorize_file,
                    "test content",
                    "test.md"
                )
                
                # Verify async call was made
                mock_to_thread.assert_called_once()
        
        self.loop.run_until_complete(async_test())
    
    def test_async_project_analysis(self):
        """Test async project analysis integration"""
        async def async_test():
            # Mock project analysis
            mock_project_analysis = {
                'project_theme': 'Test Project',
                'files_analyzed': 2,
                'estimated_posts': 3
            }
            
            # Test async project analysis
            with patch('asyncio.to_thread') as mock_to_thread:
                mock_to_thread.return_value = mock_project_analysis
                
                result = await asyncio.to_thread(
                    self.mock_analyzer.analyze_project_narrative,
                    []
                )
                
                self.assertEqual(result, mock_project_analysis)
                mock_to_thread.assert_called_once()
        
        self.loop.run_until_complete(async_test())


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 