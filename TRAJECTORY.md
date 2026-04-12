# TRAJECTORY.md

*Updated at every session close — early, before context pressure. Minimum viable update: one sentence per vector. Bill edits Destinations directly or via Telegram intention. Closing instance proposes destination changes; Bill confirms.*

*Last updated: 2026-04-12 (session: arch-redesign, bill-initiated — persona retirement and bootstrap reduction)*

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
**Session 2026-04-12 (arch-redesign) update:** No progress on TCA bug. Skill cleanup for perspective/horizon-review/struggle-log now actionable — requires a follow-up bill-initiated session (sentinel write-protection confirmed).
**Next milestone:** Fix TCA inbox bug — change uuid LIKE filter to eq in Execute Inbox Action node. Reference: execution 1996.
**Validation:** Execute a Telegram inbox action; no operator error in execution log.
**Research:** Self-healing system patterns; circuit breaker implementations in distributed systems.

---

### 2. Lesson System Effectiveness
**→ Destination 1**
**Session 2026-04-12 (arch-redesign) update:** No direct lesson system work this session — zero_applied count remains 97 as of last sentinel session. Watching for trend across next 3 sessions.
**Current state:** Fix is structurally in place. Measurement window too short to confirm. Watching the count over multiple sessions is the right signal.
**Next milestone:** Run diagnose at next 3 sessions and track zero_applied count. If not trending down by session 3, diagnose whether inject_context_v3 fix is landing or the fix applies to a different code path than what lesson_injector uses.
**Validation:** `SELECT COUNT(*) FROM lessons_learned WHERE times_applied = 0;` returns a number meaningfully below 97 over next 3 sessions.
**Research:** Knowledge retrieval architectures; how retrieval-augmented systems weight recency vs. relevance.

---

### 3. Autonomous Task Decomposition
**→ Destination 1**
**Session 2026-04-12 (arch-redesign) update:** No progress — next milestone unchanged.
**Current state:** autonomous_growth_scheduler inserts rotate-through tasks (explore/build/research) every 6 hours — autonomous in scheduling but not in decomposing intentions. No pipeline exists for taking a high-level Bill intention and breaking it into concrete subtasks without asking.
**Next milestone:** Design the intention decomposition workflow — given "build X" from Bill, what does the system do? Document the design as an ADR and get Bill's review.
**Validation:** Design document written to architecture/decisions/, reviewed by Bill.
**Research:** Multi-agent task decomposition patterns; how goal-to-subtask pipelines handle ambiguity.

---

### 4. Roblox Build Pipeline
**→ Destination 2**
**Session 2026-04-12 (arch-redesign) update:** No progress — research spike findings from sentinel session stand. Lune install on Pi is the next concrete action.
**Session 2026-04-12 (roblox-spike) update:** Research spike completed. Full findings in ChromaDB (roblox_research_spike_2026-04-12) and Supabase research_topics. Key: headless publish pipeline is Pi-feasible. Lune v0.10.4 has linux-aarch64 binary — can create .rbxl files programmatically. Open Cloud API publishes via HTTP POST. Studio (Win/Mac only) needed once for base game creation.
**Current state:** Toolchain understood. Pipeline design documented. Zero implementation — no Roblox account, no base game, Lune not yet installed on Pi.
**Next milestone:** Install Lune on Pi (download lune-0.10.4-linux-aarch64.zip), write a minimal Luau script that creates a simple place file, verify Lune can serialize it to valid .rbxl. This can be done without a Roblox account.
**Validation:** `lune run create_place.luau` produces a valid .rbxl file on Pi.
**Blocked on:** Creating a live Roblox game requires a Roblox account (Bill's action) + Studio on Win/Mac.
**Research:** Lune Roblox API reference (lune-org.github.io), minimal .rbxl structure via rbx-dom docs.

---

## Parked Directions

- **Bill's monitoring interface audit** — cosmos_report, session_health_reporter, and daily_briefing_agent exist but their current output hasn't been reviewed against what Bill actually needs. Parked until Destination 3 work begins — reviewing existing reporters is the natural first step.
- **Haiku self-critic** — retired 2026-04-05. Replaced by behavioral_health_check for agent quality assessment.
- **Wikipedia serendipity engine (sandbox)** — retired 2026-04-05. Replaced by serendipity_engine_prod.
