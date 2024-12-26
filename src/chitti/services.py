"""Service layer for Chitti"""

from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from .hookspecs import PromptRequest, PromptResponse
from .manager import PluginManager

class ChittiService:
    """Main service for Chitti functionality"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not ChittiService._initialized:
            self.manager = PluginManager()
            # Register core plugins
            try:
                self.manager.pm.register(self, name="chitti_core")
            except ValueError:
                # Already registered, ignore
                pass
            ChittiService._initialized = True

    async def process_prompt(self, request: PromptRequest, stream: bool = False) -> Union[PromptResponse, AsyncGenerator[str, None]]:
        """Process a prompt request"""
        # Fallback to provider
        provider = self.manager.get_provider(request.provider)
        
        if stream:
            return provider.generate_stream(request.prompt)
        else:
            response = await provider.generate(request.prompt)
            return PromptResponse(
                response=response,
                metadata={
                    "provider": provider.get_provider_name(),
                    "model": request.model
                }
            )

    def list_providers(self) -> List[str]:
        """List available providers"""
        return self.manager.list_providers()

    def list_agents(self) -> List[str]:
        """List available agents"""
        return self.manager.list_agents()

    def list_tools(self) -> List[str]:
        """List available tools"""
        return self.manager.list_tools()

    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get provider information"""
        return self.manager.get_provider_info(provider)

    def get_agent_info(self, agent: str) -> Dict[str, Any]:
        """Get agent information"""
        return self.manager.get_agent_info(agent)

    def get_tool_info(self, tool: str) -> Dict[str, Any]:
        """Get tool information"""
        return self.manager.get_tool_info(tool)

    def set_default_provider(self, provider: str):
        """Set default provider"""
        self.manager.set_default_provider(provider)

    def set_default_model(self, provider: str, model: str):
        """Set default model for provider"""
        self.manager.set_default_model(provider, model)

    def get_default_settings(self) -> Dict[str, Any]:
        """Get default settings"""
        provider = self.manager.get_provider()
        return {
            "provider": provider.get_provider_name(),
            "model": self.manager.get_default_model(provider.get_provider_name())
        } 