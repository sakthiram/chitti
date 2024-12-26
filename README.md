# Chitti: A Modular AI Ecosystem

Chitti is an extensible AI ecosystem that allows you to interact with various AI models and agents through a unified interface. It provides both CLI and API access, with support for plugins to extend its functionality.

## Features

### Core Features
- 🔌 **Plugin System**: Easily extend with new providers, agents, and tools
- 🤖 **Multiple Model Support**: Use different AI models through a unified interface
- 🛠️ **CLI & API**: Access functionality through both CLI and REST API
- ⚙️ **Configuration Management**: Flexible settings for providers and models

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

# Using pip
pip install chitti
```

## Usage

### CLI Commands

1. Generate text using AI models:
```bash
# Using default provider and model
chitti prompt generate "What is Python?"

# Using specific model
chitti prompt generate --model "anthropic.claude-3-sonnet-20240229-v1:0" "What is Python?"
```

2. Configure settings:
```bash
# View current settings
chitti config info

# Set default provider
chitti config set-provider bedrock

# Set default model
chitti config set-model "anthropic.claude-3-sonnet-20240229-v1:0"
```

3. Using agents (when installed):
```bash
# Use bash agent
chitti bash prompt "Create a script to backup files"
chitti bash serve  # Start bash agent server
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

# Get settings
curl -X GET "http://localhost:8000/settings"
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

Apache-2.0 license - see LICENSE file for details

