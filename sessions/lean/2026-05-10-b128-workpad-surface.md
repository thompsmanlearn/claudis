# Session: B-128 Workpad Surface
Date: 2026-05-10
Type: lean
Directive: B-128
Code commits: claude-dashboard f57254d, claudis a1580af (uplink callables), 29912f7 (TRAJECTORY)

## Tasks completed
- Created `workpad_state` Supabase table (singleton row, id=1 CHECK constraint)
- Added 5 uplink callables: `get_workpad_state`, `save_workpad_input`, `fetch_url_content`, `clear_workpad`, `promote_workpad_to_thread`
- Replaced Form1 Workpad placeholder with full implementation: input textarea, URL field, 4 action buttons, debounced auto-save (2s dirty-flag Timer), scrollable output entries (newest-first, 600-char truncation + Show more), inline promote mini-form
- Restarted aadp-anvil; uplink connected and keepalive verified

## Key decisions
- HTML stripping: stdlib `re.sub` + `html.unescape` — bs4 and html2text not in venv, this covers real-world HTML adequately
- Truncation at 600 chars (card suggested 500 — bumped for denser content readability)
- Debounce: 2s periodic Timer with dirty flag rather than true debounce — simpler, same user-visible effect
- Copy fallback: separate `_wp_copy_fallback` ColumnPanel below feedback label, not mixed into output entries panel
- State loads on first tab open (lazy, like threads) not on page load

## Capability delta
**Before:** Workpad tab existed as a stub placeholder with a "coming in B-128" label.
**After:** Workpad is a live investigation surface. Bill can: paste content, fetch a URL and read its text, copy input to clipboard, clear with confirmation, promote current input to a new thread (with charter entry automatically added). All state persists across page reloads via Supabase singleton row.

## Lessons written
1. `lesson_stdlib_html_strip_2026-05-10` — stdlib re+html.unescape adequate for HTML stripping when libraries unavailable

## Branches
- claude-dashboard: `attempt/b128-workpad-surface` → merged to master

## Usage
~15% session, ~40% weekly est.
