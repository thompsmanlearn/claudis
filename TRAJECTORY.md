# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research using 5 broader queries
- Anvil UI: 43 callables; Research tab complete with Run, Export, rate/comment/status, feedback boxes
- research_articles: 16 total; research micro-version fully closed (B-054 through B-058)
- Boot feedback pickup live: both LEAN_BOOT (step 10) and bootstrap (step 3) read agent_feedback at start
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** No immediate directive set. Bill chooses next direction at session start.

---

## Handoff (pick up here)

**2026-04-26 (consolidation):**
- **What I was doing:** Backlog audit, research micro-version milestone ADR, TRAJECTORY.md cleanup.
- **What I learned:** B-053 was complete since 2026-04-25 (commit 92e766d) — TRAJECTORY.md was carrying a stale "still open" reference. BACKLOG.md was already clean; misalignment was only in handoff notes.
- **Continue:** Bill sets next direction. DIRECTIVES.md is empty — no card queued.
- **Left better:** Stale B-053 references cleared; milestone ADR in architecture/decisions/ documents the round-trip pattern for future sessions.
- **Usage:** session ~15%, weekly ~85%

**2026-04-26 (B-058):** Boot feedback pickup — agent_feedback step in LEAN_BOOT (step 10) and bootstrap (step 3). Research micro-version closed.

**2026-04-26 (B-057):** get_research_bundle callable + Export button. PostgREST OR+AND pattern confirmed.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
