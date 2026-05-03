# Session: 2026-05-03 — B-082: Add Company Engineering Blogs as Fetched Source

## Card
B-082: Add Anthropic, OpenAI, and DeepMind engineering blogs as a new RSS-based source for `context_engineering_research`.

## What happened

**RSS URL verification (pre-code):**
- OpenAI: ✅ `https://openai.com/news/rss.xml` — confirmed RSS 2.0, valid XML
- DeepMind: ✅ `https://deepmind.google/blog/rss.xml` — confirmed RSS 2.0, valid XML
- Anthropic: ❌ No public RSS feed. Tried 10+ URL patterns including `/news/rss.xml`, `/rss.xml`, `/feed.xml`, `/feed`, `/news/feed`, `/blog/rss.xml`, `/news/index.xml`, `?format=rss` (returns HTML). Anthropic is a Next.js site that does not expose a machine-readable feed. Surfaced to Bill via Telegram. Decision: proceed with 2 feeds, defer Anthropic.

**Build:**
- Added `COMPANY_ENGINEERING_BLOGS` constant and `_COMPANY_BLOG_CAP = 3` near the fetcher functions in stats_server.py
- Added `_fetch_company_engineering_blogs()`: freshness-driven (30-day cutoff via RFC 2822 `parsedate_to_datetime`), cap 3 per feed, per-feed failure isolation with journald logging, consistent HTTP/XML pattern with existing fetchers
- Wired into `run_context_research` Phase 1 after lobste.rs block
- Added `"openai"`, `"deepmind"` to `SKIP_FETCH_SOURCES` — RSS description used as raw_content, no page fetch attempted
- Added source-name guard in netloc override block — preserves `openai`/`deepmind` exact strings (card requires `source IN ('openai', 'deepmind')`)

**Smoke test (triggered directly on Source expansion thread 946033c2-6acb-4164-8db2-3c60d4a8f9dd):**
- 6 articles inserted, 51 dupes skipped
- 3 × deepmind (healthcare/co-clinician, Korea partnership, Decoupled DiLoCo)
- 3 × openai (Advanced Account Security, goblins origin story, Stargate compute infrastructure)
- All source fields: exact org names, not netloc
- All query_used: "freshness-driven"
- All summaries: neutral (B-081 prompt working — no Reflexion/AADP framing)
- B-080 gather-entry path not re-verified in this session (articles already duped; path is unchanged and was verified in B-080 session)

**Lesson captured:**
- `anthropic_no_rss_2026-05-03` written to both Supabase lessons_learned and ChromaDB: Anthropic has no public RSS feed as of 2026-05-03; adding Anthropic requires RSS publication or HTML scraping.

## First build-from-input loop

This is the system's first build-from-input loop in the redesign sense. Bill annotated a thread noting three source gaps (session 946033c2-6acb-4164-8db2-3c60d4a8f9dd, 2026-05-03). That annotation became B-082. This session built the fetcher. The gap identified during consumption of research output became a system improvement — closed in the same session it was filed.

## Scope delta

COMPANY_ENGINEERING_BLOGS has a commented-out Anthropic entry. Adding Anthropic is a one-line config change if/when they publish RSS. No other scope changes.

## Files changed

- `stats-server/stats_server.py` — new constant, new function, 3 wiring edits
- `DEEP_DIVE_BRIEF.md` — source count updated to 8, Anthropic note added
- `agents/INDEX.md` — context_engineering_research entry updated

## Commit

`60f4433` on claudis main. Deployed to `~/aadp/stats-server/stats_server.py`. Service restarted (`aadp-stats` active).
