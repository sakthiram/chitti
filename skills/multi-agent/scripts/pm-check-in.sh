#!/bin/bash
# Trigger PM check-in: nudge scribe first, then PM

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TASK_NAME=""
PROJECT_DIR="$(pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    *)
      if [[ -z "$TASK_NAME" ]]; then TASK_NAME="$1"; fi
      shift
      ;;
  esac
done

if [[ -z "$TASK_NAME" ]]; then
  echo "Usage: $0 <task-name> [--project <path>]"
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

# Nudge PM (PM now handles progress tracking directly)
echo "Nudging PM..."
tmux send-keys -t "${SESSION}:pm" ""
tmux send-keys -t "${SESSION}:pm" C-m
sleep 1

PM_MESSAGE="# PM Check-in: ${TIMESTAMP}

Check status and make decisions:

1. Scan handoffs/ for new files since last check-in
2. Check pm_state.json for current phase and spawned agents
3. Evaluate progress signals:
   - Any agent completed? (STATUS: COMPLETE in handoff)
   - Any agent blocked? (STATUS: BLOCKED)
   - Any agent needs review? (STATUS: NEEDS_REVIEW)
   - Missing handoff? Use capture-pane fallback
4. Check human_review_gates:
   - If plan gate is 'awaiting', STOP and wait for human
5. Decide next action:
   - Spawn next agent if current complete
   - Send follow-up if agent needs guidance
   - Kill and respawn if context is stale
   - Mark task BLOCKED if truly stuck
6. Update pm_state.json with last_checkin timestamp
7. Update progress.md with current state

Current time: ${TIMESTAMP}"

tmux send-keys -t "${SESSION}:pm" -l "${PM_MESSAGE}"
sleep 1
tmux send-keys -t "${SESSION}:pm" C-m

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
