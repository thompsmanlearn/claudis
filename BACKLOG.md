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

## B-121: Fix working bundle output quality
Status: ready
Depends on: B-120

### Goal
Working bundle output is structurally right but content is unusable. Truncated summaries, broken filter on the "flagged" section, and "(no delta)" lines surfacing without explanation. Fix so the bundle is something a desktop session can actually read and act on.

### Context
First run on 2026-05-10. Bill's note landed correctly. Issues:
- Session summaries truncated mid-sentence (e.g. "Bill can write free-text notes via the Workspace tab. Notes persist in `bill_not")
- "What Claude Code flagged" section returns recent sessions broadly, not just sessions matching failed/stuck/blocked/unresolved. The filter logic in get_working_bundle isn't working as intended.
- "(no delta)" appears as a session outcome on most entries. Either these sessions wrote no real outcome line, or the parser is misreading the artifact format. Either way, "(no delta)" entries shouldn't surface as notable activity.

### Done when
- Session summaries in the bundle show either: the full outcome/learned line from the artifact, OR a clean one-line summary capped at ~120 chars with no mid-word truncation
- The "What Claude Code flagged" section ONLY contains sessions where the artifact body contains "failed", "stuck", "blocked", "unresolved", or "error" (case-insensitive). Verify by running the callable and confirming non-matching sessions don't appear.
- "(no delta)" sessions either get filtered out of the bundle entirely, or get a clear label explaining what (no delta) means. Pick one. Document the choice in the callable's docstring.
- Re-run get_working_bundle() and paste the output back so Bill can verify before closing the card.

### Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py (get_working_bundle only)
Do not touch: bill_notes table, add_bill_note, mark_bill_note_addressed, the Workspace UI, or any other callable.
## B-122: Build audit bundle for system-wide review
Status: ready
Depends on: B-121

### Goal
Create a second export callable that produces a broader system snapshot for design and review sessions. Where the working bundle shows what's current and active, the audit bundle shows what exists, what's accumulated, and what's changed. Desktop Claude reads this when the session is about reviewing or redesigning the system, not running daily work.

### Context
Working bundle (B-120, B-121) covers daily collaboration — Bill's notes, recent flags, recent activity. The audit bundle is the companion for periodic system review. Bill hits it when something feels off or when we're doing design work. It should give a desktop session enough ground truth to audit a store's health, question whether something is earning its keep, or notice drift.

The audit bundle is intentionally bigger than the working bundle. It's not read every session. It's read when we need the wider view.

### Done when
- New uplink callable `get_audit_bundle()` returns markdown with the following sections:

  **## Store sizes and activity (last 14 days)**
  One line per accumulating store. Columns: name, total size, additions in last 14d, last write timestamp.
  Stores to include: `lessons_learned` (Supabase), `lessons_learned` (ChromaDB), `research_articles`, `research_findings` (ChromaDB), `threads`, `thread_entries`, `agent_feedback`, `bill_notes`, `session_memory` (ChromaDB), `reference_material` (ChromaDB).

  **## Agent fleet**
  Total count, count by status (active / paused / sandbox / retired). List all active agents with one-line description (from agent_registry) and last run timestamp if available.

  **## Recent sessions (last 14 days, all)**
  Full list of session artifacts in this window, one line each: date, title, one-line outcome (same _clean_summary logic from B-121). No filter.

  **## Open work**
  Current contents of DIRECTIVES.md (raw). Count of pending and claimed items in work_queue. Count of unaddressed bill_notes.

  **## What's changed since last audit**
  If a row in `system_config` named `last_audit_at` exists, show stores whose row counts grew since that timestamp. If no such row exists, note "no prior audit recorded" and skip the section. Do NOT update `last_audit_at` automatically — that's a separate manual call.

- New uplink callable `mark_audit_taken()` writes/updates `last_audit_at` in `system_config` to now(). Called manually after Bill exports the bundle.

- "Export audit bundle" button added to the Workspace tab, below the existing working bundle export. Copies `get_audit_bundle()` output to clipboard. Separate button from working bundle — they're different exports for different purposes.

- Run `get_audit_bundle()` once and paste the output back so Bill can verify before closing.

### Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py (new callables), ~/aadp/claude-dashboard/client_code/Form1/__init__.py (add Export audit bundle button to Workspace tab)
Do not touch: get_working_bundle, bill_notes table, any other existing callable, any other tab.
