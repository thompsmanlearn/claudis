# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 10 active agents; context_engineering_research pulls from 6 sources (HN, arXiv, dev.to, GitHub, lobste.rs, Medium)
- Anvil UI: 52 callables (7 new bundle callables); all 7 tabs have ⬇ Export buttons — Fleet, Sessions, Lessons, Memory, Errors, Skills, Artifacts
- Export pattern complete: every tab produces a structured markdown bundle (YAML frontmatter + Summary + domain sections) paste-ready for desktop Claude analysis
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-061a (bring close-session.md/bootstrap.md into claudis version control) is ready. Or Bill chooses new direction.

---

## Handoff (pick up here)

**2026-04-26 (B-061):**
- **What I was doing:** B-061 — Generalizing Export across all dashboard tabs. Added 7 uplink callables and ⬇ Export buttons to every tab.
- **What I learned:** `_run_export()` helper cleanly abstracts the clipboard-then-fallback pattern; Errors export lives inside Memory tab (sb_row) not as a standalone tab. Fleet tab needed a new header FlowPanel since it has no `_build_fleet_layout()` method.
- **Continue:** B-061a (bring close-session.md/bootstrap.md into claudis version control) is the natural next step.
- **Left better:** All tabs now export paste-ready markdown bundles for desktop Claude analysis — the pattern proven by B-057 Research export is now system-wide.
- **Usage:** session ~25%, weekly ~100%

**2026-04-26 (B-060):**
- **What I was doing:** B-060 — Anvil feedback thread visibility. Made agent_feedback write-back trail visible in Research tab as conversation threads.
- **What I learned:** Anvil has no "muted" role — use font_size=13 vs 14 for visual weight distinction between deferred and acted responses.
- **Continue:** B-061 generalize export. Done this session.
- **Left better:** Research tab shows full feedback conversation surface with ✅/⏸ icons.
- **Usage:** session ~15%, weekly ~100%

**2026-04-26 (expand-sources):**
- **What I was doing:** Expanding context_engineering_research from 2 sources to 6. Fixed empty-fetch. Closed 2 stale work_queue items.
- **What I learned:** dev.to broad tags return noisy articles; domain-specific tags required.
- **Continue:** Bill sets next direction.
- **Left better:** research_articles growing from richer source set; empty-fetch errors no longer produce thin rows.
- **Usage:** session ~10%, weekly ~95%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
