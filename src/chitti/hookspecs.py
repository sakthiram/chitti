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

from typing import Dict, Any, List, Optional, AsyncGenerator, Protocol
import click
from fastapi import APIRouter
import pluggy
from pydantic import BaseModel, Field

hookspec = pluggy.HookspecMarker("chitti")

class PromptRequest(BaseModel):
    """Model for prompt requests"""
    prompt: str = Field(..., description="The prompt text")
    model: Optional[str] = Field(None, description="Model to use")
    provider: Optional[str] = Field(None, description="Provider to use")
    tools: List[str] = Field(default_factory=list, description="Tools to use")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class PromptResponse(BaseModel):
    """Model for prompt responses"""
    response: str = Field(..., description="The response text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")

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
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""

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
        """Execute a task"""

class ToolSpec:
    """Tool specifications"""

    @hookspec(firstresult=True)
    def execute(self, input_data: Any) -> Any:
        """Execute tool functionality"""

    @hookspec(firstresult=True)
    def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information"""
