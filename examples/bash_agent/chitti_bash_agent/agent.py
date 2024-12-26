"""Bash agent implementation"""

import os
import subprocess
from typing import Dict, Any, Optional
import click
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pluggy
from chitti import AgentSpec

hookimpl = pluggy.HookimplMarker("chitti")

class CommandRequest(BaseModel):
    command: str
    workdir: Optional[str] = None

@click.group(name="bash")
def commands():
    """Bash agent commands"""
    pass

@commands.command()
@click.argument('command')
@click.option('--workdir', help='Working directory for command execution')
def run(command: str, workdir: str = None):
    """Run a bash command"""
    try:
        if workdir:
            os.chdir(workdir)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo(f"Error: {result.stderr}", err=True)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@commands.command()
@click.option('--host', default="127.0.0.1", help="Host to bind to")
@click.option('--port', default=8001, help="Port to bind to")
def serve(host: str, port: int):
    """Start the bash agent server"""
    import uvicorn
    uvicorn.run(
        "chitti_bash_agent.server:app",
        host=host,
        port=port,
        reload=True
    )

class BashAgent:
    """Bash command execution agent"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/bash", tags=["bash"])
        self.setup_routes()
    
    def setup_routes(self):
        @self.router.post("/run/")
        async def run_command(request: CommandRequest):
            """Run a bash command"""
            try:
                if request.workdir:
                    try:
                        os.chdir(request.workdir)
                    except (FileNotFoundError, NotADirectoryError) as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Invalid working directory: {str(e)}"
                        )
                
                result = subprocess.run(
                    request.command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {"output": result.stdout}
                else:
                    # Check if command not found
                    if "command not found" in result.stderr.lower():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Command not found: {request.command}"
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=result.stderr
                        )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )
    
    @hookimpl
    def get_agent_name(self) -> str:
        """Get the unique name of this agent"""
        return "bash"
    
    @hookimpl
    def get_commands(self) -> click.Group:
        """Get Click command group for this agent"""
        return commands
    
    @hookimpl
    def get_router(self) -> APIRouter:
        """Get FastAPI router for agent endpoints"""
        return self.router
    
    @hookimpl
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "bash",
            "description": "Execute bash commands",
            "version": "0.1.0",
            "capabilities": {
                "command_execution": True,
                "streaming": False
            }
        } 