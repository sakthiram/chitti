from typing import Dict, Any, List, Optional, AsyncGenerator
import click
import pluggy
from fastapi import APIRouter
from pydantic import BaseModel

hookspec = pluggy.HookspecMarker("chitti")

class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None  # If None, use default provider
    tools: List[str] = []

class PromptResponse(BaseModel):
    response: str
    metadata: Dict[str, Any] = {}

class ModelProviderSpec:
    """Hook specifications for model providers"""

    @hookspec
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the model without streaming"""
        pass

    @hookspec
    def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text using the model with streaming"""
        pass

    @hookspec
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information including available models, 
        default model, pricing, and other metadata"""
        pass

    @hookspec
    def get_provider_name(self) -> str:
        """Get the unique name of this provider"""
        pass

class ProviderManager:
    """Manages model providers and default settings"""
    
    def __init__(self):
        self._default_provider = None
        self._default_models = {}  # provider_name -> model_id
        self._providers = {}  # provider_name -> provider_instance
    
    def register_provider(self, provider: Any):
        """Register a provider and set its default model"""
        name = provider.get_provider_name()
        self._providers[name] = provider
        
        # Set as default if no default provider
        if not self._default_provider:
            self.set_default_provider(name)
        
        # Set default model for this provider
        info = provider.get_model_info()
        if info["models"]:
            self._default_models[name] = info["models"][0]
    
    def set_default_provider(self, provider_name: str):
        """Set the default provider"""
        if provider_name not in self._providers:
            raise ValueError(f"Provider {provider_name} not found")
        self._default_provider = provider_name
    
    def set_default_model(self, provider_name: str, model_id: str):
        """Set the default model for a provider"""
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")
        
        info = provider.get_model_info()
        if model_id not in info["models"]:
            raise ValueError(f"Model {model_id} not found for provider {provider_name}")
        
        self._default_models[provider_name] = model_id
    
    def get_provider(self, name: Optional[str] = None) -> Any:
        """Get a provider by name or the default provider if name is None"""
        provider_name = name or self._default_provider
        if not provider_name:
            raise ValueError("No provider specified and no default provider set")
        
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider {provider_name} not found")
        return provider
    
    def get_default_model(self, provider_name: Optional[str] = None) -> Optional[str]:
        """Get the default model for a provider"""
        name = provider_name or self._default_provider
        if not name:
            return None
        return self._default_models.get(name)

class ToolSpec:
    """Hook specifications for tools"""

    @hookspec
    def execute(self, input_data: Any) -> Any:
        """Execute tool functionality"""
        pass

    @hookspec
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information"""
        pass

class AgentSpec:
    """Hook specifications for agents"""

    @hookspec
    def get_router(self) -> APIRouter:
        """Get FastAPI router for agent endpoints"""
        pass

    @hookspec
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        pass
        
    @hookspec
    def get_commands(self) -> click.Group:
        """Get Click command group for this agent"""
        pass
        
    @hookspec
    def get_agent_name(self) -> str:
        """Get the unique name of this agent"""
        pass
