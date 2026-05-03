# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture complete (B-070–B-083): schema, callables, read view, action panel, extraction passback, thread-aware gather with output wiring, standing summary at top — all live
- context_engineering_research: 8 sources, neutral summaries, thread-aware query derivation; articles tagged with thread_id; gather entries written back to originating thread automatically
- Fleet: 10 active agents, unchanged
- Redesign chapter complete; system in use-period — no card pending; Bill scopes next direction
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Bill smoke-tests extraction: paste desktop analysis into a thread, verify four-bucket output; test uncertain-item resolution buttons. Then: Gap A (automated agent→thread wiring) or ChromaDB leverage card.

---

## Handoff (pick up here)

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
