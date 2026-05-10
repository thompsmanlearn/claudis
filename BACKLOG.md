## B-120: Build "Bill's mind" capture and working bundle
Status: ready
Depends on: none

### Goal
Create a free-text input in Anvil for Bill to write whatever is on his mind — thoughts, dissatisfactions, things to look at — that has no current home. The contents flow into a "working bundle" callable that desktop Claude reads at session start. Closes the gap where Bill's general input has no destination outside of directives or thread-attached annotations.

### Context
Investigation on 2026-05-10 confirmed: directive field is the only structured intention-capture, and it's narrow ("do this"). Annotations on threads don't flow anywhere actionable. There's no path for Bill to leave a note like "lessons retrieval feels off" that a desktop session would actually see and act on.

This card builds the smallest viable version: one input, one storage location, one bundle callable, one export button. No classification, no card generation, no automation yet. Just the channel.

### Done when
- New table `bill_notes` in Supabase: id, content, created_at, addressed (bool default false), addressed_at
- New uplink callable `add_bill_note(content)` writes a row
- New uplink callable `get_working_bundle()` returns markdown with three sections:
  - "What's on Bill's mind" — all bill_notes where addressed=false, newest first
  - "What Claude Code flagged" — last 14 days of session artifacts where outcome contains "failed", "stuck", "blocked", or "unresolved" (one-line summary each)
  - "Recent activity" — last 5 session artifact titles and outcomes
- New uplink callable `mark_bill_note_addressed(note_id)` flips addressed flag
- New Anvil panel on the Control tab (or new "Workspace" tab — pick whichever is cleaner): textarea, "Add note" button, list of unaddressed notes with "Mark addressed" button each, and an "Export working bundle" button that copies get_working_bundle() output to clipboard

### Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py, Supabase schema (new table)
Do not touch: agent_feedback, thread_entries, directives flow, anything else
