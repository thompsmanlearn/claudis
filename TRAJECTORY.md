# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research now using 5 broader queries (autonomous agent, agent dashboard, vector memory, n8n orchestration, Reflexion/ExpeL)
- Anvil UI: 43 callables (get_research_counters added); Research tab status line shows total · unreviewed · new(24h)
- research_articles: 16 total (10 fresh from new queries, 0 dupes, 5 capped); all 4 bundle-review feedback rows marked processed
- Research micro-version: Cards 1–5 complete. Card 6 (boot feedback pickup) queued as B-058.
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits
- B-053 (bootstrap step 10) still open

**Project arc next:** B-058 (boot-time feedback pickup) — add agent_feedback query step to LEAN_BOOT.md and bootstrap skill. Closes the research micro-version.

---

## Handoff (pick up here)

**2026-04-26 (bundle review):**
- **What I was doing:** Acted on 3 of 4 desktop Claude bundle review items: (1) confirmed PER_RUN_CAP=10 already set, replaced 5 narrow queries with broader ones; (2) added get_research_counters() callable + counters to Research tab status line; (3) marked all 4 feedback rows processed. Ran agent: 10 fresh articles inserted, 5 capped, 0 dupes.
- **What I learned:** stats-server runs from ~/aadp/stats-server/, not ~/aadp/claudis/stats-server/ — must cp after editing. arXiv exact-phrase matching fails for HN-style queries; for new query set, arXiv returns 0 (acceptable). claudis repo push requires pull --rebase if desktop session pushed first.
- **Continue:** B-058 — add agent_feedback pickup step to LEAN_BOOT.md (between steps 9 and 10) and bootstrap skill. Deferred item 4 (artifact visibility UI polish) not actioned.
- **Left better:** Research agent now finds genuinely different articles each run. Research tab shows live counters. Feedback loop closed: 4 items reviewed, acted on, marked processed.
- **Usage:** session ~45%, weekly ~75%

**2026-04-26 (B-057):** get_research_bundle callable + Export button. PostgREST OR+AND pattern confirmed.

**2026-04-26 (B-056 + fixes):** Research tab complete; run_context_research dedup fixed; GitHub Pages iframe updated.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
