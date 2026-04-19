# Session: 2026-04-18 — Sessions tab (B-039)

## Directive
B-039: Add a Sessions tab to the Anvil dashboard for live session visibility and artifact history.

## What Changed

**Supabase:** `session_status` table created with schema: `id (uuid PK)`, `session_id (text UNIQUE)`, `card_id`, `phase`, `current_action`, `started_at`, `updated_at`.

**lean_runner.sh** (`~/aadp/sentinel/lean_runner.sh` — disk-only):
- Loads `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` from `.env` at startup
- Sets `SESSION_ID` (timestamp + PID) at startup; `CARD_ID` populated after directive parsing
- `write_phase()` function: upserts a row into `session_status` via Supabase REST with `Prefer: resolution=merge-duplicates`
- Writes `started` phase after directive parsing (CARD_ID known), `executing` just before Claude launches, and `complete`/`error`/`timeout` at exit

**claudis/anvil/uplink_server.py** (committed, pushed to main):
- `get_session_status()` — returns most recent `session_status` row (or None)
- `get_session_artifacts(limit=10)` — lists `~/aadp/claudis/sessions/lean/*.md` sorted desc, extracts title from first H1, returns `[{filename, title, date, content}]`

**claude-dashboard/client_code/Form1/__init__.py** (committed, pushed to master):
- Sessions tab button added to tab row (between Fleet and Lessons)
- `_sessions_panel` built in `_build_sessions_layout()`: status card at top, artifact list below
- `_show_sessions_tab()`: hides Fleet/Lessons, shows Sessions, calls `_load_sessions()`
- `_load_sessions()`: queries `get_session_status` (phase + card + timestamp), then `get_session_artifacts` (15 most recent)
- `_build_artifact_card()`: title + date header, `+` expand button to reveal full markdown content
- Tab switching updated in all three `_show_*_tab` methods to hide Sessions panel correctly

**aadp-anvil.service** restarted — new callables live.

## What Was Learned

The `write_phase` upsert in lean_runner.sh requires `UNIQUE(session_id)` on the table for `Prefer: resolution=merge-duplicates` to work — the schema was created with that constraint. Without it the upsert would INSERT duplicates instead.

Lean sessions with pointer-style directives (`Run: B-NNN`) set `CARD_ID` after git pull and directive parsing — the `write_phase("started")` call is placed after that block so `CARD_ID` is populated in the status row.

## Unfinished

Nothing. All done-when criteria met:
- `session_status` table exists ✓
- `lean_runner.sh` writes started/executing/complete phases ✓
- Sessions tab shows current session state ✓
- Sessions tab shows recent artifacts with drill-down ✓
- Callables registered: `get_session_status()`, `get_session_artifacts()` ✓
- Phone-width usable (FlowPanel + ColumnPanel layout, consistent with existing tabs) ✓
- Both repos committed and pushed ✓
