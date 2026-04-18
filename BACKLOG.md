B-028: Add Anvil Uplink key to .env and verify connection
Status: complete (2026-04-18)
Depends on: none
Goal
Add the Anvil server Uplink key to the environment file so the Pi can connect to Anvil's cloud. This completes the manual setup Bill did in the browser (account, app, Uplink enabled) and unblocks B-027.
Context
Bill created an Anvil app ("Claude Dashboard") at anvil.works with server Uplink enabled. The key is server_BYUWVDIOIIZOT65Y46QEDLQ7-PUCVGRU3KBBGPNPH. The anvil-uplink pip package may not be installed yet — check and install if needed. The uplink script will eventually be a systemd service but that's B-027 scope. This card just gets the key stored and the connection proven.
Done when

ANVIL_UPLINK_KEY line present in ~/aadp/mcp-server/.env
pip install anvil-uplink confirmed (in the appropriate venv if applicable)
A minimal test script connects to Anvil and prints confirmation (then exits)
Commit pushed to main

Scope
Touch: ~/aadp/mcp-server/.env
Do not touch: stats_server.py, any systemd units, any Anvil app code

B-027: Build Anvil Uplink service and read-only dashboard
Status: complete (2026-04-18)
Depends on: B-028
Goal
Build the Pi-side Uplink service as a systemd unit and create a read-only Anvil dashboard showing system status, agent fleet, and work queue. Prove the architecture end-to-end before adding interactive controls.
Context
Anvil app "Claude Dashboard" is live at anvil.works, App ID PUCVGRU3KBBGPNPH. GitHub integration connected to thompsmanlearn/claude-dashboard (default branch: master, not main) — push to that repo and Anvil syncs automatically. Server Uplink key is in ~/aadp/mcp-server/.env as ANVIL_UPLINK_KEY. Connection verified (B-028). The Uplink script should delegate to existing infrastructure — stats_server endpoints and Supabase — not reimplement business logic. See DEEP_DIVE_BRIEF Section 13 for the proposed uplink function table (read-only functions only: get_system_status, get_agent_fleet, get_work_queue — write functions deferred to a later card). The Anvil app is Material Design 3 theme. Build the app using the programmatic approach (add_component() in __init__.py) — it's more natural for Claude Code than writing YAML. Bill has no SSH access to the Pi — all Pi work must go through Claude Code.
Done when

aadp-anvil.service systemd unit running and auto-restarting
Uplink script registers callable functions: get_system_status(), get_agent_fleet(), get_work_queue()
Anvil app displays a dashboard with those three data views
Dashboard accessible from browser and usable on phone
App code committed and pushed to thompsmanlearn/claude-dashboard
Uplink service code committed to thompsmanlearn/claudis
Commit pushed to main

Scope
Touch: ~/aadp/claudis/anvil/, thompsmanlearn/claude-dashboard repo, systemd unit files
Do not touch: stats_server.py, mcp-server/server.py, .env (already configured), n8n workflows


## B-029: Add interactive controls to Anvil dashboard

**Status:** complete (2026-04-18)
**Depends on:** B-027

### Goal
Turn the dashboard from a read-only monitor into a control surface. Add callable functions and UI controls for triggering lean sessions, writing directives, and approving inbox items.

### Context
B-027 proved the architecture. This card added trigger_lean_session, write_directive, approve_inbox_item, deny_inbox_item, and get_inbox callables to the uplink server, plus full control UI in the Anvil app.

### Done when
- Three new callables registered and live
- Dashboard UI has controls for lean trigger, directive writing, inbox approve/deny
- Uplink service restarted and verified
- Commits pushed to both repos

### Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, thompsmanlearn/claude-dashboard client_code
Do not touch: stats_server.py, mcp-server/server.py, systemd unit file, .env

B-030: Agent fleet detail view with controls and feedback
Status: ready
Depends on: B-029
Goal
Replace the simple agent name list with a detailed fleet view showing description, status, schedule, and last activity for each agent. Add activate/pause controls and a thumbs-up/thumbs-down feedback mechanism per agent. This is the governance surface — it lets Bill see what's running, whether it's useful, and act on that judgment without opening a terminal.
Context
The current dashboard shows agent names grouped by status. The agent_registry table in Supabase has: agent_name, display_name, description, status, schedule, workflow_id, performance_metrics (jsonb), updated_at. Status values: active, paused, retired, building, broken, sandbox. The uplink server is at ~/aadp/claudis/anvil/uplink_server.py, Anvil app at thompsmanlearn/claude-dashboard (master branch). Feedback ratings don't have a table yet — create a simple agent_feedback table in Supabase with: id (uuid), agent_name (text), rating (int, 1 or -1), comment (text nullable), created_at (timestamptz). The uplink pattern for Supabase CRUD is proven from B-029. The activate/pause control should PATCH agent_registry.status — only allow toggling between active and paused. Do not allow changing to/from retired, building, broken, or sandbox from the dashboard.
Done when

get_agent_fleet() returns description, status, schedule, updated_at per agent
Each agent in the dashboard shows: display_name, description, status, schedule, last updated
Activate/pause toggle button per agent (only active↔paused)
Thumbs-up/thumbs-down buttons per agent, with optional short comment field
agent_feedback table created in Supabase
New callables: set_agent_status(agent_name, status), submit_agent_feedback(agent_name, rating, comment)
Uplink service restarted and verified
Commits pushed to both repos

Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, thompsmanlearn/claude-dashboard client_code, Supabase DDL (new table only)
Do not touch: stats_server.py, mcp-server/server.py, n8n workflows, agent behavior
