"""Command line interface for Chitti"""

import click
import asyncio
import datetime
from typing import Optional, Dict, List, Any, Union
import uvicorn
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import os
import json
from pathlib import Path
from .services import ChittiService
from .hookspecs import PromptRequest, PromptResponse, AgentResponse
from .manager import PluginManager

# Initialize singleton services
service = ChittiService()

# Create main CLI group
@click.group()
def cli():
    """Chitti - AI agent ecosystem"""
    pass

# Add providers group
@cli.group()
def providers():
    """Manage Chitti providers"""
    pass

@providers.command(name="list")
def list_providers():
    """List available providers"""
    providers = service.manager.list_providers()
    if not providers:
        click.echo("No providers installed")
        return
    
    click.echo("\nAvailable providers:")
    for name in providers:
        info = service.manager.get_provider_info(name)
        click.echo(f"\n{name}:")
        click.echo(f"  Description: {info.get('description', 'No description')}")
        click.echo(f"  Models: {', '.join(info.get('models', []))}")

@providers.command(name="info")
@click.argument("provider_name")
def provider_info(provider_name: str):
    """Get provider information"""
    try:
        info = service.manager.get_provider_info(provider_name)
        click.echo(f"\n{provider_name}:")
        click.echo(f"  Description: {info.get('description', 'No description')}")
        click.echo(f"  Models: {', '.join(info.get('models', []))}")
        click.echo("  Capabilities:")
        for cap, enabled in info.get("capabilities", {}).items():
            click.echo(f"    - {cap}: {'✓' if enabled else '✗'}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

@providers.command(name="models")
@click.argument("provider_name")
def provider_models(provider_name: str):
    """List available models for a provider"""
    try:
        info = service.manager.get_provider_info(provider_name)
        models = info.get("models", [])
        if not models:
            click.echo(f"No models available for provider {provider_name}")
            return
        
        click.echo(f"\nAvailable models for {provider_name}:")
        for model in models:
            click.echo(f"  - {model}")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)

class InteractiveSession:
    def __init__(self):
        self.history_dir = Path.home() / ".chitti" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.session = PromptSession(
            history=FileHistory(str(self.history_dir / "command_history")),
            auto_suggest=AutoSuggestFromHistory()
        )
        self.conversation_history: List[Dict] = []
        self.session_params: Dict = {}
    
    def save_conversation(self, filename: Optional[str] = None):
        """Save the current conversation history"""
        if not filename:
            existing = len([f for f in os.listdir(self.history_dir) if f.startswith("conversation_")])
            filename = f"conversation_{existing + 1}.json"
        filepath = self.history_dir / filename
        with open(filepath, 'w') as f:
            json.dump(self.conversation_history, f, indent=2)
        click.echo(f"Conversation saved to {filepath}")
    
    def new_session(self, save_history: bool = True):
        """Start a new session"""
        if save_history and self.conversation_history:
            self.save_conversation()
        self.conversation_history = []
        self.session_params = {}
        click.echo("Started new session")
    
    def set_context(self, key: str, value: str):
        """Set a context parameter"""
        self.session_params[key] = value
        click.echo(f"Set {key} = {value}")
    
    def add_to_history(self, command: str, response: Optional[Union[PromptResponse, AgentResponse]] = None):
        """Add command and response to conversation history"""
        entry = {
            "type": "interaction",
            "timestamp": str(datetime.datetime.now()),
            "context": self.session_params.copy(),
            "command": command
        }
        
        if response:
            if isinstance(response, PromptResponse):
                entry["response"] = response.response
                entry["metadata"] = response.metadata
            elif isinstance(response, AgentResponse):
                entry["response"] = response.content
                entry["success"] = response.success
                entry["error"] = response.error
                entry["metadata"] = response.metadata
                entry["suggestions"] = response.suggestions
                # Update session context if agent provides updates
                if response.context_updates:
                    self.session_params.update(response.context_updates)
                    entry["updated_context"] = self.session_params.copy()
        
        self.conversation_history.append(entry)
    
    def handle_set_command(self, parts: List[str]):
        """Handle set commands in interactive mode"""
        if len(parts) < 3:
            click.echo("Usage: set <key> <value>", err=True)
            return
        
        key = parts[1]
        value = parts[2]
        
        try:
            if key == "provider":
                service.manager.set_default_provider(value)
                click.echo(f"Default provider set to: {value}")
            elif key == "model":
                # Get current default provider
                settings = service.manager.get_default_settings()
                provider = settings.get("provider")
                if not provider:
                    click.echo("Error: Set default provider first", err=True)
                    return
                service.manager.set_default_model(provider, value)
                click.echo(f"Default model set to: {value}")
            else:
                # Regular context parameter
                self.set_context(key, value)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
    
    def handle_show_command(self, parts: List[str]):
        """Handle show commands in interactive mode"""
        if len(parts) < 2:
            click.echo("Usage: show <what>", err=True)
            return
        
        what = parts[1]
        try:
            if what == "providers":
                providers = service.manager.list_providers()
                click.echo("\nAvailable providers:")
                for name in providers:
                    info = service.manager.get_provider_info(name)
                    click.echo(f"\n{name}:")
                    click.echo(f"  Description: {info.get('description', 'No description')}")
                    click.echo(f"  Models: {', '.join(info.get('models', []))}")
            elif what == "models":
                if len(parts) < 3:
                    click.echo("Usage: show models <provider>", err=True)
                    return
                provider = parts[2]
                info = service.manager.get_provider_info(provider)
                models = info.get("models", [])
                click.echo(f"\nAvailable models for {provider}:")
                for model in models:
                    click.echo(f"  - {model}")
            elif what == "settings":
                settings = service.manager.get_default_settings()
                click.echo("\nCurrent settings:")
                for key, value in settings.items():
                    click.echo(f"  {key}: {value}")
            else:
                click.echo(f"Unknown show command: {what}", err=True)
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)

@cli.command()
def interactive():
    """Start an interactive Chitti session"""
    session = InteractiveSession()
    click.echo("Welcome to Chitti Interactive Mode!")
    click.echo("Type 'help' for available commands or 'exit' to quit")
    
    while True:
        try:
            # Get input with prompt
            command = session.session.prompt("chitti> ").strip()
            
            # Skip empty commands
            if not command:
                continue
            
            # Handle special commands
            if command.lower() == 'exit':
                if session.conversation_history:
                    if click.confirm("Save conversation history?", default=True):
                        session.save_conversation()
                break
            
            elif command.lower() == 'help':
                click.echo("""
Available Commands:
  General:
    help                    - Show this help message
    exit                    - Exit interactive mode
    
  Session Management:
    new                     - Start new session
    save [filename]         - Save conversation history
    context                 - Show current context
    set <key> <value>      - Set context parameter
    
  Configuration:
    set provider <name>     - Set default provider
    set model <name>        - Set default model for current provider
    show providers         - List available providers
    show models <provider> - List available models for provider
    show settings         - Show current settings
    
  Regular CLI:
    Any regular Chitti command (e.g., 'bash', 'prompt', etc.)
    Note: You can omit 'chitti' prefix in interactive mode
                """)
                continue
            
            elif command.lower() == 'new':
                save = click.confirm("Save current conversation?", default=True)
                session.new_session(save_history=save)
                continue
            
            elif command.lower() == 'save':
                filename = click.prompt("Enter filename (optional)", default='', show_default=False)
                session.save_conversation(filename if filename else None)
                continue
            
            elif command.lower() == 'context':
                click.echo("\nCurrent Session Context:")
                if not session.session_params:
                    click.echo("No context parameters set")
                else:
                    for key, value in session.session_params.items():
                        click.echo(f"{key}: {value}")
                continue
            
            elif command.lower().startswith('set '):
                self.handle_set_command(command.split())
            elif command.lower().startswith('show '):
                self.handle_show_command(command.split())
            
            # Handle regular CLI commands
            try:
                # Split command respecting quotes
                import shlex
                args = shlex.split(command)
                
                # Create a new Click context
                ctx = click.Context(cli)
                
                # Find the command in the CLI group
                cmd_name = args[0]
                if cmd_name in cli.commands:
                    cmd = cli.commands[cmd_name]
                    # Run the command through the main CLI group
                    result = cli.main(args=args, prog_name='chitti', standalone_mode=False)
                    
                    # Add to conversation history
                    if isinstance(result, (PromptResponse, AgentResponse)):
                        session.add_to_history(command, result)
                    else:
                        session.add_to_history(command)
                else:
                    click.echo(f"Unknown command: {cmd_name}", err=True)
            
            except click.exceptions.Exit:
                continue
            except Exception as e:
                click.echo(f"Error: {str(e)}", err=True)
                session.add_to_history(command, AgentResponse(
                    content="",
                    success=False,
                    error=str(e)
                ))
        
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

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
            ["python", "-m", "pip", "install", f"chitti-{agent_name}-agent"],
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
                ["python", "-m", "pip", "install", "-e", example_path],
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
            ["python", "-m", "pip", "uninstall", "-y", f"chitti-{agent_name}-agent"],
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
