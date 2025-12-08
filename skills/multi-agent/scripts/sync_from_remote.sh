#!/bin/bash
# Pull handoffs/artifacts from remote task directory
# Usage: sync_from_remote.sh --task <name> --remote user@host:/path [--project <path>]

set -e

TASK_NAME=""
REMOTE=""
PROJECT_DIR="$(pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --task) TASK_NAME="$2"; shift 2 ;;
    --remote) REMOTE="$2"; shift 2 ;;
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --help|-h)
      echo "Pull handoffs/artifacts from remote task directory"
      echo ""
      echo "Usage: $0 --task <name> --remote user@host:/path [--project <path>]"
      echo ""
      echo "Options:"
      echo "  --task <name>              Task name (required)"
      echo "  --remote user@host:/path   Remote SSH target (required)"
      echo "  --project <path>           Local project directory (default: pwd)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$TASK_NAME" ]] || [[ -z "$REMOTE" ]]; then
  echo "Error: --task and --remote are required"
  echo "Usage: $0 --task <name> --remote user@host:/path [--project <path>]"
  exit 1
fi

SSH_TARGET="${REMOTE%%:*}"
REMOTE_PATH="${REMOTE#*:}"
REMOTE_TASK_DIR="${REMOTE_PATH}/tasks/${TASK_NAME}"
LOCAL_TASK_DIR="${PROJECT_DIR}/tasks/${TASK_NAME}"

echo "Syncing from ${SSH_TARGET}:${REMOTE_TASK_DIR} to ${LOCAL_TASK_DIR}"

# Pull handoffs
scp -r "${SSH_TARGET}:${REMOTE_TASK_DIR}/handoffs/" "${LOCAL_TASK_DIR}/"
echo "Synced handoffs/"

# Pull artifacts
scp -r "${SSH_TARGET}:${REMOTE_TASK_DIR}/artifacts/" "${LOCAL_TASK_DIR}/"
echo "Synced artifacts/"

echo "Sync complete"
