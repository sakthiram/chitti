"""Unit tests for plugin manager"""

import pytest
import pluggy
from chitti.manager import PluginManager
from chitti.hookspecs import ModelProviderSpec, AgentSpec

hookimpl = pluggy.HookimplMarker("chitti")

class MockProvider:
    """Mock provider for testing"""
    
    def __init__(self, name="mock", models=None):
        self.name = name
        self.models = models or ["model1", "model2"]
        self.default_model = self.models[0]
    
    @hookimpl
    def get_provider_name(self) -> str:
        return self.name
    
    @hookimpl    
    def get_model_info(self):
        return {
            "name": self.name,
            "description": "Mock provider for testing",
            "models": self.models,
            "default_model": self.default_model,
            "capabilities": {
                "streaming": False,
                "function_calling": False,
                "vision": False
            },
            "pricing": {
                model: {"input_cost_per_1k": 0.001, "output_cost_per_1k": 0.002}
                for model in self.models
            }
        }
    
    @hookimpl    
    def generate(self, prompt: str, **kwargs):
        model = kwargs.get('model', self.default_model)
        if model not in self.models:
            raise ValueError(f"Unsupported model: {model}")
        return f"Response from {model}: {prompt}"

class MockAgent:
    """Mock agent for testing"""
    
    def __init__(self, name="mock_agent"):
        self.name = name
    
    @hookimpl
    def get_agent_name(self) -> str:
        return self.name
    
    @hookimpl
    def get_agent_info(self):
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
def manager():
    """Create a plugin manager instance"""
    manager = PluginManager()
    # Clear any existing plugins
    manager._providers.clear()
    manager._agents.clear()
    manager._default_models.clear()
    return manager

def test_register_provider(manager):
    """Test provider registration"""
    provider = MockProvider()
    manager.register_provider(provider)
    
    assert provider.name in manager._providers
    assert manager._providers[provider.name] == provider

def test_register_agent(manager):
    """Test agent registration"""
    agent = MockAgent()
    manager.register_agent(agent)
    
    assert agent.name in manager._agents
    assert manager._agents[agent.name] == agent

def test_get_provider(manager):
    """Test getting provider"""
    provider = MockProvider()
    manager.register_provider(provider)
    
    assert manager.get_provider(provider.name) == provider
    
    with pytest.raises(ValueError, match="Provider invalid not found"):
        manager.get_provider("invalid")

def test_get_agent(manager):
    """Test getting agent"""
    agent = MockAgent()
    manager.register_agent(agent)
    
    assert manager.get_agent(agent.name) == agent
    
    with pytest.raises(ValueError, match="Agent invalid not found"):
        manager.get_agent("invalid")

def test_get_default_provider(manager):
    """Test getting default provider"""
    provider = MockProvider()
    manager.register_provider(provider)
    manager.set_default_provider(provider.name)
    
    assert manager.get_default_provider() == provider
    
    # Test when no default provider is set
    manager._default_provider = None
    with pytest.raises(ValueError, match="No default provider set"):
        manager.get_default_provider()

def test_get_default_model(manager):
    """Test getting default model"""
    provider = MockProvider()
    manager.register_provider(provider)
    
    # Test with provider's default model
    assert manager.get_default_model(provider.name) == provider.default_model
    
    # Test with custom default model
    custom_model = "model2"
    manager.set_default_model(provider.name, custom_model)
    assert manager.get_default_model(provider.name) == custom_model
    
    # Test with invalid model
    with pytest.raises(ValueError, match="Model invalid not found"):
        manager.set_default_model(provider.name, "invalid")

def test_list_providers(manager):
    """Test listing providers"""
    provider1 = MockProvider("provider1")
    provider2 = MockProvider("provider2")
    
    manager.register_provider(provider1)
    manager.register_provider(provider2)
    
    providers = manager.list_providers()
    assert len(providers) == 2
    assert "provider1" in providers
    assert "provider2" in providers

def test_list_agents(manager):
    """Test listing agents"""
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    
    manager.register_agent(agent1)
    manager.register_agent(agent2)
    
    agents = manager.list_agents()
    assert len(agents) == 2
    assert "agent1" in agents
    assert "agent2" in agents

def test_get_provider_info(manager):
    """Test getting provider information"""
    provider = MockProvider()
    manager.register_provider(provider)
    
    info = manager.get_provider_info(provider.name)
    assert info["name"] == provider.name
    assert "models" in info
    assert "pricing" in info

def test_get_agent_info(manager):
    """Test getting agent information"""
    agent = MockAgent()
    manager.register_agent(agent)
    
    info = manager.get_agent_info(agent.name)
    assert info["name"] == agent.name
    assert "description" in info
    assert "version" in info
    assert "capabilities" in info

def test_generate(manager):
    """Test generating response"""
    provider = MockProvider()
    manager.register_provider(provider)
    
    response = manager.generate("Test prompt", provider=provider.name)
    assert response == "Response from model1: Test prompt"
    
    # Test with specific model
    response = manager.generate(
        "Test prompt",
        provider=provider.name,
        model="model2"
    )
    assert response == "Response from model2: Test prompt"
    
    # Test with invalid model
    with pytest.raises(ValueError, match="Unsupported model: invalid"):
        manager.generate(
            "Test prompt",
            provider=provider.name,
            model="invalid"
        ) 