---
name: multi-agent
description: Orchestrate autonomous agent teams to complete complex tasks. PM dynamically selects specialized agents based on task classification and enforces non-negotiable principles. Supports local and remote agents, persistent sessions, and continuous learning through skills.
---

# Multi-Agent Orchestrator

## Overview

This skill enables long-running (4-8 hour) autonomous agent workflows. A PM agent **dynamically selects** specialized agents (explore, plan, architect, dev, test, review, scribe) based on task needs, enforcing software engineering principles.

**Key Features:**
- **Dynamic agent selection** based on task classification
- **Non-negotiable principles** (review always, scribe for non-trivial, plan usually)
- Signal-based decisions (no hardcoded timeouts)
- Persistent agent sessions with follow-up instructions
- Remote coding support (dev/architect via SSH)
- Standardized handoff documents for agent communication
- Scribe agent maintains high-level progress view
- Project-agnostic framework (tasks/skills in project directory)
- Supports both Claude and Kiro CLI

## Getting Started

### Step 1: Setup Agents (One-Time)

Generate the agent catalog for your project:

```bash
./scripts/setup-agents /path/to/project
```

This creates `.claude/agents/*.md` and `.kiro/agents/*.json`. Run once per project.

### Step 2: Create a Task

```bash
# Interactive (prompts for goal, criteria, context)
./scripts/task --project /path/to/project create my-feature

# Non-interactive (agent bootstraps task.md from goal)
./scripts/task --project /path/to/project --goal "Add user authentication" create my-feature

# Non-interactive (use existing task.md file)
./scripts/task --project /path/to/project --task-file ./my-task.md create my-feature
```

This creates `tasks/my-feature/` with directories and a `task.md` file.

### Step 3: Refine task.md (Optional)

Edit `task.md` to add agent configuration, especially for remote coding:

```bash
vi tasks/my-feature/task.md
```

Example task.md with agent config:

```markdown
# Task: my-feature

## Goal
Add user authentication to the API

## Acceptance Criteria
- [ ] Login endpoint returns JWT token
- [ ] Token validation middleware works
- [ ] Tests pass

## Context
Using existing Express app in src/api/

## Validation
```bash
npm test
curl -X POST localhost:3000/login -d '{"user":"test"}'
```

## Agent Config
```yaml
dev:
  cwd: user@remote:/path/to/project   # Remote coding via SSH
  skills: [my-project-skill]

architect:
  cwd: user@remote:/path/to/project

test:
  cwd: /local/path                    # Device access is always local
  skills: [device-access]
```
```

### Step 4: Start PM

```bash
./scripts/task --project /path/to/project start my-feature

# Or with different CLI
./scripts/task --project /path/to/project --cli claude start my-feature
```

### Step 5: Monitor Progress

```bash
# Check status
./scripts/task status my-feature

# Trigger PM check-in (or set up cron)
./scripts/pm-check-in.sh my-feature

# Attach to watch PM work
./scripts/task attach my-feature
```

### Step 6: Complete

```bash
./scripts/task stop my-feature
```

## Quick Reference

```bash
./scripts/setup-agents <project>                    # One-time: create agents
./scripts/task create <name> [--goal "text"]        # Create task (no PM)
./scripts/task start <name> [--cli claude|kiro]     # Start PM for task
./scripts/task status <name>                        # Check task status
./scripts/task attach <name>                        # Attach to PM session
./scripts/task logs <name>                          # View task logs
./scripts/task stop <name>                          # Stop task
./scripts/pm-check-in.sh <name>                     # Trigger PM check-in
```

**Typical workflow:**
```bash
./scripts/task --project /my/project create my-task --goal "Fix bug X"
vi /my/project/tasks/my-task/task.md   # Refine, add agent config
./scripts/task --project /my/project --cli claude start my-task
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

## Agent Catalog

Before starting tasks, generate the agent catalog for your project:

```bash
./scripts/setup-agents /path/to/project
```

This is a **one-time setup** that creates:
- `.claude/agents/*.md` - Claude agent files
- `.kiro/agents/*.json` - Kiro agent files

The agent catalog contains all available agents the PM can choose from. **Existing agents are skipped** (not overwritten). After bootstrap, you can:
- Edit agent prompts to customize behavior
- Add new agents for project-specific needs
- Adjust tools, model, or skills per agent

The generated agents are yours to modify. Re-running `setup-agents` will only add missing agents.

## Dynamic Agent Selection

PM dynamically selects agents based on:

### Task Classification

| Dimension | Options | Impact |
|-----------|---------|--------|
| **Complexity** | low / medium / high | Determines planning depth |
| **Type** | feature / bugfix / refactor / research / hotfix | Suggests agent patterns |
| **Scope** | single-file / module / cross-cutting | Affects architecture needs |
| **Familiarity** | known / unknown area | Affects exploration needs |

### Non-Negotiable Principles

| Principle | Requirement | Agent |
|-----------|-------------|-------|
| **Validate & Iterate** | All work reviewed before completion | review (ALWAYS) |
| **Document Decisions** | Capture context for posterity | scribe (ALWAYS for non-trivial) |
| **Plan Before Code** | Understand approach before implementing | plan (unless trivial) |
| **Design Before Build** | Complex changes need architecture | architect (when needed) |

### PM Agent Delegation Rules (CRITICAL)

**PM orchestrates, PM does NOT investigate.**

| PM Should | PM Should NOT |
|-----------|---------------|
| Create handoff documents | Read logs directly |
| Spawn explore/dev agents | Run grep/search commands |
| Monitor agent progress | Analyze code/data itself |
| Make workflow decisions | Debug issues directly |
| Summarize agent findings | Write implementation code |

**If PM finds itself investigating directly (reading logs, running searches), it should STOP and spawn an explore agent instead.**

### Handoff Best Practices

Every handoff to an agent should include:

1. **Task description** - Clear, specific goal
2. **Skills reference from task.md** - Include skills the agent should use:
   ```yaml
   Skills available:
     skills: [amelia-logs, amelia-athena]
   ```
3. **Search commands** - Specific commands to run
4. **Expected output location** - Where to write findings
5. **Done criteria** - How agent knows it's finished

**When user corrects PM:**
- Update handoff with correction
- Spawn NEW agent with corrected instructions
- Don't try to fix it in current PM context

### Agent Selection Matrix

| Task Type | explore | plan | architect | dev | test | review | scribe |
|-----------|:-------:|:----:|:---------:|:---:|:----:|:------:|:------:|
| **Feature (high)** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Feature (med)** | ? | ✓ | ? | ✓ | ? | ✓ | ✓ |
| **Feature (low)** | - | ? | - | ✓ | ? | ✓ | ✓ |
| **Bugfix** | ? | ? | - | ✓ | ✓ | ✓ | ✓ |
| **Hotfix** | - | - | - | ✓ | ? | ✓ | ? |
| **Refactor** | ✓ | ✓ | ? | ✓ | ✓ | ✓ | ✓ |
| **Research** | ✓ | - | - | - | - | ? | ✓ |

**Legend:** ✓ = Always, ? = Conditional, - = Usually skip

PM documents selection rationale in `pm_state.json`, including why agents were selected or skipped.

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
# Create task (does NOT start PM)
./scripts/task create <name> [--goal <text>] [--task-file <path>]

# Start PM for existing task
./scripts/task start <name> [--cli claude|kiro]

# Other commands
./scripts/task status <name>
./scripts/task list
./scripts/task attach <name>
./scripts/task stop <name>
./scripts/task logs <name>

# Global flags (before command)
--project <path>      # Project directory
--cli claude|kiro     # CLI to use (default: kiro)
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
| Agent STATUS: COMPLETE | Spawn next agent in selected workflow |
| Agent STATUS: NEEDS_REVIEW | Spawn review |
| Agent STATUS: BLOCKED | Evaluate: unblock or escalate |
| Review RESULT: PASS | Spawn scribe, complete task |
| Review RESULT: FAIL | Send follow-up to dev with feedback |

**Review owns retry logic.** No "max 3 attempts" - review decides if more iterations worthwhile.

### pm_state.json Structure

PM tracks dynamic selection and rationale:

```json
{
  "status": "ACTIVE",
  "task_classification": {
    "complexity": "medium",
    "type": "feature",
    "scope": "module",
    "scope_paths": ["src/api/", "src/models/"],
    "familiarity": "known"
  },
  "available_agents": ["explore", "plan", "architect", "dev", "test", "review", "scribe"],
  "selected_workflow": {
    "agents": ["explore", "plan", "dev", "review", "scribe"],
    "skipped": {
      "architect": "no new interfaces, extending existing pattern",
      "test": "no testable acceptance criteria specified"
    },
    "rationale": "Medium complexity feature, familiar codebase area",
    "adaptations": []
  },
  "principles_satisfied": {
    "validate_and_iterate": "pending",
    "document_decisions": "pending",
    "plan_before_code": true,
    "design_before_build": "skipped - no new interfaces"
  },
  "current_phase": "dev",
  "iteration": 1,
  "spawned_agents": [
    {"agent": "explore", "window": 1, "status": "complete"},
    {"agent": "plan", "window": 2, "status": "complete"},
    {"agent": "dev", "window": 3, "status": "active"}
  ],
  "last_checkin": "2025-11-30T10:30:00Z"
}
```

## References

- `references/agent-prompts/*.md` - System prompts for each agent
- `references/claude_agents.md` - Claude agent configs (tools, model)
- `references/kiro_agents.md` - Kiro agent configs (tools, model)
- `references/decision-protocols.md` - PM decision framework
- `references/task-template.md` - Template for task.md
- `docs/PRFAQ-Agent-Orchestrator.md` - Product vision
- `docs/Implementation-Agent-Orchestrator.md` - Technical design
