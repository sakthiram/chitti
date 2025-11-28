# Kiro Agent Definitions

Agent configurations for Kiro CLI. Tools use Kiro's tool names.

---

## pm
description: Orchestrates the agent team for task completion
tools: read, write, edit, bash, glob, grep
model: claude-sonnet-4

---

## explore
description: Research and analyze codebase, find patterns and dependencies
tools: read, glob, grep

---

## plan
description: Design implementation approach and break down into steps
tools: read, write

---

## architect
description: Make high-level design decisions and define interfaces
tools: read, write, glob, grep

---

## dev
description: Implement code changes according to plan
tools: read, write, edit, bash
model: claude-sonnet-4

---

## test
description: Deploy and run tests, capture logs and results
tools: read, bash, write

---

## review
description: Quality gate - evaluate work against acceptance criteria
tools: read, glob, grep

---

## scribe
description: Maintain progress summary by reading handoffs and artifacts
tools: read, write, glob
