"""
Tests for the AI Content Service.
"""

import pytest
from unittest.mock import Mock, patch
from implemented.ai_service import AIContentService

@pytest.fixture
def ai_service():
    """Create an AI service instance with mock API key."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        return AIContentService()

@pytest.fixture
def mock_openai():
    """Create a mock OpenAI response."""
    class MockResponse:
        class Usage:
            def __init__(self):
                self.total_tokens = 150
                
        class Choice:
            def __init__(self):
                self.message = Mock(content="Generated content")
                self.finish_reason = "stop"
                
        def __init__(self):
            self.choices = [self.Choice()]
            self.usage = self.Usage()
            
    return MockResponse()

@pytest.mark.asyncio
async def test_generate_content(ai_service, mock_openai):
    """Test content generation with mock OpenAI response."""
    with patch('openai.ChatCompletion.acreate', return_value=mock_openai):
        result = await ai_service.generate_content(
            "Test prompt",
            context={'system_message': 'Test system message'}
        )
        
        assert isinstance(result, dict)
        assert 'content' in result
        assert 'metadata' in result
        assert result['content'] == "Generated content"
        assert result['metadata']['tokens_used'] == 150
        assert result['metadata']['finish_reason'] == "stop"

@pytest.mark.asyncio
async def test_generate_content_with_context(ai_service, mock_openai):
    """Test content generation with full context."""
    context = {
        'system_message': 'Test system message',
        'examples': [
            {
                'input': 'Test input',
                'output': 'Test output'
            }
        ]
    }
    
    with patch('openai.ChatCompletion.acreate', return_value=mock_openai):
        result = await ai_service.generate_content(
            "Test prompt",
            context=context
        )
        
        assert isinstance(result, dict)
        assert 'content' in result
        assert result['content'] == "Generated content"

def test_build_messages(ai_service):
    """Test message building for API call."""
    prompt = "Test prompt"
    context = {
        'system_message': 'Test system message',
        'examples': [
            {
                'input': 'Test input',
                'output': 'Test output'
            }
        ]
    }
    
    messages = ai_service._build_messages(prompt, context)
    
    assert len(messages) == 4  # system + 2 example messages + prompt
    assert messages[0]['role'] == 'system'
    assert messages[0]['content'] == 'Test system message'
    assert messages[-1]['role'] == 'user'
    assert messages[-1]['content'] == prompt

def test_validate_response(ai_service):
    """Test response validation."""
    valid_response = {
        'choices': [
            {
                'message': {
                    'content': 'Test content'
                }
            }
        ],
        'usage': {
            'total_tokens': 100
        }
    }
    
    invalid_response = {
        'choices': []
    }
    
    assert ai_service._validate_response(valid_response) is True
    assert ai_service._validate_response(invalid_response) is False

@pytest.mark.asyncio
async def test_error_handling(ai_service):
    """Test error handling in content generation."""
    with patch('openai.ChatCompletion.acreate', side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await ai_service.generate_content("Test prompt")
        assert "API Error" in str(exc_info.value)

def test_initialization_without_api_key():
    """Test service initialization without API key."""
    with patch.dict('os.environ', clear=True):
        with pytest.raises(ValueError) as exc_info:
            AIContentService()
        assert "API key must be provided" in str(exc_info.value)

@pytest.mark.asyncio
async def test_custom_parameters(ai_service, mock_openai):
    """Test content generation with custom parameters."""
    custom_params = {
        'model': 'gpt-3.5-turbo',
        'temperature': 0.9,
        'max_tokens': 500
    }
    
    with patch('openai.ChatCompletion.acreate', return_value=mock_openai) as mock_create:
        await ai_service.generate_content(
            "Test prompt",
            context={},
            **custom_params
        )
        
        call_args = mock_create.call_args[1]
        assert call_args['model'] == custom_params['model']
        assert call_args['temperature'] == custom_params['temperature']
        assert call_args['max_tokens'] == custom_params['max_tokens'] 