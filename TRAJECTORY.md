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
- **B-131 complete (2026-05-17):** Desktop Claude export live. `get_desktop_bundle()` callable in uplink_server.py; "Export for Desktop Claude" button on Home tab. Export covers active threads (summaries expanded), recent research (full URLs), session artifacts (capability delta), fragilities, store counts. Commits: claudis 8fb3337, claude-dashboard 730aae2.
- **Phase 1 remaining:** Boot path unification (bootstrap + LEAN_BOOT.md → one sequence). Needs design pass before card.

**Project arc next:** Phase 1 — boot path unification. Then Phase 2 (close the research output loop).

---

## Handoff (pick up here)

**2026-05-17 (B-131 Desktop Claude export):**
- **What I was doing:** B-131 — added `get_desktop_bundle()` callable and "Export for Desktop Claude" button on Home tab. Commits: claudis dd616d5 (attempt), 8fb3337 (main merge); claude-dashboard 0414d3c (attempt), 730aae2 (master merge).
- **What I learned:** Cards may say "Workspace tab" but the actual tab is "Home" — always verify UI element names by reading Form1/__init__.py rather than trusting card descriptions.
- **Continue:** Boot path unification (Phase 1 remaining). Needs design pass with Desktop Claude before writing the card. Gate question to ask: "After unification, what specifically will Bill do differently?"
- **Left better:** Desktop Claude now has a purpose-built export — Bill can paste it into a take-stock conversation and get threads, research, fragilities, and deltas in one shot.

**2026-05-16 (B-130 + system evaluation):**
- **What I was doing:** Full system evaluation with Bill and Desktop Claude. Executed B-130: retired lesson_injector + session_health_reporter, added 6h schedule to agent_health_monitor. Commit 3e9eb6c.
- **What I learned:** Sandbox Notify (Ls0znhBx9W5Cr6sV) already sends Telegram with 24h rate limiting — not an orphan sink as the agent description implied. Agent descriptions can be misleading; read the workflow before assuming.
- **Continue:** Phase 1 remaining (boot path unification) per above.
- **Left better:** Fleet cleaned to 7 active agents. agent_health_monitor alerts Bill on Telegram if any agent accumulates 3+ consecutive errors.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
