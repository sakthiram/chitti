"""Tests for service layer"""

import pytest
from chitti.services import ChittiService
from chitti.hookspecs import ModelProviderSpec, AgentSpec, PromptRequest
from tests.utils import MockProvider

class MockAgent(AgentSpec):
    """Mock agent for testing"""
    
    def get_agent_name(self):
        return "mock_agent"
        
    def get_agent_info(self):
        return {
            "name": "mock_agent",
            "description": "Mock agent",
            "version": "0.1.0"
        }

class BrokenProvider(ModelProviderSpec):
    """Provider that raises errors"""
    
    def get_provider_name(self):
        raise RuntimeError("Provider error")

class BrokenAgent(AgentSpec):
    """Agent that raises errors"""
    
    def get_agent_name(self):
        raise RuntimeError("Agent error")

@pytest.fixture
def service():
    """Create service instance"""
    return ChittiService()

@pytest.mark.asyncio
async def test_process_prompt(service):
    """Test prompt processing"""
    provider = MockProvider()
    service._manager.register_provider(provider)
    
    # Test with default provider/model
    response = await service.process_prompt(PromptRequest(prompt="test"))
    assert "Mock response" in response.response
    assert response.metadata["provider"] == "mock"
    assert response.metadata["model"] == provider.get_model_info()["default_model"]
    
    # Test with specified provider/model
    response = await service.process_prompt(
        PromptRequest(prompt="test", provider="mock", model="model2")
    )
    assert "Mock response" in response.response
    assert response.metadata["provider"] == "mock"
    assert response.metadata["model"] == "model2"

@pytest.mark.asyncio
async def test_process_prompt_streaming(service):
    """Test prompt processing with streaming"""
    service._manager.register_provider(MockProvider())
    
    # Test with streaming
    chunks = []
    async for chunk in await service.process_prompt(
        PromptRequest(prompt="test"),
        stream=True
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
    assert "Mock response" in chunks[0]

def test_set_default_provider(service):
    """Test setting default provider"""
    provider = MockProvider()
    service._manager.register_provider(provider)
    service.set_default_provider("mock")
    
    assert service._manager.get_default_provider() == provider

def test_set_default_model(service):
    """Test setting default model"""
    service._manager.register_provider(MockProvider())
    service.set_default_model("mock", "model2")
    
    assert service._manager.get_default_model("mock") == "model2"

def test_get_provider_info(service):
    """Test getting provider info"""
    service._manager.register_provider(MockProvider())
    info = service.get_provider_info("mock")
    
    assert info["name"] == "mock"
    assert "models" in info
    assert "default_model" in info

def test_get_default_settings(service):
    """Test getting default settings"""
    provider = MockProvider()
    service._manager.register_provider(provider)
    service._manager.set_default_provider("mock")
    
    settings = service.get_default_settings()
    assert settings["provider"] == "mock"
    assert settings["model"] == provider.get_model_info()["default_model"]

def test_invalid_provider(service):
    """Test handling invalid provider"""
    with pytest.raises(ValueError):
        service.get_provider_info("nonexistent")

def test_invalid_model(service):
    """Test handling invalid model"""
    service._manager.register_provider(MockProvider())
    with pytest.raises(ValueError):
        service.set_default_model("mock", "nonexistent")

def test_plugin_loading_error(service, monkeypatch):
    """Test handling plugin loading errors"""
    def mock_iter_entry_points(group):
        class MockEntryPoint:
            name = "broken"
            def load(self):
                raise ImportError("Failed to load")
        return [MockEntryPoint()]
    
    monkeypatch.setattr("pkg_resources.iter_entry_points", mock_iter_entry_points)
    
    # Should not raise exception
    service._load_plugins()

def test_plugin_loading_validation(service):
    """Test validation during plugin loading"""
    # Test loading invalid provider
    with pytest.raises(TypeError):
        service._manager.register_provider(object())
    
    # Test loading broken provider
    with pytest.raises(RuntimeError):
        service._manager.register_provider(BrokenProvider())
    
    # Test loading broken agent
    with pytest.raises(RuntimeError):
        service._manager.register_agent(BrokenAgent())

@pytest.mark.asyncio
async def test_process_prompt_error_handling(service):
    """Test error handling in prompt processing"""
    class ErrorProvider(MockProvider):
        async def generate(self, prompt, **kwargs):
            raise RuntimeError("Generation error")
    
    service._manager.register_provider(ErrorProvider())
    with pytest.raises(RuntimeError):
        await service.process_prompt(PromptRequest(prompt="test"))

def test_set_default_provider_validation(service):
    """Test validation in set_default_provider"""
    with pytest.raises(ValueError):
        service.set_default_provider("nonexistent")

def test_set_default_model_validation(service):
    """Test validation in set_default_model"""
    with pytest.raises(ValueError):
        service.set_default_model("nonexistent", "model1") 