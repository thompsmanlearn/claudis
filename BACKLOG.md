# B-022–B-031: archived 2026-04-18. All complete. See session artifacts in sessions/lean/.
B-032: Dashboard mobile UX — collapsible sections, agent filtering, and protected indicators
Status: ready
Depends on: B-030
Goal
Make the Anvil dashboard usable on a phone screen. The current layout renders all 32 agents as a flat list with full detail and controls on each, which is unusable on mobile. Add collapsible status groups, a search/filter mechanism, compact agent cards that expand on tap, and the ⚠️ protected agent indicator. Also collapse the other panels (system status, work queue, inbox, controls) so the dashboard opens fast and Bill can drill into what he needs.
Context
The dashboard is at thompsmanlearn/claude-dashboard (master branch). All UI is built programmatically in client_code/Form1/__init__.py using add_component(). Material Design 3 theme. The agent_registry table has a protected boolean field already — just needs to be included in the get_agent_fleet() select and rendered in the UI. The Anvil skill reference is at skills/anvil/REFERENCE.md. Current agent status groups: active (22), paused (10), plus sandbox/building/broken/retired. Key constraint: Anvil free plan may not support all MD3 components — test what works. The programmatic approach means collapsible sections are likely done with show/hide logic on ColumnPanels controlled by button click handlers.
Done when

All dashboard sections (System Status, Agent Fleet, Work Queue, Inbox, Controls) are collapsible with a header tap — default collapsed except System Status
Agent fleet grouped by status with count badges (e.g. "Active (22)") — each group collapsible independently
Agent cards are compact by default (name, status icon, protected indicator) — tap to expand full detail, controls, and feedback
⚠️ icon shown next to protected agents
Search/filter text input at top of agent fleet section — filters by agent name as you type
get_agent_fleet() updated to include protected field
Dashboard loads and is usable on a phone-width screen
Commits pushed to both repos

Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py (add protected to select), thompsmanlearn/claude-dashboard client_code
Do not touch: stats_server.py, mcp-server/server.py, systemd units, Supabase schema, .env
