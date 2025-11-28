# Agent Orchestrator: Implementation Narrative
**Document Type:** Six-Pager | **Date:** November 27, 2025

---

## 1. Purpose

This document describes the implementation design for the Agent Orchestrator system. It covers architecture decisions, communication protocols, file structures, and agent behaviors that enable long-running (4-8 hour) autonomous agent workflows.

**Recommendation:** Approve the hub-and-spoke architecture where PM is the sole orchestrator, with file-based communication via timestamped handoff documents.

---

## 2. Background

Embedded engineers need AI agents that can run for hours without supervision. Current agent implementations fail because:
- Single agents hit context limits after 30-60 minutes
- Agents stop to ask questions, requiring constant human attention
- Without review cycles, agents produce low-quality outputs

The Agent Orchestrator solves this by coordinating specialized agents through a PM agent that manages lifecycle, communication, and decision-making.

---

## 3. Architecture

### 3.1 Project Structure

The multi-agent skill is **project-agnostic** and can be shared across projects. Project-specific content lives in the project directory.

```
~/.claude/skills/multi-agent/       # Shared framework (this skill)
├── scripts/                        # Setup & orchestration scripts
│   ├── task                        # Task management (start, status, stop)
│   ├── spawn_pm.sh                 # Spawn PM agent
│   ├── spawn_agent.sh              # Spawn execution agents
│   └── pm-check-in.sh              # Trigger PM check-in
├── references/                     # Agent prompts, protocols
└── SKILL.md                        # Skill documentation

<project>/                          # Project-specific
├── .claude/skills/                 # Project-specific skills
│   ├── device-access/              # e.g., how to access this project's devices
│   └── dds-testing/                # e.g., DDS-specific testing patterns
├── tasks/                          # Task instances
│   └── {task-name}/
│       ├── task.md                 # Requirements + CWD config
│       ├── pm_state.json
│       ├── progress.md
│       ├── handoffs/
│       ├── artifacts/
│       └── scratchpad/
└── src/                            # Project source code
```

**Key principle:** Multi-agent skill provides the framework. Project provides the context (skills, tasks, code).

### 3.2 Hub-and-Spoke Model

Only PM has orchestration logic. Other agents execute instructions and communicate only via handoff files.

```
                    ┌─────────────────┐
                    │   Human User    │
                    │   (task.md)     │
                    └────────┬────────┘
                             │ uses multi-agent skill
                             ▼
                    ┌─────────────────┐
                    │    PM Agent     │◄──── pm-check-in (every 10 min)
                    │  (orchestrator) │
                    │                 │
                    │ Uses skills:    │
                    │ - multi-agent   │
                    └────────┬────────┘
                             │ tmux messages
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   Explore   │   │    Plan     │   │  Architect  │
    │   (local)   │   │   (local)   │   │(local/remote)│
    └─────────────┘   └─────────────┘   └─────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │    Dev      │   │    Test     │   │   Review    │
    │(local/remote)│   │   (local)   │   │   (local)   │
    └─────────────┘   └─────────────┘   └─────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │ writes handoffs
                             ▼
                    ┌─────────────────┐
                    │    handoffs/    │
                    │    artifacts/   │
                    └────────┬────────┘
                             │ reads (by mtime)
                             ▼
                    ┌─────────────────┐
                    │  Scribe Agent   │───▶ progress.md
                    │  (local only)   │
                    └─────────────────┘
```

**Local vs Remote:**
- **Local agents**: Explore, Plan, Test, Review, Scribe (device access is local)
- **Local or Remote**: Dev, Architect (coding can be remote via SSH)
- Remote is defined per-task in task.md

### 3.3 Agent Roles

| Agent | Responsibility | Location | Inputs | Outputs |
|-------|---------------|----------|--------|---------|
| PM | Orchestrate workflow, spawn/terminate agents | Local | task.md, progress.md, handoffs/ | handoffs/pm-*.md |
| Explore | Analyze codebase, docs, existing artifacts | Local | PM handoff | Analysis artifacts |
| Plan | Design approach, break down tasks | Local | PM handoff, explore artifacts | Strategy artifacts |
| Architect | Design decisions, interfaces, structure | Local/Remote | PM handoff | Design artifacts |
| Dev | Implement code changes | Local/Remote | PM handoff, design artifacts | Code artifacts |
| Test | Deploy to devices, run tests, capture logs | Local | PM handoff, code artifacts | Test results |
| Review | Validate artifacts, provide feedback | Local | PM handoff, any artifacts | Review feedback |
| Scribe | Read handoffs/artifacts, write progress | Local | handoffs/, artifacts/ | progress.md |

### 3.4 Static Agents

All agents are **static files** generated by `setup-agents`:

**Claude** (`.claude/agents/<name>.md`):
```markdown
---
name: dev
description: Implement code changes according to plan
tools: Read, Write, Edit, Bash
model: sonnet
---

System prompt here...
```

**Kiro** (`.kiro/agents/<name>.json`):
```json
{
  "name": "dev",
  "description": "Implement code changes according to plan",
  "tools": ["read", "write", "edit", "bash"],
  "prompt": "System prompt here...",
  "model": "claude-sonnet-4"
}
```

**Agent lifecycle:**
1. `setup-agents` bootstraps default agents from skill templates
2. User customizes agents as needed (edit prompts, tools, add new agents)
3. PM spawns agents by name: `claude dev` or `kiro-cli --agent dev`
4. Re-running `setup-agents` only adds missing agents (no overwrite)

**Creating new agents:**
PM can create project-specific agents by writing to `.claude/agents/` or `.kiro/agents/`:
```bash
# Create a specialized agent
cat > .claude/agents/security-reviewer.md << 'EOF'
---
name: security-reviewer
description: Security-focused code review
tools: Read, Grep, Glob
---
You are a security reviewer. Focus on...
EOF
```

---

## 4. Communication Protocol

### 4.1 PM Check-in Cycle

Every 10 minutes (via cron or manual trigger):

1. PM reads `progress.md` (scribe's output)
2. PM scans `handoffs/` for files modified after `last_checkin` timestamp
3. PM decides next action based on signals
4. PM sends tmux message to target agent with handoff file location
5. Agent executes, writes handoff when done
6. Scribe reads new handoffs + artifacts, updates `progress.md`

```
┌─────────┐  tmux msg   ┌─────────┐  writes   ┌─────────────────┐
│   PM    │────────────▶│  Agent  │──────────▶│ handoffs/       │
└─────────┘             └─────────┘           │ {agent}-{ts}.md │
     ▲                                        └────────┬────────┘
     │                                                 │
     │  reads                                   reads  │
     │                                                 ▼
┌────┴────────┐                              ┌─────────────────┐
│ progress.md │◀─────────────────────────────│     Scribe      │
└─────────────┘         updates              └─────────────────┘
```

### 4.2 Handoff Document Naming

```
handoffs/{source_agent}-{YYYYMMDD}-{HHMMSS}.md
```

Examples:
- `handoffs/pm-20251127-153000.md` (PM's instructions)
- `handoffs/dev-20251127-154500.md` (Dev's completion report)

PM uses `last_checkin` from `pm_state.json` to filter new handoffs.

### 4.3 Handoff Document Structure

**PM → Agent (instructions):**
```markdown
# Handoff: pm
**Timestamp:** 2025-11-27 15:30:00 PST
**Target:** dev
**Status:** IN_PROGRESS

## Instructions
[What the agent should do]

## Context
[Background information]

## Skills to Load
- [skill-name-1]
- [skill-name-2]

## Success Criteria
[How to know when done]
```

**Agent → PM (completion):**
```markdown
# Handoff: dev
**Timestamp:** 2025-11-27 15:45:00 PST
**Status:** COMPLETE | BLOCKED | NEEDS_REVIEW

## Completed Work
[What was accomplished]

## Artifacts Generated
- artifacts/path/to/file1.py
- artifacts/path/to/file2.md

## Blockers (if BLOCKED)
[What prevented progress]

## Skill Gaps (if BLOCKED)
[What skill/context is missing]
```

---

## 5. File Structure

### 5.1 Task Directory

Tasks live in `<project>/tasks/`:

```
<project>/tasks/{task-name}/
├── task.md                         # Requirements + agent CWD config
├── pm_state.json                   # PM state (last_checkin, phase)
├── progress.md                     # Scribe output (updated each check-in)
├── handoffs/                       # Timestamped agent communication
│   ├── pm-20251127-090000.md
│   ├── explore-20251127-093000.md
│   └── ...
├── artifacts/                      # Generated outputs (mtime-based)
│   ├── analysis/
│   ├── design/
│   ├── code/
│   ├── tests/
│   └── reviews/
└── scratchpad/                     # Per-agent working files (ephemeral)
    ├── explore/
    ├── dev/
    └── ...
```

### 5.2 task.md CWD Configuration

task.md defines where agents operate. Default CWD is `<project>` (root of tasks dir).

**Generic task (default CWD):**
```markdown
# Task: Refactor logging module

## Goal
Improve logging performance across the codebase.

## Success Criteria
- Reduce log overhead by 50%
- All tests pass
```

**Task with specific CWD:**
```markdown
# Task: Optimize DDS writer pool

## Goal
Fix WriterPool exhaustion under high client load.

## Agent Config
cwd: /path/to/dds-module          # Local path for dev/architect
# OR
cwd: user@remote:/path/to/repo    # Remote SSH for dev/architect

## Success Criteria
- Reproduction test triggers crash
- Fix handles 100+ concurrent clients
```

When `cwd` includes `user@host:`, PM spawns dev/architect agents remotely via SSH.

### 5.3 Remote Coding Setup

For remote dev/architect agents:

1. PM creates task directory on remote: `ssh user@host "mkdir -p /path/tasks/{task}/{handoffs,artifacts,scratchpad}"`
2. PM sends handoff TO remote on-demand
3. PM starts cron for continuous sync FROM remote to local
4. Remote agent writes to remote `handoffs/` and `artifacts/`
5. Cron syncs to local so scribe can read

```
┌───────────────┐  on-demand TO   ┌────────────────┐
│  Local PM     │────────────────▶│  Remote        │
│               │                 │  Dev/Architect │
│               │◀────────────────│                │
└───────────────┘  cron FROM      └────────────────┘
                  (continuous)
```

**Cron setup:**
```bash
*/2 * * * * rsync -avz user@host:/path/tasks/{task}/ <project>/tasks/{task}/
```

**Note:** Device access (test agent) is always local. Only coding (dev/architect) can be remote.

---

## 6. Agent Spawn Protocol

### 6.1 Spawn Preamble

When PM spawns any agent, it includes this standard preamble:

```markdown
# Agent: {agent_type}
**Task:** {task_name}
**Spawned:** {timestamp}

## Protocol

### File Structure
Your working directory: {cwd}

Ensure this structure exists:
- {cwd}/tasks/{task}/handoffs/
- {cwd}/tasks/{task}/artifacts/{agent_type}/
- {cwd}/tasks/{task}/scratchpad/{agent_type}/

### When You Finish (or Get Blocked)
Write handoff to: handoffs/{agent_type}-{YYYYMMDD}-{HHMMSS}.md

Include:
- Status: COMPLETE | BLOCKED | NEEDS_REVIEW
- Completed Work
- Artifacts Generated (full paths)
- Blockers (if BLOCKED)

### Rules
1. Do NOT communicate with other agents directly
2. Write all outputs to handoffs/ and artifacts/
3. PM will read your handoff and coordinate next steps

---

## Your Instructions
{contents of PM's handoff file}
```

### 6.2 Remote Agent Addition

For remote agents, PM adds:

```markdown
### Remote Setup
You are running on: {remote_host}
Local PM syncs your outputs via rsync (cron every 2 min)

Create task directory at: {remote_cwd}/tasks/{task}/
```

---

## 7. PM Decision Protocol

### 7.1 Signal-Based Decisions

PM makes decisions based on signals, not hardcoded timeouts:

| Signal | Interpretation | Action |
|--------|----------------|--------|
| Agent completes subtask | Progress made | Spawn next agent or mark milestone |
| Agent requests review | Quality gate | Spawn review agent |
| Agent reports blocker | Missing context | Retry with different approach or escalate |
| No progress for 30+ min | Potential stuck | Evaluate: exploring or spinning? |
| Review rejects artifact | Quality issue | Spawn agent again with feedback |
| 3+ review rejections | Fundamental problem | Escalate to human or replan |

### 7.2 PM State Machine

```
                    ┌─────────────┐
                    │   PLANNING  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ EXPLORING│ │DEVELOPING│ │ TESTING  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             └────────────┼────────────┘
                          ▼
                    ┌──────────┐
                    │ REVIEWING│
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌──────────┐ ┌────────┐ ┌─────────┐
        │ COMPLETE │ │BLOCKED │ │ ITERATE │
        └──────────┘ └────────┘ └────┬────┘
                                     │
                                     └──▶ (back to relevant phase)
```

---

## 8. Scribe Behavior

Scribe gathers information by reading files, not by communicating with agents.

**Process:**
1. Scan `handoffs/` for files modified since last check-in (by mtime)
2. Read new handoff documents to extract status and completed work
3. Scan `artifacts/` for new files (by mtime)
4. Synthesize into `progress.md`

**Scribe does NOT:**
- Talk to other agents
- Execute any tasks
- Modify handoffs or artifacts

**Output format:**
```markdown
# Task Progress: {task_name}
**Last Updated:** {timestamp}
**Last Check-in:** {previous_timestamp}

## Recent Activity (since last check-in)
- {handoff-file}: {summary}
- New artifact: {path}

## Milestone Summary
| Milestone | Status | Last Handoff | Notes |
|-----------|--------|--------------|-------|
| ... | ... | ... | ... |

## Current Blockers
{blockers or "None"}

## Artifacts Generated
- {path} ({time})
- ...
```

---

## 9. Skill Loading

Agents load skills based on task requirements (progressive disclosure):

1. PM analyzes task.md for relevant skills
2. PM includes skill references in spawn preamble
3. Agent loads only specified skills
4. If agent needs additional skill, it documents in handoff as skill gap

Skills are additive: add when blocked, not comprehensive upfront.

---

## 10. Multi-Agent Skill Scripts

The multi-agent skill provides scripts for both **users** (to start tasks) and **PM** (to orchestrate).

### 10.1 User-Facing Scripts

**`scripts/task`** - Task management CLI
```bash
# Start a new task (creates folder, spawns PM)
scripts/task start <task-name> --project <project-path>

# Check task status
scripts/task status <task-name>

# List all tasks
scripts/task list

# Stop a task (terminates PM and agents)
scripts/task stop <task-name>

# Attach to PM session (for debugging)
scripts/task attach <task-name>
```

**What `task start` does:**
1. Creates `<project>/tasks/<task-name>/` directory structure
2. Copies task.md template if not exists
3. Creates tmux session for PM
4. Spawns PM agent with multi-agent skill loaded
5. Sets up cron for pm-check-in (every 10 min)

### 10.2 PM-Facing Scripts

**`scripts/spawn_agent.sh`** - Spawn execution agents
```bash
# Spawn local agent
scripts/spawn_agent.sh <agent-type> \
  --task-dir <project>/tasks/<task> \
  --handoff handoffs/pm-20251127-153000.md

# Spawn remote agent (for dev/architect only)
scripts/spawn_agent.sh dev \
  --task-dir <project>/tasks/<task> \
  --remote user@host:/path/to/repo \
  --handoff handoffs/pm-20251127-153000.md
```

**What `spawn_agent.sh` does:**
1. Creates tmux session for agent
2. Injects spawn preamble (protocol, file structure, rules)
3. Points agent to PM's handoff file
4. For remote: creates remote task directory, starts rsync cron

**`scripts/pm-check-in.sh`** - Trigger PM to check status
```bash
scripts/pm-check-in.sh <task-name>
```

Called by cron every 10 minutes. PM reads progress.md and new handoffs, then decides next action.

### 10.3 Setup Flow

```
User                          Multi-Agent Skill              Project
─────                         ─────────────────              ───────
                                                             
"Start task X"
      │
      ▼
scripts/task start X ────────▶ Creates tasks/X/
                               Creates tmux session
                               Spawns PM agent
                               Sets up cron
                                      │
                                      ▼
                              PM reads task.md ◀──────────── task.md
                              PM uses multi-agent skill
                              PM spawns agents via scripts
                                      │
                                      ▼
                              Agents write handoffs ────────▶ tasks/X/handoffs/
                              Agents write artifacts ───────▶ tasks/X/artifacts/
```

---

## 11. Next Steps

1. **Week 1-2**: Implement spawn scripts with preamble injection
2. **Week 3-4**: Implement PM check-in cycle and handoff parsing
3. **Week 5-6**: Implement scribe agent and progress.md generation
4. **Week 7-8**: Implement remote sync (rsync cron) and remote spawn
5. **Week 9-12**: Integration testing with embedded device workflows

---

## Appendix A: User Journey

```
1. TASK CREATION
   User creates task.md with requirements

2. PM INITIALIZATION
   bash scripts/task start {task-name}
   - Creates task directory structure
   - Spawns PM agent with task.md

3. EXPLORATION PHASE
   PM spawns explore agent → handoff → artifacts

4. PLANNING PHASE
   PM spawns plan agent → handoff → artifacts

5. EXECUTION PHASE (iterative)
   Dev → Test → Review → (iterate on feedback)

6. COMPLETION OR BLOCK
   COMPLETE: All criteria met, artifacts generated
   BLOCKED: Missing context documented, skill gap identified

7. USER RETURN
   bash scripts/task status {task-name}
   Reviews progress.md and artifacts/
```

---

## Appendix B: Example Handoff Sequence

```
09:00 - pm-20251127-090000.md      PM → explore: "Analyze DDS module"
09:30 - explore-20251127-093000.md  Explore → PM: COMPLETE, found 3 modules
09:35 - pm-20251127-093500.md      PM → plan: "Design test strategy"
10:30 - plan-20251127-103000.md    Plan → PM: COMPLETE, 4 tests designed
10:35 - pm-20251127-103500.md      PM → dev: "Implement test 1"
11:30 - dev-20251127-113000.md     Dev → PM: NEEDS_REVIEW
11:35 - pm-20251127-113500.md      PM → review: "Review test 1"
12:00 - review-20251127-120000.md  Review → PM: COMPLETE, approved
...
```
