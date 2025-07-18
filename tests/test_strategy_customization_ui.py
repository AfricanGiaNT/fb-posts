"""
Test cases for StrategyCustomizationUI class.
Tests UI components for strategy customization interface.
"""

import pytest
from implemented.strategy_customization_ui import StrategyCustomizationUI

# Test data
@pytest.fixture
def sample_strategy():
    """Create sample strategy data for testing."""
    return {
        'project_theme': 'Test Project',
        'recommended_sequence': [
            {
                'file_id': 'file1',
                'filename': 'test1.md',
                'theme': 'planning',
                'tone': 'behind-the-build'
            },
            {
                'file_id': 'file2',
                'filename': 'test2.md',
                'theme': 'implementation',
                'tone': 'technical-deep-dive'
            }
        ],
        'cross_references': [
            {
                'source_id': 'file1',
                'target_id': 'file2',
                'type': 'continuation'
            }
        ],
        'available_files': [
            {
                'file_id': 'file3',
                'filename': 'test3.md',
                'theme': 'testing'
            }
        ],
        'custom_post_count': 0
    }

def test_show_strategy_overview(sample_strategy):
    """Test strategy overview display."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_strategy_overview(sample_strategy)
    
    # Check content
    assert '📋 Content Strategy Overview' in result
    assert 'Test Project' in result
    assert 'test1.md' in result
    assert 'test2.md' in result
    assert 'planning' in result
    assert 'implementation' in result
    assert 'behind-the-build' in result
    assert 'technical-deep-dive' in result
    assert 'file1 → file2' in result
    
    # Check options
    assert '🔄 Reorder sequence' in result
    assert '➕ Add custom post' in result
    assert '➖ Remove post' in result
    assert '🎨 Change tone' in result
    assert '✅ Confirm strategy' in result
    
    # Test error handling
    result = ui.show_strategy_overview({})
    assert '⚠️' in result

def test_show_sequence_editor(sample_strategy):
    """Test sequence editor interface."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_sequence_editor(sample_strategy)
    
    # Check content
    assert '🔄 Sequence Editor' in result
    assert 'test1.md' in result
    assert 'test2.md' in result
    assert 'planning' in result
    assert 'implementation' in result
    
    # Check instructions
    assert 'Enter new sequence' in result
    assert "'3,1,2,4'" in result
    assert 'done' in result
    assert 'cancel' in result
    
    # Test error handling
    result = ui.show_sequence_editor({})
    assert '⚠️' in result

def test_show_tone_selector(sample_strategy):
    """Test tone selector interface."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_tone_selector('file1', sample_strategy)
    
    # Check content
    assert '🎨 Tone Selector' in result
    assert 'file1' in result
    assert 'behind-the-build' in result
    
    # Check tone options
    assert '🏗️ Behind-the-Build' in result
    assert '💔 What Broke' in result
    assert '🎯 Problem → Solution' in result
    assert '✨ Finished & Proud' in result
    assert '📚 Mini Lesson' in result
    
    # Test error handling
    result = ui.show_tone_selector('invalid_id', {})
    assert '⚠️' in result

def test_show_cross_reference_editor(sample_strategy):
    """Test cross-reference editor interface."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_cross_reference_editor(sample_strategy)
    
    # Check content
    assert '🔗 Cross-Reference Editor' in result
    assert 'file1 → file2' in result
    assert 'continuation' in result
    
    # Check reference types
    assert 'continuation - Sequential story flow' in result
    assert 'related - Similar themes or concepts' in result
    assert 'technical - Technical dependencies' in result
    assert 'contrast - Different perspectives' in result
    
    # Check instructions
    assert 'add source_id target_id type' in result
    assert 'remove #' in result
    assert 'done' in result
    
    # Test error handling
    result = ui.show_cross_reference_editor({})
    assert '⚠️' in result

def test_show_custom_post_creator(sample_strategy):
    """Test custom post creator interface."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_custom_post_creator(sample_strategy)
    
    # Check content
    assert '➕ Custom Post Creator' in result
    assert 'test3.md' in result  # Available file
    assert 'file3' in result
    assert 'testing' in result
    
    # Check instructions
    assert 'Enter file ID' in result
    assert 'Choose tone (1-5)' in result
    assert 'Set position' in result
    assert 'cancel' in result
    
    # Test error handling
    result = ui.show_custom_post_creator({})
    assert '⚠️' in result

def test_show_confirmation_prompt(sample_strategy):
    """Test confirmation prompt interface."""
    ui = StrategyCustomizationUI()
    
    result = ui.show_confirmation_prompt(sample_strategy)
    
    # Check content
    assert '✅ Confirm Strategy' in result
    assert 'test1.md' in result
    assert 'test2.md' in result
    assert 'planning' in result
    assert 'implementation' in result
    assert 'behind-the-build' in result
    assert 'technical-deep-dive' in result
    
    # Check stats
    assert 'Cross-References: 1' in result
    assert 'Custom Posts: 0' in result
    
    # Check options
    assert 'confirm' in result
    assert 'edit' in result
    assert 'cancel' in result
    
    # Test error handling
    result = ui.show_confirmation_prompt({})
    assert '⚠️' in result 