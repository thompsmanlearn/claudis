# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture v0.1 + manual inflow complete (B-070–B-078): schema, callables, read view, all action affordances, both add-to-thread surfaces, and extraction passback channel all live in Anvil
- "Add desktop analysis" now runs extraction: Haiku 4.5 parses prose into synthesis (analysis entry), conclusions (summary entry), screening decisions (screening/screening_uncertain entries), and sub-question candidates; confident screening patches research_articles immediately; uncertain items await Bill's Confirm/Override/Reject
- Research tab article cards: "Add to thread" button still live (source=research_articles:{id})
- Fleet: 10 active agents, unchanged; anthropic 0.97.0 added to mcp-server venv
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Bill smoke-tests extraction: paste desktop analysis into a thread, verify four-bucket output; test uncertain-item resolution buttons. Then: Gap A (automated agent→thread wiring) or ChromaDB leverage card.

---

## Handoff (pick up here)

**2026-05-02 (B-078):**
- **What I was doing:** B-078 — extraction step for desktop-Claude analysis paste: `extract_analysis` callable + `resolve_screening_uncertain` callable in uplink_server.py; Form1 `_add_analysis` rewired; four new entry types rendered; both repos merged and pushed.
- **What I learned:** `_make_screening_handlers` factory pattern is the right idiom for Anvil action closures needing per-entry state — avoids Python closure-in-loop issue cleanly. Supabase JSONB PATCH via PostgREST accepts Python dicts directly. anthropic 0.97.0 installs into mcp-server venv.
- **Continue:** Bill smoke-tests extraction end-to-end: paste desktop Claude analysis into a thread, confirm four-bucket output renders correctly; test Confirm/Override/Reject buttons on a screening_uncertain entry. Uplink needs restart (exit and re-enter Claude Code) to pick up new callables.
- **Left better:** Passback channel complete — desktop Claude can now reason over thread content and have structured implications recovered by the system. The thread architecture is fully functional for the human-in-the-loop research workflow.
- **Usage:** session ~%, weekly ~%

**2026-04-30 (B-075):**
- **What I was doing:** B-075 — Add-to-thread affordances: 106 lines added to Form1/__init__.py; "Add desktop analysis" section + "Add to thread" inline picker on Research tab; merged to master, pushed.
- **What I learned:** get_threads(state='active') already existed from B-071 — no new callable needed; toggle-to-dismiss pattern keeps article cards clean without a modal.
- **Continue:** B-078 completed.
- **Left better:** Threads accumulate content manually from two surfaces.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-073):**
- **What I was doing:** B-073 — Threads tab actions: 251 lines added to Form1; 135 to uplink_server.py (trigger_thread_gather, get_thread_bundle); pushed.
- **What I learned:** Mutable `[t_state]` closure pattern; rebuild actions_panel after wire/unwire only.
- **Continue:** B-075 + B-078 completed.
- **Left better:** Thread architecture v0.1 functionally complete.
- **Usage:** session ~%, weekly ~%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
