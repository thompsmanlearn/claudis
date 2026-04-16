# Session: 2026-04-16 — resource-inbox-web-page

## Directive
B-023: Build a single-page web app on GitHub Pages that displays scouted resources as scrollable cards with star/dismiss buttons writing feedback to Supabase.

## What Changed

**GitHub Pages**
- Enabled on `thompsmanlearn/claudis`, serving from `main` branch `/docs` folder
- Live URL: https://thompsmanlearn.github.io/claudis/

**New files**
- `docs/index.html` — single HTML file, vanilla JS, no build step
- `docs/.nojekyll` — prevents Jekyll processing

**Supabase RLS**
- Enabled RLS on: `resources`, `inquiry_threads`, `refinements`, `feedback_log`
- Policies created:
  - anon SELECT on `resources`, `inquiry_threads`, `refinements`
  - anon INSERT on `feedback_log`
  - service_role ALL on all four tables (belt-and-suspenders; service_role bypasses RLS by default but explicit policy prevents surprises)

**Page behavior**
- Loads resources (newest first), inquiry threads, and existing feedback in parallel on page open
- Cards show: thread label, title (linked to source), Haiku one-line assessment, Star + Dismiss buttons
- Star → writes `thumbs_up` to `feedback_log`, highlights card with amber left border
- Dismiss → writes `dismiss` to `feedback_log`, hides card from default view
- "Show dismissed" toggle reveals dismissed cards at reduced opacity
- Thread filter buttons auto-generated from active `inquiry_threads` rows
- Refresh button re-fetches all data
- Feedback persists across devices (stored in Supabase, not localStorage)

**Test run**
- Page loaded 6 resources (5 scouted + 1 processed) under game-development thread
- Supabase REST API returning data correctly with anon key + RLS policies

## What Was Learned

- Supabase anon key was not in `.env` — retrieve via Management API:
  `GET https://api.github.com/v1/projects/{ref}/api-keys` with SUPABASE_MGMT_PAT
- GitHub Pages can be enabled via REST API (`POST /repos/{owner}/{repo}/pages`) without the `gh` CLI — takes ~30s to build from cold start
- `.nojekyll` in the docs root is required or GitHub's Jekyll builder may interfere with plain HTML files
- RLS was off on all Capability Amplifier tables — first time anon access was needed, so this was the natural time to enable it

## Unfinished

- No filtering by status (scouted vs processed) — page shows all resources; could add a status filter if the inbox gets noisy
- No pagination — will need it if resources grows beyond ~100
- `feedback_log` anon INSERT allows anyone who finds the anon key to insert fake feedback; acceptable for a personal tool, worth revisiting if the platform opens up
