# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Lean mode: sentinel timer disabled, `autonomous_growth_scheduler` deactivated. Desktop scopes cards; Claude Code executes.
- **Chapter 1 complete (B-084–B-093):** Foundation patterns.
- **Chapter 2 complete (B-094–B-101):** Research orchestrator.
- **Chapter 3 complete (B-106–B-112):** Cleanup + ChromaDB leverage.
- **Post-chapter additions (B-113–B-114):** Execution disciplines in CONVENTIONS. Comment-driven card loop live — B-115-cmt executed (first comment-generated card complete).
- **System review complete (2026-05-09):** B-115-cmt executed, pipeline verified end-to-end, 5 agents retired, "Document AADP on the Site" project closed. Two revision findings queued as annotations: grader blind spot for data-only cards, card generator missing schema context.
- Thread architecture complete (B-070–B-083): all live.
- **B-117 complete (2026-05-10):** Thread research agent with Brave live in sandbox. /web_search first wired. 14 findings + 3 cycle_summaries written to test thread. B-116 (charter UI) was already complete.
- **B-119 complete (2026-05-09):** Auto-wiring live. Charter save scores agents via capability_tags; wires best match (≥0.7) or queues build_request in agent_feedback. Telegram notification on wire. Form1 shows result inline.
- **Thread research pipeline bugs fixed (2026-05-10):** Duplicate findings blocked (cross-cycle dedup via existing source URLs). Memory consultation now fetches charter question from DB (authoritative). thread_research_agent webhook activated; non-200 warning added to gather trigger.
- Fleet: 9 active + 1 sandbox (thread_research_agent).
- **B-120/B-121/B-122 complete (2026-05-10):** Workspace tab live. Bill's notes capture, working bundle, and audit bundle all functional. Export buttons in Workspace tab.
- **B-123 complete (2026-05-10):** inject_context_v3 restored — 6 missing module-level constants reconstructed. Lesson retrieval and times_applied tracking working again.
- **B-124 complete (2026-05-10):** stats_server now under git version control. Own repo at ~/aadp/stats-server/ (commit d28f88c). Two-repo sync pattern; symlink ruled out (venv constraint).
- **B-125/B-126 complete (2026-05-10):** Two-pass review convention established (B-125) and extended with reader-writer discipline (B-126). CONVENTIONS.md §3 now has: which cards need review, the six-step flow, resolved standard, reader-writer check (standard question + acceptable answers), and five-field design sketch format (adds Writer and Reader fields).
- **B-127 complete (2026-05-10):** Dashboard restructured from 10 tabs to 5-tab layout. Home (status strip, primary actions, bill_notes, inbox, autonomous toggle, lean trigger), Workpad stub, Threads/Sessions unchanged, System (Fleet/Memory/Lessons/Skills/Artifacts/Research/Grader as collapsible sections with lazy-load on expand). Font pass: body 16→18, section headers 20→22, status strip 24. Commit 91b55eb.
- **B-118 already complete (verified 2026-05-10):** Gather button live in thread actions — gated on charter+wired agent+webhook, calls `trigger_thread_gather`, polls every 15s, refreshes entries on cycle_summary, surfaces errors inline. No work needed.
- **B-128 complete (2026-05-10):** Workpad surface live. `workpad_state` table (singleton), 5 uplink callables (get/save/fetch_url/clear/promote), full Form1 Workpad tab: input textarea, URL field, Read URL/Copy/Clear/Promote actions, debounced auto-save, scrollable output entries, inline promote form. Commits: claude-dashboard f57254d, claudis a1580af.
- **Next:** Chapter 4 when Bill decides.

**Project arc next:** Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-10 (B-128 Workpad surface):**
- **What I was doing:** B-128 — Workpad surface. `workpad_state` singleton table, 5 uplink callables, full Form1 Workpad tab with input/URL/actions/output/auto-save/promote. HTML stripping via stdlib `re` + `html.unescape` (bs4 not in venv). Commits: claude-dashboard f57254d, claudis a1580af.
- **What I learned:** When bs4/html2text aren't available, `re.sub(r'<[^>]+>', ' ', raw)` + `html.unescape()` covers most real-world HTML adequately. Check venv before reaching for a library.
- **Continue:** Chapter 4 when Bill decides. 1 pending agent_build in work_queue (SpecOps GUI, 2026-05-03).
- **Left better:** Workpad is live — Bill can now drop content, fetch URLs, and promote investigations to threads without leaving the dashboard.

**2026-05-10 (B-127 five-tab dashboard layout):**
- **What I was doing:** B-127 — restructured Form1 from 10 tabs to Home/Workpad/Threads/Sessions/System. Home is now the daily-use landing: status strip (24px health/agents/queue/inbox), four primary action buttons, bill_notes capture + list, inbox approvals, autonomous toggle, lean trigger. System tab wraps Fleet/Memory/Lessons/Skills/Artifacts/Research/Grader as collapsible sections with lazy-load on expand. Font pass: 16→18, 20→22 throughout. Commit 91b55eb.
- **What I learned:** Anvil widgets have single-parent ownership — avoid duplicating the same widget in multiple panels. System/Fleet got status+agents+queue only; inbox and controls were lifted to Home exclusively rather than duplicated.
- **Continue:** Covered by entry above.
- **Left better:** Dashboard is now organized by activity type. Daily work lands on Home; system internals are one System tab away.

**2026-05-10 (B-122 audit bundle):**
- **What I was doing:** B-122 — audit bundle. Added `get_audit_bundle()` and `mark_audit_taken()` to uplink_server.py. Added "Export audit bundle" button to Workspace tab. Discovered `research_articles` uses `retrieved_at` not `created_at` — fixed by parameterizing timestamp column per store as `(table, ts_col)` tuples.
- **What I learned:** Supabase stores don't all share the same timestamp column — don't assume `created_at` in cross-store queries. ChromaDB count endpoint is GET `/api/v1/collections/{id}/count`.
- **Continue:** Covered by entry above.
- **Left better:** Workspace tab now has both working bundle and audit bundle export. Audit bundle gives full system snapshot for design/review sessions.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
