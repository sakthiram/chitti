# Kiro Agent Definitions

Agent configurations for Kiro CLI. Tools use Kiro's tool names.

## Kiro Built-in Tool Reference

Per https://kiro.dev/docs/cli/reference/built-in-tools/:

| Tool | Description |
|------|-------------|
| `read` | Reads files, folders and images |
| `write` | Creates and edits files |
| `shell` | Executes bash commands (NOT `bash`) |
| `aws` | Makes AWS CLI calls |
| `web_search` | Searches the web |
| `web_fetch` | Fetches content from URLs |
| `glob` | File pattern matching |
| `grep` | Content search |

**IMPORTANT**: Use `shell` not `bash` for command execution!

---

## pm
description: Orchestrates the agent team for task completion
tools: read, write, edit, shell, aws, glob, grep

---

## explore
description: Research and analyze codebase, find patterns and dependencies
tools: read, glob, grep, shell, aws

---

## plan
description: Design implementation approach and break down into steps
tools: read, write, shell, aws

---

## architect
description: Make high-level design decisions and define interfaces
tools: read, write, glob, grep, shell, aws

---

## dev
description: Implement code changes according to plan
tools: read, write, edit, shell, aws

---

## test
description: Deploy and run tests, capture logs and results
tools: read, shell, aws, write

---

## review
description: Quality gate - evaluate work against acceptance criteria
tools: read, glob, grep, shell, aws

---

## scribe
description: Maintain progress summary by reading handoffs and artifacts
tools: read, glob, shell, aws, write
