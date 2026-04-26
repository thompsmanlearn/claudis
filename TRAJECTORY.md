# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research using 5 broader queries
- Anvil UI: 43 callables; Research tab shows total · unreviewed · new(24h) counters
- research_articles: 16 total; research micro-version fully closed (B-053 through B-058)
- B-058 complete: agent_feedback pickup added to LEAN_BOOT.md (step 10) and bootstrap skill (step 3)
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** ChromaDB better utilized — surface semantic memory in more workflows; B-053 (bootstrap step 10) still open as next candidate.

---

## Handoff (pick up here)

**2026-04-26 (B-058):**
- **What I was doing:** Added agent_feedback pending feedback pickup step to LEAN_BOOT.md (new step 10, renumbered 11–12) and bootstrap skill (new step 3, renumbered 4–7). Research micro-version now closed.
- **What I learned:** agent_feedback table has processed_in_session column — the full UPDATE pattern is ready; no schema work needed. Current table is empty (all previously processed).
- **Continue:** B-053 (bootstrap step 10 — lesson retrieval step was added but B-053 may have other scope; confirm before closing). Or pick next ChromaDB utilization card.
- **Left better:** Both entry paths (LEAN_BOOT + bootstrap) now surface Anvil feedback at boot, closing the feedback loop for all future sessions.
- **Usage:** session ~10%, weekly ~85%

**2026-04-26 (bundle review):** Research agent broader queries; get_research_counters callable; all 4 bundle-review feedback rows marked processed.

**2026-04-26 (B-057):** get_research_bundle callable + Export button. PostgREST OR+AND pattern confirmed.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
