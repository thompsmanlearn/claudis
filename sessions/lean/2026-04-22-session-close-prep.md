# Session: 2026-04-22 — session close prep (CATALOG + site status UI)

## Directive
Pre-close housekeeping: link PROJECT_STATE.md into boot chain; wire site status + regenerate gap (#3 from PROJECT_STATE.md).

## What Changed
- `~/aadp/claudis/skills/CATALOG.md` (`97e8369`): anvil row "Provides" updated to reference PROJECT_STATE.md — future Anvil sessions will know to load it.
- `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (`8d94354`):
  - `_build_sessions_layout`: added Site Status section (divider, header, Regenerate Site button, feedback label, `_site_status_card`)
  - `_load_sessions`: added site status load block calling `get_site_status()` — renders mode, agent count, generated_at, current directive, last 3 session summaries
  - `_regenerate_site_clicked`: new handler — calls `update_site()`, shows timestamp on success, refreshes site card

## What Was Learned
- Gap #3 (site status + regenerate) was genuinely the lowest-effort gap — both callables were complete, zero backend work needed.
- `update_site()` runs `generate_site.py` + git push internally, so the regenerate button is a full site rebuild, not just a status.json update.

## Unfinished
Remaining Anvil UI gaps (see PROJECT_STATE.md):
- Gap #2: Error log resolve (medium — needs new callable + UI card builder)
- Gap #1: Work queue detail (medium — expand select + card builder)
- Gap #4: Artifact comments (trivial — 3-line UI change)
- Gap #5: Per-agent invocation (medium — needs new callable + webhook_url verification)
