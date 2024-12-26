"""Unit tests for Bedrock provider"""

import pytest
import json
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from chitti.providers.bedrock.provider import BedrockProvider

@pytest.fixture
def provider():
    """Create a Bedrock provider instance"""
    with patch('boto3.Session') as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        provider = BedrockProvider()
        provider.bedrock = mock_client
        return provider

def test_get_provider_name(provider):
    """Test get_provider_name method"""
    assert provider.get_provider_name() == "bedrock"

def test_get_model_info(provider):
    """Test get_model_info method"""
    info = provider.get_model_info()
    assert info["name"] == "bedrock"
    assert isinstance(info["models"], list)
    assert isinstance(info["pricing"], dict)
    assert "default_model" in info
    assert "capabilities" in info

def test_get_request_body(provider):
    """Test _get_request_body method"""
    body = provider._get_request_body("test prompt")
    assert body["anthropic_version"] == "bedrock-2023-05-31"
    assert body["messages"][0]["content"] == "test prompt"
    assert body["max_tokens"] == 8192

    # Test with custom max_tokens
    body = provider._get_request_body("test prompt", max_tokens=100)
    assert body["max_tokens"] == 100

@pytest.mark.asyncio
async def test_generate_success(provider):
    """Test successful non-streaming generation"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Hello'}
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': ' world'}
                    }).encode()
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    response = await provider.generate("test prompt")
    assert response == "Hello world"

@pytest.mark.asyncio
async def test_generate_stream_success(provider):
    """Test successful streaming generation"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Hello'}
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': ' world'}
                    }).encode()
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    chunks = []
    async for chunk in provider.generate_stream("test prompt"):
        chunks.append(chunk)
    assert chunks == ["Hello", " world"]

@pytest.mark.asyncio
async def test_generate_invalid_model(provider):
    """Test generation with invalid model"""
    with pytest.raises(ValueError, match="Unsupported model"):
        await provider.generate("test prompt", model="invalid")

@pytest.mark.asyncio
async def test_generate_stream_invalid_model(provider):
    """Test streaming with invalid model"""
    with pytest.raises(ValueError, match="Unsupported model"):
        async for _ in provider.generate_stream("test prompt", model="invalid"):
            pass

@pytest.mark.asyncio
async def test_generate_throttling(provider):
    """Test throttling and fallback behavior for non-streaming"""
    def mock_invoke(*args, **kwargs):
        if kwargs.get('modelId') == provider.get_model_info()["default_model"]:
            raise Exception("ThrottlingException")
        return {
            'body': [
                {
                    'chunk': {
                        'bytes': json.dumps({
                            'type': 'content_block_delta',
                            'delta': {'type': 'text_delta', 'text': 'Fallback response'}
                        }).encode()
                    }
                }
            ]
        }

    provider.bedrock.invoke_model_with_response_stream.side_effect = mock_invoke
    response = await provider.generate("test prompt")
    assert response == "Fallback response"

@pytest.mark.asyncio
async def test_generate_stream_throttling(provider):
    """Test throttling and fallback behavior for streaming"""
    def mock_invoke(*args, **kwargs):
        if kwargs.get('modelId') == provider.get_model_info()["default_model"]:
            raise Exception("ThrottlingException")
        return {
            'body': [
                {
                    'chunk': {
                        'bytes': json.dumps({
                            'type': 'content_block_delta',
                            'delta': {'type': 'text_delta', 'text': 'Fallback response'}
                        }).encode()
                    }
                }
            ]
        }

    provider.bedrock.invoke_model_with_response_stream.side_effect = mock_invoke
    chunks = []
    async for chunk in provider.generate_stream("test prompt"):
        chunks.append(chunk)
    assert chunks == ["Fallback response"]

@pytest.mark.asyncio
async def test_generate_all_models_throttled(provider):
    """Test when all models are throttled for non-streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        Exception("ThrottlingException")
    
    with pytest.raises(ValueError, match="All models are throttled"):
        await provider.generate("test prompt")

@pytest.mark.asyncio
async def test_generate_stream_all_models_throttled(provider):
    """Test when all models are throttled for streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        Exception("ThrottlingException")
    
    with pytest.raises(ValueError, match="All models are throttled"):
        async for _ in provider.generate_stream("test prompt"):
            pass

@pytest.mark.asyncio
async def test_generate_expired_token(provider):
    """Test expired token error handling for non-streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        ValueError("ExpiredTokenException")
    
    with pytest.raises(ValueError, match="AWS Session Token has expired"):
        await provider.generate("test prompt")

@pytest.mark.asyncio
async def test_generate_stream_expired_token(provider):
    """Test expired token error handling for streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        ValueError("ExpiredTokenException")
    
    with pytest.raises(ValueError, match="AWS Session Token has expired"):
        async for _ in provider.generate_stream("test prompt"):
            pass

@pytest.mark.asyncio
async def test_generate_invalid_response(provider):
    """Test invalid response handling for non-streaming"""
    provider.bedrock.invoke_model_with_response_stream.return_value = {}
    
    with pytest.raises(ValueError, match="Invalid response from Bedrock"):
        await provider.generate("test prompt")

@pytest.mark.asyncio
async def test_generate_stream_invalid_response(provider):
    """Test invalid response handling for streaming"""
    provider.bedrock.invoke_model_with_response_stream.return_value = {}
    
    with pytest.raises(ValueError, match="Invalid response from Bedrock"):
        async for _ in provider.generate_stream("test prompt"):
            pass

@pytest.mark.asyncio
async def test_generate_malformed_chunk(provider):
    """Test handling of malformed response chunks for non-streaming"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': b'invalid json'
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Valid chunk'}
                    }).encode()
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    response = await provider.generate("test prompt")
    assert response == "Valid chunk"

@pytest.mark.asyncio
async def test_generate_stream_malformed_chunk(provider):
    """Test handling of malformed response chunks for streaming"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': b'invalid json'
                }
            },
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Valid chunk'}
                    }).encode()
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    chunks = []
    async for chunk in provider.generate_stream("test prompt"):
        chunks.append(chunk)
    assert chunks == ["Valid chunk"]

@pytest.mark.asyncio
async def test_generate_streaming_error(provider):
    """Test handling of streaming errors for non-streaming"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Hello'}
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': b'invalid json'
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    response = await provider.generate("test prompt")
    assert response == "Hello"

@pytest.mark.asyncio
async def test_generate_stream_error(provider):
    """Test handling of streaming errors for streaming"""
    mock_response = {
        'body': [
            {
                'chunk': {
                    'bytes': json.dumps({
                        'type': 'content_block_delta',
                        'delta': {'type': 'text_delta', 'text': 'Hello'}
                    }).encode()
                }
            },
            {
                'chunk': {
                    'bytes': b'invalid json'
                }
            }
        ]
    }
    provider.bedrock.invoke_model_with_response_stream.return_value = mock_response
    
    chunks = []
    async for chunk in provider.generate_stream("test prompt"):
        chunks.append(chunk)
    assert chunks == ["Hello"]

@pytest.mark.asyncio
async def test_generate_general_error(provider):
    """Test handling of general errors for non-streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        Exception("General error")

    with pytest.raises(Exception, match="General error"):
        await provider.generate("test prompt")

@pytest.mark.asyncio
async def test_generate_stream_general_error(provider):
    """Test handling of general errors for streaming"""
    provider.bedrock.invoke_model_with_response_stream.side_effect = \
        Exception("General error")

    with pytest.raises(Exception, match="General error"):
        async for _ in provider.generate_stream("test prompt"):
            pass 