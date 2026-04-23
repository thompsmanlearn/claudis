# Session: 2026-04-22 — error_logs column fix (created_at → timestamp)

## Directive
Three bug fixes from PROJECT_STATE.md decomposition — error_logs column naming.

## What Changed
- `~/aadp/claudis/anvil/uplink_server.py` (`c7302d6`):
  - `get_table_rows` error_logs `select`: `created_at` → `timestamp`
  - `get_table_rows` error_logs `order`: `created_at.desc` → `timestamp.desc`
- `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (`50e3970`):
  - Error log card render: `row.get('created_at')` → `row.get('timestamp')`
- Fix #3 (LEAN_BOOT.md `error_log` → `error_logs`): **skipped** — LEAN_BOOT.md was rewritten to 34 lines in the 2026-04-22 boot chain restructure; the table reference no longer exists in that file.

## What Was Learned
- `claude-dashboard` uses `master` branch, not `main` — separate repo from `claudis`.
- The `error_logs` table column is named `timestamp` (not `created_at`), which is non-standard for Supabase. Worth noting when writing future error_logs queries.

## Unfinished
- Anvil UI error log view still read-only — resolve button (Gap #2 from PROJECT_STATE.md) not yet built.
- Site regeneration, artifact comments, work queue detail, per-agent invocation remain open (see PROJECT_STATE.md).
