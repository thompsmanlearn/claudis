# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture substrate live (B-070): `threads` + `thread_entries` Supabase tables, `thread_entries` ChromaDB collection excluded from default boot retrieval by design
- B-074 filed: fix claudis git divergence — close-session pull-before-push (Option A) + optional Anvil Write Directive pre-flight check (Option B)
- Fleet: 10 active agents, unchanged; lesson curation stable (chromadb_id IS NULL = 0)
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-071 — thread write callables (create_thread, add_thread_entry, update_thread_state, wire_thread_agent).

---

## Handoff (pick up here)

**2026-04-28 (B-070):**
- **What I was doing:** B-070 — Thread architecture substrate: threads + thread_entries Supabase tables, thread_entries ChromaDB collection, DEEP_DIVE_BRIEF Section 7 updated.
- **What I learned:** Session opened with diverged claudis repo — local B-069 session artifact commit hadn't been pushed before Anvil wrote new DIRECTIVES.md to remote. `git pull --rebase` resolved it cleanly. B-074 filed to make close-session pull before push.
- **Continue:** B-071 — thread write callables (create_thread, add_thread_entry, update_thread_state, wire_thread_agent). All 5 B-070 acceptance criteria verified.
- **Left better:** Thread substrate live and tested; divergence failure mode documented and card filed for permanent fix.
- **Usage:** session ~%, weekly ~%

**2026-04-26 (B-062):**
- **What I was doing:** B-062 — Lesson curation: Never Applied age filter, broken-lesson backfill, recurring sync check.
- **What I learned:** When lessons are written to ChromaDB using the Supabase UUID as doc_id (older convention), the Supabase chromadb_id column may remain NULL even though the lesson IS in ChromaDB. Backfill in that case means pointing chromadb_id to the UUID, not creating a new entry.
- **Continue:** Bill sets next direction.
- **Left better:** Never Applied view trustworthy (7-day threshold); 4 backfilled lessons now visible to semantic search; close-session step 7a catches future sync gaps.
- **Usage:** session ~%, weekly ~%

**2026-04-26 (B-061a):**
- **What I was doing:** B-061a — Bring close-session.md and bootstrap.md into claudis version control. Replaced flat files with symlinks into claudis/skills/.
- **What I learned:** Symlinks from non-git directories into the versioned repo eliminate manual sync entirely — cleaner than the lean_runner.sh dual-location pattern.
- **Continue:** Bill sets next direction.
- **Left better:** close-session.md and bootstrap.md now in git; DEEP_DIVE_BRIEF gap note resolved.
- **Usage:** session ~28%, weekly ~100%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
