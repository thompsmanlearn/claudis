B-082: Add company engineering blogs as a fetched source

## Goal

Bill identified Anthropic, OpenAI, and DeepMind engineering blogs as obvious source gaps during the Source expansion smoke test (thread id 946033c2-6acb-4164-8db2-3c60d4a8f9dd, 2026-05-03). All three publish first-party technical writing on agent design, evaluation, and deployment that doesn't reliably surface through HN or Medium aggregation. All three expose RSS feeds. Add them as a new fetched source for context_engineering_research, callable from the existing gather pipeline. After this card, every thread-triggered or default gather can pull from these blogs in addition to HN, arXiv, dev.to, GitHub, lobste.rs, and Medium.

This is the system's first build-from-input loop in the redesign sense: a Bill annotation on a thread named a source gap; this card builds the fetcher.

## Context

Existing source pattern: the per-source fetchers live in stats_server.py (the Python that the n8n workflow's `/run_context_research` endpoint calls). Each source has a fetch function that returns a list of {title, url, source, query_used, raw_content} dicts; downstream the same `_summarize_article_haiku` pass produces the summary, and rows land in `research_articles`.

RSS feeds to verify before coding:
- Anthropic: https://www.anthropic.com/news/rss.xml
- OpenAI: https://openai.com/blog/rss.xml
- DeepMind: https://deepmind.google/discover/blog/rss.xml

If any of those URLs don't resolve, find the current RSS feed for that blog before writing code. Don't guess.

Treat all three as one logical source called `company_engineering_blogs`. The fetcher iterates over a configured list of (org_name, feed_url) pairs and returns combined results. This makes adding more company blogs in the future a config change, not a code change. The `source` field on each returned article is the org name (`anthropic`, `openai`, `deepmind`), not the umbrella label — so downstream filtering and display can distinguish them.

Query handling: company blog RSS feeds don't accept query parameters. They return the most recent N posts. The fetcher should ignore the incoming query list and just pull the latest N posts from each feed, capped per source. Document this in the fetcher: "this source is freshness-driven, not query-driven; queries are ignored." Future card may add post-fetch filtering by query relevance, but not this one.

Per-feed cap: 3 posts each (so up to 9 total from all three blogs per gather). Tunable in code constant.

Freshness: only return posts from the last 30 days. Skip older entries even if they're in the feed. RSS feeds for these blogs typically include several months of history; without a cutoff, the same posts would surface in every gather.

Deduplication: use the article URL as the dedupe key against existing `research_articles` rows. If the URL already exists in the table, skip the insert. Scope this dedupe to this fetcher only; do not retrofit other fetchers in this card.

Failure handling: if any one feed errors (network, parse failure, blocked), log to journald and skip that feed. Continue with the others. Do not let one feed's failure block the run.

Test path: after the fetcher is wired, trigger a gather on the existing Source expansion thread (id 946033c2-6acb-4164-8db2-3c60d4a8f9dd) and verify at least one company-blog article lands in `research_articles` with the right `source` value, gets a neutral summary (B-081 prompt), and shows up as a `gather` thread entry (B-080 plumbing).

## Done when

- New fetcher in stats_server.py: a function (e.g., `_fetch_company_engineering_blogs(...)`) that iterates over a configured list of (org, feed_url), pulls the feed via the existing HTTP pattern, parses entries (use feedparser or equivalent — whichever the existing fetchers use, for consistency), filters to last 30 days, caps at 3 per feed, returns the same dict shape as other fetchers.

- Configuration constant near the top of the fetcher names the feeds:
    COMPANY_ENGINEERING_BLOGS = [
        ("anthropic", "<verified RSS URL>"),
        ("openai", "<verified RSS URL>"),
        ("deepmind", "<verified RSS URL>"),
    ]

- The fetcher is wired into `run_context_research` so it runs as part of every gather invocation (thread-triggered or default). Source ordering shouldn't matter for correctness.

- URL-based dedupe against `research_articles.url` before insert; skip duplicates silently.

- Per-feed failure isolated: one feed erroring doesn't break the run. Errors logged to journald with the feed name and reason.

- Smoke test in session: trigger a gather on Source expansion thread (946033c2-6acb-4164-8db2-3c60d4a8f9dd). Verify in `research_articles`:
  - At least one row with source IN ('anthropic', 'openai', 'deepmind')
  - URL matches the original blog post
  - Summary is neutral (no "Reflexion-style agentic system" framing — sanity check that B-081 still applies)
  - Article appears as a `gather` thread entry in the thread (B-080 plumbing)

- Document the new source in a one-liner wherever the existing source list is documented (likely the agent description, CATALOG entry, or section 8 of DEEP_DIVE_BRIEF — find where, update it).

- One commit on claudis main with the stats_server.py changes. Deploy copy via `cp claudis/stats-server/stats_server.py ~/aadp/stats-server/` per the existing dual-location pattern (see Section 12 of DEEP_DIVE_BRIEF). Service restart at end of session per normal practice.

- Session artifact written. Include a note that this is the first build-from-input loop in the redesign sense — Bill identified a source gap on a thread; this card built the fetcher.

## Scope

Touch:
- ~/aadp/claudis/stats-server/stats_server.py (add fetcher function; wire into run_context_research)
- ~/aadp/stats-server/stats_server.py (deploy copy after editing)
- Agent or CATALOG documentation where the source list lives (find and update; one line)
- session artifact

Do not touch:
- The n8n workflow gzCSocUFNxTGIzSD — no changes needed; the workflow calls /run_context_research and the new source slots in transparently
- Any uplink callable
- Any schema (research_articles already has source, url, title, summary, retrieved_at, agent_run_id, thread_id)
- The existing fetchers for HN, arXiv, dev.to, GitHub, lobste.rs, Medium
- The summarization prompt (B-081)
- Form1 in claude-dashboard

If you find yourself wanting to:
- Add a UI for managing the company-blog list — stop. Config in code is fine; UI is future.
- Add per-blog query filtering — stop. Future card.
- Change how other fetchers handle dedupe — stop. Out of scope; only the new fetcher needs URL-based dedupe.
- Add a fourth or fifth company blog because it occurred to you — stop. Anthropic, OpenAI, DeepMind only. Adding more is a future card or config change.
- Build a sources-shaped output schema (the type-mismatch fix from the thread analysis) — stop. Different card, different scope, future.

Two-hour ceiling check: if RSS feed URLs are missing or the parse pattern is more fiddly than expected, surface that early. Likely fault line if it tips: URL discovery + 1 feed working = Card A; remaining 2 feeds + dedupe = Card B. Don't ship Card A alone — one feed is barely a source.- URL-based dedupe against `research_articles.url` before insert; skip duplicates silently.
- Per-feed failure isolated: one feed erroring doesn't break the run. Errors logged to journald with the feed name and reason.
- Smoke test in session: trigger a gather on Source expansion thread (`946033c2-6acb-4164-8db2-3c60d4a8f9dd`). Verify in `research_articles`:
  - At least one row with `source IN ('anthropic', 'openai', 'deepmind')` 
  - URL matches the original blog post
  - Summary is neutral (no "Reflexion-style agentic system" framing — sanity check that B-081 still applies)
  - Article appears as a `gather` thread entry in the thread (B-080 plumbing)
- Update `architecture_review` agent's awareness if relevant, OR document the new source in a one-liner in CONTEXT.md or wherever the existing source list is documented (likely in the agent description or CATALOG entry — find where, update it).
- Lessons captured if anything surprising surfaces during the build (RSS feed quirks, parsing edge cases, dedupe issues). Do not pre-write lessons.
- One commit on claudis main with the stats_server.py changes. Stats server deployed via the existing `cp claudis/stats-server/stats_server.py ~/aadp/stats-server/` pattern (see Section 12 of DEEP_DIVE_BRIEF — dual-location reality). Service restart at end of session per normal practice.
- Session artifact written. Include a note that this is the first build-from-input loop in the redesign sense — Bill identified a source gap on a thread; this card built the fetcher.

## Scope

Touch:
- `~/aadp/claudis/stats-server/stats_server.py` (add fetcher function; wire into `run_context_research`)
- `~/aadp/stats-server/stats_server.py` (deploy copy after editing)
- Agent or CATALOG documentation where the source list lives (find and update; one line)
- session artifact

Do not touch:
- The n8n workflow `gzCSocUFNxTGIzSD` — no changes needed; the workflow calls `/run_context_research` and the new source slots in transparently
- Any uplink callable
- Any schema (`research_articles` already has all the columns needed: source, url, title, summary, retrieved_at, agent_run_id, thread_id)
- The existing fetchers for HN, arXiv, dev.to, GitHub, lobste.rs, Medium
- The summarization prompt (B-081)
- Form1 in claude-dashboard

If you find yourself wanting to:
- Add a UI for managing the company-blog list — stop. Config in code is fine for now; UI is future.
- Add per-blog query filtering — stop. Future card if relevance becomes a problem.
- Change how other fetchers handle dedupe — stop. Out of scope; only the new fetcher needs URL-based dedupe.
- Add a fourth or fifth company blog because it occurred to you — stop. Anthropic, OpenAI, DeepMind. Adding more is a future card or a config change later, not this card.
- Build a sources-shaped output schema (the type-mismatch fix from the thread analysis) — stop. Different card, different scope, future.

Two-hour ceiling check: if RSS feed URLs are missing or the parse pattern is more fiddly than expected, surface that early. Likely fault line if it tips: URL discovery + 1 feed working = Card A; remaining 2 feeds + dedupe = Card B. Don't ship Card A alone — one feed is barely a source.
