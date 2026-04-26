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

**2026-04-26 (B-055):**
- **What I was doing:** Building context_engineering_research agent — stats_server /run_context_research, n8n webhook (gzCSocUFNxTGIzSD), Haiku summarization, dedup by URL, error_logs. 2 articles inserted first run, dedup confirmed second run, error path verified.
- **What I learned:** error_logs.workflow_id is NOT NULL with no default — any non-n8n error writer must include it. _sb_upsert (merge-duplicates) fails 400 on tables without unique constraints — need plain INSERT with `Prefer: return=minimal`.
- **Continue:** Execute B-053 — add lesson retrieval (step 10) to bootstrap skill and switch boot query to Haiku expansion.
- **Left better:** research_articles is now being filled by a live agent. HN+arXiv search pattern documented as reusable lesson for future cards.
- **Usage:** session ~35%, weekly ~55%

**2026-04-25:** B-052 complete. Boot step 10 coverage gap identified — absent from all Bill-initiated sessions. lesson_injector accounts for all times_applied counts (8–30, Sentinel path only).

**2026-04-25:** B-048 complete. LEAN_BOOT is now the single boot path; live-state ping at step 9; session_notes archived.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
