# Claude Agent Definitions

Agent configurations for Claude CLI. Tools use Claude's tool names.

---

## pm
description: Orchestrates the agent team for task completion
tools: Read, Write, Edit, Bash, Glob, Grep
model: sonnet
skills: multi-agent

---

## explore
description: Research and analyze codebase, find patterns and dependencies
tools: Read, Glob, Grep

---

## plan
description: Design implementation approach and break down into steps
tools: Read, Write

---

## architect
description: Make high-level design decisions and define interfaces
tools: Read, Write, Glob, Grep

---

## dev
description: Implement code changes according to plan
tools: Read, Write, Edit, Bash
model: sonnet

---

## test
description: Deploy and run tests, capture logs and results
tools: Read, Bash, Write

---

## review
description: Quality gate - evaluate work against acceptance criteria
tools: Read, Glob, Grep
