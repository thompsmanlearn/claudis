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
- **2026-05-22 lean session (thread retirement):** Thread system fully retired. Threads tab removed from Form1 (978 lines). Thread callables removed from uplink_server.py (1049 lines — Thread callables, Extraction, Sub-question spawning, Watch state, Research charter, promote_workpad_to_thread). thread_research_agent retired in agent_registry. Dashboard now 4 tabs: Home/Workpad/Sessions/System. Commits: claudis 42f98ea, claude-dashboard c96c3a6.
- **B-137 complete (2026-05-25):** Two-pass deep research pipeline live. "Deep Research" button in Workpad tab. 7 sources (Brave, Tavily, GitHub, Semantic Scholar, arXiv, Wikipedia, Guardian). Gemini: query expansion + relevance screening/clustering + gap identification. Haiku: gap-to-source routing. Artifacts written to ~/aadp/research_artifacts/; get_desktop_bundle() includes 3 most recent. Commits: claudis 3ec1457, claude-dashboard da0cdad.

**Project arc next:** System tab pruning. Deep research pipeline is live — evaluate artifact quality on first real use.

---

## Handoff (pick up here)

**2026-05-22 (lean session — thread retirement):**
- **What I was doing:** Retired the thread system — Threads tab (978 lines) removed from Form1, thread callables (1049 lines) removed from uplink_server.py, thread_research_agent retired. Dashboard is now 4 tabs. Commits: claudis 42f98ea, claude-dashboard c96c3a6.
- **What I learned:** Python `str.replace` on large Anvil files is reliable for contiguous block removal; boundary markers (section headers + known successor lines) make removal robust without fragile line numbers.
- **Continue:** System tab pruning — identify dead sections in the System tab, same pruning pattern.
- **Left better:** ~2000 lines of dead thread code gone. Dashboard is leaner; uplink server has no unreachable callables.

**2026-05-25 (lean session — B-137 deep research):**
- **What I was doing:** Built the two-pass deep research pipeline — 7 sources, 4 AI calls (3 Gemini + 1 Haiku), background job pattern (job_id + polling), artifact to ~/aadp/research_artifacts/, "Deep Research" button in Workpad, desktop bundle updated. Commits: claudis 3ec1457, claude-dashboard da0cdad.
- **What I learned:** Anvil's 30-second callable timeout makes any pipeline over ~25s require the background-thread + job_id + poll pattern. The existing `search_all` pushed the limit at 45s; deep research at 60-120s needed the explicit async pattern.
- **Continue:** System tab pruning (identified as next step before B-137). Then use the deep research pipeline on a real query to evaluate artifact quality.
- **Left better:** Research pipeline now has a reader — artifacts land in ~/aadp/research_artifacts/ and surface in Desktop Claude export bundle. Loop is closed.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
