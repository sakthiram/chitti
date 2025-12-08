#!/bin/bash
# Send message to a remote agent via SSH + tmux
#
# Usage: send_to_remote_agent.sh --task <name> --window <num> --remote user@host --message "your message"
#
# The remote session name is: task-{TASK_NAME}-agents
# Each agent runs in its designated window number

set -e

TASK_NAME=""
WINDOW=""
REMOTE=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --task) TASK_NAME="$2"; shift 2 ;;
    --window) WINDOW="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --message|-m) MESSAGE="$2"; shift 2 ;;
    --help|-h)
      echo "Send message to remote agent"
      echo ""
      echo "Usage: $0 --task <name> --window <num> --remote user@host --message 'your message'"
      echo ""
      echo "Options:"
      echo "  --task <name>        Task name (required)"
      echo "  --window <num>       Window number where agent runs (required)"
      echo "  --remote <host>      SSH target user@host (required)"
      echo "  --message, -m <msg>  Message to send (required)"
      echo ""
      echo "The script sends to: task-{task}-agents:{window}"
      echo ""
      echo "Window numbers are sequential based on spawn order."
      echo "Check pm_state.json for agent window assignments."
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$TASK_NAME" ]] || [[ -z "$WINDOW" ]] || [[ -z "$REMOTE" ]] || [[ -z "$MESSAGE" ]]; then
  echo "Error: Missing required arguments"
  echo "Usage: $0 --task <name> --window <num> --remote user@host --message 'your message'"
  exit 1
fi

# Extract just the host part (in case user@host:/path was passed)
SSH_TARGET="${REMOTE%%:*}"

# Remote session name
REMOTE_SESSION="task-${TASK_NAME}-agents"

echo "Sending to ${SSH_TARGET} -> ${REMOTE_SESSION}:${WINDOW}"

# Send the message
ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' -l '${MESSAGE}'"
sleep 0.5
ssh "$SSH_TARGET" "tmux send-keys -t '${REMOTE_SESSION}:${WINDOW}' C-m"

echo "Message sent successfully"
