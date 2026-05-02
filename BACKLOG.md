## B-076: Redesign thread detail view (read-only) for signal-over-plumbing

**Status:** ready

### Goal
Restructure the thread detail view in Anvil so the question, current standing, and meaningful entries (annotations, gather-with-content, analyses) are foreground, while state-change entries collapse into a History log drawer. Pure read-side rearrangement — no schema changes, no new actions, no new input channels yet. The point is to validate that the new shape feels right before building further redesign work on top of it.

### Context
A redesign effort began 2026-04-30 after first real use of thread architecture v0.1 surfaced that the substrate works but the UI buries signal under operational plumbing. Current thread view in `claude-dashboard/client_code/Form1/__init__.py` renders all `thread_entries` flat, with state_change rows dominating the view visually.

Companion design doc (kept in Bill's Drive) lays out:
- **Top:** question, one-line state, standing-summary slot (most recent analysis entry's first paragraph if any, blank otherwise)
- **Middle:** annotations, gathers, analyses as readable content blocks in chronological order — no state_change rows
- **Bottom:** sub-questions placeholder section (sub-questions not yet modeled in schema; render an empty section so the layout slot is in place)
- **History log:** collapsed drawer below main content, expands to show state_change entries on click

Existing `get_thread_entries(thread_id)` callable returns all entries; this card partitions them by `entry_type` at render time. No callable or schema changes.

Anvil dashboard is built programmatically (`add_component()` in `Form1/__init__.py`), MD3 theme. Load `skills/anvil/REFERENCE.md` (auto-routed) and explicitly view `/mnt/skills/public/frontend-design/SKILL.md` before starting for layout and typography guidance.

### Done when
- Thread detail view shows three sections in order: header (question + one-line state + standing-summary slot), main content (annotation, gather, analysis entries chronologically, no state_change rows), sub-questions placeholder
- History log toggle below main content; collapsed by default; expands to show state_change entries when clicked
- Standing-summary slot renders first paragraph (text to first blank line, or 300 chars) of most recent analysis entry if any exist; empty otherwise
- TEST thread (only state_change entries) shows empty main content with History log drawer present and expandable
- Consumer AI thread shows question, standing summary from most recent analysis, annotation and analysis entries as content blocks, no state_change rows in main view, History log drawer below
- Commit pushed to `claude-dashboard` `master` branch
- Session artifact at `~/aadp/claudis/sessions/lean/2026-MM-DD-thread-view-redesign.md`

### Scope
Touch:
- `claude-dashboard/client_code/Form1/__init__.py` — thread detail rendering only
- `claude-dashboard/client_code/Form1/form_template.yaml` — only if structurally required

Do not touch:
- `anvil/uplink_server.py` — no callable changes
- Supabase schema, ChromaDB collections — no changes
- Other Anvil tabs (Fleet, Sessions, Lessons, Memory, Research, Skills, Artifacts)
- Action panel at bottom of thread detail — stays as-is this card
- Threads list view on left — no changes
