#!/bin/bash
# Spawn static agent in tmux window (local or remote)
# Agents must be defined in .claude/agents/*.md or .kiro/agents/*.json
#
# Remote agents: Creates windows in a SINGLE remote tmux session per task
# - Session name: task-{TASK_NAME}-agents
# - Each agent gets its own window (by window number)
# - No local window created - use iTerm to attach to remote session
# - PM sends commands via SSH: ssh host "tmux send-keys -t session:window 'msg' Enter"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
TASK_NAME=""
AGENT=""
WINDOW=""
HANDOFF=""
REMOTE=""
CWD=""
CLI=""
PROJECT_DIR="$(pwd)"
TOPIC=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --task) TASK_NAME="$2"; shift 2 ;;
    --agent) AGENT="$2"; shift 2 ;;
    --window) WINDOW="$2"; shift 2 ;;
    --handoff) HANDOFF="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --cwd) CWD="$2"; shift 2 ;;
    --cli) CLI="$2"; shift 2 ;;
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --topic) TOPIC="$2"; shift 2 ;;
    *)
      # Positional args for backward compat: task agent window
      if [[ -z "$TASK_NAME" ]]; then TASK_NAME="$1"
      elif [[ -z "$AGENT" ]]; then AGENT="$1"
      elif [[ -z "$WINDOW" ]]; then WINDOW="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$TASK_NAME" ]] || [[ -z "$AGENT" ]] || [[ -z "$WINDOW" ]] || [[ -z "$HANDOFF" ]] || [[ -z "$CLI" ]]; then
  echo "Usage: $0 --task <name> --agent <type> --window <num> --handoff <file> --cli <claude|kiro> [options]"
  echo ""
  echo "Required:"
  echo "  --task <name>              Task name"
  echo "  --agent <type>             Agent type (explore, plan, dev, etc.)"
  echo "  --window <num>             Window number"
  echo "  --handoff <file>           Handoff file with instructions"
  echo "  --cli claude|kiro          CLI to use (REQUIRED)"
  echo ""
  echo "Options:"
  echo "  --topic <short-name>       Topic for window name (e.g., explore-hotplug)"
  echo "  --remote user@host:/path   Remote SSH target for dev/architect"
  echo "  --cwd <path>               Working directory (default: project root)"
  echo "  --project <path>           Project directory (default: pwd)"
  echo ""
  echo "Remote agents:"
  echo "  All remote agents for a task share ONE tmux session: task-{name}-agents"
  echo "  Each agent gets its own window within that session"
  echo "  Attach from iTerm: ssh -t host 'tmux attach -t task-{name}-agents'"
  echo ""
  echo "Agents must be defined in:"
  echo "  claude: <project>/.claude/agents/<agent>.md"
  echo "  kiro:   <project>/.kiro/agents/<agent>.json"
  exit 1
fi

# Window name: agent-topic if topic provided, else just agent
if [[ -n "$TOPIC" ]]; then
  WINDOW_NAME="${AGENT}-${TOPIC}"
else
  WINDOW_NAME="${AGENT}"
fi

TASK_DIR="${PROJECT_DIR}/tasks/${TASK_NAME}"
SESSION="task-${TASK_NAME}-pm"

# For local spawn, PM session must exist
if [[ -z "$REMOTE" ]]; then
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Error: PM session not found: ${SESSION}"
    exit 1
  fi
fi

# Check agent exists
if [[ "$CLI" == "kiro" ]]; then
  AGENT_FILE="${PROJECT_DIR}/.kiro/agents/${AGENT}.json"
else
  AGENT_FILE="${PROJECT_DIR}/.claude/agents/${AGENT}.md"
fi

if [[ ! -f "$AGENT_FILE" ]]; then
  echo "Error: Agent not found: ${AGENT_FILE}"
  echo "Run 'setup-agents ${PROJECT_DIR}' to create agents."
  exit 1
fi

# Default working directory is project root (not task dir)
WORK_DIR="${CWD:-$PROJECT_DIR}"

# Generate timestamp for handoff output
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT_HANDOFF="handoffs/${AGENT}-${TIMESTAMP}.md"

# Generate artifact directory path (namespaced by agent-topic)
if [[ -n "$TOPIC" ]]; then
  ARTIFACT_DIR="artifacts/${AGENT}-${TOPIC}"
else
  ARTIFACT_DIR="artifacts/${AGENT}"
fi

# Build prompt - for Claude CLI, instruct to use subagent
# (Kiro CLI uses --agent flag instead)
if [[ "$CLI" == "claude" ]]; then
  AGENT_INSTRUCTION="Use the ${AGENT} subagent to complete the task.

"
else
  AGENT_INSTRUCTION=""
fi

if [[ -n "$HANDOFF" ]]; then
  # Extract just the filename from handoff path
  HANDOFF_BASENAME=$(basename "$HANDOFF")
  PROMPT="${AGENT_INSTRUCTION}You are the ${AGENT} agent for task: ${TASK_NAME}
Task directory: ${TASK_DIR}/
Read your instructions from: handoffs/${HANDOFF_BASENAME}
Write your handoff to: ${OUTPUT_HANDOFF}
Store artifacts in: ${ARTIFACT_DIR}/
Begin now."
else
  PROMPT="${AGENT_INSTRUCTION}You are the ${AGENT} agent for task: ${TASK_NAME}
Task directory: ${TASK_DIR}/
Write your handoff to: ${OUTPUT_HANDOFF}
Store artifacts in: ${ARTIFACT_DIR}/
Begin now."
fi

# Remote spawn - single session, multiple windows
if [[ -n "$REMOTE" ]]; then
  SSH_TARGET="${REMOTE%%:*}"
  REMOTE_PATH="${REMOTE#*:}"
  REMOTE_TASK_DIR="${REMOTE_PATH}/tasks/${TASK_NAME}"

  # Single remote session for ALL agents of this task
  REMOTE_SESSION="task-${TASK_NAME}-agents"

  echo "Setting up remote agent on ${SSH_TARGET}..."
  echo "Remote session: ${REMOTE_SESSION}, window: ${WINDOW} (${WINDOW_NAME})"

  # Create remote directories
  ssh "$SSH_TARGET" "mkdir -p ${REMOTE_TASK_DIR}/{handoffs,artifacts,scratchpad}"

  # Create agent-specific artifact directory
  ssh "$SSH_TARGET" "mkdir -p ${REMOTE_TASK_DIR}/${ARTIFACT_DIR}"

  # Copy agent file to remote
  if [[ "$CLI" == "kiro" ]]; then
    REMOTE_AGENT_DIR="${REMOTE_PATH}/.kiro/agents"
    ssh "$SSH_TARGET" "mkdir -p ${REMOTE_AGENT_DIR}"
    scp "$AGENT_FILE" "${SSH_TARGET}:${REMOTE_AGENT_DIR}/"
  else
    REMOTE_AGENT_DIR="${REMOTE_PATH}/.claude/agents"
    ssh "$SSH_TARGET" "mkdir -p ${REMOTE_AGENT_DIR}"
    scp "$AGENT_FILE" "${SSH_TARGET}:${REMOTE_AGENT_DIR}/"
  fi

  # Copy handoff to remote if provided (handle both full path and relative)
  if [[ -n "$HANDOFF" ]]; then
    HANDOFF_BASENAME=$(basename "$HANDOFF")
    if [[ -f "$HANDOFF" ]]; then
      scp "$HANDOFF" "${SSH_TARGET}:${REMOTE_TASK_DIR}/handoffs/${HANDOFF_BASENAME}"
    elif [[ -f "${TASK_DIR}/handoffs/${HANDOFF_BASENAME}" ]]; then
      scp "${TASK_DIR}/handoffs/${HANDOFF_BASENAME}" "${SSH_TARGET}:${REMOTE_TASK_DIR}/handoffs/"
    fi
  fi

  # NOTE: No automatic rsync/cron - PM must use sync_from_remote.sh to pull results

  # Step 1: Create or reuse single remote tmux session for this task
  if ssh "$SSH_TARGET" "tmux has-session -t '${REMOTE_SESSION}' 2>/dev/null"; then
    echo "Remote session '${REMOTE_SESSION}' exists"
  else
    echo "Creating remote tmux session '${REMOTE_SESSION}'..."
    ssh "$SSH_TARGET" "cd ${REMOTE_PATH} && tmux new-session -d -s '${REMOTE_SESSION}' -n 'main' 'zsh -l'"
    sleep 1
  fi

  # Step 2: Create new window in remote session for this agent
  # Check if window already exists
  if ssh "$SSH_TARGET" "tmux list-windows -t '${REMOTE_SESSION}' | grep -q '^${WINDOW}:'"; then
    echo "Warning: Window ${WINDOW} already exists in ${REMOTE_SESSION}"
    echo "Sending prompt to existing window..."
  else
    echo "Creating window ${WINDOW} (${WINDOW_NAME}) in remote session..."
    ssh "$SSH_TARGET" "tmux new-window -t '${REMOTE_SESSION}:${WINDOW}' -n '${WINDOW_NAME}' -c '${REMOTE_PATH}' 'zsh -l'"
    sleep 1

    # Start CLI in the new window
    if [[ "$CLI" == "kiro" ]]; then
      ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' 'kiro-cli chat --trust-all-tools --agent ${AGENT}' C-m"
    else
      ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' 'claude --dangerously-skip-permissions' C-m"
    fi

    # Wait for CLI to load
    echo "Waiting for CLI to load..."
    sleep 10
  fi

  # Step 3: Send the context prompt to agent
  ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' -l '${PROMPT}'"
  sleep 1
  ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' C-m"

  echo ""
  echo "=========================================="
  echo "Remote agent spawned successfully!"
  echo "=========================================="
  echo "Session: ${REMOTE_SESSION}"
  echo "Window:  ${WINDOW} (${WINDOW_NAME})"
  echo ""
  echo "To monitor agents, open iTerm and run:"
  echo "  ssh -t ${SSH_TARGET} 'tmux attach -t ${REMOTE_SESSION}'"
  echo ""
  echo "To send commands to this agent:"
  echo "  ssh ${SSH_TARGET} \"tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' 'your message' Enter\""
  echo "=========================================="

else
  # Local spawn - working directory is project root by default
  tmux new-window -t "${SESSION}:${WINDOW}" -n "${WINDOW_NAME}" -c "${WORK_DIR}"

  # TODO: Remove --trust-all-tools / --dangerously-skip-permissions once proper tool configs are set up
  # C-m must be separate send-keys call
  if [[ "$CLI" == "kiro" ]]; then
    tmux send-keys -t "${SESSION}:${WINDOW}" "kiro-cli chat --trust-all-tools --agent ${AGENT}"
    tmux send-keys -t "${SESSION}:${WINDOW}" C-m
  else
    tmux send-keys -t "${SESSION}:${WINDOW}" "claude --dangerously-skip-permissions"
    tmux send-keys -t "${SESSION}:${WINDOW}" C-m
  fi

  # Wait for CLI to load, then send the context prompt
  sleep 12
  # Use tmux literal mode (-l) to avoid interpreting special chars
  tmux send-keys -t "${SESSION}:${WINDOW}" -l "${PROMPT}"
  sleep 1
  tmux send-keys -t "${SESSION}:${WINDOW}" C-m

  echo "Spawned ${WINDOW_NAME} agent in window ${WINDOW}"
fi
