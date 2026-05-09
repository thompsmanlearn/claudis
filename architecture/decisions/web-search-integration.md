# ADR: Web Search Integration

**Date:** 2026-05-08
**Status:** Active

## Decision

Use **Brave Search API** as the primary web search provider, accessed via stats_server endpoints `/web_search` and `/web_fetch`.

## Provider Choice

| Provider | Free tier | Result format | Notes |
|---|---|---|---|
| **Brave Search** ✅ | 2,000 queries/month | Structured JSON (url, title, description, meta) | Selected |
| Exa | 1,000 queries/month | Semantic search, better citation extraction | More expensive at scale |
| Perplexity API | None | Natural language answers | Doesn't fit provider-agnostic interface |
| Gemini grounding | n/a | Model-integrated | Not a standalone endpoint |

Brave chosen for: generous free tier, structured output, no aggressive rate limits, no requirement for natural language reformulation of queries.

## Configuration

`BRAVE_API_KEY` in `~/aadp/mcp-server/.env`.

Rate limits: 2,000 queries/month on free tier. Each `/web_search` call = 1 query.

## Endpoints

### POST /web_search
Input: `{query, max_results=10, freshness_window=null}`
- `freshness_window`: `pd` (past day), `pw` (past week), `pm` (past month), `py` (past year), or null
Output: `{results: [{url, title, snippet, source_domain, published_date}], query, count}`

Error handling:
- HTTP 429 → rate limit, returns `retry_after`
- Timeout (15s) → 500
- Brave unavailable → 502

### POST /web_fetch
Input: `{url, max_chars=8000}`
Output: `{url, content, content_type, length}`

Behavior:
- Checks robots.txt before fetching (best effort — allows if robots.txt unreachable)
- User-Agent: `AADP-Research/1.0`
- Reads up to 200KB of raw HTML, strips tags, trims to max_chars
- Does NOT execute JavaScript — returns server-rendered HTML only
- Limitation: JavaScript-heavy SPAs may return minimal content

## Cost Tracking

Every call to `/web_search` and `/web_fetch` logs to `external_api_usage`:
`(provider, endpoint, query, result_count, response_ms, created_at)`

## Switching Providers

The interface is provider-agnostic at the endpoint level. To switch:
1. Add new provider's API key to `.env`
2. Replace `_brave_search()` function in stats_server.py
3. Update this ADR
4. No changes needed in callers (orchestrator, etc.)

## Limitations

- Server-rendered HTML only (no JavaScript execution)
- 2,000/month query cap on free Brave tier
- robots.txt check is best-effort (no caching of robots.txt responses)
- Some sites block non-browser user agents regardless of robots.txt
