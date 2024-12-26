"""Integration tests for server"""

import pytest
from fastapi.testclient import TestClient
import httpx
from chitti.server import app
from chitti.services import ChittiService
from chitti.hookspecs import ModelProviderSpec
from tests.utils import MockProvider

@pytest.fixture
def mock_service():
    """Create mock service"""
    from chitti.services import ChittiService
    service = ChittiService()
    service._manager._providers.clear()
    provider = MockProvider("mock")
    service._manager.register_provider(provider)
    service._manager.set_default_provider("mock")
    service._manager.set_default_model("mock", "model1")
    return service

@pytest.fixture
def client(mock_service):
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def async_client(mock_service):
    """Create async test client"""
    return httpx.AsyncClient(base_url="http://test", transport=httpx.ASGITransport(app=app))

def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["title"] == "Chitti API"

async def test_prompt_endpoint(client):
    """Test prompt endpoint with non-streaming"""
    response = client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": None,
            "provider": None,
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "metadata" in data

@pytest.mark.asyncio
async def test_prompt_endpoint_streaming(async_client):
    """Test prompt endpoint with streaming"""
    response = await async_client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": None,
            "provider": None,
            "stream": True
        }
    )
    assert response.status_code == 200
    chunks = []
    async for line in response.aiter_lines():
        if line:
            chunks.append(line)
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_prompt_endpoint_with_model(client):
    """Test prompt endpoint with specific model"""
    response = client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": "model2",
            "provider": None,
            "stream": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "metadata" in data
    assert data["metadata"]["model"] == "model2"

@pytest.mark.asyncio
async def test_prompt_endpoint_with_model_streaming(async_client):
    """Test prompt endpoint with specific model and streaming"""
    response = await async_client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": "model2",
            "provider": None,
            "stream": True
        }
    )
    assert response.status_code == 200
    chunks = []
    async for line in response.aiter_lines():
        if line:
            chunks.append(line)
    assert len(chunks) > 0

def test_prompt_endpoint_with_invalid_model(client):
    """Test prompt endpoint with invalid model"""
    response = client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": "invalid_model",
            "provider": None,
            "stream": False
        }
    )
    assert response.status_code == 400

def test_prompt_endpoint_with_invalid_provider(client):
    """Test prompt endpoint with invalid provider"""
    response = client.post(
        "/prompt/",
        json={
            "prompt": "Test prompt",
            "model": None,
            "provider": "invalid_provider",
            "stream": False
        }
    )
    assert response.status_code == 400

def test_providers_endpoint(client):
    """Test providers endpoint"""
    response = client.get("/providers/")
    assert response.status_code == 200
    providers = response.json()
    assert len(providers) > 0
    assert "mock" in providers

def test_provider_info_endpoint(client):
    """Test provider info endpoint"""
    response = client.get("/providers/mock")
    assert response.status_code == 200
    info = response.json()
    assert info["name"] == "mock"
    assert info["models"] == ["model1", "model2"]

def test_provider_info_endpoint_invalid(client):
    """Test provider info endpoint with invalid provider"""
    response = client.get("/providers/invalid")
    assert response.status_code == 400

def test_agents_endpoint(client):
    """Test agents endpoint"""
    response = client.get("/agents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_agent_info_endpoint(client):
    """Test agent info endpoint"""
    response = client.get("/agents/")
    assert response.status_code == 200
    agents = response.json()
    if len(agents) > 0:
        agent = agents[0]
        response = client.get(f"/agents/{agent}")
        assert response.status_code == 200
        info = response.json()
        assert "name" in info
        assert "description" in info

def test_agent_info_endpoint_invalid(client):
    """Test agent info endpoint with invalid agent"""
    response = client.get("/agents/invalid")
    assert response.status_code == 400

def test_default_settings_endpoint(client):
    """Test default settings endpoint"""
    response = client.get("/settings/default")
    assert response.status_code == 200
    settings = response.json()
    assert "provider" in settings
    assert "model" in settings

def test_set_default_provider_endpoint(client):
    """Test setting default provider endpoint"""
    response = client.post(
        "/settings/default/provider",
        json={"provider": "mock"}
    )
    assert response.status_code == 200

def test_set_default_model_endpoint(client):
    """Test setting default model endpoint"""
    response = client.post(
        "/settings/default/model",
        json={"provider": "mock", "model": "model2"}
    )
    assert response.status_code == 200 

def test_prompt_endpoint_error_handling(client):
    """Test error handling in prompt endpoint"""
    # Test missing prompt
    response = client.post(
        "/prompt/",
        json={
            "model": "model1",
            "provider": "mock"
        }
    )
    assert response.status_code == 422  # Validation error
    
    # Test empty prompt
    response = client.post(
        "/prompt/",
        json={
            "prompt": "",
            "model": "model1",
            "provider": "mock"
        }
    )
    assert response.status_code == 400
    assert "Empty prompt" in response.json()["detail"]
    
    # Test invalid JSON
    response = client.post(
        "/prompt/",
        data="invalid json"
    )
    assert response.status_code == 422  # JSON validation error

def test_provider_info_endpoint_error_handling(client):
    """Test error handling in provider info endpoint"""
    # Test non-existent provider
    response = client.get("/providers/nonexistent")
    assert response.status_code == 400
    assert "Provider not found" in response.json()["detail"]
    
    # Test invalid provider name format
    response = client.get("/providers/invalid@provider")
    assert response.status_code == 400
    assert "Invalid provider name" in response.json()["detail"]

def test_agent_info_endpoint_error_handling(client):
    """Test error handling in agent info endpoint"""
    # Test non-existent agent
    response = client.get("/agents/nonexistent")
    assert response.status_code == 400
    assert "Agent not found" in response.json()["detail"]
    
    # Test invalid agent name format
    response = client.get("/agents/invalid@agent")
    assert response.status_code == 400
    assert "Invalid agent name" in response.json()["detail"]

def test_set_default_provider_endpoint_error_handling(client):
    """Test error handling in set default provider endpoint"""
    # Test non-existent provider
    response = client.post(
        "/settings/default/provider",
        json={"provider": "nonexistent"}
    )
    assert response.status_code == 400
    assert "Provider not found" in response.json()["detail"]
    
    # Test missing provider field
    response = client.post(
        "/settings/default/provider",
        json={}
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid JSON
    response = client.post(
        "/settings/default/provider",
        data="invalid json"
    )
    assert response.status_code == 422  # JSON validation error

def test_set_default_model_endpoint_error_handling(client):
    """Test error handling in set default model endpoint"""
    # Test non-existent provider
    response = client.post(
        "/settings/default/model",
        json={
            "provider": "nonexistent",
            "model": "model1"
        }
    )
    assert response.status_code == 400
    assert "Provider not found" in response.json()["detail"]
    
    # Test non-existent model
    response = client.post(
        "/settings/default/model",
        json={
            "provider": "mock",
            "model": "nonexistent"
        }
    )
    assert response.status_code == 400
    assert "Model not found" in response.json()["detail"]
    
    # Test missing fields
    response = client.post(
        "/settings/default/model",
        json={}
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid JSON
    response = client.post(
        "/settings/default/model",
        data="invalid json"
    )
    assert response.status_code == 422  # JSON validation error 

def test_validation_error_handling(client):
    """Test validation error handling"""
    # Test invalid field type
    response = client.post(
        "/prompt/",
        json={
            "prompt": 123,  # Should be string
            "model": "model1"
        }
    )
    assert response.status_code == 422
    
    # Test extra fields
    response = client.post(
        "/prompt/",
        json={
            "prompt": "test",
            "model": "model1",
            "extra_field": "value"
        }
    )
    assert response.status_code == 200  # FastAPI ignores extra fields
    
    # Test invalid JSON format
    response = client.post(
        "/prompt/",
        data="{invalid json"
    )
    assert response.status_code == 422

def test_set_default_model_endpoint_error_handling(client):
    """Test error handling in set default model endpoint"""
    # Test non-existent provider
    response = client.post(
        "/settings/default/model",
        json={"provider": "nonexistent", "model": "model1"}
    )
    assert response.status_code == 400
    assert "Provider not found" in response.json()["detail"]
    
    # Test non-existent model
    response = client.post(
        "/settings/default/model",
        json={"provider": "mock", "model": "nonexistent"}
    )
    assert response.status_code == 400
    assert "Model not found" in response.json()["detail"]
    
    # Test invalid provider name format
    response = client.post(
        "/settings/default/model",
        json={"provider": "invalid@provider", "model": "model1"}
    )
    assert response.status_code == 400
    assert "Invalid provider name" in response.json()["detail"]
    
    # Test missing fields
    response = client.post("/settings/default/model", json={})
    assert response.status_code == 422

def test_service_level_exceptions(client, monkeypatch):
    """Test handling of service-level exceptions"""
    def mock_process_prompt(*args, **kwargs):
        raise RuntimeError("Service error")
    
    from chitti.services import ChittiService
    monkeypatch.setattr(ChittiService, "process_prompt", mock_process_prompt)
    
    response = client.post(
        "/prompt/",
        json={"prompt": "test"}
    )
    assert response.status_code == 500
    assert "Service error" in response.json()["detail"]

def test_default_settings_error_handling(client):
    """Test error handling in default settings endpoint"""
    # Clear the service to simulate no providers
    from chitti.services import ChittiService
    service = ChittiService()
    service._manager._providers.clear()
    service._manager._default_provider = None
    
    response = client.get("/settings/default")
    assert response.status_code == 500

def test_list_endpoints_error_handling(client, monkeypatch):
    """Test error handling in list endpoints"""
    def mock_list_providers(self):
        raise RuntimeError("Service error")
    
    def mock_list_agents(self):
        raise RuntimeError("Service error")
    
    # Test providers endpoint error
    monkeypatch.setattr(ChittiService, "list_providers", mock_list_providers)
    response = client.get("/providers/")
    assert response.status_code == 500
    assert "Service error" in response.json()["detail"]
    
    # Test agents endpoint error
    monkeypatch.setattr(ChittiService, "list_agents", mock_list_agents)
    response = client.get("/agents/")
    assert response.status_code == 500
    assert "Service error" in response.json()["detail"]

def test_prompt_validation_comprehensive(client):
    """Test comprehensive prompt validation"""
    # Test whitespace-only prompt
    response = client.post(
        "/prompt/",
        json={"prompt": "   "}
    )
    assert response.status_code == 400
    assert "Empty prompt" in response.json()["detail"]
    
    # Test newline-only prompt
    response = client.post(
        "/prompt/",
        json={"prompt": "\n\n"}
    )
    assert response.status_code == 400
    assert "Empty prompt" in response.json()["detail"]
    
    # Test valid prompt with whitespace
    response = client.post(
        "/prompt/",
        json={"prompt": "  test  "}
    )
    assert response.status_code == 200 

def test_provider_name_validation(client):
    """Test provider name validation"""
    # Test invalid characters
    response = client.get("/providers/invalid@provider")
    assert response.status_code == 400
    assert "Invalid provider name" in response.json()["detail"]
    
    # Test spaces
    response = client.get("/providers/invalid~provider")
    assert response.status_code == 400
    assert "Invalid provider name" in response.json()["detail"]
    
    # Test valid format but non-existent provider
    response = client.get("/providers/nonexistent")
    assert response.status_code == 400
    assert "Provider not found" in response.json()["detail"]

def test_agent_name_validation(client):
    """Test agent name validation"""
    # Test invalid characters
    response = client.get("/agents/invalid@agent")
    assert response.status_code == 400
    assert "Invalid agent name" in response.json()["detail"]
    
    # Test spaces
    response = client.get("/agents/invalid agent")
    assert response.status_code == 400
    assert "Invalid agent name" in response.json()["detail"]
    
    # Test special characters
    response = client.get("/agents/invalid&agent")
    assert response.status_code == 400
    assert "Invalid agent name" in response.json()["detail"]
    
    # Test valid format but non-existent agent
    response = client.get("/agents/nonexistent")
    assert response.status_code == 400
    assert "Agent not found" in response.json()["detail"]

def test_prompt_request_validation(client):
    """Test prompt request validation"""
    # Test missing prompt field
    response = client.post("/prompt/", json={})
    assert response.status_code == 422
    
    # Test null prompt
    response = client.post("/prompt/", json={"prompt": None})
    assert response.status_code == 422
    
    # Test invalid provider format
    response = client.post(
        "/prompt/",
        json={
            "prompt": "test",
            "provider": "invalid@provider"
        }
    )
    assert response.status_code == 400
    assert "Invalid provider name" in response.json()["detail"]
    
    # Test valid provider format but non-existent provider
    response = client.post(
        "/prompt/",
        json={
            "prompt": "test",
            "provider": "nonexistent"
        }
    )
    assert response.status_code == 400
    assert "Provider nonexistent not found" in response.json()["detail"] 