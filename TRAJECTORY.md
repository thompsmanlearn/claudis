# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research pulls from 6 sources (HN, arXiv, dev.to, GitHub, lobste.rs, Medium) with per-source cap=5, global cap=20, skip-on-empty-fetch
- Anvil UI: 43 callables; Research tab complete with Run, Export, rate/comment/status, feedback boxes
- research_articles: 58 total; 2 stale work_queue items closed
- Boot feedback pickup live: both LEAN_BOOT (step 10) and bootstrap (step 3) read agent_feedback at start
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** No immediate directive set. Bill chooses next direction at session start.

---

## Handoff (pick up here)

**2026-04-26 (expand-sources):**
- **What I was doing:** Expanding context_engineering_research from 2 sources (HN, arXiv) to 6 (+ dev.to, GitHub, lobste.rs, Medium). Fixed empty-fetch to skip rather than insert thin rows. Closed 2 stale work_queue items.
- **What I learned:** dev.to broad tags ("ai", "machinelearning") return noisy popular articles; domain-specific tags ("agents", "n8n", "llmops") are required. Per-source cap prevents one source dominating insertion budget.
- **Continue:** Bill sets next direction. DIRECTIVES.md is empty.
- **Left better:** research_articles growing from richer source set (58 total); empty-fetch errors no longer produce thin rows.
- **Usage:** session ~10%, weekly ~95%

**2026-04-26 (consolidation):**
- **What I was doing:** Backlog audit, research micro-version milestone ADR, TRAJECTORY.md cleanup.
- **What I learned:** B-053 was complete since 2026-04-25 — TRAJECTORY.md was carrying a stale reference. BACKLOG.md was already clean.
- **Continue:** Bill sets next direction. DIRECTIVES.md is empty — no card queued.
- **Left better:** Stale B-053 references cleared; milestone ADR documents the round-trip pattern.
- **Usage:** session ~15%, weekly ~85%

**2026-04-26 (B-058):** Boot feedback pickup — agent_feedback step in LEAN_BOOT (step 10) and bootstrap (step 3). Research micro-version closed.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
