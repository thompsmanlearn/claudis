# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents (11th — autonomous_growth_scheduler — paused); context_engineering_research added (B-055), on-demand research agent writing to research_articles
- Boot chain: 11 steps — live-state ping (step 9), lesson retrieval from ChromaDB (step 10), execute (step 11)
- Anvil UI complete: 35 callables, all 5 UI gaps closed; dashboard covers fleet, sessions, lessons, memory, skills, artifacts
- research_articles + agent_feedback schema live (B-054). Research agent live (B-055). Cards 3–6 of the research micro-version remain.
- ChromaDB loop: boot step 10 coverage gap (B-053) still open — absent from Bill-initiated sessions.

**Project arc next:** B-053 (add step 10 to bootstrap skill). After that: Card 3 of research micro-version (Anvil view + Run button for context_engineering_research). GT-4/GT-5 lesson rewrites still pending.

---

## Handoff (pick up here)

**2026-04-26:** B-055 complete. context_engineering_research agent built: stats_server /run_context_research, n8n webhook trigger, Haiku summarization, dedup by URL, error_logs integration. Search via HN Algolia + arXiv (no external search API key required). 2 articles from first run; dedup confirmed on second run; error path verified. Branch merged, pushed.
- **Next action:** B-053 — add step 10 to bootstrap skill. Then Card 3 of research micro-version (Anvil Run button + view).

**2026-04-25:** B-052 complete. Primary finding: boot step 10 (lesson retrieval) absent from all Bill-initiated sessions — coverage gap. lesson_injector accounts for all existing times_applied counts (8–30, valid, Sentinel path).

**2026-04-25:** B-048 complete. LEAN_BOOT is now the single boot path; live-state ping runs at step 9 before execute. developer_context_load deprecated; session_notes archived.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
