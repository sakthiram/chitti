#!/bin/bash
# Spawn static agent in tmux window (local or remote)
# Agents must be defined in .claude/agents/*.md or .kiro/agents/*.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
TASK_NAME=""
AGENT=""
WINDOW=""
HANDOFF=""
REMOTE=""
CWD=""
CLI="kiro"
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

if [[ -z "$TASK_NAME" ]] || [[ -z "$AGENT" ]] || [[ -z "$WINDOW" ]]; then
  echo "Usage: $0 --task <name> --agent <type> --window <num> [options]"
  echo ""
  echo "Options:"
  echo "  --topic <short-name>       Topic for window name (e.g., explore-hotplug)"
  echo "  --handoff <file>           Handoff file with instructions"
  echo "  --remote user@host:/path   Remote SSH target for dev/architect"
  echo "  --cwd <path>               Working directory (default: project root)"
  echo "  --cli claude|kiro          CLI to use (default: claude)"
  echo "  --project <path>           Project directory (default: pwd)"
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

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Error: PM session not found: ${SESSION}"
  exit 1
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
  PROMPT="${AGENT_INSTRUCTION}You are the ${AGENT} agent for task: ${TASK_NAME}
Task directory: ${TASK_DIR}/
Read your instructions from: handoffs/${HANDOFF}
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

# Remote spawn
if [[ -n "$REMOTE" ]]; then
  SSH_TARGET="${REMOTE%%:*}"
  REMOTE_PATH="${REMOTE#*:}"
  REMOTE_TASK_DIR="${REMOTE_PATH}/tasks/${TASK_NAME}"

  echo "Setting up remote agent on ${SSH_TARGET}..."

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

  # Copy handoff to remote if provided
  if [[ -n "$HANDOFF" ]] && [[ -f "${TASK_DIR}/${HANDOFF}" ]]; then
    scp "${TASK_DIR}/${HANDOFF}" "${SSH_TARGET}:${REMOTE_TASK_DIR}/${HANDOFF}"
  fi

  # Start rsync cron (FROM remote to local)
  CRON_CMD="*/2 * * * * rsync -avz ${SSH_TARGET}:${REMOTE_TASK_DIR}/ ${TASK_DIR}/ 2>/dev/null"
  if ! crontab -l 2>/dev/null | grep -q "${TASK_NAME}.*${SSH_TARGET}"; then
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "Started rsync cron: ${SSH_TARGET} -> local (every 2 min)"
  fi

  # Remote tmux session name (unique per task+agent+topic)
  if [[ -n "$TOPIC" ]]; then
    REMOTE_SESSION="agent-${TASK_NAME}-${AGENT}-${TOPIC}"
  else
    REMOTE_SESSION="agent-${TASK_NAME}-${AGENT}"
  fi

  # Step 1: Create detached tmux session on remote (or reuse existing)
  # This allows the agent to survive SSH disconnection
  if ssh "$SSH_TARGET" "tmux has-session -t '${REMOTE_SESSION}' 2>/dev/null"; then
    echo "Remote tmux session '${REMOTE_SESSION}' already exists, will attach..."
  else
    echo "Creating remote tmux session '${REMOTE_SESSION}'..."
    # TODO: Remove --trust-all-tools / --dangerously-skip-permissions once proper tool configs are set up
    if [[ "$CLI" == "kiro" ]]; then
      ssh "$SSH_TARGET" "cd ${REMOTE_PATH} && tmux new-session -d -s '${REMOTE_SESSION}' 'kiro-cli chat --trust-all-tools --agent ${AGENT}'"
    else
      ssh "$SSH_TARGET" "cd ${REMOTE_PATH} && tmux new-session -d -s '${REMOTE_SESSION}' 'claude --dangerously-skip-permissions'"
    fi
  fi

  # Step 2: Create local window that attaches to remote tmux session
  tmux new-window -t "${SESSION}:${WINDOW}" -n "${WINDOW_NAME}"
  tmux send-keys -t "${SESSION}:${WINDOW}" "ssh -t ${SSH_TARGET} 'tmux attach -t ${REMOTE_SESSION}'"
  tmux send-keys -t "${SESSION}:${WINDOW}" C-m

  # Step 3: Wait for CLI to load, then send the context prompt
  sleep 8
  tmux send-keys -t "${SESSION}:${WINDOW}" -l "${PROMPT}"
  sleep 1
  tmux send-keys -t "${SESSION}:${WINDOW}" C-m

  echo "Spawned remote ${AGENT} agent in window ${WINDOW} (remote tmux: ${REMOTE_SESSION})"
  echo "Remote agent survives SSH disconnection. Reconnect with: ssh -t ${SSH_TARGET} 'tmux attach -t ${REMOTE_SESSION}'"

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
