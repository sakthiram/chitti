# Kiro Agent Definitions

Agent configurations for Kiro CLI. Tools use Kiro's tool names.

---

## pm
description: Orchestrates the agent team for task completion
tools: read, write, edit, bash, glob, grep

---

## explore
description: Research and analyze codebase, find patterns and dependencies
tools: read, glob, grep, bash

---

## plan
description: Design implementation approach and break down into steps
tools: read, write, bash

---

## architect
description: Make high-level design decisions and define interfaces
tools: read, write, glob, grep, bash

---

## dev
description: Implement code changes according to plan
tools: read, write, edit, bash

---

## test
description: Deploy and run tests, capture logs and results
tools: read, bash, write

---

## review
description: Quality gate - evaluate work against acceptance criteria
tools: read, glob, grep, bash
