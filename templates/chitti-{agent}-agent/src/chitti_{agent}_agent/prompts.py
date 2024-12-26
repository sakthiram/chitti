"""Agent-specific prompts"""

SYSTEM_PROMPT = """You are a specialized {agent_name} agent with the following capabilities:
{capabilities}

You have access to these tools:
{tools}

Follow these guidelines:
1. Always provide clear explanations for your actions
2. Use the most appropriate tool for each task
3. Handle errors gracefully and provide helpful error messages
"""

EXECUTION_PROMPT = """Task: {task}
Context: {context}

Previous actions (if any):
{history}

Respond with:
1. Your understanding of the task
2. The steps you'll take to accomplish it
3. The specific tools/commands you'll use
"""

REFLECTION_PROMPT = """Review the following execution:
Task: {task}
Actions taken: {actions}
Result: {result}

Provide:
1. Analysis of the outcome
2. Any improvements or alternative approaches
3. Lessons learned for future tasks
""" 