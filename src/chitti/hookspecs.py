"""Hook specifications for Chitti plugins.

Design Tenets:
1. Core Functionality as Plugins:
   - Even core features like prompt handling are plugins
   - This ensures consistent extension patterns
   - Allows replacing core functionality if needed

2. Plugin Categories:
   - Core Plugins: Essential services (prompt, llm, tools)
   - Agents: Task-specific implementations
   - Providers: Model/API providers
   - Tools: Shared utilities

3. Extension Points:
   - Use hooks for extensible behavior
   - Use base classes for shared functionality
   - Combine both for optimal flexibility

4. State Management:
   - Hooks for stateless operations
   - Base classes for stateful components
   - Service classes for shared state
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Protocol, Union
import click
from fastapi import APIRouter
import pluggy
from pydantic import BaseModel, Field

hookspec = pluggy.HookspecMarker("chitti")

class PromptRequest(BaseModel):
    """Request model for prompt generation"""
    prompt: str
    model: Optional[str] = None
    provider: Optional[str] = None
    context: Dict[str, Any] = {}

class PromptResponse(BaseModel):
    """Response model for prompt generation"""
    response: str
    metadata: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    """Standardized response type for all agents"""
    content: str
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    suggestions: List[str] = []  # Suggested next actions/commands
    context_updates: Dict[str, Any] = {}  # Updates to session context

    class Config:
        json_schema_extra = {
            "example": {
                "content": "Command output or agent response",
                "success": True,
                "metadata": {"agent": "bash", "command": "ls"},
                "suggestions": ["cd directory", "cat file"],
                "context_updates": {"workdir": "/new/path"}
            }
        }

class CorePluginSpec:
    """Core plugin specifications"""
    
    @hookspec(firstresult=True)
    def process_prompt(self, request: PromptRequest) -> PromptResponse:
        """Process a prompt request"""

    @hookspec
    def stream_prompt(self, request: PromptRequest) -> AsyncGenerator[str, None]:
        """Stream a prompt response"""

class ModelProviderSpec:
    """Model provider specifications"""

    @hookspec(firstresult=True)
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the model"""

    @hookspec
    def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Generate text using the model with streaming"""

    @hookspec(firstresult=True)
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information
        
        Returns:
            Dict containing:
            - name: str - Provider name
            - description: str - Provider description
            - models: List[str] - Available models
            - capabilities: Dict[str, bool] - Provider capabilities
        """

    @hookspec(firstresult=True)
    def get_provider_name(self) -> str:
        """Get provider name"""

class AgentSpec:
    """Agent specifications"""

    @hookspec(firstresult=True)
    def get_agent_name(self) -> str:
        """Get agent name"""

    @hookspec(firstresult=True)
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""

    @hookspec(firstresult=True)
    def get_router(self) -> APIRouter:
        """Get FastAPI router"""

    @hookspec(firstresult=True)
    def get_commands(self) -> click.Group:
        """Get CLI commands"""

    @hookspec(firstresult=True)
    def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task with the agent
        
        Args:
            task: The task to execute (e.g., command for bash agent, prompt for chat agent)
            context: Additional context for task execution
            
        Returns:
            Dict containing at minimum:
            - output: str - The task output
            - success: bool - Whether the task succeeded
            - suggestion: str - Suggested next action
        """

class ToolSpec:
    """Tool specifications"""

    @hookspec(firstresult=True)
    def execute(self, input_data: Any) -> Any:
        """Execute tool functionality"""

    @hookspec(firstresult=True)
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information"""
