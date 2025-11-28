# PR/FAQ: Long-Running Agent Orchestrator
**Document Type:** PR/FAQ | **Date:** November 27, 2025

---

## Press Release

**FOR IMMEDIATE RELEASE**

### Agent Orchestrator Enables Engineers to Delegate Multi-Hour Tasks to AI Teams

*Embedded engineers can now assign complex debugging tasks and walk away*

**Seattle, WA** — Amazon today announced the Agent Orchestrator, a system that enables embedded software engineers to delegate complex, multi-hour tasks to coordinated AI agent teams without constant supervision.

"Before Agent Orchestrator, I had to babysit my AI assistant every 10 minutes," said an embedded engineer working on device firmware. "Now I assign a task like 'investigate this crash and create reproduction tests,' go to lunch, and come back to either completed tests deployed on my device or a clear list of what context I need to add. The system learns from every blocked task, so it gets stuck less often over time."

The Agent Orchestrator addresses three problems that prevent AI agents from running reliably for hours:

1. **Context limits**: A PM agent coordinates specialized agents, preventing any single agent from exceeding context limits
2. **Early stopping**: Agents communicate only via handoff files. The PM makes all decisions about when to escalate or retry
3. **Quality issues**: Mandatory review cycles ensure agents iterate on feedback before marking tasks complete

When agents encounter blockers, they document exactly what skill or context is missing. Engineers add that knowledge once, and all future tasks benefit.

"We embraced non-determinism," said the development team. "Sometimes tasks complete fully, sometimes they block. But they always make progress, always document their state, and always tell you exactly what they need to continue."

Agent Orchestrator is available today for embedded development teams.

---

## FAQ

### Customer Questions

**Q1: Who is this for?**

Embedded software engineers who need to test designs, configurations, and builds on actual hardware devices. These engineers work on firmware, device drivers, system optimization, and hardware-software integration. Their workflows require closing the loop on physical devices, which traditionally requires manual intervention at every step.

**Q2: What problem does this solve?**

Today, when engineers assign complex tasks to AI agents, three things happen:

1. **Context limits**: After 30-60 minutes, the agent's context fills up. It starts producing garbage or hallucinating.

2. **Constant interruption**: The agent stops every 10 minutes to ask questions. Engineers cannot walk away.

3. **Poor quality**: Without review cycles, agents produce half-correct solutions. They skip validation and mark tasks complete prematurely.

The result: Engineers babysit agents for 8 hours instead of delegating and focusing on higher-value work.

**Q3: Can you give a concrete example?**

Consider a DDS (Data Distribution Service) crash investigation on an embedded device:

*Without Agent Orchestrator:*
- Engineer assigns: "Investigate WriterPool exhaustion crash"
- 15 minutes later: Agent asks "Where are the device logs?"
- 30 minutes later: Agent's context is full, starts repeating itself
- 1 hour later: Agent produces a test that does not compile
- Engineer spends 6 hours manually guiding the agent

*With Agent Orchestrator:*
- Engineer assigns the same task at 9am and goes AFK
- PM agent coordinates explore, plan, dev, test, and review agents
- Engineer returns at 5pm to find:
  - 4 hypothesis tests created and deployed
  - Device logs captured and analyzed
  - Root cause identified
  - Recommended fix documented

**Q4: What if the agent gets stuck?**

The system handles blockers explicitly:

1. **PM judgment**: If an agent makes no progress, the PM evaluates whether to try a different approach or escalate. No agent stops on its own.

2. **Documented blockers**: When blocked, the system creates a clear handoff:
   - What was accomplished
   - What is blocking progress
   - What skill or context is missing
   - How to resume once the blocker is resolved

3. **Skill-based learning**: The engineer adds the missing skill once. All future tasks benefit.

**Q5: How does the system learn over time?**

Through skill updates:

1. **Agents identify gaps**: When blocked, agents document what context or capability was missing
2. **Humans write skills**: Engineers add skills based on blocker feedback
3. **Progressive disclosure**: Agents load only relevant skills for their current task
4. **Continuous improvement**: Each skill addition reduces future blockers

Agents are consumers of skills, not owners. They do not modify skills.

**Q6: What does "AFK-able" mean?**

You can assign a task and walk away for hours. The system:
- Runs without human input
- Tracks progress via regular status updates
- Never stops silently
- Produces resumable state via handoff documents

**Q7: How long can tasks run?**

The system supports two time scales:
- **Short tasks (30 min - 2 hours)**: "Run this specific test on device"
- **Medium tasks (4-8 hours)**: "Investigate this crash and recommend fixes"

For tasks longer than 8 hours, break them into medium-sized subtasks.

---

### Technical Questions

**Q8: How does the system prevent context blowup?**

The PM agent manages context through agent lifecycle:
- Specialized agents have focused context (dev only sees code, test only sees device)
- PM spawns agents for specific subtasks, then terminates them when complete
- State transfers between agents via handoff files, not conversation history

**Q9: What is the agent architecture?**

Hub-and-spoke model where PM is the only orchestrator:
- **PM**: Coordinates workflow, spawns agents, makes decisions
- **Explore/Plan**: Analysis and design (local)
- **Architect/Dev**: Implementation (local or remote via SSH)
- **Test**: Device validation (local, device access is local)
- **Review**: Quality gates (local)
- **Scribe**: Progress tracking (local)

Only PM has orchestration logic. Other agents execute instructions and communicate only via handoff files.

**Q10: How do agents communicate?**

Only PM talks to agents. All other agents:
1. Receive instructions via tmux message pointing to a handoff file
2. Execute the instructions
3. Write a completion handoff with artifacts list

Scribe reads handoff files and artifacts to build progress summaries.

**Q11: How does remote coding work?**

For dev/architect agents that need to work on remote codebases:
- task.md specifies remote CWD: `cwd: user@host:/path/to/repo`
- PM spawns agent via SSH with same protocols
- Cron syncs handoffs/artifacts from remote to local continuously
- Scribe (local) reads synced outputs

Device access (test agent) is always local. Only coding can be remote.

---

### Business Questions

**Q12: What are the success metrics?**

Three dimensions:

1. **Autonomy**: Time between human interventions
   - Baseline: 10-15 minutes
   - Target: 4+ hours

2. **Quality**: Tasks completed without rework
   - Baseline: 40%
   - Target: 85%

3. **Learning**: Reduction in repeated blockers
   - Baseline: Same blockers recur
   - Target: Each blocker resolved once via skill addition

**Q13: What are the risks?**

1. **Runaway agents**: Agent works in wrong direction for hours
   - Mitigation: Scribe monitors for deviation, PM check-ins every 10 minutes

2. **Context still blows up**: Handoff documents grow too large
   - Mitigation: Strict format limits, artifact references instead of embedding

3. **Skill maintenance burden**: Too many skills to maintain
   - Mitigation: Skills are additive (add when blocked), not comprehensive

**Q14: What is the rollout plan?**

Three phases:

1. **Phase 1 (4 weeks)**: Single-agent validation
   - Test each agent type independently
   - Validate skills for 2-hour autonomous operation

2. **Phase 2 (4 weeks)**: Multi-agent orchestration
   - Enable PM to coordinate 2-3 agents
   - Validate handoff protocol

3. **Phase 3 (4 weeks)**: Full system with learning loop
   - Enable full agent team
   - Implement skill gap detection
   - Pilot with embedded device workflows

---

## Appendix: Implementation Details

For detailed design decisions, protocols, and architecture, see: **[Agent Orchestrator Implementation Narrative](./Implementation-Agent-Orchestrator.md)**
