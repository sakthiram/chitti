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

## Iteration Config (Optional - for exploratory tasks)

For bug reproduction, root cause analysis, or exploratory research that may require multiple attempts.

```yaml
# max_iterations: 5              # Max attempts before escalating to human
# blocked_after: 3               # Flag as blocked after N failures
# plan_iterations: true          # Spawn plan agent between iterations (default: true)
# success_criteria: |
#   - Specific outcome 1
#   - Specific outcome 2
```

## Human Review Overrides (Optional)

Control human review gates. Default is `required` for all gates.

```yaml
# Options: required (default) | auto | skip
# initial_plan_review: required      # Human reviews initial plan.md
# iteration_plan_review: required    # Human reviews each iteration plan
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
