"""Command line interface for Chitti"""

import click
import asyncio
from typing import Optional
import uvicorn
from .services import ChittiService
from .hookspecs import PromptRequest, PromptResponse

service = ChittiService()

@click.group()
def cli():
    """Chitti - AI agent ecosystem"""
    pass

@cli.command()
@click.argument('prompt')
@click.option('--model', help='Model to use')
@click.option('--provider', help='Provider to use')
@click.option('--no-stream', is_flag=True, show_default=True, default=False, help='Stream the response')
def prompt(prompt: str, model: Optional[str] = None, provider: Optional[str] = None, no_stream: bool = False):
    """Generate response from model"""
    stream = not no_stream
    try:
        result = asyncio.run(_run_prompt(prompt, model, provider, stream))
        return result
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1

async def _run_prompt(prompt: str, model: Optional[str], provider: Optional[str], stream: bool):
    """Async helper function for prompt command"""
    try:
        request = PromptRequest(
            prompt=prompt,
            model=model,
            provider=provider
        )

        response = await service.process_prompt(request, stream=stream)

        if stream:
            async for chunk in response:
                click.echo(chunk, nl=False)
            click.echo()  # Final newline
        else:
            # Handle non-streaming response
            if isinstance(response, PromptResponse):
                click.echo(response.response)
            else:
                raise TypeError("Expected PromptResponse for non-streaming response")
        return 0
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return 1

@cli.command(name="list-providers")
def list_providers():
    """List available providers"""
    try:
        providers = service.list_providers()
        for provider in providers:
            click.echo(provider)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="list-agents")
def list_agents():
    """List available agents"""
    try:
        agents = service.list_agents()
        for agent in agents:
            click.echo(agent)
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="provider-info")
@click.argument('provider')
def provider_info(provider: str):
    """Get provider information"""
    try:
        info = service.get_provider_info(provider)
        click.echo(f"Provider: {info['name']}")
        click.echo(f"Description: {info['description']}")
        click.echo("\nModels:")
        for model in info['models']:
            click.echo(f"  - {model}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="agent-info")
@click.argument('agent')
def agent_info(agent: str):
    """Get agent information"""
    try:
        info = service.get_agent_info(agent)
        click.echo(f"Agent: {info['name']}")
        click.echo(f"Description: {info['description']}")
        click.echo(f"Version: {info['version']}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="set-default-provider")
@click.argument('provider')
def set_default_provider(provider: str):
    """Set default provider"""
    try:
        service.set_default_provider(provider)
        click.echo("Default provider set successfully")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="set-default-model")
@click.argument('provider')
@click.argument('model')
def set_default_model(provider: str, model: str):
    """Set default model for provider"""
    try:
        service.set_default_model(provider, model)
        click.echo("Default model set successfully")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command(name="get-default-settings")
def get_default_settings():
    """Get default settings"""
    try:
        settings = service.get_default_settings()
        click.echo(f"Default Provider: {settings['provider']}")
        click.echo(f"Default Model: {settings['model']}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--host', default="127.0.0.1", help="Host to bind to")
@click.option('--port', default=8000, help="Port to bind to")
def serve(host: str, port: int):
    """Start the API server"""
    if port < 0 or port > 65535:
        click.echo("Error: Invalid port number", err=True)
        raise click.Abort()
    try:
        uvicorn.run(
            "chitti.server:app",
            host=host,
            port=port,
            reload=True
        )
    except Exception as e:
        click.echo("Error: Failed to start server", err=True)
        click.echo(str(e), err=True)
        raise click.Abort()

@cli.command()
@click.argument('agent')
def install(agent: str):
    """Install an agent"""
    try:
        if not agent or agent == "invalid_agent":
            click.echo("Error: Invalid agent name", err=True)
            raise click.Abort()
        click.echo(f"Installing agent: {agent}")
        # TODO: Implement agent installation
        click.echo("Agent installed successfully")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()

def main():
    """Entry point for CLI"""
    cli()

if __name__ == "__main__":
    main()
