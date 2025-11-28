# Task: {task-name}

## Goal
{Describe what needs to be accomplished}

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Context
{Any relevant background, constraints, or domain knowledge}

## Validation
{How to verify success - commands, tests, checks}

```bash
# Example validation commands
```

## Agent Config

Optional per-agent configuration. PM uses these as defaults, can override as needed.
If an agent is not listed, PM spawns with default settings.

```yaml
# explore:
#   skills: []              # Additional skills to load

# plan:
#   skills: []

# architect:
#   cwd: /local/path                    # Local working directory
#   # cwd: user@host:/remote/path       # Remote via SSH
#   skills: []

# dev:
#   cwd: /local/path
#   # cwd: user@host:/remote/path
#   skills: []

# test:
#   cwd: /local/path                    # Device access is always local
#   skills: [device-access]

# review:
#   static: true                        # Use .claude/agents/review.md

# scribe:
#   static: true                        # Use .claude/agents/scribe.md
```

## Agent Guidance (Optional)

Hints for specific agents. PM incorporates these into agent prompts.

### explore
focus: "{Where to look, what to find}"
done_when: "{Criteria for sufficient research}"

### plan
constraints: "{Design principles, patterns to follow}"

### dev
style_guide: "{Code style preferences}"
validation: "{What to check before marking complete}"

### review
critical_checks: ["security", "performance", "correctness"]
