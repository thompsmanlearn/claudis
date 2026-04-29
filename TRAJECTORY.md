# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread callable layer live (B-071): create_thread, add_thread_entry, update_thread_state, wire_thread_agent, get_threads, get_thread_entries registered in uplink_server.py; last_activity_at trigger in Supabase
- Thread substrate complete (B-070 + B-071): threads + thread_entries tables, trigger, ChromaDB collection, callable API — ready for Anvil UI (B-072)
- Fleet: 10 active agents, unchanged; lesson curation stable
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-072 — Anvil Threads tab read view.

---

## Handoff (pick up here)

**2026-04-29 (B-071):**
- **What I was doing:** B-071 — Thread write callables: 6 uplink callables + last_activity_at Supabase trigger. Smoke test passed (10/10). Merged and pushed.
- **What I learned:** Supabase trigger for denormalized timestamps (last_activity_at) is the right pattern — putting it in callable code means every future writer has to remember; trigger guarantees it automatically. Use `_insert_thread_entry` as a shared helper so all callers (create_thread, update_thread_state, wire_thread_agent) share the embed/chromadb logic.
- **Continue:** B-072 — Anvil Threads tab read view (get_threads + get_thread_entries callables already available).
- **Left better:** Thread callable layer live; threads are now a usable working surface from code.
- **Usage:** session ~20%, weekly ~%

**2026-04-29 (B-074 Option A):**
- **What I was doing:** B-074 — Adding `git pull --rebase` before first push in close-session. Direct edit to skills/close-session.md on main (no branch — doc change).
- **What I learned:** `git pull --rebase` fails with "unstaged changes" if called before staging — must commit or stash first. The rule belongs after staging, not before. Exercised successfully on its own commit.
- **Continue:** B-071 — thread write callables (create_thread, add_thread_entry, update_thread_state, wire_thread_agent).
- **Left better:** close-session v30 now pulls before pushing; divergence failure mode eliminated at the source.
- **Usage:** session ~%, weekly ~%

**2026-04-28 (B-070):**
- **What I was doing:** B-070 — Thread architecture substrate: threads + thread_entries Supabase tables, thread_entries ChromaDB collection, DEEP_DIVE_BRIEF Section 7 updated.
- **What I learned:** Session opened with diverged claudis repo — local B-069 artifact commit hadn't been pushed before Anvil wrote new DIRECTIVES.md to remote. `git pull --rebase` resolved it. B-074 filed and now shipped.
- **Continue:** B-071 — thread write callables. All 5 B-070 acceptance criteria verified.
- **Left better:** Thread substrate live and tested; divergence failure mode now permanently fixed.
- **Usage:** session ~%, weekly ~%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
