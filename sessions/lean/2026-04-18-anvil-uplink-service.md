# Session: 2026-04-18 — anvil-uplink-service

## Directive
B-027: Build Anvil Uplink service and read-only dashboard (system status, agent fleet, work queue).

## What Changed

**Pi service (`~/aadp/claudis/anvil/uplink_server.py`)**
- Registers three `@anvil.server.callable` functions: `get_system_status()`, `get_agent_fleet()`, `get_work_queue()`
- `get_system_status` delegates to stats_server `http://localhost:9100/system_status`
- `get_agent_fleet` queries Supabase `agent_registry` (agent_name, status, workflow_id)
- `get_work_queue` queries Supabase `work_queue` (non-complete tasks, newest first)
- Reads credentials from `~/aadp/mcp-server/.env` at startup

**Systemd unit (`/etc/systemd/system/aadp-anvil.service`)**
- Enabled and started; auto-restarts on failure (RestartSec=15)
- Uses MCP server venv: `/home/thompsman/aadp/mcp-server/venv/bin/python3`
- Confirmed connected: "Connected to Default Environment as SERVER"

**Anvil app (`thompsmanlearn/claude-dashboard`, branch: master)**
- `client_code/Form1/__init__.py` — programmatic M3 dashboard with three outlined-card panels
- Calls all three uplink functions on load; Refresh button triggers re-fetch
- Agent fleet grouped: Active / Sandbox / Other with bullet list per group

**Commits pushed:**
- `thompsmanlearn/claudis` main: `82186f4`
- `thompsmanlearn/claude-dashboard` master: `a6d1108` (Anvil syncs from this repo automatically)

## What Was Learned
- `agent_registry` uses `agent_name` column, not `name` — verify column names against live schema before writing any query
- Both `anvil-uplink` and `requests` are in the MCP server venv — the uplink service must use that venv's Python, not system Python
- Anvil GitHub sync: push to `thompsmanlearn/claude-dashboard` master → Anvil picks up automatically, no manual deploy step

## Unfinished
- Dashboard not manually confirmed in browser — Bill needs to open the Anvil app and verify the three panels render live data. The uplink is connected, so this should work.
- Interactive controls (write functions) deferred to a later card per B-027 scope.
- architecture_review agent (7mVc61pDCIObJFos) behavioral_health_check still pending (TRAJECTORY Vector 1 next milestone).
