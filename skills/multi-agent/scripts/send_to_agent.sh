#!/bin/bash
# Send follow-up instructions to existing agent window

set -e

TASK_NAME=""
AGENT=""
HANDOFF=""
MESSAGE=""
PROJECT_DIR="$(pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --task) TASK_NAME="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --handoff) HANDOFF="$2"; shift 2 ;;
    --message) MESSAGE="$2"; shift 2 ;;
    --project) PROJECT_DIR="$2"; shift 2 ;;
    *)
      # Positional: task agent handoff
      if [[ -z "$TASK_NAME" ]]; then TASK_NAME="$1"
      elif [[ -z "$AGENT" ]]; then AGENT="$1"
      elif [[ -z "$HANDOFF" ]]; then HANDOFF="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$TASK_NAME" ]] || [[ -z "$AGENT" ]]; then
  echo "Usage: $0 --task <name> --agent <type> [--handoff <file>] [--message <text>]"
  echo "   or: $0 <task-name> <agent> [handoff-file]"
  exit 1
fi

SESSION="task-${TASK_NAME}-pm"
TASK_DIR="${PROJECT_DIR}/tasks/${TASK_NAME}"

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Error: PM session not found: ${SESSION}"
  exit 1
fi

# Find window by agent name
WINDOW=$(tmux list-windows -t "$SESSION" -F "#{window_index}:#{window_name}" 2>/dev/null | grep ":${AGENT}$" | cut -d: -f1)

if [[ -z "$WINDOW" ]]; then
  echo "Error: Agent window not found: ${AGENT}"
  echo "Available windows:"
  tmux list-windows -t "$SESSION" -F "  #{window_index}: #{window_name}"
  exit 1
fi

# Build message
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
INSTRUCTION=""

if [[ -n "$HANDOFF" ]]; then
  INSTRUCTION="Read and execute new instructions: ${HANDOFF}

Remember to write your output to: handoffs/${AGENT}-${TIMESTAMP}.md"
elif [[ -n "$MESSAGE" ]]; then
  INSTRUCTION="${MESSAGE}

Write output to: handoffs/${AGENT}-${TIMESTAMP}.md"
else
  echo "Error: Must provide --handoff or --message"
  exit 1
fi

# Send to agent
# First send empty enter to ensure clean prompt, then send instruction
tmux send-keys -t "${SESSION}:${WINDOW}" ""
tmux send-keys -t "${SESSION}:${WINDOW}" C-m
sleep 1
# Use -l for literal mode to preserve multiline text
tmux send-keys -t "${SESSION}:${WINDOW}" -l "${INSTRUCTION}"
sleep 1
tmux send-keys -t "${SESSION}:${WINDOW}" C-m

echo "Sent instructions to ${AGENT} agent (window ${WINDOW})"
