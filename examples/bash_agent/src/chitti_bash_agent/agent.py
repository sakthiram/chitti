"""Bash agent implementation using hybrid approach"""

import os
import subprocess
from typing import Dict, Any, Optional
import click
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pluggy

from chitti.base import BaseAgent
from chitti.services import ChittiService
from chitti.hookspecs import AgentResponse
from .prompts import SYSTEM_PROMPT, EXECUTION_PROMPT

hookimpl = pluggy.HookimplMarker("chitti")

class CommandRequest(BaseModel):
    """Request model for bash command execution"""
    command: str = Field(..., description="Command to execute")
    workdir: Optional[str] = Field(None, description="Working directory")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "command": "ls -la",
                "workdir": "/home/user",
                "context": {}
            }
        }

class CommandResponse(BaseModel):
    """Response model for bash command execution"""
    suggestion: str = Field(..., description="Suggested next action")
    output: Optional[str] = Field(None, description="Command output")
    error: Optional[str] = Field(None, description="Error message if any")
    context: Dict[str, Any] = Field(default_factory=dict, description="Updated context")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion": "ls -la",
                "output": "total 0\ndrwxr-xr-x  2 user user  40 Apr 15 10:00 .",
                "error": None,
                "context": {"workdir": "/home/user"}
            }
        }

class BashAgent(BaseAgent):
    """Bash command execution agent with LLM integration"""

    def __init__(self):
        """Initialize bash agent"""
        self.command_history = []
        self.router = APIRouter()
        self.commands = None
        self.service = ChittiService()  # Get existing singleton
        self.setup_routes()
        self.setup_commands()

    @property
    def name(self) -> str:
        return "bash"

    def format_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Format prompt with bash-specific context"""
        return EXECUTION_PROMPT.format(
            task=prompt,
            workdir=context.get("workdir", os.getcwd()),
            history=self.command_history,
            system_info=os.uname()
        )

    def setup_routes(self):
        """Setup FastAPI routes"""
        router = APIRouter()

        @router.post("/suggest")
        async def suggest_command(request: CommandRequest) -> AgentResponse:
            """Get command suggestion from LLM"""
            try:
                result = await self.execute_task(
                    task=request.command,
                    context={
                        "workdir": request.workdir,
                        **request.context
                    }
                )
                return AgentResponse(
                    content=result["suggestion"],
                    success=True,
                    metadata={
                        "agent": "bash",
                        "command": request.command,
                        "workdir": request.workdir,
                        "executed": False
                    },
                    suggestions=[],
                    context_updates={"last_command": result["suggestion"]}
                )
            except Exception as e:
                return AgentResponse(
                    content="",
                    success=False,
                    error=str(e),
                    metadata={"agent": "bash", "command": request.command}
                )

        @router.post("/execute")
        async def execute_command(request: CommandRequest) -> AgentResponse:
            """Execute a bash command"""
            try:
                result = await self.execute_command(
                    command=request.command,
                    workdir=request.workdir
                )
                return AgentResponse(
                    content=result["output"],
                    success=result["success"],
                    metadata={
                        "agent": "bash",
                        "command": request.command,
                        "workdir": request.workdir,
                        "executed": True
                    },
                    suggestions=[],
                    context_updates={
                        "workdir": request.workdir,
                        "last_command": result["suggestion"]
                    } if request.workdir else {"last_command": result["suggestion"]}
                )
            except Exception as e:
                return AgentResponse(
                    content="",
                    success=False,
                    error=str(e),
                    metadata={"agent": "bash", "command": request.command}
                )

        self.router = router

    def setup_commands(self):
        """Setup Click commands"""
        @click.group(name=self.name)
        def commands():
            """Bash agent commands"""
            pass

        @commands.command(name="run")
        @click.argument("command")
        @click.option("--workdir", help="Working directory for command execution")
        def run_command(command: str, workdir: str = None) -> AgentResponse:
            """Run a bash command with LLM assistance"""
            import asyncio
            try:
                # First get suggestion
                result = asyncio.run(self.execute_task(
                    task=command,
                    context={"workdir": workdir} if workdir else {}
                ))
                
                click.echo(f"Suggested command: {result['suggestion']}")
                
                if click.confirm("Execute this command?", default=True):
                    # Then execute if approved
                    exec_result = asyncio.run(self.execute_command(
                        command=result["suggestion"],
                        workdir=workdir
                    ))
                    click.echo(exec_result["output"])
                    return AgentResponse(
                        content=exec_result["output"],
                        success=exec_result["success"],
                        metadata={
                            "agent": "bash",
                            "command": command,
                            "workdir": workdir,
                            "executed": True
                        },
                        suggestions=[],
                        context_updates={
                            "workdir": workdir,
                            "last_command": exec_result["suggestion"]
                        } if workdir else {"last_command": exec_result["suggestion"]}
                    )
                return AgentResponse(
                    content="Command execution cancelled",
                    success=True,
                    metadata={
                        "agent": "bash",
                        "command": command,
                        "executed": False
                    },
                    suggestions=[],
                    context_updates={"last_command": result["suggestion"]}
                )
            except Exception as e:
                error_msg = str(e)
                click.echo(f"Error: {error_msg}", err=True)
                return AgentResponse(
                    content="",
                    success=False,
                    error=error_msg,
                    metadata={"agent": "bash", "command": command}
                )

        @commands.command()
        @click.option("--host", default="127.0.0.1", help="Host to bind to")
        @click.option("--port", default=8001, help="Port to bind to")
        def serve(host: str, port: int):
            """Start the bash agent server"""
            import uvicorn
            uvicorn.run(
                "chitti_bash_agent.server:app",
                host=host,
                port=port,
                reload=True
            )

        # Set the commands attribute for the agent
        self.commands = commands

    @hookimpl
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "description": "Execute bash commands with LLM assistance",
            "version": "0.1.0",
            "capabilities": {
                "llm_integration": True,
                "command_execution": True,
                "streaming": False
            }
        }

    @hookimpl
    async def execute_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get command suggestion from LLM"""
        context = context or {}
        # Get command suggestion from LLM
        suggested_command = await self.execute_with_llm(task, context)
        return {
            "output": "",
            "suggestion": suggested_command,
            "success": True,
            "executed": False
        }
    
    async def execute_command(self, command: str, workdir: Optional[str] = None) -> Dict[str, Any]:
        """Execute a bash command"""
        if workdir:
            original_dir = os.getcwd()
            os.chdir(workdir)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            
            output = result.stdout if result.returncode == 0 else result.stderr
            self.command_history.append(command)
            
            return {
                "output": output,
                "suggestion": command,
                "success": result.returncode == 0,
                "executed": True
            }
        finally:
            if workdir:
                os.chdir(original_dir)

    @hookimpl
    def get_commands(self) -> click.Group:
        """Get CLI commands"""
        return self.commands 