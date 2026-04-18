# B-022–B-030: archived 2026-04-18. All complete. See session artifacts in sessions/lean/.

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
