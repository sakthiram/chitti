#!/bin/bash
# Spawn PM agent in new tmux session for a task
# Uses static PM agent from .claude/agents/pm.md or .kiro/agents/pm.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

TASK_NAME=$1
shift || true

# Parse flags
PROJECT_DIR="$(pwd)"
CLI="claude"

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --cli) CLI="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$TASK_NAME" ]]; then
  echo "Usage: $0 <task-name> [--project <path>] [--cli claude|kiro]"
  exit 1
fi

TASK_DIR="${PROJECT_DIR}/tasks/${TASK_NAME}"

if [[ ! -d "$TASK_DIR" ]]; then
  echo "Error: Task directory not found: $TASK_DIR"
  exit 1
fi

# Check PM agent exists
if [[ "$CLI" == "kiro" ]]; then
  AGENT_FILE="${PROJECT_DIR}/.kiro/agents/pm.json"
else
  AGENT_FILE="${PROJECT_DIR}/.claude/agents/pm.md"
fi

if [[ ! -f "$AGENT_FILE" ]]; then
  echo "Error: PM agent not found: ${AGENT_FILE}"
  echo "Run 'setup-agents ${PROJECT_DIR}' first."
  exit 1
fi

SESSION="task-${TASK_NAME}-pm"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Error: PM session already exists: ${SESSION}"
  echo "Attach: tmux attach -t ${SESSION}"
  exit 1
fi

# Create tmux session with project as cwd
tmux new-session -s "$SESSION" -n "pm" -d -c "$PROJECT_DIR"

# Context message for PM
CONTEXT="Task: ${TASK_NAME}
Task directory: ${TASK_DIR}/
Skill directory: ${SKILL_DIR}/

Start by reading task.md and planning your approach."

# TODO: Remove --trust-all-tools / --dangerously-skip-permissions once proper tool configs are set up
# Start CLI with PM agent
if [[ "$CLI" == "kiro" ]]; then
  tmux send-keys -t "${SESSION}:pm" "cd ${PROJECT_DIR} && kiro-cli --trust-all-tools --agent pm" C-m
else
  tmux send-keys -t "${SESSION}:pm" "cd ${PROJECT_DIR} && claude --dangerously-skip-permissions pm" C-m
fi

# Wait for agent to start, then send context
sleep 2
tmux send-keys -t "${SESSION}:pm" "${CONTEXT}" C-m

echo "PM session started: ${SESSION}"
echo "Attach: tmux attach -t ${SESSION}"
