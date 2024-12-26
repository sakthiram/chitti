# Chitti: A Modular AI Ecosystem

Chitti is an extensible AI ecosystem that allows you to interact with various AI models and agents through a unified interface. It provides both CLI and API access, with support for plugins to extend its functionality.

## Features

### Core Features
- 🔌 **Plugin System**: Easily extend with new providers, agents, and tools
- 🤖 **Multiple Model Support**: Use different AI models through a unified interface
- 🛠️ **CLI & API**: Access functionality through both CLI and REST API
- ⚙️ **Configuration Management**: Flexible settings for providers and models
- 💬 **Interactive Mode**: Rich interactive shell with session management and history

### Model Providers
- 🌟 **AWS Bedrock** (built-in)
  - Claude 3 Opus, Sonnet, and Haiku models
  - Streaming support
  - Automatic throttling handling
  - Token usage tracking

### Extensibility
- 🔧 **Custom Agents**: Add new agents for specialized tasks
- 🛠️ **Custom Tools**: Integrate external tools and APIs
- 🎯 **Custom Providers**: Add support for new AI models

## Installation

```bash
# Using uv (recommended)
uv pip install chitti
```

## Usage

### Interactive Mode
```bash
# Start interactive mode
chitti interactive

# Available commands in interactive mode:
help                    # Show available commands
new                     # Start new session
save [filename]         # Save conversation history
context                 # Show current context
exit                   # Exit interactive mode

# Configuration commands:
set provider bedrock                                           # Set default provider
set model "anthropic.claude-3-sonnet-20240229-v1:0"          # Set default model
show providers                                                # List available providers
show models bedrock                                          # List models for provider
show settings                                                # Show current settings

# Regular CLI commands work without 'chitti' prefix
prompt "What is Python?"
bash run "list files"  # Two-step execution with confirmation
```

### Direct CLI Commands

1. Prompt Generation:
```bash
# Basic prompt
chitti prompt "What is Python?"

# With specific model
chitti prompt --model "anthropic.claude-3-sonnet-20240229-v1:0" "What is Python?"

# With streaming
chitti prompt --stream "Write a long explanation"
```

2. Agent Commands:
```bash
# Bash agent (two-step execution)
chitti bash run "list all files sorted by date"  # Will show suggestion and ask for confirmation

# Other agents follow same pattern
chitti <agent> run "task description"
```

3. Agent Management:
```bash
# List installed agents
chitti agents list

# Install an agent
chitti agents install bash

# Uninstall an agent
chitti agents uninstall bash
```

4. Provider Commands:
```bash
# List available providers
chitti providers list

# Get provider information
chitti providers info bedrock

# List available models for provider
chitti providers models bedrock
```

### API Usage

1. Start the server:
```bash
chitti serve
```

2. Make API requests:
```bash
# Generate text
curl -X POST "http://localhost:8000/prompt/" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?", "model": "anthropic.claude-3-sonnet-20240229-v1:0"}'

# Use agent (two-step process)
# 1. Get suggestion
curl -X POST "http://localhost:8000/bash/suggest" \
  -H "Content-Type: application/json" \
  -d '{"task": "list files", "context": {}}'

# 2. Execute task
curl -X POST "http://localhost:8000/bash/execute" \
  -H "Content-Type: application/json" \
  -d '{"task": "ls -la", "context": {}}'
```

## Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/sakthiram/chitti.git
cd chitti

# Create and activate virtual environment (using uv)
uv venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install development dependencies
uv pip install -e ".[dev]"
```

### Project Structure
```
chitti/
├── src/
│   └── chitti/
│       ├── __init__.py
│       ├── cli.py          # CLI implementation
│       ├── services.py     # Core services
│       ├── hookspecs.py    # Plugin specifications
│       └── providers/      # Built-in Model providers
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── examples/              # Example plugins
└── setup.py
```

### Testing

#### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v --cov=src/chitti
```

### Creating Plugins

1. Create a new provider:
```python
from chitti import ModelProviderSpec

class MyProvider:
    @hookimpl
    def get_provider_name(self) -> str:
        return "my_provider"
        
    @hookimpl
    def generate(self, prompt: str, **kwargs) -> str:
        # Implementation
        pass
```

2. Create a new agent:
```python
from chitti import AgentSpec
import click

@click.group(name="my_agent")
def commands():
    """My agent commands"""
    pass

class MyAgent:
    @hookimpl
    def get_agent_name(self) -> str:
        return "my_agent"
        
    @hookimpl
    def get_commands(self) -> click.Group:
        return commands
```

3. Register your plugin:
```python
# setup.py
setup(
    name="my-chitti-plugin",
    entry_points={
        "chitti.providers": [
            "my_provider=my_package.provider:MyProvider"
        ],
        "chitti.agents": [
            "my_agent=my_package.agent:MyAgent"
        ]
    }
)
```

### Creating a New Agent

1. Create from template:
```bash
# Create new agent from template
chitti agents create my_agent

# Or manually:
git clone https://github.com/sakthiram/chitti.git
cp -r templates/chitti-{agent}-agent chitti-my_agent-agent
cd chitti-my_agent-agent
```

2. Implement agent logic:
```python
# src/chitti_my_agent_agent/agent.py

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"
    
    async def execute_specific_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Implement your agent's task execution logic here"""
        # Your implementation
        return {
            "output": "task output",
            "suggestion": "suggested action",
            "success": True,
            "executed": True
        }
```

3. Customize prompts:
```python
# src/chitti_my_agent_agent/prompts.py

SYSTEM_PROMPT = """You are a specialized my_agent with capabilities:
1. [List your agent's capabilities]
2. [Add more capabilities]
"""

EXECUTION_PROMPT = """Task: {task}
Context: {context}
History: {history}

Suggest the most appropriate action for this task."""
```

4. Install and test:
```bash
# Install in development mode
pip install -e .

# Test your agent
chitti my_agent run "test task"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

Apache-2.0 license - see LICENSE file for details

