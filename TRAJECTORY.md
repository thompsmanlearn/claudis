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
- **Post-chapter additions (B-113–B-114):** Execution disciplines in CONVENTIONS + close-session scope check (B-113). Comment-driven card generation loop (B-114) — classifier-routed comments auto-generate B-NNN-cmt backlog cards, non-blocking execution, grader-gated. Fleet tab: thumbs-up/down removed, Comment button wired to v2 classifier path, "✏️ Comment work" export button, per-agent modification indicator.
- Thread architecture complete (B-070–B-083): all live.
- Fleet: 9 active agents. B-115-cmt in BACKLOG.md (first comment-generated card, unexecuted). 9 curation candidates in Anvil queue.
- **Next session:** System review — examine, test, and revise. DIRECTIVES.md set.

**Project arc next:** System review, then Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-09 (B-113–B-114 + system review prep):**
- **What I was doing:** B-113 (Karpathy execution disciplines → CONVENTIONS + close-session scope check). B-114 (comment-driven card loop — /generate_card_from_comment Sonnet endpoint, annotate() trigger, /export_comment_driven_results, Fleet tab "✏️ Comment work" button + per-agent indicator, USERS_MANUAL.md). Also: DEEP_DIVE_BRIEF Section 7/8 accuracy pass (wrong line count, stale endpoints, missing DB tables), removed Fleet thumbs-up/down (performative → classifier-routed Comment button).
- **What I learned:** stats_server doesn't import pathlib at module level — use os.path. annotate() was fire-and-forget for classify_annotation; changed to synchronous read so card gen trigger can check result. The comment_box in the Fleet tab had no submit button — the thumbs were its only submit path; had to add a Comment button as part of the removal.
- **Continue:** Next session is a system review. Read DIRECTIVES.md. B-115-cmt (first comment-generated card) is in BACKLOG.md unexecuted. 9 curation candidates await decisions. "Document AADP on the Site" needs project_completion decision.
- **Left better:** Full comment→card→execute→grade→export loop live. Fleet tab has real annotation path. USERS_MANUAL.md explains comment framing. Execution disciplines codified.

**2026-05-08 (Chapter 3: B-106–B-112):**
- **What I was doing:** Chapter 3 — cleanup + ChromaDB leverage. B-106 (retire context_engineering_research), B-107 (auto-cycle approval gate), B-108 (lean_runner.sh symlink), B-110 (session_memory verified + backfilled), B-111 (/lesson_stats), B-109 (curation pass — 10 candidates, greeter_bot retired), B-112 (doc wrap).
- **What I learned:** inject_context_v3 already queries session_memory — the gap was missing close-session writes. agent_registry has no last_used column. system_config value is JSONB. live uplink_server.py runs from claudis directly.
- **Continue:** B-113 and B-114 executed same day. See above entry.

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
