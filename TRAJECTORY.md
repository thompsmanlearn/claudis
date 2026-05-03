# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Thread architecture v0.1 + manual inflow complete (B-070–B-078): schema, callables, read view, all action affordances, both add-to-thread surfaces, and extraction passback channel all live in Anvil
- "Add desktop analysis" now runs extraction: Haiku 4.5 parses prose into synthesis (analysis entry), conclusions (summary entry), screening decisions (screening/screening_uncertain entries), and sub-question candidates; confident screening patches research_articles immediately; uncertain items await Bill's Confirm/Override/Reject
- Research tab article cards: "Add to thread" button still live (source=research_articles:{id})
- Fleet: 10 active agents, unchanged; anthropic 0.97.0 added to mcp-server venv
- context_engineering_research (B-081/B-082): neutral summaries live; now 8 sources — added openai RSS + deepmind RSS (freshness-driven, 30-day window, 3/feed); Anthropic has no public RSS, deferred (lesson: anthropic_no_rss_2026-05-03)
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** Bill smoke-tests extraction: paste desktop analysis into a thread, verify four-bucket output; test uncertain-item resolution buttons. Then: Gap A (automated agent→thread wiring) or ChromaDB leverage card.

---

## Handoff (pick up here)

**2026-05-03 (B-082):**
- **What I was doing:** B-082 — added `_fetch_company_engineering_blogs()` to stats_server.py; wired into `run_context_research`; smoke-tested on Source expansion thread: 3 openai + 3 deepmind articles with correct source names and neutral summaries. Anthropic has no public RSS — deferred, lesson written.
- **What I learned:** Anthropic does not publish a public RSS feed as of 2026-05-03 (tried 10+ paths). First confirmed build-from-input loop: Bill annotated a thread noting a source gap; this session closed it.
- **Continue:** B-078 smoke test still pending — paste desktop Claude analysis into a thread, confirm four-bucket output, test Confirm/Override/Reject buttons. 14 unresolved errors in error_logs.
- **Left better:** context_engineering_research now pulls from 8 sources; first-party company blog content will surface alongside HN/arXiv/Medium on every gather.
- **Usage:** session ~%, weekly ~%

**2026-05-03 (B-081):**
- **What I was doing:** B-081 — rewrote `_summarize_article_haiku` in stats_server.py to remove Reflexion/AADP framing; deployed, smoke-tested 9 new articles across the Consumer AI thread.
- **What I learned:** context_engineering_research's prompt lives in stats_server.py:_summarize_article_haiku, not in the n8n workflow — n8n is a thin webhook→stats server call. Baked-in consumer-specific lens becomes a leak when the agent has multiple consumers (threads with different questions).
- **Continue:** B-082 completed same session.
- **Left better:** Articles gathered by thread-triggered runs now get neutral summaries — relevance judgment happens at the extraction/thread layer, not inside the summarizer.
- **Usage:** session ~%, weekly ~%

**2026-05-02 (B-078):**
- **What I was doing:** B-078 — extraction step for desktop-Claude analysis paste: `extract_analysis` callable + `resolve_screening_uncertain` callable in uplink_server.py; Form1 `_add_analysis` rewired; four new entry types rendered; both repos merged and pushed.
- **What I learned:** `_make_screening_handlers` factory pattern is the right idiom for Anvil action closures needing per-entry state — avoids Python closure-in-loop issue cleanly. Supabase JSONB PATCH via PostgREST accepts Python dicts directly. anthropic 0.97.0 installs into mcp-server venv.
- **Continue:** B-082 completed 2026-05-03. B-078 smoke test still pending.
- **Left better:** Passback channel complete — desktop Claude can now reason over thread content and have structured implications recovered by the system.
- **Usage:** session ~%, weekly ~%


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
