# Chitti Agent Template

This template provides a standardized way to create new agents for the Chitti framework. It includes:

- Base agent class with LLM integration
- Standardized prompt templates
- FastAPI server setup
- Click CLI integration
- Plugin registration

## Creating a New Agent

```bash
# Create a new agent
python create_agent.py my_agent

# Install the new agent
cd chitti-my_agent-agent
pip install -e .
```

## Template Structure

```
chitti-{agent}-agent/
├── src/
│   └── chitti_{agent}_agent/
│       ├── __init__.py
│       ├── agent.py      # Main agent implementation
│       ├── base.py       # Base agent class
│       ├── prompts.py    # Agent-specific prompts
│       └── server.py     # FastAPI server
├── tests/               # Add your tests here
└── setup.py            # Package setup
```

## Customizing Your Agent

1. Edit `agent.py`:
   - Override the `name` property
   - Implement agent-specific logic in `format_prompt`
   - Add custom routes and commands

2. Edit `prompts.py`:
   - Customize prompts for your agent's needs
   - Add new prompt templates

3. Add Dependencies:
   - Update `setup.py` with additional requirements

## Integration with Chitti

The agent will automatically register with Chitti through the entry point in `setup.py`:

```python
entry_points={
    "chitti.agents": [
        "{agent}=chitti_{agent}_agent.agent:CustomAgent"
    ]
}
```

## Usage

After installation:

```python
from chitti_{agent}_agent import CustomAgent

# Create agent instance
agent = CustomAgent()

# Use via CLI
chitti {agent} execute "task"
chitti {agent} serve

# Use via API
# Start server:
chitti {agent} serve
# Then send requests to: http://localhost:8000/{agent}/execute/
```

## Best Practices

1. **LLM Integration**:
   - Use `execute_with_llm` for AI-powered decisions
   - Customize prompts for specific use cases

2. **Error Handling**:
   - Implement proper error handling in routes
   - Provide clear error messages

3. **Testing**:
   - Add tests for agent-specific logic
   - Test LLM integration
   - Test API endpoints

4. **Documentation**:
   - Document agent capabilities
   - Include usage examples
   - Document custom commands

## Example Agents

Check the examples directory for reference implementations:
- Bash Agent: Command execution
- Python Agent: Code execution
- Orchestrator Agent: Multi-agent coordination 