"""Command line interface for Chitti"""

import click
import asyncio
import logging
from typing import Optional
import uvicorn
from .services import ChittiService
from .hookspecs import PromptRequest, PromptResponse
from .manager import PluginManager

# Initialize singleton services
service = ChittiService()

# Create main CLI group
@click.group()
def cli():
    """Chitti - AI agent ecosystem"""
    pass

# Add core commands
@cli.command()
@click.argument('prompt')
@click.option('--model', help='Model to use')
@click.option('--provider', help='Provider to use')
@click.option('--stream', is_flag=True, help='Stream the response')
def prompt(prompt: str, model: Optional[str] = None, provider: Optional[str] = None, stream: bool = False):
    """Send a prompt to Chitti"""
    async def run():
        request = PromptRequest(
            prompt=prompt,
            model=model,
            provider=provider
        )
        
        if stream:
            response = await service.process_prompt(request, stream=True)
            async for chunk in response:
                click.echo(chunk, nl=False)
            click.echo()  # Final newline
        else:
            response = await service.process_prompt(request)
            click.echo(response.response)

    asyncio.run(run())

# Plugin management commands
@cli.group()
def agents():
    """Manage Chitti agents"""
    pass

@agents.command()
@click.argument("agent_name")
def install(agent_name: str):
    """Install a Chitti agent"""
    try:
        # Try installing from PyPI first
        click.echo(f"Installing {agent_name} agent...")
        import subprocess
        result = subprocess.run(
            ["pip", "install", f"chitti-{agent_name}-agent"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo(f"Successfully installed {agent_name} agent")
        else:
            click.echo(f"Error installing from PyPI: {result.stderr}")
            # Try installing from local examples
            example_path = f"examples/{agent_name}_agent"
            click.echo(f"Trying to install from {example_path}...")
            result = subprocess.run(
                ["pip", "install", "-e", example_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                click.echo(f"Successfully installed {agent_name} agent from examples")
            else:
                click.echo(f"Error installing from examples: {result.stderr}")
                raise click.ClickException(f"Failed to install {agent_name} agent")
    except Exception as e:
        raise click.ClickException(str(e))

@agents.command()
def list():
    """List installed Chitti agents"""
    agents = service.manager.list_agents()
    if not agents:
        click.echo("No agents installed")
        return
    
    click.echo("\nInstalled agents:")
    for name in agents:
        info = service.manager.get_agent_info(name)
        click.echo(f"\n{name}:")
        click.echo(f"  Description: {info.get('description', 'No description')}")
        click.echo(f"  Version: {info.get('version', 'Unknown')}")
        click.echo("  Capabilities:")
        for cap, enabled in info.get("capabilities", {}).items():
            click.echo(f"    - {cap}: {'✓' if enabled else '✗'}")

@agents.command()
@click.argument("agent_name")
def uninstall(agent_name: str):
    """Uninstall a Chitti agent"""
    try:
        click.echo(f"Uninstalling {agent_name} agent...")
        import subprocess
        result = subprocess.run(
            ["pip", "uninstall", "-y", f"chitti-{agent_name}-agent"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            click.echo(f"Successfully uninstalled {agent_name} agent")
        else:
            raise click.ClickException(f"Failed to uninstall {agent_name} agent: {result.stderr}")
    except Exception as e:
        raise click.ClickException(str(e))

# Load agent commands
for agent_name in service.manager.list_agents():
    try:
        agent = service.manager.get_agent(agent_name)
        cli.add_command(agent.get_commands())
    except Exception as e:
        click.echo(f"Warning: Failed to load commands for agent {agent_name}: {str(e)}", err=True)

def main():
    """Entry point for CLI"""
    cli()

if __name__ == "__main__":
    main()
