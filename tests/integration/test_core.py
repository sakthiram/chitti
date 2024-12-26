"""Integration tests for Chitti core functionality"""

import pytest
from chitti.services import ChittiService
from chitti.manager import PluginManager
from chitti.hookspecs import ModelProviderSpec, AgentSpec, PromptRequest
from tests.utils import MockProvider

class MockProvider(ModelProviderSpec):
    """Mock provider for testing"""
    
    def __init__(self, name="mock"):
        """Initialize mock provider"""
        self.name = name
        self.models = ["model1", "model2"]
        self.default_model = "model1"
        self.pricing = {
            "model1": {
                "input_cost_per_1k": 0.01,
                "output_cost_per_1k": 0.02
            },
            "model2": {
                "input_cost_per_1k": 0.02,
                "output_cost_per_1k": 0.03
            }
        }
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.name
    
    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "name": self.name,
            "description": "Mock provider for testing",
            "models": self.models,
            "default_model": self.default_model,
            "pricing": self.pricing,
            "capabilities": {
                "streaming": True,
                "function_calling": False,
                "vision": False
            }
        }
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate non-streaming response"""
        model = kwargs.get('model', self.default_model)
        if model and model not in self.models:
            raise ValueError(f"Model {model} not found")
        return f"Mock response from {self.name} using {model}: {prompt}"
        
    async def generate_stream(self, prompt: str, **kwargs):
        """Generate streaming response"""
        model = kwargs.get('model', self.default_model)
        if model and model not in self.models:
            raise ValueError(f"Model {model} not found")
        yield f"Mock response from {self.name} using {model}: {prompt}"

class MockAgent(AgentSpec):
    """Mock agent for testing"""
    
    def __init__(self, name="mock_agent"):
        """Initialize mock agent"""
        self.name = name
    
    def get_agent_name(self) -> str:
        """Get agent name"""
        return self.name
    
    def get_agent_info(self) -> dict:
        """Get agent information"""
        return {
            "name": self.name,
            "description": "Mock agent for testing",
            "version": "0.1.0",
            "capabilities": {
                "command_execution": True,
                "streaming": False
            }
        }

@pytest.fixture
def service():
    """Create a fresh service instance for each test"""
    service = ChittiService()
    service._manager = PluginManager()  # Reset manager
    return service

def test_plugin_loading(service):
    """Test loading and registering plugins"""
    # Register providers
    provider1 = MockProvider("provider1")
    provider2 = MockProvider("provider2")
    service._manager.register_provider(provider1)
    service._manager.register_provider(provider2)
    
    # Register agents
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    service._manager.register_agent(agent1)
    service._manager.register_agent(agent2)
    
    # Verify providers are loaded
    providers = service.list_providers()
    assert len(providers) == 2
    assert "provider1" in providers
    assert "provider2" in providers
    
    # Verify agents are loaded
    agents = service.list_agents()
    assert len(agents) == 2
    assert "agent1" in agents
    assert "agent2" in agents

@pytest.mark.asyncio
async def test_provider_switching(service):
    """Test switching between providers"""
    # Register providers
    provider1 = MockProvider("provider1")
    provider2 = MockProvider("provider2")
    service._manager.register_provider(provider1)
    service._manager.register_provider(provider2)

    # Test with first provider
    response = await service.process_prompt(
        PromptRequest(
            prompt="Test prompt",
            provider="provider1"
        )
    )
    assert "Mock response" in response.response

    # Test with second provider
    response = await service.process_prompt(
        PromptRequest(
            prompt="Test prompt",
            provider="provider2"
        )
    )
    assert "Mock response" in response.response

@pytest.mark.asyncio
async def test_model_switching(service):
    """Test switching between models"""
    provider = MockProvider("test_provider")
    service._manager.register_provider(provider)

    # Test with first model
    response = await service.process_prompt(
        PromptRequest(
            prompt="Test prompt",
            provider="test_provider",
            model="model1"
        )
    )
    assert response.metadata["model"] == "model1"

    # Test with second model
    response = await service.process_prompt(
        PromptRequest(
            prompt="Test prompt",
            provider="test_provider",
            model="model2"
        )
    )
    assert response.metadata["model"] == "model2"

@pytest.mark.asyncio
async def test_default_settings(service):
    """Test default provider and model settings"""
    # Register providers
    provider1 = MockProvider("provider1")
    provider2 = MockProvider("provider2")
    service._manager.register_provider(provider1)
    service._manager.register_provider(provider2)

    # Set defaults
    service.set_default_provider("provider2")
    service.set_default_model("provider2", "model2")

    # Verify defaults
    settings = service.get_default_settings()
    assert settings["provider"] == "provider2"
    assert settings["model"] == "model2"

    # Test prompt with defaults
    response = await service.process_prompt(
        PromptRequest(
            prompt="Test prompt"
        )
    )
    assert "Mock response" in response.response

def test_provider_info(service):
    """Test getting provider information"""
    provider = MockProvider("test_provider")
    service._manager.register_provider(provider)
    
    info = service.get_provider_info("test_provider")
    assert info["name"] == "test_provider"
    assert info["models"] == ["model1", "model2"]
    assert info["default_model"] == "model1"
    assert "pricing" in info

def test_agent_info(service):
    """Test getting agent information"""
    agent = MockAgent("test_agent")
    service._manager.register_agent(agent)
    
    info = service.get_agent_info("test_agent")
    assert info["name"] == "test_agent"
    assert info["version"] == "0.1.0"
    assert "capabilities" in info

@pytest.mark.asyncio
async def test_error_handling(service):
    """Test error handling for invalid operations"""
    provider = MockProvider("test_provider")
    service._manager.register_provider(provider)

    # Test invalid provider
    with pytest.raises(ValueError):
        await service.process_prompt(
            PromptRequest(
                prompt="Test prompt",
                provider="invalid_provider"
            )
        )

    # Test invalid model
    with pytest.raises(ValueError):
        await service.process_prompt(
            PromptRequest(
                prompt="Test prompt",
                model="invalid_model"
            )
        )

def test_service_singleton(service):
    """Test that ChittiService maintains singleton state"""
    # Create multiple service instances
    service1 = ChittiService()
    service2 = ChittiService()
    
    # Register provider on first instance
    provider = MockProvider("test_provider")
    service1._manager.register_provider(provider)
    
    # Verify provider is available on second instance
    assert "test_provider" in service2.list_providers()
    
    # Set default on first instance
    service1.set_default_provider("test_provider")
    
    # Verify default is set on second instance
    settings = service2.get_default_settings()
    assert settings["provider"] == "test_provider" 