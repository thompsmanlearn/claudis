# TRAJECTORY.md

*Updated at every session close — early, before context pressure. Minimum viable update: one sentence per vector. Bill edits Destinations directly or via Telegram intention. Closing instance proposes destination changes; Bill confirms.*

---

## Destinations

*(Stable. Edited by Bill.)*

1. The system can receive an intention from Bill and autonomously research, build needed capabilities, and begin execution — without Bill directing each step.
2. The system can publish professional-quality games on Roblox.
3. Bill has a functional interface for monitoring trajectory, providing direction, and reviewing system output.
4. The system detects and recovers from its own failures without Bill discovering them first.

---

## Active Vectors

### 1. Fault Detection and Recovery
**→ Destination 4**
**Current state:** agent_health_monitor promoted 2026-04-12 — monitors consecutive execution errors across active agents. Known gap: building-status agents with errors are invisible to this monitoring. TCA inbox-approval bug is the current known unaddressed failure (uuid ~~ unknown in Execute Inbox Action node, workflow kddIKvA37UDw4x6e).
**Next milestone:** Fix TCA inbox bug — change uuid LIKE filter to eq in Execute Inbox Action node. Reference: execution 1996.
**Validation:** Execute a Telegram inbox action; no operator error in execution log.
**Research:** Self-healing system patterns; circuit breaker implementations in distributed systems.

---

### 2. Lesson System Effectiveness
**→ Destination 1**
**Current state:** 155 lessons in Supabase. inject_context_v3 fixed 2026-04-12 — was retrieving generic phrases for explore tasks, leaving 92 lessons with zero applications. Fix verified structurally but runtime effect unconfirmed.
**Next milestone:** Run diagnose and confirm zero_applied count trending below 92. If not decreasing, diagnose why the fix isn't landing.
**Validation:** `SELECT COUNT(*) FROM lessons_learned WHERE times_applied = 0;` returns a number meaningfully below 92.
**Research:** Knowledge retrieval architectures; how retrieval-augmented systems weight recency vs. relevance.

---

### 3. Autonomous Task Decomposition
**→ Destination 1**
**Current state:** autonomous_growth_scheduler inserts rotate-through tasks (explore/build/research) every 6 hours — autonomous in scheduling but not in decomposing intentions. No pipeline exists for taking a high-level Bill intention and breaking it into concrete subtasks without asking.
**Next milestone:** Design the intention decomposition workflow — given "build X" from Bill, what does the system do? Document the design as an ADR and get Bill's review.
**Validation:** Design document written to architecture/decisions/, reviewed by Bill.
**Research:** Multi-agent task decomposition patterns; how goal-to-subtask pipelines handle ambiguity.

---

### 4. Roblox Research Spike
**→ Destination 2**
**Current state:** Zero foothold. No knowledge, no agent, no Luau experience, no Studio access documented anywhere in the system.
**Next milestone:** Research spike — document what it takes to publish a minimal Roblox game. Key questions: What is Luau? What does the Studio publishing pipeline look like? Can any part of the pipeline be automated from a headless environment? What APIs are accessible externally?
**Validation:** Research document written to research_papers (Supabase + ChromaDB) covering: toolchain requirements, first build milestone, automation feasibility from Pi environment.
**Research:** Roblox Developer Hub, Luau language reference, Roblox Open Cloud API.

---

## Parked Directions

- **Bill's monitoring interface audit** — cosmos_report, session_health_reporter, and daily_briefing_agent exist but their current output hasn't been reviewed against what Bill actually needs. Parked until Destination 3 work begins — reviewing existing reporters is the natural first step.
- **Haiku self-critic** — retired 2026-04-05. Replaced by behavioral_health_check for agent quality assessment.
- **Wikipedia serendipity engine (sandbox)** — retired 2026-04-05. Replaced by serendipity_engine_prod.
