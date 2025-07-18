"""
Test cases for SessionManager class.
Tests session persistence, backup, and recovery functionality.
"""

import pytest
import os
import json
import shutil
from datetime import datetime, timedelta
from implemented.session_manager import SessionManager
import asyncio

# Test data
@pytest.fixture
def sample_session():
    """Create sample session data for testing."""
    return {
        'series_id': 'test-series',
        'session_started': datetime.now().isoformat(),
        'source_files': [
            {
                'file_id': 'file1',
                'filename': 'test1.md',
                'content': 'Test content 1'
            }
        ]
    }

@pytest.fixture
def test_backup_dir(tmp_path):
    """Create temporary backup directory."""
    backup_dir = tmp_path / "test_backups"
    backup_dir.mkdir()
    yield str(backup_dir)
    # Cleanup
    shutil.rmtree(str(backup_dir))

@pytest.mark.asyncio
async def test_save_and_load_session(test_backup_dir, sample_session):
    """Test saving and loading session."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Save session
    success = await manager.save_session(user_id, sample_session)
    assert success
    
    # Verify file exists
    session_file = os.path.join(test_backup_dir, f"session_{user_id}.json")
    assert os.path.exists(session_file)
    
    # Load session
    loaded_session = await manager.load_session(user_id)
    assert loaded_session is not None
    assert loaded_session['series_id'] == sample_session['series_id']
    assert len(loaded_session['source_files']) == 1
    
    # Test loading non-existent session
    loaded_session = await manager.load_session(99999)
    assert loaded_session is None

@pytest.mark.asyncio
async def test_session_expiration(test_backup_dir, sample_session):
    """Test session expiration handling."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Create expired session
    expired_session = sample_session.copy()
    expired_session['session_started'] = (
        datetime.now() - timedelta(minutes=31)
    ).isoformat()
    
    # Save expired session
    await manager.save_session(user_id, expired_session)
    
    # Try to load expired session
    loaded_session = await manager.load_session(user_id)
    assert loaded_session is None
    
    # Verify session file was cleared
    session_file = os.path.join(test_backup_dir, f"session_{user_id}.json")
    assert not os.path.exists(session_file)

@pytest.mark.asyncio
async def test_backup_creation(test_backup_dir, sample_session):
    """Test backup creation and cleanup."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Create multiple backups with small delays
    for i in range(7):
        success = await manager.create_backup(user_id, sample_session)
        assert success
        await asyncio.sleep(0.1)  # Add small delay between backups
    
    # Check only 5 backups are kept
    backup_files = [
        f for f in os.listdir(test_backup_dir)
        if f.startswith(f"backup_{user_id}_")
    ]
    assert len(backup_files) == 5

@pytest.mark.asyncio
async def test_backup_restoration(test_backup_dir, sample_session):
    """Test restoring from backup."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Create backup
    await manager.create_backup(user_id, sample_session)
    
    # Clear session
    await manager.clear_session(user_id)
    
    # Restore from backup
    restored_session = await manager.restore_from_backup(user_id)
    assert restored_session is not None
    assert restored_session['series_id'] == sample_session['series_id']
    
    # Test restoring with no backup
    restored_session = await manager.restore_from_backup(99999)
    assert restored_session is None

@pytest.mark.asyncio
async def test_periodic_backup(test_backup_dir, sample_session):
    """Test periodic backup task."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Start backup task
    await manager.start_backup_task(user_id, sample_session)
    assert manager._backup_task is not None
    assert not manager._backup_task.done()
    
    # Stop backup task
    await manager.stop_backup_task()
    assert manager._backup_task.done()

@pytest.mark.asyncio
async def test_clear_session(test_backup_dir, sample_session):
    """Test session clearing."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Save session
    await manager.save_session(user_id, sample_session)
    
    # Clear session
    success = await manager.clear_session(user_id)
    assert success
    
    # Verify session is cleared
    session_file = os.path.join(test_backup_dir, f"session_{user_id}.json")
    assert not os.path.exists(session_file)
    
    # Test clearing non-existent session
    success = await manager.clear_session(99999)
    assert success  # Should return True even if file doesn't exist

def test_backup_directory_creation():
    """Test backup directory creation."""
    test_dir = "temp_test_backups"
    try:
        manager = SessionManager(backup_dir=test_dir)
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

@pytest.mark.asyncio
async def test_error_handling(test_backup_dir):
    """Test error handling in session operations."""
    manager = SessionManager(backup_dir=test_backup_dir)
    user_id = 12345
    
    # Test with invalid session data
    success = await manager.save_session(user_id, None)
    assert not success
    
    # Test with invalid backup directory
    manager.backup_dir = "/invalid/path"
    success = await manager.save_session(user_id, {})
    assert not success
    
    loaded_session = await manager.load_session(user_id)
    assert loaded_session is None 