"""Plugin management for Chitti"""

import logging
from typing import Dict, Any, Optional, List
import pluggy
import pkg_resources

from .hookspecs import ModelProviderSpec, AgentSpec, ToolSpec, CorePluginSpec

logger = logging.getLogger(__name__)

class PluginManager:
    """Manager for Chitti plugins"""

    _instance = None
    _initialized = False
    _loading = False  # Flag to prevent recursive loading

    # Storage for plugins - class level
    _providers: Dict[str, Any] = {}
    _agents: Dict[str, Any] = {}
    _tools: Dict[str, Any] = {}
    _default_models: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize plugin manager
            cls._instance.pm = pluggy.PluginManager("chitti")
            cls._instance.pm.add_hookspecs(CorePluginSpec)
            cls._instance.pm.add_hookspecs(ModelProviderSpec)
            cls._instance.pm.add_hookspecs(AgentSpec)
            cls._instance.pm.add_hookspecs(ToolSpec)
        return cls._instance

    def __init__(self):
        if not PluginManager._initialized:
            # Load plugins
            if not PluginManager._loading:
                self.load_plugins()
            PluginManager._initialized = True

    def load_plugins(self):
        """Load all installed plugins"""
        try:
            PluginManager._loading = True
            
            # Load providers
            for entry_point in pkg_resources.iter_entry_points("chitti.providers"):
                try:
                    provider_class = entry_point.load()
                    provider = provider_class()
                    self.register_provider(provider)
                    logger.info(f"Loaded provider: {entry_point.name}")
                except Exception as e:
                    logger.error(f"Error loading provider {entry_point.name}: {str(e)}")

            # Load agents
            for entry_point in pkg_resources.iter_entry_points("chitti.agents"):
                try:
                    agent_class = entry_point.load()
                    agent = agent_class()
                    self.register_agent(agent)
                    logger.info(f"Loaded agent: {entry_point.name}")
                except Exception as e:
                    logger.error(f"Error loading agent {entry_point.name}: {str(e)}")

            # Load tools
            for entry_point in pkg_resources.iter_entry_points("chitti.tools"):
                try:
                    tool_class = entry_point.load()
                    tool = tool_class()
                    self.register_tool(tool)
                    logger.info(f"Loaded tool: {entry_point.name}")
                except Exception as e:
                    logger.error(f"Error loading tool {entry_point.name}: {str(e)}")
        finally:
            PluginManager._loading = False

    def register_provider(self, provider: Any):
        """Register a provider plugin"""
        try:
            name = provider.get_provider_name()
            self.__class__._providers[name] = provider
            self.pm.register(provider)
        except Exception as e:
            logger.error(f"Error registering provider: {str(e)}")
            raise

    def register_agent(self, agent: Any):
        """Register an agent plugin"""
        try:
            self.pm.register(agent)
            name = agent.get_agent_name()
            self._agents[name] = agent
        except Exception as e:
            logger.error(f"Error registering agent: {str(e)}")
            raise

    def register_tool(self, tool: Any):
        """Register a tool plugin"""
        try:
            self.pm.register(tool)
            name = tool.get_tool_name()
            self._tools[name] = tool
        except Exception as e:
            logger.error(f"Error registering tool: {str(e)}")
            raise

    def get_provider(self, name: Optional[str] = None) -> Any:
        """Get a provider by name"""
        if name is None:
            # Return first provider if none specified
            if not self._providers:
                raise ValueError("No providers available")
            return next(iter(self._providers.values()))
        
        if name not in self._providers:
            raise ValueError(f"Provider not found: {name}")
        return self._providers[name]

    def get_agent(self, name: str) -> Any:
        """Get an agent by name"""
        if name not in self._agents:
            raise ValueError(f"Agent not found: {name}")
        return self._agents[name]

    def get_tool(self, name: str) -> Any:
        """Get a tool by name"""
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        return self._tools[name]

    def list_providers(self) -> List[str]:
        """List available providers"""
        return list(self._providers.keys())

    def list_agents(self) -> List[str]:
        """List available agents"""
        return list(self._agents.keys())

    def list_tools(self) -> List[str]:
        """List available tools"""
        return list(self._tools.keys())

    def get_provider_info(self, name: str) -> Dict[str, Any]:
        """Get provider information"""
        provider = self.get_provider(name)
        return provider.get_provider_info()

    def get_agent_info(self, name: str) -> Dict[str, Any]:
        """Get agent information"""
        agent = self.get_agent(name)
        return agent.get_agent_info()

    def get_tool_info(self, name: str) -> Dict[str, Any]:
        """Get tool information"""
        tool = self.get_tool(name)
        return tool.get_tool_info()

    def set_default_provider(self, name: str):
        """Set default provider"""
        if name not in self._providers:
            raise ValueError(f"Provider not found: {name}")
        self._default_provider = name

    def set_default_model(self, provider: str, model: str):
        """Set default model for provider"""
        if provider not in self._providers:
            raise ValueError(f"Provider not found: {provider}")
        self._default_models[provider] = model

    def get_default_model(self, provider: str) -> Optional[str]:
        """Get default model for provider"""
        return self._default_models.get(provider) 