"""Tests for hook specifications"""

import pytest
from fastapi import APIRouter
import click
from chitti.hookspecs import (
    ModelProviderSpec, AgentSpec, ToolSpec,
    PromptRequest, PromptResponse, ProviderManager
)

class TestModelProviderSpec:
    """Test model provider specification"""
    
    def test_provider_interface(self):
        """Test provider interface methods"""
        provider = ModelProviderSpec()
        
        # Test base methods return None
        assert provider.generate("test") is None
        assert provider.get_model_info() is None
        assert provider.get_provider_name() is None

class TestAgentSpec:
    """Test agent specification"""
    
    def test_agent_interface(self):
        """Test agent interface methods"""
        agent = AgentSpec()
        
        # Test base methods return None
        assert agent.get_router() is None
        assert agent.get_agent_info() is None
        assert agent.get_commands() is None
        assert agent.get_agent_name() is None

class TestToolSpec:
    """Test tool specification"""
    
    def test_tool_interface(self):
        """Test tool interface methods"""
        tool = ToolSpec()
        
        # Test base methods return None
        assert tool.execute("test") is None
        assert tool.get_tool_info() is None

class TestProviderManager:
    """Test provider manager"""
    
    class MockProvider:
        def get_provider_name(self):
            return "mock"
            
        def get_model_info(self):
            return {
                "models": ["model1", "model2"],
                "default_model": "model1"
            }
    
    @pytest.fixture
    def manager(self):
        return ProviderManager()
    
    @pytest.fixture
    def provider(self):
        return self.MockProvider()
    
    def test_register_provider(self, manager, provider):
        """Test provider registration"""
        manager.register_provider(provider)
        assert "mock" in manager._providers
        assert manager._default_models["mock"] == "model1"
    
    def test_set_default_provider(self, manager, provider):
        """Test setting default provider"""
        manager.register_provider(provider)
        manager.set_default_provider("mock")
        assert manager._default_provider == "mock"
        
        with pytest.raises(ValueError):
            manager.set_default_provider("nonexistent")
    
    def test_set_default_model(self, manager, provider):
        """Test setting default model"""
        manager.register_provider(provider)
        manager.set_default_model("mock", "model2")
        assert manager._default_models["mock"] == "model2"
        
        with pytest.raises(ValueError):
            manager.set_default_model("mock", "nonexistent")
        with pytest.raises(ValueError):
            manager.set_default_model("nonexistent", "model1")
    
    def test_get_provider(self, manager, provider):
        """Test getting provider"""
        manager.register_provider(provider)
        assert manager.get_provider("mock") == provider
        assert manager.get_provider() == provider  # Default provider
        
        with pytest.raises(ValueError):
            manager.get_provider("nonexistent")
    
    def test_get_default_model(self, manager, provider):
        """Test getting default model"""
        manager.register_provider(provider)
        assert manager.get_default_model("mock") == "model1"
        assert manager.get_default_model() == "model1"  # Default provider

def test_prompt_request():
    """Test prompt request model"""
    request = PromptRequest(prompt="test")
    assert request.prompt == "test"
    assert request.model is None
    assert request.provider is None
    assert request.tools == []
    
    request = PromptRequest(
        prompt="test",
        model="model1",
        provider="provider1",
        tools=["tool1", "tool2"]
    )
    assert request.prompt == "test"
    assert request.model == "model1"
    assert request.provider == "provider1"
    assert request.tools == ["tool1", "tool2"]

def test_prompt_response():
    """Test prompt response model"""
    response = PromptResponse(response="test")
    assert response.response == "test"
    assert response.metadata == {}
    
    response = PromptResponse(
        response="test",
        metadata={"key": "value"}
    )
    assert response.response == "test"
    assert response.metadata == {"key": "value"} 