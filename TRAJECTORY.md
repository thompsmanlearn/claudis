# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture v0.1 complete (B-070–B-073): schema, callables, read view, and all action affordances live in Anvil
- Threads tab: create-thread form at top; per-card: annotate, state change, wire agent, gather (webhook-gated), export bundle; inline card refresh after each action
- Fleet: 10 active agents, unchanged; 4 agents have webhook_urls eligible for wire/gather
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Bill smoke-tests Threads tab end-to-end; then decide next vector (thread-aware gathering, ChromaDB leverage, or surface from use).

---

## Handoff (pick up here)

**2026-04-29 (B-073):**
- **What I was doing:** B-073 — Threads tab actions: 251 lines added to Form1/__init__.py; 135 lines added to uplink_server.py (trigger_thread_gather, get_thread_bundle); both repos merged to main/master and pushed; aadp-anvil restarted.
- **What I learned:** Anvil actions pattern: use mutable `[t_state]` closure to track thread state across action closures without full tab reload; rebuild actions_panel after wire/unwire (gather visibility changes) but only reload entries after annotate/state-change. PostgREST `or=(col.is.null,col.eq.false)` works as a query param for OR-filter across null/false.
- **Continue:** Bill smoke-tests via Anvil UI. After smoke test: decide next card — thread-aware gathering (agent writes back to thread_entries), or pivot to ChromaDB leverage.
- **Left better:** Thread architecture v0.1 functionally complete; Bill can now create, annotate, manage state, wire agents, trigger gathers, and export bundles from Anvil.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-072):**
- **What I was doing:** B-072 — Anvil Threads tab read view: 198 lines added to Form1/__init__.py; Threads tab between Research and Skills; state filter, collapsed cards, lazy-loaded entries, entry-type icons; 2 test threads + 7 entries seeded.
- **What I learned:** Anvil client Python supports `datetime.fromisoformat()` and `datetime.now(timezone.utc)` for relative timestamps. Edit tool cannot match files with literal `\uXXXX` Python string escapes (JSON encoding converts them to characters before matching) — use Bash+Python for those edits.
- **Continue:** B-073 complete this session.
- **Left better:** Threads fully visible in Anvil for the first time.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-071):**
- **What I was doing:** B-071 — Thread write callables: 6 uplink callables + last_activity_at Supabase trigger. Smoke test passed (10/10). Merged and pushed.
- **What I learned:** Supabase trigger for denormalized timestamps (last_activity_at) is the right pattern — putting it in callable code means every future writer has to remember; trigger guarantees it automatically.
- **Continue:** B-072 + B-073 both completed.
- **Left better:** Thread callable layer live.
- **Usage:** session ~20%, weekly ~%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
