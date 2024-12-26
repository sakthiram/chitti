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

        @router.post("/run", response_model=CommandResponse)
        async def run_command(request: CommandRequest) -> Dict[str, Any]:
            """Run a bash command with LLM assistance"""
            try:
                result = await self.execute_task(request.command, {
                    "workdir": request.workdir,
                    **request.context
                })
                return {
                    "suggestion": result["suggestion"],
                    "output": result.get("output"),
                    "error": result.get("error"),
                    "context": result.get("context", {})
                }
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
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
        def run_command(command: str, workdir: str = None):
            """Run a bash command with LLM assistance"""
            import asyncio
            try:
                result = asyncio.run(self.execute_task(
                    command,
                    {"workdir": workdir} if workdir else {}
                ))
                
                suggestion = result["suggestion"]
                click.echo(f"Suggested command: {suggestion}")
                
                if click.confirm("Execute this command?"):
                    click.echo(result["output"])
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)

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
        """Execute a bash command task"""
        context = context or {}
        
        # Handle working directory
        if workdir := context.get("workdir"):
            try:
                os.chdir(workdir)
            except (FileNotFoundError, NotADirectoryError) as e:
                raise ValueError(f"Invalid working directory: {str(e)}")

        # Get command suggestion from LLM
        suggestion = await self.execute_with_llm(
            task,
            context
        )

        # Execute the suggested command
        try:
            result = subprocess.run(
                suggestion,
                shell=True,
                capture_output=True,
                text=True
            )

            # Update command history
            self.command_history.append(suggestion)
            if len(self.command_history) > 10:  # Keep last 10 commands
                self.command_history.pop(0)

            if result.returncode == 0:
                return {
                    "suggestion": suggestion,
                    "output": result.stdout,
                    "error": None,
                    "context": {
                        "workdir": os.getcwd(),
                        "history": self.command_history
                    }
                }
            else:
                if "command not found" in result.stderr.lower():
                    raise ValueError(f"Command not found: {suggestion}")
                else:
                    raise ValueError(result.stderr)
        except Exception as e:
            raise ValueError(f"Command execution failed: {str(e)}") 

    @hookimpl
    def get_commands(self) -> click.Group:
        """Get CLI commands"""
        return self.commands 