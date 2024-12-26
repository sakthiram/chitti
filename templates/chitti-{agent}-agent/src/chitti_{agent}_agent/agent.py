"""Template for agent implementation.

This template demonstrates the hybrid approach using both base classes and hooks.
"""

from typing import Dict, Any, Optional
import click
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pluggy

from chitti.base import BaseAgent
from chitti.services import ChittiService
from .prompts import SYSTEM_PROMPT, EXECUTION_PROMPT, REFLECTION_PROMPT

hookimpl = pluggy.HookimplMarker("chitti")

class AgentRequest(BaseModel):
    """Request model for agent execution"""
    task: str
    context: Dict[str, Any] = {}

class CustomAgent(BaseAgent):
    """Custom agent implementation using hybrid approach.
    
    Inherits common functionality from BaseAgent while using hooks for extensibility.
    """

    def __init__(self, service: Optional[ChittiService] = None):
        super().__init__(service)
        # Add any agent-specific initialization here
        self.history = []

    @property
    def name(self) -> str:
        return "custom"  # Override with your agent name

    def format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Format prompt with agent-specific context"""
        return EXECUTION_PROMPT.format(
            task=prompt,
            context=context,
            history=self.history
        )

    def setup_routes(self):
        """Setup FastAPI routes"""
        @self.router.post("/execute/")
        async def execute(request: AgentRequest):
            """Execute agent task"""
            try:
                return await self.execute_task(request.task, request.context)
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

    def setup_commands(self):
        """Setup Click commands"""
        @click.group(name=self.name)
        def commands():
            """Agent commands"""
            pass

        @commands.command()
        @click.argument("task")
        def execute(task: str):
            """Execute agent task"""
            import asyncio
            try:
                result = asyncio.run(self.execute_task(task))
                click.echo(result["result"])
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)

        @commands.command()
        @click.option("--host", default="127.0.0.1", help="Host to bind to")
        @click.option("--port", default=8000, help="Port to bind to")
        def serve(host: str, port: int):
            """Start the agent server"""
            import uvicorn
            uvicorn.run(
                f"chitti_{self.name}_agent.server:app",
                host=host,
                port=port,
                reload=True
            )

        self.commands = commands

    @hookimpl
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "description": "Custom agent description",
            "version": "0.1.0",
            "capabilities": {
                "llm_integration": True,
                "tool_execution": True,
                # Add your agent's capabilities here
            }
        }

    @hookimpl
    async def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task using LLM and agent-specific logic"""
        context = context or {}
        
        # Get LLM suggestion
        result = await self.execute_with_llm(
            task,
            context
        )
        
        # Update history
        self.history.append({
            "task": task,
            "result": result
        })
        if len(self.history) > 10:  # Keep last 10 tasks
            self.history.pop(0)
        
        return {
            "result": result,
            "context": {
                "history": self.history
            }
        } 