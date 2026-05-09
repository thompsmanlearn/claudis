# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Lean mode: sentinel timer disabled, `autonomous_growth_scheduler` deactivated. Desktop scopes cards; Claude Code executes.
- **Chapter 1 complete (B-084–B-093):** Foundation patterns — boot consolidation, annotation backbone + classifier, grader, auth tiers, capability index, skill resolution, carry documents.
- **Chapter 2 complete (B-094–B-101):** Research orchestrator — web search (Brave), charter format, cycle orchestrator, cycle grader, watch state, memory consultation, sub-question spawning. context_engineering_research deprecated.
- **Chapter 3 complete (B-106–B-112):** Cleanup + ChromaDB leverage — context_engineering_research retired, auto-cycle approval gate, lean_runner.sh symlink, boot episodic memory verified + backfilled, lesson utilization visibility (/lesson_stats), capability curation pass (greeter_bot retired, 9 candidates in Anvil queue), doc consolidation.
- Thread architecture complete (B-070–B-083): all live.
- Fleet: 9 active agents. lean_runner.sh is now a symlink — edit canonical only. Hourly watch timer enabled.
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits.

**Project arc next:** Chapter 4 when Bill decides. Destinations: Life OS integration, automated agent→thread wiring (Gap A), system self-repair. 9 curation candidates pending Bill's Anvil review (retire_agent/retire_skill callables ready).

---

## Handoff (pick up here)

**2026-05-08 (Chapter 3: B-106–B-112):**
- **What I was doing:** Desktop session scoped Chapter 3 (dropped B-110 grader formatting, folded B-111 convention into B-112, added C-1/C-2 as ChromaDB cards). Executed B-106 (retire context_engineering_research — n8n workflow deleted, webhook 404 confirmed), B-107 (auto-cycle approval gate — annotation instead of auto-PATCH, 2 new callables), B-108 (lean_runner.sh symlink), B-110 (boot episodic memory — verified inject_context_v3 already queries session_memory; backfilled Chapter 1+2 narratives; close-session step 9 updated with Do Not Skip warning), B-111 (/lesson_stats: 255 lessons, 83 never-applied/32.5%; work_queue compression item closed), B-109 (capability curation: 10 candidates surfaced, greeter_bot retired, 9 in queue), B-112 (this wrap).
- **What I learned:** inject_context_v3 already queries session_memory — the April/May gap was missing close-session step 9 writes, not missing queries. agent_registry has no last_used column — curation uses updated_at + workflow_id presence. system_config value column is JSONB — must cast booleans. live uplink_server.py runs directly from claudis (no separate copy).
- **Continue:** Chapter 4 when Bill decides. 9 curation candidates in Anvil queue for retirement decisions. "Document AADP on the Site" project has project_completion annotation (all 8 nodes done).
- **Left better:** Annotation queue has real items; grader calibrated; session_memory episodic tier populated; lesson utilization visible; curation infrastructure live; all sediment retired.

**2026-05-08 (Chapter 1: B-084–B-093):**
- **What I was doing:** Executed all 10 Chapter 1 foundation cards in a single session. B-084 (boot consolidation), B-085 (annotation backbone), B-086 (classifier), B-087 (grader + dashboard tab), B-088 (auth tiers), B-089 (capability index), B-090 (skill resolver), B-091 (carry docs), B-092 (retire INQUIRIES), B-093 (chapter wrap).
- **What I learned:** LEAN_BOOT was already 104 lines (not 168 as card assumed) — prior cleanup had already removed the duplicated sections. skills_registry pre-existed. The grader correctly issues "pause" when the graded card's commit is outside the HEAD~3 diff window — expected behavior for manual smoke tests on old cards.
- **Continue:** Chapter 2 when Bill is ready. Read CARRY_QUESTIONS.md, CARRY_PROPOSALS.md, CARRY_HEALTH.md at session start for orientation.
- **Left better:** Annotation backbone live, classifier live, grader live (Anvil tab), auth tiers defined, carry docs auto-generated, skill resolution deterministic.
- **Usage:** session ~%, weekly ~%

**2026-05-03 (cleanup + B-083):**
- **What I was doing:** Cleanup pass — updated DEEP_DIVE_BRIEF.md sections 4/5/7/8/12, anvil-redesign-principles-and-plan.md, TRAJECTORY.md. Verified all 6 recent lessons exist in both ChromaDB and Supabase (confirmed). Classified 19 unresolved errors: all fetch_error from context_engineering_research (Medium/URL empty-fetch or SSL timeout — expected behavior, all resolved). Also shipped B-083: standing summary at top of thread page.
- **What I learned:** All 19 error_log entries are expected operational noise — Medium bot-blocking and external URL timeouts. The error_logs table is being used as a fetch-attempt log, not a failure log; these entries should be resolved on sight rather than accumulating.
- **Continue:** Thread architecture complete. System in use-period. B-078 smoke test still pending — paste desktop Claude analysis into a thread, confirm four-bucket output, test Confirm/Override/Reject buttons. Next chapter: Bill decides. Candidates: Gap A completion (automated agent→thread wiring beyond current B-080 path), ChromaDB leverage card, or Life OS direction.
- **Left better:** Docs current; 19 stale errors cleared; lessons verified dual-store.
- **Usage:** session ~%, weekly ~%

**2026-05-03 (B-082):**
- **What I was doing:** B-082 — added `_fetch_company_engineering_blogs()` to stats_server.py; wired into `run_context_research`; smoke-tested on Source expansion thread: 3 openai + 3 deepmind articles with correct source names and neutral summaries. Anthropic has no public RSS — deferred, lesson written.
- **What I learned:** Anthropic does not publish a public RSS feed as of 2026-05-03 (tried 10+ paths). First confirmed build-from-input loop: Bill annotated a thread noting a source gap; this session closed it.
- **Continue:** See cleanup entry above.
- **Left better:** context_engineering_research now pulls from 8 sources; first-party company blog content will surface alongside HN/arXiv/Medium on every gather.
- **Usage:** session ~%, weekly ~%

**2026-05-03 (B-081):**
- **What I was doing:** B-081 — rewrote `_summarize_article_haiku` in stats_server.py to remove Reflexion/AADP framing; deployed, smoke-tested 9 new articles across the Consumer AI thread.
- **What I learned:** context_engineering_research's prompt lives in stats_server.py:_summarize_article_haiku, not in the n8n workflow — n8n is a thin webhook→stats server call. Baked-in consumer-specific lens becomes a leak when the agent has multiple consumers (threads with different questions).
- **Continue:** B-082 completed same session.
- **Left better:** Articles gathered by thread-triggered runs now get neutral summaries — relevance judgment happens at the extraction/thread layer, not inside the summarizer.
- **Usage:** session ~%, weekly ~%


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
