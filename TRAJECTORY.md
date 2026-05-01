# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture v0.1 + manual inflow complete (B-070–B-075): schema, callables, read view, all action affordances, and both add-to-thread surfaces live in Anvil
- Threads tab expanded card: annotate, state change, wire agent, gather, export bundle, + "Add desktop analysis" (TextArea + type dropdown, source=desktop_claude)
- Research tab article cards: "Add to thread" button opens inline thread picker, writes gather entry with formatted content block (source=research_articles:{id})
- Fleet: 10 active agents, unchanged
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Bill smoke-tests add-to-thread affordances end-to-end; then decide next vector (automated Gap A fix: agent output lands in triggering thread, or ChromaDB leverage).

---

## Handoff (pick up here)

**2026-04-30 (B-075):**
- **What I was doing:** B-075 — Add-to-thread affordances: 106 lines added to Form1/__init__.py; "Add desktop analysis" section in Threads tab expanded card + "Add to thread" inline picker on Research tab article cards; merged to master, pushed.
- **What I learned:** get_threads(state='active') already existed from B-071 — no new callable needed for the picker; the existing callable returns sorted by last_activity_at desc which is exactly the right default. Toggle-to-dismiss pattern (second click on "Add to thread" hides picker) keeps article cards clean without a modal.
- **Continue:** Bill smoke-tests: (1) paste analysis into Consumer AI thread; (2) toggle type to 'conclusion'; (3) promote a Research tab article. After test: decide Gap A card (automated agent→thread wiring) or ChromaDB leverage.
- **Left better:** Threads can now accumulate content manually — desktop Claude analyses and promoted research articles both flow in. Thread architecture is livable until automated inflow is built.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-073):**
- **What I was doing:** B-073 — Threads tab actions: 251 lines added to Form1/__init__.py; 135 lines added to uplink_server.py (trigger_thread_gather, get_thread_bundle); both repos merged to main/master and pushed; aadp-anvil restarted.
- **What I learned:** Anvil actions pattern: use mutable `[t_state]` closure to track thread state across action closures without full tab reload; rebuild actions_panel after wire/unwire (gather visibility changes) but only reload entries after annotate/state-change.
- **Continue:** B-075 completed.
- **Left better:** Thread architecture v0.1 functionally complete.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-072):**
- **What I was doing:** B-072 — Anvil Threads tab read view: 198 lines added to Form1/__init__.py; state filter, collapsed cards, lazy-loaded entries, entry-type icons; 2 test threads + 7 entries seeded.
- **What I learned:** Anvil client Python supports `datetime.fromisoformat()` and `datetime.now(timezone.utc)`. Edit tool cannot match files with literal `\uXXXX` escapes — use Bash+Python for those.
- **Continue:** B-073 + B-075 both completed.
- **Left better:** Threads fully visible in Anvil for the first time.
- **Usage:** session ~%, weekly ~%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
