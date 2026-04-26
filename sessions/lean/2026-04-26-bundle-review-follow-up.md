# Bundle Review Follow-Up

**Date:** 2026-04-26
**Session type:** Lean — directive-driven (desktop Claude bundle review)
**Commits:** claudis 605dac9, 6f17bc1 · claude-dashboard c3554b7

---

## Tasks Completed

- Verified PER_RUN_CAP=10 already set — no change needed
- Replaced 5 narrow context-engineering queries with broader platform/architecture queries in run_context_research
- Deployed updated stats_server.py to ~/aadp/stats-server/ (running location) and confirmed sync with claudis repo
- Added get_research_counters() callable to uplink_server.py (total, unreviewed, last_24h)
- Updated Research tab status line to show counters alongside Last run info
- Ran agent: 10 articles inserted, 5 capped, 0 dupes, 0 errors
- Marked all 4 agent_feedback rows processed (processed_in_session='desktop-claude-2026-04-26-bundle-review')
- Deferred item 4 (artifact table UI) — fields already exist in research_articles; no action

## Key Decisions

- arXiv exact-phrase matching returns 0 for HN-style queries — accepted, HN alone delivers 10 articles/run
- stats-server has a two-location problem: claudis/stats-server/ is git source, ~/aadp/stats-server/ is what runs; cp is the deploy step
- Counter label format: `{total} total · {unreviewed} unreviewed · {last_24h} new (24h)` appended to existing Last run line

## Capability Delta

**Before:** Research agent used 5 narrow "context engineering" queries; Research tab showed only last-run timestamp; feedback rows were unprocessed backlog.

**After:** Agent searches 5 broader platform/architecture topics yielding fresh articles each run. Research tab status line shows live counts. All 4 queued feedback items reviewed, acted on, or consciously deferred and marked closed.

## Verification

- `inserted: 10, skipped_dupe: 0, capped: 5, errors_logged: 0` on first run with new queries
- Counters smoke test: total=16, unreviewed=10, last_24h=16
- All 4 feedback rows confirmed processed in Supabase

## Lessons Written

1. stats-server deploy path (~/aadp/stats-server/ ≠ claudis/stats-server/)
2. arXiv exact phrase fails for HN-style queries

## Usage

Session ~45% · Weekly ~75%
