# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 9 active agents (10th — autonomous_growth_scheduler — paused, workflow_id null)
- Boot chain: single path via LEAN_BOOT.md; Step 9 live-state ping added 2026-04-25
- developer_context_load deprecated; session_notes retired and archived
- Anvil backend has 33 callables; UI has known gaps

**Project arc next:** Close UI gaps — work queue detail, error log resolve, site status + regenerate, artifact comments, per-agent invocation.

---

## Handoff (pick up here)

**2026-04-25:** B-048 complete. LEAN_BOOT is now the single boot path; live-state ping runs at step 9 before execute. developer_context_load deprecated; session_notes archived.
- **Still open:** Close-session skill Step 3 needs update (stop appending trajectory logs; rewrite current state instead). `PROJECT_STATE.md` not yet created.
- **Then:** Return to Anvil UI — close UI gaps (see project arc next).

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
