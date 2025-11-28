# Implementation Plan: Multi-Agent Orchestrator

## Current State

Existing scripts provide good foundation:
- `scripts/task` - CLI with start/list/status/attach/stop/logs/ui
- `scripts/spawn_pm.sh` - Spawns PM in tmux session
- `scripts/spawn_agent.sh` - Spawns persistent agents (review, scribe)
- `scripts/spawn_inline_agent.sh` - Spawns inline agents with --agents JSON
- `scripts/pm-check-in.sh` - Nudges PM to check status
- `SKILL.md` - Comprehensive PM instructions
- `references/agent-prompts/` - Templates for agents

## Key Clarifications from Discussion

1. **Agent sessions stay alive** - PM sends follow-up instructions to same session
2. **PM kills/respawns only when** context is stale or subtask complete
3. **Scribe is LLM agent** (persistent, like review)
4. **Device access is local** - only dev/architect can be remote
5. **CWD defined in task.md** - can be local path or `user@host:/path`
6. **Multi-agent skill is project-agnostic** - tasks/skills in project dir
7. **Use `C-m` not `Enter`** for tmux send-keys

## Gaps to Address

### 1. Project-Aware Task Management

**Current:** `task start` creates tasks in skill directory
**Needed:** Create tasks in `<project>/tasks/`, use `--project` flag

**Changes to `scripts/task`:**
```bash
# Add --project flag (default: current directory)
PROJECT_DIR="${PROJECT:-$(pwd)}"
TASKS_DIR="${PROJECT_DIR}/tasks"

# task start should:
# 1. Prompt for task details (goal, cwd, skills needed)
# 2. Create task.md with user input
# 3. Support cwd config for dev/architect agents
```

### 2. Handoff Document Protocol

**Current:** Handoffs named by content (research.md, plan.md, PR.md)
**Needed:** Timestamped naming for PM to track new handoffs

**Naming convention:**
```
handoffs/{agent}-{YYYYMMDD}-{HHMMSS}.md
```

**Changes:**
- Update agent prompts to use timestamped output names
- Add `last_checkin` to pm_state.json
- PM filters handoffs by mtime > last_checkin

### 3. Send Instructions to Existing Agent

**Current:** `spawn_agent.sh` creates new window
**Needed:** Script to send follow-up instructions to existing agent

**New script: `scripts/send_to_agent.sh`**
```bash
#!/bin/bash
# Send instructions to existing agent window
TASK_NAME=$1
AGENT=$2
HANDOFF_FILE=$3

SESSION="task-${TASK_NAME}-pm"
# Find window by name
WINDOW=$(tmux list-windows -t "$SESSION" -F "#{window_index}:#{window_name}" | grep ":${AGENT}$" | cut -d: -f1)

tmux send-keys -t "${SESSION}:${WINDOW}" \
  "Read and execute: ${HANDOFF_FILE}" C-m
```

### 4. Remote Coding Support

**Current:** No remote support
**Needed:** SSH spawn + rsync for dev/architect

**Changes to `scripts/spawn_agent.sh`:**
```bash
# Add --remote flag
if [[ -n "$REMOTE" ]]; then
  # Parse user@host:/path
  SSH_TARGET="${REMOTE%%:*}"
  REMOTE_PATH="${REMOTE#*:}"
  
  # Create remote task directory
  ssh "$SSH_TARGET" "mkdir -p ${REMOTE_PATH}/tasks/${TASK_NAME}/{handoffs,artifacts,scratchpad}"
  
  # Copy handoff to remote
  scp "${HANDOFF_FILE}" "${SSH_TARGET}:${REMOTE_PATH}/tasks/${TASK_NAME}/handoffs/"
  
  # Start rsync cron (FROM remote)
  CRON_CMD="*/2 * * * * rsync -avz ${SSH_TARGET}:${REMOTE_PATH}/tasks/${TASK_NAME}/ ${PROJECT_DIR}/tasks/${TASK_NAME}/"
  (crontab -l 2>/dev/null | grep -v "${TASK_NAME}"; echo "$CRON_CMD") | crontab -
  
  # Spawn agent on remote via SSH
  ssh "$SSH_TARGET" "cd ${REMOTE_PATH} && tmux new-session -d -s task-${TASK_NAME}-${AGENT} && tmux send-keys -t task-${TASK_NAME}-${AGENT} 'claude --prompt \"...\"' C-m"
fi
```

### 5. Cleanup Script

**Current:** `task stop` kills tmux session
**Needed:** Also stop rsync cron, clean up remote

**Changes to `scripts/task` cmd_stop:**
```bash
# Remove rsync cron entries for this task
crontab -l 2>/dev/null | grep -v "${TASK_NAME}" | crontab -

# Kill remote tmux sessions if any
# (read remote config from task.md or pm_state.json)
```

### 6. Scribe Agent

**Current:** Mentioned but not fully implemented
**Needed:** Scribe agent that reads handoffs/artifacts and writes progress.md

**Create: `references/agent-prompts/scribe-template.txt`**
```
You are the Scribe agent for task: {TASK_NAME}

## Your Role
Maintain high-level progress view by reading handoffs and artifacts.

## On Each Check-in
1. Scan handoffs/ for files modified since last update
2. Read new handoffs, extract status and completed work
3. Scan artifacts/ for new files
4. Update progress.md with current state

## Output: progress.md
```markdown
# Task Progress: {task_name}
**Last Updated:** {timestamp}

## Recent Activity
- {handoff}: {summary}

## Milestone Summary
| Milestone | Status | Last Handoff | Notes |
|-----------|--------|--------------|-------|

## Current Blockers
{blockers or "None"}

## Artifacts Generated
- {path} ({time})
```

## Do NOT
- Talk to other agents
- Execute tasks
- Modify handoffs or artifacts
```

### 7. Agent Preamble

**Current:** Agents get task-specific prompt only
**Needed:** Standard preamble with protocol + task-specific instructions

**Update spawn scripts to inject preamble:**
```bash
PREAMBLE="You are a ${AGENT} agent for task: ${TASK_NAME}

## Protocol
- Write handoff when done: handoffs/${AGENT}-\$(date +%Y%m%d-%H%M%S).md
- Include: STATUS (COMPLETE|BLOCKED|NEEDS_REVIEW), completed work, artifacts list
- Do NOT communicate with other agents directly

## Your Instructions
"

# Combine preamble + task-specific prompt
FULL_PROMPT="${PREAMBLE}${TASK_PROMPT}"
```

### 8. CLI Flag for Claude vs Q

**Current:** Hardcoded `claude`
**Needed:** `--cli claude|q` flag

**Changes:**
```bash
CLI="${CLI:-claude}"  # Default to claude
# Use throughout: $CLI instead of claude
```

---

## Implementation Phases

### Phase 1: Core Updates (Week 1)

1. **Update `scripts/task start`**
   - Add `--project` flag (default: pwd)
   - Prompt for task details (goal, dev/architect cwd, skills)
   - Generate task.md from user input
   - Support `cwd: user@host:/path` in task.md

2. **Update handoff naming**
   - Timestamped: `{agent}-{YYYYMMDD}-{HHMMSS}.md`
   - Add `last_checkin` to pm_state.json
   - Update PM to filter by mtime

3. **Create `scripts/send_to_agent.sh`**
   - Send follow-up instructions to existing agent window
   - PM uses this instead of respawning for follow-ups

### Phase 2: Agent Protocol (Week 2)

4. **Add agent preamble injection**
   - Standard protocol in all spawn scripts
   - Timestamped handoff output
   - No direct agent communication rule

5. **Create scribe agent**
   - `references/agent-prompts/scribe-template.txt`
   - Reads handoffs/artifacts by mtime
   - Writes progress.md

6. **Update PM template**
   - Use `send_to_agent.sh` for follow-ups
   - Kill/respawn only when context stale
   - Read progress.md from scribe

### Phase 3: Remote Support (Week 3)

7. **Add remote spawn support**
   - Parse `cwd: user@host:/path` from task.md
   - SSH to create remote task directory
   - Copy handoff to remote
   - Start rsync cron (FROM remote)
   - Spawn agent on remote

8. **Update cleanup**
   - Remove rsync cron on task stop
   - Kill remote tmux sessions

### Phase 4: Polish (Week 4)

9. **Add `--cli` flag**
   - Support claude vs q CLI
   - Default to claude

10. **Error handling**
    - Detect crashed agents (no handoff + tmux gone)
    - PM retry logic

11. **Update SKILL.md and docs**
    - Reflect all changes
    - Add examples

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `scripts/task` | Update | Add --project, prompt for task details, cleanup cron |
| `scripts/spawn_pm.sh` | Update | Add --cli flag, preamble injection |
| `scripts/spawn_agent.sh` | Update | Add --remote, --cli, preamble injection |
| `scripts/spawn_inline_agent.sh` | Update | Add --cli, preamble injection |
| `scripts/send_to_agent.sh` | Create | Send follow-up to existing agent |
| `scripts/pm-check-in.sh` | Update | Trigger scribe before PM |
| `references/agent-prompts/scribe-template.txt` | Create | Scribe agent template |
| `references/agent-prompts/pm-template.txt` | Update | Use send_to_agent, progress.md |
| `references/task-template.md` | Update | Add cwd config section |
| `SKILL.md` | Update | Document new features |

---

## Decisions Finalized

1. **Scribe trigger**: Part of pm-check-in (scribe updates progress.md first, then PM reads it)

2. **Remote monitoring**: Rsync brings handoffs to local → PM reads local copy

3. **Agent config in task.md**: Per-agent struct with cwd, skills
   ```yaml
   dev:
     cwd: user@host:/remote/path
     skills: [project-skill]
   ```

4. **Multiple remotes**: Yes, per-agent cwd supported

5. **Handoff naming**: `{content}-{timestamp}.md` (e.g., `PR-20251127-153000.md`)

6. **Static agents only**: Agents defined in `.claude/agents/*.md` and `.kiro/agents/*.json`

7. **Agent setup**: `setup-agents` script generates both Claude and Kiro agents from shared templates

8. **Default cwd**: Project root (`<project>`) for all agents, not task directory

---

## Agent File Structure

**Shared templates** (in skill):
- `references/agent-prompts/system-prompts.md` - System prompts for all agents
- `references/claude_agents.md` - Claude-specific config (tools, model)
- `references/kiro_agents.md` - Kiro-specific config (tools, model)

**Generated agents** (in project):
- `.claude/agents/<agent>.md` - Markdown with YAML frontmatter
- `.kiro/agents/<agent>.json` - JSON format

---

## Implementation Status

### Completed ✅

1. `scripts/setup-agents` - Generates agents for both CLIs
2. `scripts/task` - Main CLI with --project, --cli flags
3. `scripts/spawn_agent.sh` - Spawns static agents (local/remote)
4. `scripts/send_to_agent.sh` - Send follow-up to existing agent
5. `scripts/spawn_pm.sh` - Spawns PM agent
6. `scripts/pm-check-in.sh` - Nudges scribe then PM
7. `references/agent-prompts/system-prompts.md` - Shared prompts
8. `references/claude_agents.md` - Claude agent configs
9. `references/kiro_agents.md` - Kiro agent configs
10. `SKILL.md` - Updated documentation
11. `README.md` - Updated documentation

### Removed ❌

- `scripts/spawn_inline_agent.sh` - No longer needed (static agents only)
- `pending_agent_spawn` in pm_state.json - No longer needed

### To Test

1. Run `setup-agents` on a test project
2. Verify Claude agent files generated correctly
3. Verify Kiro agent files generated correctly
4. Test `task start` flow
5. Test `spawn_agent.sh` with both CLIs
6. Test remote agent spawning
7. Test pm-check-in flow
