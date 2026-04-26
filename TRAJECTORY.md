# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research live (B-055), writing to research_articles
- Anvil UI: 41 callables (6 added B-056); Research tab live with article cards, Run button (fire-and-forget), rating/comment/status, feedback boxes
- GitHub Pages site: iframe now embeds full dashboard (https://inborn-rotating-anole.anvil.app) at 900px; EmbedControl still exists but no longer embedded
- Research micro-version: Cards 1–3 complete. Card 4 (bundle export) queued as B-057. Card 5 (GitHub embed) done. Card 6 (boot feedback pickup) queued as B-058.
- run_context_research fixed: batch dedup, 5-per-source fetch, 10-article cap per run — confirmed 4 fresh articles on first fixed run
- B-053 (bootstrap step 10) still open — boot lesson retrieval absent from Bill-initiated sessions

**Project arc next:** B-057 (research bundle export). Then B-058 (boot-time feedback pickup). B-053 still pending but lower priority than completing the research micro-version.

---

## Handoff (pick up here)

**2026-04-26 (B-056 + fixes):**
- **What I was doing:** B-056 Research tab complete; then diagnosed and fixed run_context_research dedup (batch dedup, deeper fetch, 10-article cap); fixed Anvil Link target kwarg; fixed invoke_agent 15s timeout (fire-and-forget thread); updated GitHub Pages iframe to full dashboard; wrote B-057 and B-058.
- **What I learned:** Anvil's Link component does not accept target='_blank' in client Python. invoke_agent must be fire-and-forget (background thread) for long-running n8n workflows — the webhook holds the connection open until the workflow completes. run_context_research was fetching only 1 result per source, so the dedup exhausted the well after one run.
- **Continue:** B-057 — add get_research_bundle callable to uplink_server.py and Export button to Research tab.
- **Left better:** Research tab is fully functional: Run button fires in ~1s, 4+ fresh articles per run, rating/comment/status/feedback all wired. GitHub site shows full dashboard.
- **Usage:** session ~55%, weekly ~65%

**2026-04-26 (B-055):** context_engineering_research agent live. 2 articles inserted first run, dedup confirmed second run.

**2026-04-25:** B-052 complete. Boot step 10 coverage gap identified — absent from Bill-initiated sessions.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
