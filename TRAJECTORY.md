# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research pulls from 6 sources (HN, arXiv, dev.to, GitHub, lobste.rs, Medium)
- Anvil UI: 52 callables; all 7 tabs have ⬇ Export buttons; Never Applied filter now excludes lessons < 7 days old
- Lesson curation: 4 broken lessons backfilled (chromadb_id IS NULL → 0); close-session now checks sync integrity on every close
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-062 complete. Bill sets next direction.

---

## Handoff (pick up here)

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

**2026-04-26 (B-061):**
- **What I was doing:** B-061 — Generalizing Export across all dashboard tabs. Added 7 uplink callables and ⬇ Export buttons to every tab.
- **What I learned:** `_run_export()` helper cleanly abstracts the clipboard-then-fallback pattern; Fleet tab has no `_build_fleet_layout()` — needed inline header FlowPanel.
- **Continue:** B-061a. Done above.
- **Left better:** All 7 tabs export paste-ready markdown bundles for desktop Claude analysis.
- **Usage:** session ~25%, weekly ~100%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
