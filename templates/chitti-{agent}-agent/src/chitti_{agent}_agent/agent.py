"""Template for creating a new Chitti agent"""

import os
from typing import Dict, Any, Optional
import click
from fastapi import APIRouter
from pydantic import BaseModel, Field
import pluggy

from chitti.base import BaseAgent
from chitti.services import ChittiService
from chitti.hookspecs import AgentResponse
from .prompts import SYSTEM_PROMPT, EXECUTION_PROMPT

hookimpl = pluggy.HookimplMarker("chitti")

class TaskRequest(BaseModel):
    """Request model for agent task execution"""
    task: str = Field(..., description="Task to execute")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "task": "example task",
                "context": {"key": "value"}
            }
        }

class CustomAgent(BaseAgent):
    """Template for custom agent implementation"""

    def __init__(self):
        """Initialize agent"""
        self.task_history = []  # Store task execution history
        self.router = APIRouter()
        self.commands = None
        self.service = ChittiService()  # Get existing singleton
        self.setup_routes()
        self.setup_commands()

    @property
    def name(self) -> str:
        """Agent name - override with your agent's name"""
        return "{agent}"

    def format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Format prompt with agent-specific context"""
        return EXECUTION_PROMPT.format(
            task=prompt,
            context=context,
            history=self.task_history
        )

    def setup_routes(self):
        """Setup FastAPI routes"""
        router = APIRouter()

        @router.post("/suggest")
        async def suggest_task(request: TaskRequest) -> AgentResponse:
            """Get task suggestion from LLM"""
            try:
                result = await self.execute_task(
                    task=request.task,
                    context=request.context
                )
                return AgentResponse(
                    content=result["suggestion"],
                    success=True,
                    metadata={
                        "agent": self.name,
                        "task": request.task
                    },
                    suggestions=[],
                    context_updates={"last_task": result["suggestion"]}
                )
            except Exception as e:
                return AgentResponse(
                    content="",
                    success=False,
                    error=str(e),
                    metadata={"agent": self.name, "task": request.task}
                )

        @router.post("/execute")
        async def execute_task(request: TaskRequest) -> AgentResponse:
            """Execute a specific task"""
            try:
                result = await self.execute_specific_task(
                    task=request.task,
                    context=request.context
                )
                return AgentResponse(
                    content=result["output"],
                    success=result["success"],
                    metadata={
                        "agent": self.name,
                        "task": request.task,
                        "executed": True
                    },
                    suggestions=[],
                    context_updates={"last_task": result["suggestion"]}
                )
            except Exception as e:
                return AgentResponse(
                    content="",
                    success=False,
                    error=str(e),
                    metadata={"agent": self.name, "task": request.task}
                )

        self.router = router

    def setup_commands(self):
        """Setup Click commands"""
        @click.group(name=self.name)
        def commands():
            """Agent commands"""
            pass

        @commands.command(name="run")
        @click.argument("task")
        def run_task(task: str) -> AgentResponse:
            """Run a task with LLM assistance"""
            import asyncio
            try:
                # First get suggestion
                result = asyncio.run(self.execute_task(
                    task=task,
                    context={}
                ))
                
                click.echo(f"Suggested action: {result['suggestion']}")
                
                if click.confirm("Execute this action?", default=True):
                    # Then execute if approved
                    exec_result = asyncio.run(self.execute_specific_task(
                        task=result["suggestion"]
                    ))
                    click.echo(exec_result["output"])
                    return AgentResponse(
                        content=exec_result["output"],
                        success=exec_result["success"],
                        metadata={
                            "agent": self.name,
                            "task": task,
                            "executed": True
                        },
                        suggestions=[],
                        context_updates={"last_task": exec_result["suggestion"]}
                    )
                return AgentResponse(
                    content="Task execution cancelled",
                    success=True,
                    metadata={
                        "agent": self.name,
                        "task": task,
                        "executed": False
                    },
                    suggestions=[],
                    context_updates={"last_task": result["suggestion"]}
                )
            except Exception as e:
                error_msg = str(e)
                click.echo(f"Error: {error_msg}", err=True)
                return AgentResponse(
                    content="",
                    success=False,
                    error=error_msg,
                    metadata={"agent": self.name, "task": task}
                )

        # Set the commands attribute for the agent
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
                "task_execution": True,
                "streaming": False
            }
        }

    @hookimpl
    async def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get task suggestion from LLM"""
        context = context or {}
        # Get suggestion from LLM
        suggested_task = await self.execute_with_llm(task, context)
        # Add to task history
        self.task_history.append({
            "task": task,
            "suggestion": suggested_task,
            "executed": False
        })
        return {
            "output": "",
            "suggestion": suggested_task,
            "success": True,
            "executed": False
        }
    
    async def execute_specific_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a specific task - override this method with your agent's execution logic"""
        # Add your task execution logic here
        # This is just a placeholder implementation
        output = f"Executed task: {task}"
        
        # Update task history
        if self.task_history and self.task_history[-1]["suggestion"] == task:
            self.task_history[-1]["executed"] = True
            self.task_history[-1]["output"] = output
            self.task_history[-1]["success"] = True
        else:
            self.task_history.append({
                "task": task,
                "suggestion": task,
                "executed": True,
                "output": output,
                "success": True
            })
        
        return {
            "output": output,
            "suggestion": task,
            "success": True,
            "executed": True
        }

    @hookimpl
    def get_commands(self) -> click.Group:
        """Get CLI commands"""
        return self.commands 