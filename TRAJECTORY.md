# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Lean mode: sentinel timer disabled, `autonomous_growth_scheduler` deactivated. Three-way collaboration model active: Bill directs, Claude Code executes, Desktop Claude is design skeptic.
- **Chapters 1–3 complete (B-084–B-112).** Post-chapter: execution disciplines, comment-driven cards, two-pass review, reader-writer check.
- **B-129 complete (2026-05-10):** Workpad Brave search live. Full dashboard: Home/Workpad/Threads/Sessions/System (5 tabs).
- **2026-05-16 system evaluation:** Full audit of what's performative vs. useful. Key finding: research pipeline finds and synthesizes but output lands in `experimental_outputs` with no reader — loop broken. Dashboard not used. Three-way collaboration ritual established. Phase 1–4 rebuild plan scoped with Desktop Claude.
- **B-130 complete (2026-05-16):** lesson_injector and session_health_reporter retired (n8n workflows deleted). agent_health_monitor wired to 6h schedule — already had Telegram path via Sandbox Notify. Fleet: 9 → 7 active. Commit 3e9eb6c.
- **Phase 1 next:** Boot path unification (bootstrap + LEAN_BOOT.md → one sequence) and export redesign (research-shaped, Desktop Claude as named reader). Both need design passes before cards.

**Project arc next:** Phase 1 — close the input loop. Boot path unification, export redesign.

---

## Handoff (pick up here)

**2026-05-16 (B-130 + system evaluation):**
- **What I was doing:** Full system evaluation with Bill and Desktop Claude. Identified performative complexity pattern throughout: features that satisfy spec shape but don't close the loop. Executed B-130: retired lesson_injector + session_health_reporter, added 6h schedule to agent_health_monitor. Commit 3e9eb6c.
- **What I learned:** Sandbox Notify (Ls0znhBx9W5Cr6sV) already sends Telegram with 24h rate limiting — not an orphan sink as the agent description implied. Agent descriptions can be misleading; read the workflow before assuming.
- **Continue:** Phase 1 — boot path unification and export redesign. Both need design passes (Desktop Claude as skeptic) before cards are written. Gate: "After this is built, Bill will specifically do X."
- **Left better:** Fleet cleaned to 7 active agents. agent_health_monitor now runs every 6h and will alert Bill on Telegram if any agent accumulates 3+ consecutive errors.

**2026-05-10 (B-129 Workpad Brave search):**
- **What I was doing:** B-129 — wired Brave Search into Workpad. `search_brave` uplink callable wraps stats_server `/web_search`. Commits: claudis 00e805d, claude-dashboard 32be089.
- **What I learned:** When BACKLOG.md has a card cut off mid-sentence, halt and Telegram before executing.
- **Continue:** Phase 1 per above. 1 pending agent_build in work_queue (SpecOps GUI, 2026-05-03).
- **Left better:** Workpad supports full research motion: search → click result → read full page.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
