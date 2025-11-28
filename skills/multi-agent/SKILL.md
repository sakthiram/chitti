---
name: multi-agent
description: Orchestrate autonomous agent teams to complete complex tasks. PM spawns specialized agents, makes signal-based decisions, and manages workflow adaptively. Supports local and remote agents, persistent sessions, and continuous learning through skills.
---

# Multi-Agent Orchestrator

## Overview

This skill enables long-running (4-8 hour) autonomous agent workflows. A PM agent orchestrates specialized agents (explore, plan, architect, dev, test, review, scribe) to complete complex tasks without constant human supervision.

**Key Features:**
- Signal-based decisions (no hardcoded timeouts)
- Persistent agent sessions with follow-up instructions
- Remote coding support (dev/architect via SSH)
- Standardized handoff documents for agent communication
- Scribe agent maintains high-level progress view
- Project-agnostic framework (tasks/skills in project directory)
- Supports both Claude and Kiro CLI

## Quick Start

```bash
# 1. Setup agents for your project (creates .claude/agents/ and .kiro/agents/)
./scripts/setup-agents /path/to/project

# 2. Start a new task
./scripts/task start my-feature --project /path/to/project

# 3. Check status
./scripts/task status my-feature

# 4. Trigger PM check-in (or set up cron)
./scripts/pm-check-in.sh my-feature

# 5. Attach to PM session
./scripts/task attach my-feature

# 6. Stop task
./scripts/task stop my-feature
```

## CLI Support

| CLI | Agent Location | Agent Format | Invoke |
|-----|----------------|--------------|--------|
| claude | `.claude/agents/<name>.md` | Markdown with YAML frontmatter | `claude <name>` |
| kiro | `.kiro/agents/<name>.json` | JSON | `kiro-cli --agent <name>` |

The `setup-agents` script generates agents for both CLIs from shared templates.

## Project Structure

```
~/.claude/skills/multi-agent/       # This skill (shared framework)
├── scripts/                        # CLI and orchestration scripts
├── references/
│   ├── agent-prompts/system-prompts.md  # Shared system prompts
│   ├── claude_agents.md            # Claude-specific config (tools, model)
│   └── kiro_agents.md              # Kiro-specific config (tools, model)
└── SKILL.md

<project>/                          # Your project
├── .claude/agents/                 # Generated Claude agents
├── .kiro/agents/                   # Generated Kiro agents
├── .claude/skills/                 # Project-specific skills
├── tasks/                          # Task instances
│   └── {task-name}/
│       ├── task.md                 # Requirements + agent config
│       ├── pm_state.json           # PM tracking state
│       ├── progress.md             # Scribe's status summary
│       ├── handoffs/               # Agent communication
│       ├── artifacts/              # Generated outputs
│       └── scratchpad/             # Agent working files
└── src/                            # Project source code
```

## Agent Setup

Before starting tasks, generate agents for your project:

```bash
./scripts/setup-agents /path/to/project
```

This creates:
- `.claude/agents/*.md` - Claude agent files
- `.kiro/agents/*.json` - Kiro agent files

**Existing agents are skipped** (not overwritten). After bootstrap, you can:
- Edit agent prompts to customize behavior
- Add new agents for project-specific needs
- Adjust tools, model, or skills per agent

The generated agents are yours to modify. Re-running `setup-agents` will only add missing agents.

## Handoff Naming Convention

All handoffs use: `{content}-{YYYYMMDD}-{HHMMSS}.md`

| Agent | Output Pattern | Example |
|-------|---------------|---------|
| explore | `research-{ts}.md` | `research-20251127-090000.md` |
| plan | `plan-{ts}.md` | `plan-20251127-100000.md` |
| architect | `design-{ts}.md` | `design-20251127-110000.md` |
| dev | `PR-iter{N}-{ts}.md` | `PR-iter1-20251127-120000.md` |
| test | `test-results-{ts}.md` | `test-results-20251127-150000.md` |
| review | `review-iter{N}-{ts}.md` | `review-iter1-20251127-160000.md` |
| PM | `pm-to-{agent}-{ts}.md` | `pm-to-dev-20251127-170000.md` |

## Scripts

### Setup

**`scripts/setup-agents`** - Generate agent files for project
```bash
./scripts/setup-agents /path/to/project
```

### User-Facing

**`scripts/task`** - Main CLI
```bash
./scripts/task start <name> [--project <path>] [--cli claude|kiro]
./scripts/task status <name>
./scripts/task list
./scripts/task attach <name>
./scripts/task stop <name>
./scripts/task logs <name>
```

### PM-Facing

**`scripts/spawn_agent.sh`** - Spawn agent in tmux window
```bash
# Local agent (cwd defaults to project root)
./scripts/spawn_agent.sh --task <name> --agent <type> --window <N> [--handoff <file>]

# Remote agent (dev/architect only)
./scripts/spawn_agent.sh --task <name> --agent dev --window 3 \
  --remote user@host:/path --handoff <file>
```

**`scripts/send_to_agent.sh`** - Send follow-up to existing agent
```bash
./scripts/send_to_agent.sh --task <name> --agent <type> --handoff <file>
```

**`scripts/pm-check-in.sh`** - Trigger PM check-in
```bash
./scripts/pm-check-in.sh <task-name> [--project <path>]
```

## Agent Config in task.md

task.md can specify per-agent configuration:

```yaml
## Agent Config

dev:
  cwd: user@host:/remote/path    # Remote coding via SSH
  skills: [project-skill]

architect:
  cwd: user@host:/remote/path

test:
  cwd: /local/path               # Device access is always local
  skills: [device-access]
```

Default cwd for all agents is `<project>` (project root).

## PM Check-in Flow

```
pm-check-in.sh triggered (cron or manual)
         │
         ▼
┌─────────────────────────┐
│  1. Nudge Scribe        │  (updates progress.md)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  2. Nudge PM            │  (reads progress.md, decides next action)
└─────────────────────────┘
```

Set up cron for periodic check-ins:
```bash
*/10 * * * * /path/to/scripts/pm-check-in.sh my-task --project /path/to/project
```

## Tmux Session Structure

Session: `task-{task-name}-pm`

| Window | Agent | Purpose |
|--------|-------|---------|
| 0 | pm | Orchestrator |
| 1 | explore | Research |
| 2 | plan | Design |
| 3 | dev | Implementation |
| 4 | test | Validation |
| 5 | review | Quality gate |
| 6 | scribe | Progress tracking |

## Decision Framework

PM makes signal-based decisions (NO hardcoded timeouts):

| Signal | Action |
|--------|--------|
| Agent STATUS: COMPLETE | Spawn next agent |
| Agent STATUS: NEEDS_REVIEW | Spawn review |
| Agent STATUS: BLOCKED | Evaluate: unblock or escalate |
| Review RESULT: PASS | Spawn scribe, complete task |
| Review RESULT: FAIL | Send follow-up to dev with feedback |

**Review owns retry logic.** No "max 3 attempts" - review decides if more iterations worthwhile.

## References

- `references/agent-prompts/*.md` - System prompts for each agent
- `references/claude_agents.md` - Claude agent configs (tools, model)
- `references/kiro_agents.md` - Kiro agent configs (tools, model)
- `references/decision-protocols.md` - PM decision framework
- `references/task-template.md` - Template for task.md
- `docs/PRFAQ-Agent-Orchestrator.md` - Product vision
- `docs/Implementation-Agent-Orchestrator.md` - Technical design
