"""
Test cases for BatchUploadUI class.
Tests UI components and message formatting for batch file uploads.
"""

import pytest
from datetime import datetime, timedelta
from implemented.batch_upload_ui import BatchUploadUI

# Test data
@pytest.fixture
def sample_file_data():
    """Create sample file data for testing."""
    return {
        'file_id': 'test1',
        'filename': 'test1.md',
        'content': 'Test content',
        'upload_timestamp': datetime.now(),
        'file_phase': 'planning',
        'processing_status': 'processing',
        'word_count': 100,
        'key_themes': ['architecture', 'planning']
    }

@pytest.fixture
def sample_session():
    """Create sample session data for testing."""
    return {
        'series_id': 'test-series',
        'session_started': datetime.now(),
        'source_files': [
            {
                'file_id': 'file1',
                'filename': 'test1.md',
                'content': 'Test content 1',
                'upload_timestamp': datetime.now(),
                'file_phase': 'planning',
                'processing_status': 'analyzed',
                'word_count': 100
            },
            {
                'file_id': 'file2',
                'filename': 'test2.md',
                'content': 'Test content 2',
                'upload_timestamp': datetime.now(),
                'file_phase': 'implementation',
                'processing_status': 'processing',
                'word_count': 200
            }
        ],
        'project_overview': {
            'project_theme': 'Test Project',
            'technical_stack': ['Python', 'AsyncIO'],
            'key_challenges': ['Challenge 1', 'Challenge 2']
        }
    }

@pytest.mark.asyncio
async def test_show_upload_progress(sample_file_data):
    """Test upload progress message generation."""
    ui = BatchUploadUI()
    
    # Test normal progress message
    result = await ui.show_upload_progress(sample_file_data)
    assert '🔄' in result  # Processing status emoji
    assert 'test1.md' in result
    assert 'planning' in result
    assert '100' in result
    assert 'architecture' in result
    
    # Test error handling
    invalid_data = {}
    result = await ui.show_upload_progress(invalid_data)
    assert '⚠️' in result

@pytest.mark.asyncio
async def test_show_batch_status(sample_session):
    """Test batch status message generation."""
    ui = BatchUploadUI()
    
    result = await ui.show_batch_status(sample_session)
    assert '📚 Batch Upload Status (1/2)' in result
    assert 'Time Remaining' in result
    assert '/project' in result
    assert '/strategy' in result
    assert '/done' in result
    assert '/cancel' in result
    
    # Test error handling
    invalid_session = {}
    result = await ui.show_batch_status(invalid_session)
    assert '⚠️' in result

def test_show_timeout_warning(sample_session):
    """Test timeout warning message generation."""
    ui = BatchUploadUI()
    
    # Test no warning needed
    result = ui.show_timeout_warning(sample_session)
    assert result is None
    
    # Test warning needed
    sample_session['session_started'] = datetime.now() - timedelta(minutes=26)
    result = ui.show_timeout_warning(sample_session)
    assert '⚠️' in result
    assert 'Session will expire' in result
    
    # Test error handling
    invalid_session = {}
    result = ui.show_timeout_warning(invalid_session)
    assert result is None

def test_show_completion_summary(sample_session):
    """Test completion summary message generation."""
    ui = BatchUploadUI()
    
    result = ui.show_completion_summary(sample_session)
    assert '✅ Batch Upload Complete' in result
    assert 'Files Processed: 2' in result
    assert 'Total Words: 300' in result
    assert 'Test Project' in result
    assert 'Python' in result
    assert 'Key Challenges: 2' in result
    
    # Test without project overview
    del sample_session['project_overview']
    result = ui.show_completion_summary(sample_session)
    assert '✅ Batch Upload Complete' in result
    assert 'N/A' in result
    
    # Test error handling
    invalid_session = {}
    result = ui.show_completion_summary(invalid_session)
    assert '⚠️' in result

def test_status_emoji():
    """Test status emoji generation."""
    ui = BatchUploadUI()
    
    assert ui._get_status_emoji('pending') == '⏳'
    assert ui._get_status_emoji('processing') == '🔄'
    assert ui._get_status_emoji('analyzed') == '✅'
    assert ui._get_status_emoji('error') == '❌'
    assert ui._get_status_emoji('unknown') == '❓'

def test_format_status():
    """Test status string formatting."""
    ui = BatchUploadUI()
    
    assert ui._format_status('pending') == 'Pending'
    assert ui._format_status('in_progress') == 'In Progress'
    assert ui._format_status('error_occurred') == 'Error Occurred'

def test_calculate_time_remaining(sample_session):
    """Test time remaining calculation."""
    ui = BatchUploadUI()
    
    # Test normal case
    result = ui._calculate_time_remaining(sample_session)
    assert 'minutes' in result
    
    # Test expired session
    sample_session['session_started'] = datetime.now() - timedelta(minutes=31)
    result = ui._calculate_time_remaining(sample_session)
    assert result == 'Session expired'
    
    # Test error handling
    invalid_session = {}
    result = ui._calculate_time_remaining(invalid_session)
    assert result == 'Unknown' 