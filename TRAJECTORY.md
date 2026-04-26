# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research live, writing to research_articles
- Anvil UI: 42 callables (get_research_bundle added B-057); Research tab now has ⬇ Export button — calls bundle callable, tries clipboard, falls back to TextArea
- Research micro-version: Cards 1–5 complete. Card 6 (boot feedback pickup) queued as B-058.
- Live data confirmed: 4 articles in most recent run, 4 pending feedback rows surfaced in bundle
- B-053 (bootstrap step 10) still open — boot lesson retrieval absent from Bill-initiated sessions

**Project arc next:** B-058 (boot-time feedback pickup) — query agent_feedback at boot, surface pending rows in summary, mark consumed when acted on. Closes the research micro-version.

---

## Handoff (pick up here)

**2026-04-26 (B-057):**
- **What I was doing:** B-057 complete — get_research_bundle callable added to uplink_server.py; ⬇ Export button added to Research tab header; uplink restarted cleanly; both repos pushed.
- **What I learned:** PostgREST `or=(processed.is.null,processed.eq.false)` combined with a separate `target_type=in.(agent,anvil_view)` filter works as AND + OR — no need for separate requests. Verified on live data: 4 articles, 4 pending feedback rows.
- **Continue:** B-058 — add agent_feedback pickup step to LEAN_BOOT.md (between current steps 9 and 10) and to bootstrap skill. Query pending feedback at boot, surface in summary, mark rows processed when acted on.
- **Left better:** Bundle export wired end-to-end. Bill can press Export, paste markdown into desktop Claude, and get full run context with ratings, comments, and pending feedback in one shot.
- **Usage:** session ~30%, weekly ~70%

**2026-04-26 (B-056 + fixes):** Research tab complete; run_context_research dedup fixed (4 fresh articles/run); GitHub Pages iframe updated.

**2026-04-26 (B-055):** context_engineering_research agent live. 2 articles inserted first run.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
