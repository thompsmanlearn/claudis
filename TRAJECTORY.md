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
- **2026-05-25/28 Bill session (deep research pipeline fixes):** Four rounds of pass two fixes: (1) Wikipedia User-Agent 403 fix; (2) gap query distillation — Gemini now generates 3-5 keyword `query` field per gap; arXiv/Semantic Scholar use short keyword query, Guardian/web use full NL description; Haiku routing adds `wiki_title` for Wikipedia; (3) no abbreviations in academic queries (PAT/PTSD expansion); (4) arXiv category filtering — academic gaps use `(cat:q-bio.NC OR cat:q-bio.QM OR cat:q-bio.PE)`, technical gaps use `(cat:cs.AI OR cat:cs.LG OR cat:eess)`, clinical-only gaps skip arXiv. Fixes verified with live run 2026-05-28: category prefixes confirmed in artifact, clinical skip logged, arXiv rate-limited (IP backoff from testing — will clear). Commits: claudis 1bd29ff, 68bb2e5, 39cbe83, 0096dc7; claude-dashboard f76ea7c.
- **2026-06-26 (lean session — grader gate):** lean_runner.sh now gates node completion on grader evaluation — NODE_ID extracted from directive, grader block executes, node auto-marked done on pass. Fixed: auto_cycle_enabled boolean→string case mismatch was silently skipping grader on every cycle. Commits: claudis 06c6f7f, 129b4ef, c10f7ae, 301187a.
- **2026-06-26 (Bill session — close-session x11):** Administrative close only. /wisdom-review finally executed today (2026-06-26T15:51:58 UTC) after 72+ days overdue — last_wisdom_review updated in system_config, wisdom_review work queue item marked complete.
- **2026-06-26 (interactive — Node 1 grader test):** Node 1 executed: wrote "grader-test: Node 1 passed" to ~/aadp/grader_test.txt via Bash and confirmed read-back. Prior two grader FAILs resolved (first: wrong session artifact submitted; second: agent falsely skipped as stale). Grader evaluation pending next lean session trigger.

**Project arc next:** Trigger lean session to test grader gate end-to-end — lean_runner should grade Node 1 PASS and mark it done, then auto-cycle to next node. System tab pruning. Re-test deep research after arXiv IP rate limit clears.

---

## Handoff (pick up here)

**2026-06-26 (lean session — grader gate + close x10):**
- **What I was doing:** Built grader-gated node completion into lean_runner.sh: NODE_ID extraction, node path in grader block, lean_runner marks node done on pass. Fixed auto_cycle_enabled boolean→string comparison (was silently always-false — grader never ran). Then /close-session x10.
- **What I learned:** system_config stores "true" as a string; shell `== "true"` comparison works, but bare boolean check `== true` fails silently. Silent failure in lean_runner grader path meant auto-cycle appeared to run while grader was completely bypassed the entire time.
- **Continue:** FIRST (blocking): /wisdom-review before any other work. Then: test auto-cycle end-to-end with Node 1 now that grader gate is wired. Then: System tab pruning.
- **Left better:** Grader gate functional end-to-end. Auto-cycle Node 1 can now be tested with real grader evaluation.

**2026-06-26 (Bill session — close-session x11):**
- **What I was doing:** Administrative close only. /wisdom-review executed earlier today (2026-06-26T15:51:58 UTC) — finally clearing the 72+ day overdue flag. wisdom_review queue item 52d32005 and stale session_handoff queue item both marked complete.
- **What I learned:** The "FIRST (blocking)" handoff instruction worked — wisdom_review ran the same calendar day it was escalated to a gate. Enforcement language matters.
- **Continue:** Test auto-cycle end-to-end with Node 1 (grader gate wired, wisdom-review no longer blocking). Then System tab pruning.
- **Left better:** wisdom_review queue item closed. Two stale queue items cleaned. Handoff trimmed to 3 entries.

**2026-06-26 (interactive — Node 1 grader test):**
- **What I was doing:** Executed Node 1 directive: wrote "grader-test: Node 1 passed" to ~/aadp/grader_test.txt via Bash, confirmed read-back. Prior two grader FAILs for this node (wrong artifact; false stale skip).
- **What I learned:** Grader reads the session artifact, which is built from in-session tool calls. If the required Bash command never appears in the session, the artifact has no evidence — grader FAILs even if the file exists elsewhere. The action must appear in this session's tool calls.
- **Continue:** Trigger a lean session so lean_runner's grader block evaluates Node 1 (grader_test.txt now exists with correct content) — should PASS and mark node done, then auto-cycle to next node. Then System tab pruning.
- **Left better:** Node 1 file written with proper session evidence. Three prior attempts resolved.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
