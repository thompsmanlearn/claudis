B-131: Redesign Desktop Claude Export

Status: ready Depends on: none
Goal

Replace the current working bundle and audit bundle with a single export shaped for Desktop Claude as the named reader. The existing exports return counts and fleet status — useful for sysadmin review, not for a collaborator who needs to ask "what has the system been thinking about, what did it find, and where is it stuck?"
Context

Two export callables exist in anvil/uplink_server.py: get_working_bundle() and get_audit_bundle(). Both return markdown. Both are triggered from the Workspace tab in the Anvil dashboard. The audit bundle has a companion mark_audit_taken() that upserts last_audit_at in system_config.

The named reader for the new export is Desktop Claude in a take-stock conversation. Desktop Claude cannot load files autonomously — the export must be self-contained. It will be pasted into a chat by Bill.

Desktop Claude's working questions when it receives the export:

    What has the system actually been doing since last time?
    What did the research pipeline find — with enough detail to evaluate relevance?
    What's broken, stale, or uncertain?
    What's unresolved that needs a judgment call?

Done when

    get_desktop_bundle() callable registered in uplink_server.py and returns without error
    Export contains: (1) active threads with most recent summary entry text expanded, not just count; (2) up to 10 recent research articles with title, full URL, source, and summary field — not just counts; (3) up to 5 recent session artifacts with Capability delta section expanded if present, "(no delta recorded)" if absent; (4) known fragilities — query agent_feedback WHERE processed = false AND target_type IN ('agent','skill','capability') ORDER BY created_at DESC LIMIT 10, return target and content; (5) store counts (keep from audit bundle — these are useful at a glance)
    "Export for Desktop Claude" button added to Workspace tab, calls get_desktop_bundle()
    Existing get_working_bundle() and get_audit_bundle() left in place — do not remove
    Commit pushed to master branch of claude-dashboard repo

Scope

Touch: anvil/uplink_server.py, client_code/Form1/__init__.py Do not touch: get_working_bundle(), get_audit_bundle(), stats server, any n8n workflows, any Supabase schema
B-132: Bill Input Channel — Question / Comment / Command
Status: ready
Depends on: none
Goal
Add a three-mode input panel to the Anvil Home tab that Bill can use before triggering a lean session. UI input is processed at boot before any backlog directive. Claude Code reads the pending input, acts on it based on mode, writes a response back, and marks it consumed.
Context
Design fully resolved in session 2026-05-17 with Claude Code and Desktop Claude. All decisions are settled — execute against this spec without redesigning.
Priority rule: bill_input is checked before DIRECTIVES.md. A Command replaces DIRECTIVES.md for that session. Question and Comment leave DIRECTIVES.md intact and the existing directive still runs after.
Trigger Lean Session button is confirmed working — Bill's intended workflow is: type input → hit Trigger Lean Session → session processes input at boot.
Done when

bill_input table exists in Supabase with columns: id (uuid pk), mode (text), text (text), status (text default 'pending'), response (text), created_at (timestamptz), processed_at (timestamptz)
submit_bill_input(mode, text) callable registered in uplink_server.py — upserts a single row (overwrites any existing row), status=pending
get_bill_input_response() callable registered in uplink_server.py — returns current row's status and response text
LEAN_BOOT.md has a new step inserted between current step 4 (CONVENTIONS) and step 5 (DIRECTIVES): query bill_input WHERE status='pending' LIMIT 1; if found, process by mode (see Scope); mark processed with processed_at; if not found, skip silently
Command mode behavior verified: text written to DIRECTIVES.md, git commit + push, response written as "Command written to DIRECTIVES.md — executing as directive this session"
Question mode behavior verified: answer generated and written to response field, existing DIRECTIVES.md unchanged
Comment mode behavior verified: saved to lessons_learned + ChromaDB, response written as "Saved as lesson: [title]", existing DIRECTIVES.md unchanged
Anvil Home tab has new panel above existing export buttons: mode selector (three buttons: Question / Comment / Command), text input area, Submit button, response panel with "Check response" button, copy button next to response
Submit clears the input box immediately; response panel shows "⏳ Awaiting Claude Code response..." until Check response is clicked and a response exists
Uplink restarted and confirmed connected after changes
Commit pushed to main (claudis) and master (claude-dashboard)

Scope
Touch: anvil/uplink_server.py, client_code/Form1/__init__.py, LEAN_BOOT.md, Supabase DDL via supabase_exec_sql
Do not touch: existing LEAN_BOOT.md steps, DIRECTIVES.md system, BACKLOG.md, existing export buttons, any n8n workflows, any agent registry entries
