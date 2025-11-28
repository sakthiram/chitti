#!/bin/bash
# Trigger PM check-in: nudge scribe first, then PM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TASK_NAME=""
PROJECT_DIR="$(pwd)"
SKIP_SCRIBE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --skip-scribe) SKIP_SCRIBE=true; shift ;;
    *)
      if [[ -z "$TASK_NAME" ]]; then TASK_NAME="$1"; fi
      shift
      ;;
  esac
done

if [[ -z "$TASK_NAME" ]]; then
  echo "Usage: $0 <task-name> [--project <path>] [--skip-scribe]"
  exit 1
fi

TASK_DIR="${PROJECT_DIR}/tasks/${TASK_NAME}"
SESSION="task-${TASK_NAME}-pm"

if [[ ! -d "$TASK_DIR" ]]; then
  echo "Error: Task not found: ${TASK_NAME}"
  exit 1
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "Error: PM session not running: ${SESSION}"
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
echo "PM Check-in: ${TASK_NAME} @ ${TIMESTAMP}"

# Step 1: Nudge scribe to update progress.md
if [[ "$SKIP_SCRIBE" != true ]]; then
  SCRIBE_WINDOW=$(tmux list-windows -t "$SESSION" -F "#{window_index}:#{window_name}" 2>/dev/null | grep ":scribe$" | cut -d: -f1)
  
  if [[ -n "$SCRIBE_WINDOW" ]]; then
    echo "Nudging scribe..."
    tmux send-keys -t "${SESSION}:${SCRIBE_WINDOW}" "" C-m
    tmux send-keys -t "${SESSION}:${SCRIBE_WINDOW}" \
      "Update progress.md now. Scan handoffs/ and artifacts/ for changes since last update. Write to ${TASK_DIR}/progress.md" C-m
    
    # Brief wait for scribe to process
    sleep 3
  fi
fi

# Step 2: Nudge PM
echo "Nudging PM..."
tmux send-keys -t "${SESSION}:pm" "" C-m
tmux send-keys -t "${SESSION}:pm" \
  "# PM Check-in: ${TIMESTAMP}

Check status and make decisions:

1. Read progress.md for high-level status (from scribe)
2. Scan handoffs/ for new files since last check-in
3. Check pm_state.json for current phase and spawned agents
4. Evaluate progress signals:
   - Any agent completed? (STATUS: COMPLETE in handoff)
   - Any agent blocked? (STATUS: BLOCKED)
   - Any agent needs review? (STATUS: NEEDS_REVIEW)
5. Decide next action:
   - Spawn next agent if current complete
   - Send follow-up if agent needs guidance
   - Kill and respawn if context is stale
   - Mark task BLOCKED if truly stuck
6. Update pm_state.json with last_checkin timestamp

Current time: ${TIMESTAMP}" C-m

# Update last_checkin in pm_state.json
if [[ -f "${TASK_DIR}/pm_state.json" ]]; then
  jq --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '.last_checkin = $ts' \
    "${TASK_DIR}/pm_state.json" > "${TASK_DIR}/pm_state.json.tmp" \
    && mv "${TASK_DIR}/pm_state.json.tmp" "${TASK_DIR}/pm_state.json"
fi

echo ""
echo "✅ Check-in sent"
echo ""
echo "View response: tmux attach -t ${SESSION}"
echo "Check status:  ${SCRIPT_DIR}/task status ${TASK_NAME}"
