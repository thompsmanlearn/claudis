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
- **B-133 design analysis complete (2026-05-17):** Boot path unification design facts delivered to Desktop Claude. Key findings: lean_runner.sh lesson injection is dead (lesson_injector deleted B-130, webhook 404); only real redundancy is double git pull; bootstrap is Sentinel-only and currently invoked by nothing active. Desktop Claude to write B-133 card.

**Project arc next:** B-133 (boot path unification) — Desktop Claude writes card, Bill brings it back. Then Phase 2.

---

## Handoff (pick up here)

**2026-05-17 (B-133 design analysis — boot path unification):**
- **What I was doing:** Design collaboration for Desktop Claude before B-133 is written. Answered 5 questions about LEAN_BOOT.md vs bootstrap divergence, active invocation paths, and double lesson injection.
- **What I learned:** lean_runner.sh lesson injection via n8n webhook is dead — lesson_injector was deleted in B-130, webhook returns 404, CONTEXT_BLOCK is always empty. Only LEAN_BOOT.md step 11 (inject_context_v3 direct) is active. Double git pull is the only live redundancy. bootstrap is Sentinel-only, invoked by nothing currently active.
- **Continue:** Desktop Claude writes B-133 card using the design analysis. Bill brings it back. Card scope: remove dead lesson injection from lean_runner.sh, clarify bootstrap as Sentinel-only, optionally add heartbeat update to LEAN_BOOT.md (currently missing from lean sessions).
- **Left better:** Complete factual picture of the boot path delivered — Desktop Claude can write the card without further research.

**2026-05-17 (B-132 Bill input channel):**
- **What I was doing:** Built the bill_input channel end-to-end: Supabase table, two Anvil callables, Home tab UI panel, LEAN_BOOT.md step 4.5. All pushed and uplink restarted.
- **What I learned:** LEAN_BOOT.md step 4.5 runs before DIRECTIVES.md — Command mode overwrites DIRECTIVES.md and the session executes that instead. The bill_input table holds at most one row; submit_bill_input deletes all existing rows before inserting.
- **Continue:** B-133 per above.
- **Left better:** Bill can now type a Question, Comment, or Command into Anvil before triggering a lean session; Claude Code processes it at boot and posts the response back.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
