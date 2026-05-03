- URL-based dedupe against `research_articles.url` before insert; skip duplicates silently.
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
