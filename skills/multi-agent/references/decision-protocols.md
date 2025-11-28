# PM Decision Protocols

## Core Principle

Make decisions based on **signals**, not hardcoded timeouts or retry limits.

## Signal Categories

### 1. Progress Signals

| Signal | Interpretation | Action |
|--------|----------------|--------|
| Agent writes handoff with STATUS: COMPLETE | Subtask done | Spawn next agent or review |
| Agent writes handoff with STATUS: NEEDS_REVIEW | Wants validation | Spawn review agent |
| Agent writes handoff with STATUS: BLOCKED | Stuck | Evaluate blocker, unblock or escalate |
| No new handoff since last check-in | Still working or stuck | Check tmux window, evaluate |

### 2. Quality Signals

| Signal | Interpretation | Action |
|--------|----------------|--------|
| Review RESULT: PASS | Meets acceptance criteria | Spawn scribe, complete task |
| Review RESULT: FAIL with minor issues | Fixable problems | Send follow-up to dev |
| Review RESULT: FAIL with major issues | Approach problem | Consider replanning |
| Review RESULT: BLOCKED | Missing requirements | Escalate to human |

### 3. Diminishing Returns Signals

| Signal | Interpretation | Action |
|--------|----------------|--------|
| Same issues appear 3+ iterations | Fundamental problem | Replan or escalate |
| Improvements < 10% per iteration | Diminishing returns | Accept partial or escalate |
| Agent asking same questions | Missing context | Provide context or escalate |
| Agent looping on same actions | Confused | Kill and respawn fresh |

## Decision Matrix

### On Check-in: What to Do

```
Read progress.md and new handoffs
         │
         ▼
┌─────────────────────────────────────┐
│ Any agent STATUS: COMPLETE?         │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │ YES               │ NO
        ▼                   ▼
┌───────────────┐   ┌───────────────────────┐
│ Spawn next    │   │ Any STATUS: BLOCKED?  │
│ agent in      │   └───────────┬───────────┘
│ workflow      │               │
└───────────────┘     ┌─────────┴─────────┐
                      │ YES               │ NO
                      ▼                   ▼
              ┌───────────────┐   ┌───────────────┐
              │ Can PM        │   │ Agents still  │
              │ unblock?      │   │ working, wait │
              └───────┬───────┘   └───────────────┘
                      │
            ┌─────────┴─────────┐
            │ YES               │ NO
            ▼                   ▼
    ┌───────────────┐   ┌───────────────┐
    │ Send guidance │   │ Mark task     │
    │ to agent      │   │ BLOCKED       │
    └───────────────┘   └───────────────┘
```

### After Review: What to Do

```
Read review handoff
         │
         ▼
┌─────────────────────────────────────┐
│ RESULT: PASS?                       │
└─────────────────┬───────────────────┘
                  │
        ┌─────────┴─────────┐
        │ YES               │ NO
        ▼                   ▼
┌───────────────┐   ┌───────────────────────┐
│ Spawn scribe  │   │ RESULT: BLOCKED?      │
│ Task complete!│   └───────────┬───────────┘
└───────────────┘               │
                      ┌─────────┴─────────┐
                      │ YES               │ NO (FAIL)
                      ▼                   ▼
              ┌───────────────┐   ┌───────────────────┐
              │ Evaluate if   │   │ Read issues       │
              │ PM can unblock│   │ from review       │
              └───────────────┘   └─────────┬─────────┘
                                            │
                                  ┌─────────┴─────────┐
                                  │ Minor issues?     │
                                  └─────────┬─────────┘
                                            │
                                  ┌─────────┴─────────┐
                                  │ YES               │ NO
                                  ▼                   ▼
                          ┌───────────────┐   ┌───────────────┐
                          │ Send follow-up│   │ Consider      │
                          │ to dev agent  │   │ replanning    │
                          └───────────────┘   └───────────────┘
```

## When to Kill vs Send Follow-up

### Send Follow-up (Keep Agent Alive)

Use `send_to_agent.sh` when:
- Agent completed subtask, needs next instruction
- Review found minor issues to fix
- Agent asked clarifying question
- Providing additional context

**Benefit:** Preserves agent's context and understanding.

### Kill and Respawn

Use `tmux kill-window` then `spawn_agent.sh` when:
- Agent context is stale (many iterations, topic changed significantly)
- Agent is confused or looping
- Starting a completely fresh phase
- Agent crashed or became unresponsive

**Benefit:** Clean slate, no accumulated confusion.

## Blocker Handling

### Soft Blockers (PM Can Resolve)

- Ambiguous requirement → Make reasonable assumption, document it
- Missing file location → Search and provide path
- Unclear priority → Make decision, note in handoff

**Action:** Send guidance to agent, continue.

### Hard Blockers (Need Human)

- Missing credentials or access
- Unclear business requirements
- External dependency not available
- Fundamental approach question

**Action:** Mark task BLOCKED, document what's needed.

## Escalation Criteria

Escalate to human when:

1. **Review marks BLOCKED** with missing requirements
2. **Same issue persists** after 3+ iterations with different approaches
3. **Agent requests** information PM cannot provide
4. **Fundamental ambiguity** in task requirements
5. **External dependency** is unavailable

## Iteration Tracking

Track in `pm_state.json`:

```json
{
  "current_phase": "dev",
  "iteration": 2,
  "iteration_history": [
    {"phase": "dev", "iteration": 1, "result": "FAIL", "issues": ["missing validation"]},
    {"phase": "dev", "iteration": 2, "result": "in_progress"}
  ]
}
```

Use iteration history to detect patterns:
- Same issues recurring → Change approach
- Issues getting smaller → Continue
- New issues each time → May need replanning

## Handoff Status Values

| Status | Meaning | PM Action |
|--------|---------|-----------|
| COMPLETE | Agent finished successfully | Spawn next agent |
| NEEDS_REVIEW | Agent wants validation | Spawn review |
| BLOCKED | Agent stuck | Evaluate and unblock or escalate |

## Review Result Values

| Result | Meaning | PM Action |
|--------|---------|-----------|
| PASS | Meets acceptance criteria | Spawn scribe, complete |
| FAIL | Issues found | Send follow-up or replan |
| BLOCKED | Cannot evaluate | Escalate to human |

## Time Considerations

While we don't use hardcoded timeouts, consider:

- **30+ minutes no progress**: Check if agent is working or stuck
- **Multiple check-ins no change**: Agent may need guidance
- **Task running 8+ hours**: Consider breaking into subtasks

These are signals to investigate, not automatic actions.
