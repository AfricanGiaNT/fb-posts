"""
Test cases for CrossFileRegenerator class.
Tests content regeneration with cross-file awareness.
"""

import pytest
from datetime import datetime
from implemented.cross_file_regenerator import CrossFileRegenerator

# Test data
@pytest.fixture
def sample_files():
    """Create sample files data for testing."""
    return [
        {
            'file_id': 'file1',
            'filename': 'test1.md',
            'content': 'Test content 1',
            'technical_elements': ['Python', 'AsyncIO'],
            'content_summary': {
                'key_points': ['Point 1', 'Point 2']
            }
        },
        {
            'file_id': 'file2',
            'filename': 'test2.md',
            'content': 'Test content 2',
            'technical_elements': ['Python', 'Testing'],
            'content_summary': {
                'key_points': ['Point 3', 'Point 4']
            }
        },
        {
            'file_id': 'file3',
            'filename': 'test3.md',
            'content': 'Test content 3',
            'technical_elements': ['Docker', 'CI/CD'],
            'content_summary': {
                'key_points': ['Point 5', 'Point 6']
            }
        }
    ]

@pytest.fixture
def sample_strategy():
    """Create sample strategy data for testing."""
    return {
        'project_theme': 'Test Project',
        'narrative_flow': 'Technical progression',
        'recommended_sequence': [
            {
                'file_id': 'file1',
                'theme': 'planning',
                'tone': 'behind-the-build'
            },
            {
                'file_id': 'file2',
                'theme': 'implementation',
                'tone': 'technical-deep-dive'
            },
            {
                'file_id': 'file3',
                'theme': 'results',
                'tone': 'finished-proud'
            }
        ],
        'cross_references': [
            {
                'source_id': 'file1',
                'target_id': 'file2',
                'type': 'continuation'
            },
            {
                'source_id': 'file2',
                'target_id': 'file3',
                'type': 'technical'
            }
        ]
    }

@pytest.mark.asyncio
async def test_regenerate_content(sample_files, sample_strategy):
    """Test content regeneration with context."""
    regenerator = CrossFileRegenerator()
    target_file = sample_files[1]  # Middle file
    feedback = "Add more technical details"
    
    # Test regeneration
    result = await regenerator.regenerate_content(
        target_file, sample_files, sample_strategy, feedback
    )
    
    # Check context was added
    assert 'regeneration_context' in result
    assert 'preserved_references' in result
    assert result['user_feedback'] == feedback
    assert 'last_regenerated' in result

def test_build_regeneration_context(sample_files, sample_strategy):
    """Test context building for regeneration."""
    regenerator = CrossFileRegenerator()
    target_file = sample_files[1]  # Middle file
    
    context = regenerator._build_regeneration_context(
        target_file, sample_files, sample_strategy
    )
    
    # Check context structure
    assert context['narrative_position'] == 2
    assert context['total_posts'] == 3
    assert len(context['previous_posts']) == 1
    assert len(context['next_posts']) == 1
    assert context['project_theme'] == 'Test Project'
    assert context['narrative_flow'] == 'Technical progression'
    assert len(context['technical_elements']) > 0

def test_extract_existing_references(sample_files, sample_strategy):
    """Test reference extraction."""
    regenerator = CrossFileRegenerator()
    target_file = sample_files[1]  # Middle file
    
    references = regenerator._extract_existing_references(
        target_file, sample_strategy
    )
    
    # Should find references where file2 is source or target
    assert len(references) == 2
    assert any(ref['source_id'] == 'file2' for ref in references)
    assert any(ref['target_id'] == 'file2' for ref in references)

def test_extract_key_points(sample_files):
    """Test key points extraction."""
    regenerator = CrossFileRegenerator()
    post = sample_files[0]
    
    # Test with content summary
    points = regenerator._extract_key_points(post)
    assert len(points) == 2
    assert 'Point 1' in points
    
    # Test with only technical elements
    del post['content_summary']
    points = regenerator._extract_key_points(post)
    assert len(points) == 2
    assert 'Python' in points
    
    # Test with no data
    points = regenerator._extract_key_points({})
    assert len(points) == 0

def test_extract_technical_elements(sample_files):
    """Test technical elements extraction."""
    regenerator = CrossFileRegenerator()
    target_file = sample_files[0]  # Contains Python, AsyncIO
    
    elements = regenerator._extract_technical_elements(
        target_file, sample_files
    )
    
    # Should combine elements from target file and related files
    # Target file has Python, AsyncIO
    # Second file has Python, Testing (related due to Python)
    # Third file has Docker, CI/CD (not related)
    assert len(elements) == 3
    assert 'Python' in elements
    assert 'AsyncIO' in elements
    assert 'Testing' in elements
    assert 'Docker' not in elements  # Not related to target file
    assert 'CI/CD' not in elements  # Not related to target file

def test_error_handling(sample_files, sample_strategy):
    """Test error handling in regeneration."""
    regenerator = CrossFileRegenerator()
    
    # Test with invalid file data
    result = regenerator._build_regeneration_context(
        {}, sample_files, sample_strategy
    )
    assert result == {}
    
    # Test with invalid strategy
    references = regenerator._extract_existing_references(
        sample_files[0], {}
    )
    assert references == []
    
    # Test with invalid post data
    points = regenerator._extract_key_points(None)
    assert points == [] 