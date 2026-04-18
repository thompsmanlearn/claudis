B-033: Lean session status indicator on Anvil dashboard
Status: ready
Goal
Add a visible status indicator next to the Trigger Lean Session button on the Anvil dashboard so Bill can see whether a lean session is currently running before triggering a new one. This prevents accidental concurrent sessions (no coordination layer exists) and closes the visibility gap on the primary control surface.
Context
The Trigger Lean Session button calls trigger_lean_session() which hits stats_server /trigger_lean. This spawns a claude -p process. There is currently no way to know from the dashboard whether a session is already running. Two concurrent sessions can silently conflict on git, Supabase, and file writes. The detection mechanism is a ps aux check for claude processes — crude but sufficient. The uplink_server.py registers callable functions that the dashboard invokes; a new callable get_lean_status() is needed. The dashboard UI is programmatic (add_component() in client_code/Form1/__init__.py). Anvil skill reference at skills/anvil/REFERENCE.md.
Done when

get_lean_status() callable registered in uplink_server.py, returns {"running": bool, "pid": int|null}
Dashboard shows status indicator next to Trigger button — idle vs running
Trigger button refreshes status after a short delay so Bill sees the state change
Trigger button disabled or shows warning when a session is already running
Both repos committed and pushed (claudis main, claude-dashboard master)

Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py
Do not touch: stats_server.py, agent fleet, n8n workflows
