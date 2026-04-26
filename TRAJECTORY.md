# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research pulls from 6 sources (HN, arXiv, dev.to, GitHub, lobste.rs, Medium)
- Anvil UI: 45 callables; Research tab now shows Feedback History threads (pending + last 10 resolved, ✅/⏸ icons, session + result link)
- agent_feedback OS pattern complete: B-059 write-back schema + B-060 thread visibility — feedback is now a full visible conversation surface
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-061a (bring close-session.md/bootstrap.md into claudis version control) is ready. Or Bill chooses new direction.

---

## Handoff (pick up here)

**2026-04-26 (B-060):**
- **What I was doing:** B-060 — Anvil feedback thread visibility. Made agent_feedback write-back trail visible in Research tab as conversation threads.
- **What I learned:** Anvil has no "muted" role — use font_size=13 vs 14 for visual weight distinction between deferred and acted responses. The OS pattern (B-059 write-back + B-060 visibility) is now fully wired.
- **Continue:** B-061a is the natural next step (bring close-session.md/bootstrap.md into claudis version control). Ready in BACKLOG.md.
- **Left better:** Research tab now shows full feedback conversation surface with ✅/⏸ icons; get_research_bundle includes resolved feedback section.
- **Usage:** session ~15%, weekly ~100%

**2026-04-26 (expand-sources):**
- **What I was doing:** Expanding context_engineering_research from 2 sources to 6. Fixed empty-fetch. Closed 2 stale work_queue items.
- **What I learned:** dev.to broad tags return noisy articles; domain-specific tags required. Per-source cap prevents budget dominance.
- **Continue:** Bill sets next direction.
- **Left better:** research_articles growing from richer source set (58 total); empty-fetch errors no longer produce thin rows.
- **Usage:** session ~10%, weekly ~95%

**2026-04-26 (B-058):** Boot feedback pickup — agent_feedback step in LEAN_BOOT (step 10) and bootstrap (step 3). Research micro-version closed.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
