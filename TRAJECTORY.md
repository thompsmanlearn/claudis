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
- **Next:** B-118 (Gather trigger in Anvil UI), then Chapter 4 when Bill decides.

**Project arc next:** System review, then Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-10 (B-123 inject_context_v3 restore):**
- **What I was doing:** B-123 — restored 6 missing module-level constants in `stats_server.py` (`_V3_TASK_ROUTING`, `_V3_DEFAULT_COLLECTIONS`, `_V3_DEFAULT_DESCRIPTIONS`, `_V3_COLLECTION_PARAMS`, `_V3_SECTION_LABELS`, `_V3_CONTENT_TRUNC`). Endpoint was 500-ing since 2026-05-09.
- **What I learned:** Card said 3 constants missing; code referenced 6. Always audit all NameError sites in a function before reconstructing — the card count was an undercount.
- **Continue:** B-118 (Gather trigger in Anvil UI). 1 pending agent_build in work_queue (SpecOps GUI, 2026-05-03). Call `mark_audit_taken()` manually after first audit export.
- **Left better:** Lesson retrieval restored. `lesson_injector` agent will resume successful runs.

**2026-05-10 (B-122 audit bundle):**
- **What I was doing:** B-122 — audit bundle. Added `get_audit_bundle()` and `mark_audit_taken()` to uplink_server.py. Added "Export audit bundle" button to Workspace tab. Discovered `research_articles` uses `retrieved_at` not `created_at` — fixed by parameterizing timestamp column per store as `(table, ts_col)` tuples.
- **What I learned:** Supabase stores don't all share the same timestamp column — don't assume `created_at` in cross-store queries. ChromaDB count endpoint is GET `/api/v1/collections/{id}/count`.
- **Continue:** Covered by entry above.
- **Left better:** Workspace tab now has both working bundle and audit bundle export. Audit bundle gives full system snapshot for design/review sessions.

**2026-05-10 (thread research pipeline bugs):**
- **What I was doing:** Fixed three bugs in the thread research pipeline: (1) duplicate findings; (2) memory consultation wrong query; (3) gather trigger silent failure — thread_research_agent workflow was inactive.
- **What I learned:** n8n sandbox workflows deactivated after testing still have webhook_url in agent_registry — POST to inactive production webhook fails immediately. fire-and-forget webhook callers must check response status.
- **Continue:** Covered by entry above.
- **Left better:** Thread research pipeline now correctly deduplicates, uses authoritative charter question, and surfaces webhook failures.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
