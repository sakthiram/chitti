"""Base classes for Chitti plugins.

Design Tenets:
1. Base Classes vs Hooks:
   - Base classes provide shared functionality and state
   - Hooks provide extension points and plugin behavior
   - Use both where appropriate

2. Composition Over Inheritance:
   - Base classes should be thin
   - Prefer composition through services
   - Use mixins for shared behavior

3. Service Integration:
   - Base classes can access core services
   - Services are injected, not hardcoded
   - Keep dependencies explicit

4. Plugin Development:
   - Make it easy to create new plugins
   - Provide sensible defaults
   - Allow full customization when needed
"""

from typing import Dict, Any, Optional, List
import click
from fastapi import APIRouter
import pluggy
from abc import ABC, abstractmethod

from .hookspecs import AgentSpec, PromptRequest, CorePluginSpec
from .services import ChittiService

hookimpl = pluggy.HookimplMarker("chitti")

class BasePromptPlugin:
    """Base class for prompt handling plugins.
    
    Core plugin that provides prompt processing functionality.
    Can be subclassed to customize prompt handling.
    """

    def __init__(self, service: ChittiService):
        self.service = service

    @hookimpl
    def process_prompt(self, request: PromptRequest) -> str:
        """Default prompt processing implementation"""
        provider = self.service.get_provider(request.provider)
        return provider.generate(request.prompt)

class BaseAgent(ABC):
    """Base class for agent implementations.
    
    Provides common functionality and interface for agents.
    Must be subclassed to create concrete agents.
    """

    def __init__(self):
        """Initialize base agent"""
        self.service = ChittiService()  # Get existing singleton
        self.router = APIRouter()
        self.commands = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the unique name of this agent"""
        pass

    @abstractmethod
    def format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Format prompt with agent-specific context"""
        pass

    @abstractmethod
    def setup_routes(self):
        """Setup FastAPI routes for this agent"""
        pass

    @abstractmethod
    def setup_commands(self):
        """Setup CLI commands for this agent"""
        pass

    async def execute_with_llm(self, 
                             prompt: str, 
                             context: Dict[str, Any], 
                             provider: Optional[str] = None) -> str:
        """Helper to invoke LLM with agent context.
        
        Uses the prompt plugin system for processing.
        """
        request = PromptRequest(
            prompt=self.format_prompt(prompt, context),
            provider=provider,
            context=context
        )
        response = await self.service.process_prompt(request)
        return response.response

    # Default hook implementations
    @hookimpl
    def get_agent_name(self) -> str:
        """Get the unique name of this agent"""
        return self.name

    @hookimpl
    def get_router(self) -> APIRouter:
        """Get FastAPI router for agent endpoints"""
        return self.router

    @hookimpl
    def get_commands(self) -> click.Group:
        """Get Click command group for this agent"""
        return self.commands

    @hookimpl
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information - override in subclass to add more info"""
        return {
            "name": self.name,
            "description": "Base agent description",
            "version": "0.1.0",
            "capabilities": {
                "llm_integration": True,
                "tool_execution": True
            }
        }

    @hookimpl
    def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task - override in subclass"""
        raise NotImplementedError 