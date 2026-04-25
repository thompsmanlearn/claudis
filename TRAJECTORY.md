# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 9 active agents (10th — autonomous_growth_scheduler — paused); `webhook_url` column added, 3 on-demand agents populated
- Boot chain: 11 steps — live-state ping (step 9), lesson retrieval from ChromaDB (step 10), execute (step 11)
- Anvil UI complete: 35 callables, all 5 UI gaps closed; dashboard covers fleet, sessions, lessons, memory, skills, artifacts
- ChromaDB loop tightened: boot retrieval + improved lesson write quality checklist + times_applied tracking

**Project arc next:** ChromaDB destination now active — validate that boot retrieval surfaces relevant lessons after a few sessions; then move toward system better leveraging ChromaDB (semantic retrieval for research, retrieval_log hygiene).

---

## Handoff (pick up here)

**2026-04-25:** Anvil UI gaps all closed (artifact comments, error log resolve, work queue detail, per-agent invocation). ChromaDB loop improved: boot now retrieves lessons at step 10; close-session lesson quality checklist added; times_applied tracking tightened. PROJECT_STATE.md created and current.
- **Next action:** Write DIRECTIVES.md for next session before closing — either a new card or free-text direction. If stale card found at boot, Telegram Bill and wait.
- **Watch:** After a few sessions, check `never_applied` count in Anvil Lessons tab — if still high, boot retrieval query quality needs tuning.

**2026-04-25:** B-048 complete. LEAN_BOOT is now the single boot path; live-state ping runs at step 9 before execute. developer_context_load deprecated; session_notes archived.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
