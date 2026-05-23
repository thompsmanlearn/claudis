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
- **2026-05-17 Bill session:** Two investigations (session status stuck, safe stop mechanism) → two bug fixes (write_phase UPSERT, Home tab status label) → Request Close button built (Option B: flag checked by lean_runner after Claude exits, second close-session invocation). GEMINI_API_KEY added. B-135 built: /run_paper_synthesis (gemini-2.5-flash), research_briefings table, Research Briefing panel on Home tab. Multiple dashboard polish fixes. Commits: claudis 9011f62, eb8d388; claude-dashboard 21af5a0, 6702a06, 9e47ece, 6283f15, 529df29, 99dc3c9, 21e0361; stats-server fce1a5e, 9fe44d4.
- **B-136 complete (2026-05-17):** close-session.md Step 5 artifact template now enforces three-field Capability Delta (Before/After/Reader) with acceptability rules and a worked example. Empty deltas caught at write time. Commit b9b8245.

- **2026-05-22 Bill session (pruning pass):** Sessions tab converted to export-only (removed 15-card artifact list, fixed get_sessions_bundle path sessions/lean→sessions/). bill_notes removed (dead writer/no reader). lean sessions now auto-close (removed Request Close button + flag mechanism). Thread system retirement directive written — next lean session executes it. Commits: claudis d7e7a30, 4904f15, 36bdef1, 926216c; claude-dashboard d2f9068, 7cfd8a5, 9286d37.

**Project arc next:** Next lean session retires thread system (Threads tab + callables + thread_research_agent). After that: System tab pruning. Research replacement TBD — Bill wants responsive question research but thread approach retired.

---

## Handoff (pick up here)

**2026-05-22 (Bill session — pruning pass):**
- **What I was doing:** Wrote thread retirement directive to DIRECTIVES.md (commit 926216c). Lean session ready to trigger.
- **What I learned:** bill_notes was a textbook reader-writer failure — button wrote to Supabase, nothing read it. Python slice `c[:n]` where n=-1 silently corrupts files (trims last char + grafts misplaced content). Always verify block_start != -1 before using it as a slice index.
- **Continue:** Trigger lean session — directive is set, will retire thread system. After that: System tab pruning. Then: think about replacing thread research with something simpler.
- **Left better:** Dashboard pruned — 3 dead features removed (artifact list, bill_notes, Request Close). Lean sessions now self-closing.

**2026-05-17 (lean session — B-136):**
- **What I was doing:** B-136 — enforcing Capability Delta in session artifacts. Updated close-session.md Step 5 with Before/After/Reader format, enforcement language, worked example. Commit b9b8245 pushed to main.
- **What I learned:** The close-session skill loaded by the Skill tool is a local copy at ~/aadp/mcp-server/.claude/skills/close-session.md — symlink verified pointing to canonical.
- **Continue:** DIRECTIVES.md updated to thread retirement — trigger lean.
- **Left better:** Session artifacts now have enforceable Capability Delta format.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
