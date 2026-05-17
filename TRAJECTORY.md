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
- **B-133 complete (2026-05-17):** Boot path cleanup done. Dead lesson injection removed from lean_runner.sh (lesson_injector deleted B-130, webhook was 404 every session). session_notes_load removed from bootstrap.md (table archived 2026-04-25). Boot heartbeat added to LEAN_BOOT.md step 1.5 — lean sessions now write claudis_current_task to system_config at start. Commit a4f334b.

**Project arc next:** Phase 2 — scoped with Desktop Claude. Research pipeline reader gap is the main open thread.

---

## Handoff (pick up here)

**2026-05-17 (post-B133 polish):**
- **What I was doing:** Two small follow-ons after B-133 close: (1) LEAN_BOOT.md stale-card briefing now includes bill_input Q&A when a Question/Comment was processed at step 4.5 (f9af0cb). (2) Anvil Home tab "Get Output" button now always visible (not hidden until submit), fetches and auto-copies in one click (98c5e74, claude-dashboard).
- **What I learned:** bill_input response panel was only shown after Submit in the current browser session — a page refresh hid it. Always-visible is the right default for output surfaces.
- **Continue:** Phase 2 scoping with Desktop Claude. Research pipeline reader gap is the main open thread. DIRECTIVES.md still says Run B-133 — update before next lean session.
- **Left better:** Bill can submit a question, trigger lean, come back later and hit "Get Output" on the Home tab — answer appears and copies in one click, even after a page refresh.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
