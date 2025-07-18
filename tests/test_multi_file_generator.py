"""
Test suite for MultiFileContentGenerator class.
"""

import pytest
from unittest.mock import Mock, patch
from implemented.multi_file_generator import MultiFileContentGenerator
from implemented.ai_service import AIContentService

@pytest.fixture
def mock_ai_service():
    """Create a mock AI service."""
    service = Mock(spec=AIContentService)
    service.generate_content.return_value = {
        'content': 'Generated test content',
        'metadata': {
            'model': 'gpt-4',
            'temperature': 0.7,
            'tokens_used': 150
        }
    }
    return service

@pytest.fixture
def generator(mock_ai_service):
    """Create a MultiFileContentGenerator instance for testing."""
    return MultiFileContentGenerator(ai_service=mock_ai_service)

@pytest.fixture
def sample_files():
    """Create sample files for testing."""
    return [
        {
            'file_id': 'file1',
            'file_phase': 'planning',
            'key_themes': ['architecture', 'scalability'],
            'technical_elements': ['python', 'aws'],
            'business_impact': ['efficiency', 'cost-reduction'],
            'position': 0
        },
        {
            'file_id': 'file2',
            'file_phase': 'implementation',
            'key_themes': ['scalability', 'security'],
            'technical_elements': ['python', 'docker'],
            'business_impact': ['efficiency', 'reliability'],
            'position': 1
        },
        {
            'file_id': 'file3',
            'file_phase': 'debugging',
            'key_themes': ['security', 'performance'],
            'technical_elements': ['docker', 'kubernetes'],
            'business_impact': ['reliability', 'maintainability'],
            'position': 2
        }
    ]

@pytest.fixture
def sample_strategy():
    """Create a sample content strategy for testing."""
    return {
        'project_theme': 'Cloud Infrastructure Modernization',
        'narrative_arc': 'From Legacy to Modern Architecture',
        'content_threads': [
            {
                'themes': ['scalability', 'performance'],
                'description': 'Evolution of system architecture'
            },
            {
                'themes': ['security', 'reliability'],
                'description': 'Ensuring robust operations'
            }
        ],
        'recommended_sequence': [
            {'tone': 'technical'},
            {'tone': 'explanatory'},
            {'tone': 'achievement'}
        ]
    }

def test_build_multi_file_prompt(generator, sample_files, sample_strategy):
    """Test prompt building with multi-file context."""
    target_file = sample_files[1]  # Use implementation phase file
    prompt = generator.build_multi_file_prompt(
        target_file,
        sample_files,
        sample_strategy,
        1
    )
    
    # Check prompt contains key elements
    assert sample_strategy['project_theme'] in prompt
    assert sample_strategy['narrative_arc'] in prompt
    assert target_file['file_phase'] in prompt
    assert 'Content Guidelines' in prompt
    assert 'Content Structure' in prompt

def test_generate_explicit_references(generator, sample_files):
    """Test generation of explicit references between posts."""
    current_file = sample_files[2]  # debugging phase
    previous_posts = sample_files[:2]  # planning and implementation
    
    references = generator.generate_explicit_references(current_file, previous_posts)
    
    assert len(references) > 0
    assert all(isinstance(ref, dict) for ref in references)
    assert all('reference_text' in ref for ref in references)
    assert all('connection_type' in ref for ref in references)

def test_generate_subtle_connections(generator, sample_files):
    """Test generation of subtle thematic connections."""
    current_file = sample_files[1]  # implementation phase
    
    connections = generator.generate_subtle_connections(current_file, sample_files)
    
    assert len(connections) > 0
    assert all(isinstance(conn, dict) for conn in connections)
    assert all('connection_text' in conn for conn in connections)
    assert all('type' in conn for conn in connections)
    assert len(connections) <= 5  # Check limit is enforced

def test_ensure_narrative_continuity(generator, sample_files):
    """Test narrative continuity maintenance."""
    previous_posts = sample_files[:2]  # planning and implementation
    current_content = "We implemented the new security features."
    
    modified_content = generator.ensure_narrative_continuity(
        previous_posts,
        current_content
    )
    
    assert modified_content != current_content
    assert modified_content[0].isupper()  # Check capitalization
    assert len(modified_content) > len(current_content)  # Should add transition

@pytest.mark.asyncio
async def test_generate_with_multi_file_context(generator, sample_files, sample_strategy):
    """Test complete generation process."""
    target_file = sample_files[1]  # implementation phase
    
    result = await generator.generate_with_multi_file_context(
        target_file,
        sample_files,
        sample_strategy,
        1
    )
    
    assert isinstance(result, dict)
    assert 'content' in result
    assert 'references' in result
    assert 'connections' in result
    assert 'metadata' in result
    assert result['metadata']['narrative_position'] == 1
    
    # Verify AI service was called
    generator.ai_service.generate_content.assert_called_once()
    call_args = generator.ai_service.generate_content.call_args
    assert isinstance(call_args[0][0], str)  # First positional arg should be prompt string
    assert len(call_args[0][0]) > 0  # Prompt should not be empty

def test_empty_previous_posts(generator):
    """Test handling of no previous posts."""
    content = "This is the first post."
    modified = generator.ensure_narrative_continuity([], content)
    assert modified == content

def test_theme_connection_generation(generator):
    """Test theme-based connection generation."""
    theme = "scalability"
    phase = "implementation"
    connection = generator._create_theme_connection(theme, 2, phase)
    
    assert theme in connection
    assert isinstance(connection, str)
    assert connection[0].isupper()

def test_technical_connection_generation(generator):
    """Test technical connection generation."""
    tech = "docker"
    phase = "debugging"
    connection = generator._create_technical_connection(tech, 2, phase)
    
    assert tech in connection
    assert isinstance(connection, str)
    assert connection[0].isupper()

def test_impact_connection_generation(generator):
    """Test business impact connection generation."""
    impact = "efficiency"
    phase = "results"
    connection = generator._create_impact_connection(impact, 2, phase)
    
    assert impact in connection
    assert isinstance(connection, str)
    assert connection[0].isupper()

def test_get_previous_posts(generator, sample_files):
    """Test previous posts retrieval."""
    current_position = 2
    previous = generator._get_previous_posts(sample_files, current_position)
    
    assert len(previous) == 2
    assert all(p['position'] < current_position for p in previous)

@pytest.mark.asyncio
async def test_error_handling(generator):
    """Test error handling in main generation method."""
    with pytest.raises(Exception):
        await generator.generate_with_multi_file_context(
            None,  # Invalid target file
            [],
            {},
            0
        )

@pytest.mark.asyncio
async def test_generate_ai_content(generator, sample_files):
    """Test AI content generation."""
    prompt = "Test prompt"
    references = [{'reference_text': 'Test reference'}]
    connections = [{'connection_text': 'Test connection'}]
    phase = 'implementation'
    
    content = await generator._generate_ai_content(
        prompt,
        references,
        connections,
        phase
    )
    
    assert content == 'Generated test content'
    generator.ai_service.generate_content.assert_called_once()

def test_build_enhanced_prompt(generator, sample_files):
    """Test enhanced prompt building with references and connections."""
    base_prompt = "Base prompt content"
    references = [
        {'reference_text': 'Reference 1'},
        {'reference_text': 'Reference 2'}
    ]
    connections = [
        {'connection_text': 'Connection 1'},
        {'connection_text': 'Connection 2'}
    ]
    phase = 'implementation'
    
    enhanced_prompt = generator._build_enhanced_prompt(
        base_prompt,
        references,
        connections,
        phase
    )
    
    # Verify prompt sections
    assert base_prompt in enhanced_prompt
    assert 'Explicit References to Include:' in enhanced_prompt
    assert 'Thematic Connections to Weave In:' in enhanced_prompt
    assert 'Phase-Specific Guidance:' in enhanced_prompt
    assert 'Reference 1' in enhanced_prompt
    assert 'Connection 1' in enhanced_prompt
    assert phase in enhanced_prompt

def test_get_system_message(generator):
    """Test system message generation."""
    phase = 'implementation'
    message = generator._get_system_message(phase)
    
    assert phase in message
    assert 'technical developer' in message.lower()
    assert 'facebook' in message.lower()

def test_get_phase_examples(generator):
    """Test phase examples retrieval."""
    phases = ['planning', 'implementation', 'debugging', 'results']
    
    for phase in phases:
        examples = generator._get_phase_examples(phase)
        assert isinstance(examples, list)
        assert len(examples) > 0
        assert all('input' in ex and 'output' in ex for ex in examples)

def test_get_phase_temperature(generator):
    """Test phase temperature settings."""
    phases = ['planning', 'implementation', 'debugging', 'results']
    
    for phase in phases:
        temp = generator._get_phase_temperature(phase)
        assert isinstance(temp, float)
        assert 0 <= temp <= 1

@pytest.mark.asyncio
async def test_ai_content_generation_error_handling(generator):
    """Test error handling in AI content generation."""
    # Mock the AI service to raise an exception
    generator.ai_service.generate_content.side_effect = Exception("AI service error")
    
    with pytest.raises(Exception):
        await generator._generate_ai_content(
            "Test prompt",
            [],
            [],
            "test_phase"
        ) 