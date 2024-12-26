"""Service layer for Chitti"""

import pkg_resources
from typing import Dict, Any, List, Optional, Generator, Union, AsyncGenerator
from .hookspecs import PromptRequest, PromptResponse, ModelProviderSpec, AgentSpec
from .manager import PluginManager

class ChittiService:
    """Service layer for Chitti"""
    
    _instance = None
    
    def __new__(cls):
        """Create singleton instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize service"""
        if self._initialized:
            return
        
        self._initialized = True
        self._manager = PluginManager()
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all installed plugins"""
        # Load providers
        for entry_point in pkg_resources.iter_entry_points('chitti.providers'):
            try:
                plugin_class = entry_point.load()
                plugin = plugin_class()
                self._manager.register_provider(plugin)
            except Exception as e:
                print(f"Failed to load provider {entry_point.name}: {str(e)}")
        
        # Load agents
        for entry_point in pkg_resources.iter_entry_points('chitti.agents'):
            try:
                plugin_class = entry_point.load()
                plugin = plugin_class()
                self._manager.register_agent(plugin)
            except Exception as e:
                print(f"Failed to load agent {entry_point.name}: {str(e)}")
    
    async def process_prompt(self, request: PromptRequest, stream: bool = False) -> Union[PromptResponse, AsyncGenerator[str, None]]:
        """Process a prompt request"""
        provider = request.provider
        model = request.model
        
        # Get provider
        if provider:
            provider_obj = self._manager.get_provider(provider)
        else:
            provider_obj = self._manager.get_default_provider()
            provider = provider_obj.get_provider_name()
        
        # Get model
        if not model:
            model = self._manager.get_default_model(provider)
        
        # Generate response
        if stream:
            # For streaming, yield each chunk
            async def stream_response():
                async for chunk in provider_obj.generate_stream(model=model, prompt=request.prompt):
                    yield chunk
            return stream_response()
        else:
            # For non-streaming, get the full response
            response = await provider_obj.generate(model=model, prompt=request.prompt)
            
            # Return the response object
            return PromptResponse(
                response=response,
                metadata={
                    "provider": provider,
                    "model": model
                }
            )
    
    def list_providers(self) -> List[str]:
        """List available providers"""
        return self._manager.list_providers()
    
    def list_agents(self) -> List[str]:
        """List available agents"""
        return self._manager.list_agents()
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get provider information"""
        return self._manager.get_provider_info(provider)
    
    def get_agent_info(self, agent: str) -> Dict[str, Any]:
        """Get agent information"""
        return self._manager.get_agent_info(agent)
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        provider = self._manager.get_default_provider()
        return {
            "provider": provider.get_provider_name(),
            "model": self._manager.get_default_model(provider.get_provider_name())
        }
    
    def set_default_provider(self, provider: str):
        """Set default provider"""
        self._manager.set_default_provider(provider)
    
    def set_default_model(self, provider: str, model: str):
        """Set default model for provider"""
        self._manager.set_default_model(provider, model) 