# 2026-05-10 — B-129: Workpad Brave Search

Code commits: claudis 00e805d, claude-dashboard 32be089

## What was built

Wired Brave Search into the Workpad tab for the first time as a user-facing surface.

**uplink_server.py — `search_brave(query, max_results=5)`:**
- POSTs to stats_server /web_search (existing endpoint with rate limiting and usage logging)
- Appends structured entry to workpad_state.output_entries: `{action, query, results: [{url, title, snippet, source_domain, published_date}], timestamp}`
- 429 → raises "Brave rate limit hit, try again in a moment"
- Other errors → raises with message from stats_server JSON body

**Form1/__init__.py — Workpad tab changes:**
- Search button added to actions row, before Read URL, disabled when input is empty
- `_wp_input_changed` and `_wp_load_state` both update Search button enabled state
- `_wp_search` handler: saves input, calls `search_brave(query, 5)`, re-fetches state, re-renders
- `_wp_render_output` extended with `action == 'search'` branch:
  - 🔍 header distinguishes from read_url entries visually
  - Clickable result rows (title as tonal button → sets URL field, domain/date meta, 200-char snippet)
  - Click flow: Search → click result → Read URL gives full page content in one motion

## Judgment calls

- Visual distinction: used 🔍 emoji prefix on header rather than background colour change — lightest approach that makes search entries scannable without adding complexity
- Kept `_make_url_setter` and `_make_expand` as factory functions defined once before the loop (not inside it), following the existing closure pattern in B-128
- No automatic Read URL trigger on result click — card specified Bill decides

## What I verified

- stats_server /web_search tested with curl — returned 2 results with correct shape
- uplink restarted cleanly (aadp-anvil systemd), connected to Anvil within ~1.5s
- Structural review: search branch is additive, else branch is unchanged from B-128

## What Bill should verify in the browser

1. Type a query, click Search — 5 results render with title, domain, snippet
2. Click a result title — URL field populates
3. Click Read URL — fetched content appears below the search entry
4. Reload page — both entries persist (search entry and read entry)
5. Clear workpad — confirm empty state
6. Search with empty input — Search button should be greyed out (cannot click)

## Left better

Workpad now supports the full research motion: search → click result → read full page — without leaving the dashboard.
