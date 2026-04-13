# TRAJECTORY.md

*Updated at every session close — early, before context pressure. Minimum viable update: one sentence per vector. Bill edits Destinations directly or via Telegram intention. Closing instance proposes destination changes; Bill confirms.*

*Last updated: 2026-04-13 (session: health-monitor-building — building/sandbox agent stale-build detection added to agent_health_monitor)*

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
**Current state:** agent_health_monitor promoted 2026-04-12. TCA inbox approval flow fully rebuilt 2026-04-13 (uuid LIKE bug fixed, /approve and /reject wired). All skill files confirmed updated to v2 on 2026-04-13 — arch redesign fully clean.
**Session 2026-04-13 (sentinel-lune-install) update:** Confirmed TCA Execute Inbox Action uses `id=eq.{inbox_id}` — fix verified. All 3 skill files (perspective, horizon-review, struggle-log) confirmed updated. Zero remaining arch-redesign cleanup items.
**Session 2026-04-13 (context-economy) update:** Operational health work. disk_prompt.md → v29 (497→407 lines, ~747 tokens removed). DCL reduced 73% (14,890→~4,025 tokens): consumed 17 stale session_notes (8,143 tokens), fixed bootstrap consume=true bug, added DCL notes cap (5), agent_registry column projection (~3,128 tokens). Lesson written to both stores.
**Session 2026-04-13 (health-monitor-building) update:** MILESTONE COMPLETE. agent_health_monitor (w5vypq4vb2rSrwdl) extended with parallel branch detecting building/sandbox agents stale >7 days. Execution 2277 confirmed both branches successful. First scan found: research_synthesis_agent (8d building, no workflow) and arxiv_aadp_pipeline (7d sandbox, has workflow). Bill notified. Lesson written to both stores. Also: store sync gap flagged (ChromaDB 213 vs Supabase 169 — 44 lesson gap).
**Next milestone:** Resolve the 44-lesson store sync gap between ChromaDB (213) and Supabase (169) — identify which entries exist in only one store and backfill or reconcile. Then implement the research_synthesis_agent (currently in building status for 8+ days).
**Validation:** `SELECT COUNT(*) FROM lessons_learned` returns a value within 2 of the ChromaDB lessons_learned collection count.
**Research:** Self-healing system patterns; circuit breaker implementations in distributed systems.

---

### 2. Lesson System Effectiveness
**→ Destination 1**
**Session 2026-04-13 (sentinel-lune-install) update:** zero_applied = 96 (down from 97). Slight improvement — new lessons added this session are zero_applied but existing pool showing small uptick in usage. Watching for continued trend.
**Current state:** Fix is structurally in place. Measurement window too short to confirm. Watching the count over multiple sessions is the right signal.
**Next milestone:** Run diagnose at next 3 sessions and track zero_applied count. If not trending down by session 3, diagnose whether inject_context_v3 fix is landing or the fix applies to a different code path than what lesson_injector uses.
**Validation:** `SELECT COUNT(*) FROM lessons_learned WHERE times_applied = 0;` returns a number meaningfully below 97 over next 3 sessions.
**Research:** Knowledge retrieval architectures; how retrieval-augmented systems weight recency vs. relevance.

---

### 3. Autonomous Task Decomposition
**→ Destination 1**
**Session 2026-04-13 (sentinel-lune-install) update:** No progress — next milestone unchanged.
**Current state:** autonomous_growth_scheduler inserts rotate-through tasks (explore/build/research) every 6 hours — autonomous in scheduling but not in decomposing intentions. No pipeline exists for taking a high-level Bill intention and breaking it into concrete subtasks without asking.
**Next milestone:** Design the intention decomposition workflow — given "build X" from Bill, what does the system do? Document the design as an ADR and get Bill's review.
**Validation:** Design document written to architecture/decisions/, reviewed by Bill.
**Research:** Multi-agent task decomposition patterns; how goal-to-subtask pipelines handle ambiguity.

---

### 4. Roblox Build Pipeline
**→ Destination 2**
**Session 2026-04-13 (sentinel-lune-install) update:** MILESTONE COMPLETE. Lune v0.10.4 installed at /usr/local/bin/lune. create_place.luau produces valid binary .rbxl (888 bytes, magic bytes <roblox! confirmed). Commit bdd5008 on branch roblox-lune-install.
**Current state:** Full headless pipeline is Pi-feasible. Lune installed, .rbxl serialization verified. Remaining gap: Bill needs a Roblox account + one-time Studio session (Win/Mac) to create the base game and get a Universe ID + Place ID for Open Cloud API.
**Next milestone:** Bill creates a Roblox account and a base game in Studio (Win/Mac, ~15 minutes). Shares Universe ID and Place ID. Then: implement Open Cloud API publish step in Lune pipeline.
**Validation:** `curl POST` to Open Cloud API with .rbxl payload returns success and game version increments in Roblox.
**Blocked on:** Bill's Roblox account + Win/Mac for one-time Studio base game creation. This is a Bill action, not an autonomous task.
**Research:** Lune Roblox API reference (lune-org.github.io), minimal .rbxl structure via rbx-dom docs.

---

## Parked Directions

- **Bill's monitoring interface audit** — cosmos_report, session_health_reporter, and daily_briefing_agent exist but their current output hasn't been reviewed against what Bill actually needs. Parked until Destination 3 work begins — reviewing existing reporters is the natural first step.
- **Haiku self-critic** — retired 2026-04-05. Replaced by behavioral_health_check for agent quality assessment.
- **Wikipedia serendipity engine (sandbox)** — retired 2026-04-05. Replaced by serendipity_engine_prod.
