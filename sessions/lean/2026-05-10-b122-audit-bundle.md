# Session: B-122 — Build Audit Bundle
Date: 2026-05-10
Type: lean
Card: B-122
Code commit: cbaefc8 (attempt/b122-audit-bundle in claudis), d5e9b21 (claude-dashboard), merged 967ee76 / 21d3429

## Tasks Completed
- Added `get_audit_bundle()` callable to `anvil/uplink_server.py` — returns markdown with store sizes, agent fleet, recent sessions (all, last 14d), open work, delta since last audit
- Added `mark_audit_taken()` callable to `anvil/uplink_server.py` — upserts `last_audit_at` in `system_config`
- Added "Export audit bundle" button to Workspace tab in `client_code/Form1/__init__.py`

## Key Decisions
- `research_articles` uses `retrieved_at` not `created_at` — parameterized timestamp column per store as `(table, ts_col)` tuples
- ChromaDB stores report total count only (no additions/last write — no native timestamp filtering)
- Delta section uses `system_config.key='last_audit_at'` with JSONB value for the stored timestamp; PostgREST upsert with `resolution=merge-duplicates`
- Sessions section: no FLAG_WORDS filter — all sessions in 14-day window, same `_clean_summary` logic as working bundle

**After:** Audit bundle callable is live and tested. All 10 stores return without error. Agent fleet, sessions, open work, and delta sections all populate correctly. Export audit bundle button is in Workspace tab. mark_audit_taken() is ready for manual call after first export.
