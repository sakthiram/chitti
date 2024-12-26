# Chitti Agent Template

This template provides a standardized way to create new agents for the Chitti framework. It includes:

- Two-step task execution (suggest → execute)
- LLM integration for task suggestions
- Task history tracking
- CLI and API interfaces
- Context management

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
│       ├── prompts.py    # Agent-specific prompts
│       └── server.py     # FastAPI server
├── tests/               # Add your tests here
└── setup.py            # Package setup
```

## Customizing Your Agent

1. Edit `agent.py`:
   - Override the `name` property with your agent's name
   - Implement `execute_specific_task` with your agent's logic
   - Customize task history and context handling
   - Add any agent-specific routes or commands

2. Edit `prompts.py`:
   - Customize prompts for your agent's needs
   - Update system prompt capabilities
   - Modify execution prompt format

3. Update `setup.py`:
   - Add agent-specific dependencies
   - Set appropriate version and metadata

## Using Your Agent

### CLI Usage
```bash
# Get task suggestion
chitti my_agent run "your task description"

# The agent will:
# 1. Get suggestion from LLM
# 2. Show the suggested action
# 3. Ask for confirmation
# 4. Execute if approved
```

### API Usage
```bash
# Get task suggestion
curl -X POST "http://localhost:8000/my_agent/suggest" \
  -H "Content-Type: application/json" \
  -d '{"task": "your task", "context": {}}'

# Execute specific task
curl -X POST "http://localhost:8000/my_agent/execute" \
  -H "Content-Type: application/json" \
  -d '{"task": "specific task", "context": {}}'
```

## Agent Response Format

```python
AgentResponse(
    content="Task output or suggestion",
    success=True,
    metadata={
        "agent": "my_agent",
        "task": "original task",
        "executed": True/False
    },
    suggestions=[],  # For future use
    context_updates={
        "last_task": "executed/suggested task"
    }
)
```

## Task History Format

```python
{
    "task": "original task",
    "suggestion": "suggested action",
    "executed": True/False,
    "output": "execution output",  # If executed
    "success": True/False         # If executed
}
```

## Best Practices

1. **Safety First**: Always validate tasks and suggestions before execution
2. **Context Awareness**: Use the provided context in task suggestions
3. **History Management**: Keep relevant task history for better suggestions
4. **Error Handling**: Provide clear error messages and handle failures gracefully
5. **Documentation**: Document agent-specific parameters and capabilities 