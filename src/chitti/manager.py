"""Plugin manager for Chitti"""

import pluggy
from typing import Dict, Any, Optional, List, Generator, Union
from .hookspecs import ModelProviderSpec, AgentSpec

class PluginManager:
    """Plugin manager for Chitti"""
    
    def __init__(self):
        """Initialize plugin manager"""
        self._providers: Dict[str, ModelProviderSpec] = {}
        self._agents: Dict[str, AgentSpec] = {}
        self._default_provider: Optional[str] = None
        self._default_models: Dict[str, str] = {}
    
    def register_provider(self, provider: ModelProviderSpec):
        """Register a model provider"""
        # Validate provider interface
        required_methods = ['get_provider_name', 'get_model_info', 'generate']
        for method in required_methods:
            if not hasattr(provider, method):
                raise TypeError(f"Provider must implement {method} method")
            
        name = provider.get_provider_name()
        self._providers[name] = provider
        
        # Set as default if no default provider or if it's the Bedrock provider
        if not self._default_provider or name == "bedrock":
            self.set_default_provider(name)
            
        # Set default model for this provider
        info = provider.get_model_info()
        if info["models"]:
            self._default_models[name] = info["models"][0]
    
    def register_agent(self, agent: AgentSpec):
        """Register an agent"""
        name = agent.get_agent_name()
        self._agents[name] = agent
    
    def get_provider(self, name: str) -> ModelProviderSpec:
        """Get provider by name"""
        if name not in self._providers:
            raise ValueError(f"Provider {name} not found")
        return self._providers[name]
    
    def get_agent(self, name: str) -> AgentSpec:
        """Get agent by name"""
        if name not in self._agents:
            raise ValueError(f"Agent {name} not found")
        return self._agents[name]
    
    def get_default_provider(self) -> ModelProviderSpec:
        """Get default provider"""
        if not self._default_provider:
            raise ValueError("No default provider set")
        return self.get_provider(self._default_provider)
    
    def set_default_provider(self, name: str):
        """Set default provider"""
        if name not in self._providers:
            raise ValueError(f"Provider {name} not found")
        self._default_provider = name
    
    def get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not found")
        
        # Return custom default model if set
        if provider in self._default_models:
            return self._default_models[provider]
        
        # Return provider's default model
        info = self.get_provider_info(provider)
        return info["default_model"]
    
    def set_default_model(self, provider: str, model: str):
        """Set default model for provider"""
        if provider not in self._providers:
            raise ValueError(f"Provider {provider} not found")
        
        # Verify model exists
        info = self.get_provider_info(provider)
        if model not in info["models"]:
            raise ValueError(f"Model {model} not found")
        
        self._default_models[provider] = model
    
    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self._providers.keys())
    
    def list_agents(self) -> List[str]:
        """List available agents"""
        return list(self._agents.keys())
    
    def get_provider_info(self, name: str) -> Dict[str, Any]:
        """Get provider information"""
        provider = self.get_provider(name)
        return provider.get_model_info()
    
    def get_agent_info(self, name: str) -> Dict[str, Any]:
        """Get agent information"""
        agent = self.get_agent(name)
        return agent.get_agent_info()
    
    def generate(self, prompt: str, provider: Optional[str] = None, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Generate response from provider with optional streaming"""
        if not provider:
            provider = self._default_provider
        
        if not provider:
            raise ValueError("No provider specified and no default provider set")
        
        provider_obj = self.get_provider(provider)
        return provider_obj.generate(prompt, stream=stream, **kwargs)
    
__all__ = ["PluginManager"] 