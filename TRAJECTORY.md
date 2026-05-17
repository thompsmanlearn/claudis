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
- **Anvil UI input flow designed (2026-05-17):** Full design settled for `bill_input` table + three-mode input surface (Question/Comment/Command) + LEAN_BOOT.md priority step + response window. Design summary ready for Desktop Claude to write the card. Trigger Lean Session button confirmed working end-to-end.
- **Phase 1 remaining:** Boot path unification (bootstrap + LEAN_BOOT.md → one sequence). Needs design pass before card.

**Project arc next:** Anvil UI input flow card (Desktop Claude writes it, Bill brings it back). Then Phase 1 boot path unification.

---

## Handoff (pick up here)

**2026-05-17 (design session — Anvil UI input flow):**
- **What I was doing:** Design discussion with Bill. Investigated bootstrap skill, confirmed Trigger Lean Session is working end-to-end, settled design for bill_input table + three-mode input surface. No code built — output is a design summary for Desktop Claude to write the card.
- **What I learned:** Trigger Lean Session spawns lean_runner.sh → `claude -p --dangerously-skip-permissions` with LEAN_BOOT.md as the prompt. The full boot sequence runs non-interactively. This means any new LEAN_BOOT.md step runs automatically when Bill hits the button.
- **Continue:** Take the design summary (in session artifact 2026-05-17-anvil-input-flow-design.md) to Desktop Claude. Ask it to write the card. Bring the card back. Card requires two-pass review marker since it creates a new table + new UI surface — it's already reviewed in this session, so Desktop Claude should include "Design reviewed by Claude Code."
- **Left better:** Design is fully resolved — no open questions remain. Desktop Claude can write the card without needing another design pass.

**2026-05-17 (B-131 Desktop Claude export):**
- **What I was doing:** B-131 — added `get_desktop_bundle()` callable and "Export for Desktop Claude" button on Home tab. Commits: claudis 8fb3337, claude-dashboard 730aae2.
- **What I learned:** Cards may say "Workspace tab" but the actual tab is "Home" — always verify UI element names by reading Form1/__init__.py rather than trusting card descriptions.
- **Continue:** Anvil UI input flow card per above.
- **Left better:** Desktop Claude now has a purpose-built export covering threads, research, session deltas, fragilities, and store counts.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
