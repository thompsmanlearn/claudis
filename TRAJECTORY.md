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
- **B-132 complete (2026-05-17):** Bill input channel live. `bill_input` table in Supabase, `submit_bill_input` + `get_bill_input_response` callables in uplink_server.py, three-mode input panel (Question/Comment/Command) on Home tab above export buttons, LEAN_BOOT.md step 4.5 checks pending input before reading DIRECTIVES.md. Commits: claudis 1d2ae51, claude-dashboard 6c87fc2.
- **Phase 1 remaining:** Boot path unification (bootstrap + LEAN_BOOT.md → one sequence). Needs design pass before card.

**Project arc next:** Phase 1 boot path unification (design pass first). Then Phase 2.

---

## Handoff (pick up here)

**2026-05-17 (B-132 Bill input channel):**
- **What I was doing:** Built the bill_input channel end-to-end: Supabase table, two Anvil callables, Home tab UI panel, LEAN_BOOT.md step 4.5. All pushed and uplink restarted.
- **What I learned:** LEAN_BOOT.md step 4.5 runs before DIRECTIVES.md — Command mode overwrites DIRECTIVES.md and the session executes that instead. The bill_input table holds at most one row; submit_bill_input deletes all existing rows before inserting.
- **Continue:** Phase 1 boot path unification — bootstrap skill + LEAN_BOOT.md → one sequence. Needs design pass with Desktop Claude before writing a card.
- **Left better:** Bill can now type a Question, Comment, or Command into Anvil before triggering a lean session; Claude Code processes it at boot and posts the response back.

**2026-05-17 (B-131 Desktop Claude export):**
- **What I was doing:** B-131 — added `get_desktop_bundle()` callable and "Export for Desktop Claude" button on Home tab. Commits: claudis 8fb3337, claude-dashboard 730aae2.
- **What I learned:** Cards may say "Workspace tab" but the actual tab is "Home" — always verify UI element names by reading Form1/__init__.py rather than trusting card descriptions.
- **Continue:** B-132 complete; next is boot path unification design pass.
- **Left better:** Desktop Claude now has a purpose-built export covering threads, research, session deltas, fragilities, and store counts.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
