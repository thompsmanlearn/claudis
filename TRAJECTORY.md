# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Lean mode: sentinel timer disabled, `autonomous_growth_scheduler` deactivated. Desktop scopes cards; Claude Code executes.
- **Chapter 1 complete (B-084–B-093):** Foundation patterns established — boot consolidation, annotation backbone + classifier, grader, authorization tiers, capability index, skill resolution, carry documents. All committed and pushed.
- Thread architecture complete (B-070–B-083): all live
- context_engineering_research: 8 sources, neutral summaries, thread-aware
- Fleet: 10 active agents, all Tier 1
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Chapter 2 — research orchestrator. Bill decides when to start. Carry documents (CARRY_QUESTIONS.md, CARRY_PROPOSALS.md, CARRY_HEALTH.md) are available at repo root for desktop session orientation.

---

## Handoff (pick up here)

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
