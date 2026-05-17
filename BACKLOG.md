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
