

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

B-031: Uplink connection watchdog and backlog archive
Status: ready
Depends on: B-030
Goal
Add a health-check mechanism that detects silent uplink disconnects and recovers automatically. The Anvil uplink websocket can go dead without the systemd service noticing — Restart=always only catches crashes, not silent disconnects. Also archive completed cards B-022–B-030 from BACKLOG.md to reduce boot-chain token load.
Context
Forum reports confirm uplink connections silently die after days of running. The current systemd unit has no liveness probe. Options: a systemd watchdog timer that calls a no-op callable and restarts the service on failure, or a periodic self-ping inside the uplink script itself. The simpler approach is a companion systemd timer that runs every 15 minutes, calls a lightweight callable (e.g. ping()), and restarts aadp-anvil.service if it fails. BACKLOG.md currently contains B-022 through B-030 — all complete. Archive them the same way B-001–B-021 were archived. This reclaims ~200 lines from every lean session's boot context.
Done when

ping() callable registered in uplink server
Watchdog timer/service pair installed: checks every 15 minutes, restarts aadp-anvil on failure
Watchdog tested (stop uplink, confirm watchdog restarts it)
B-022–B-030 archived from BACKLOG.md with archive note updated
Boot-chain file sizes reported: wc -l on PROTECTED.md, DIRECTIVES.md, CATALOG.md, CONTEXT.md, TRAJECTORY.md, BACKLOG.md
Commits pushed to main

Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, BACKLOG.md, systemd unit files
Do not touch: stats_server.py, mcp-server/server.py, dashboard client code, .env
