# Session: 2026-04-18 — anvil-watchdog

## Directive
B-031: Add uplink connection watchdog and archive backlog cards B-022–B-030.

## What Changed
- `anvil/uplink_server.py` — added `ping()` callable; background HTTP health server on localhost:9101/ping; background Supabase keepalive thread (every 10 min); health returns 503 if keepalive stale >20 min
- `anvil/anvil_watchdog.sh` — new watchdog script: hits localhost:9101/ping, restarts aadp-anvil.service on failure
- `/etc/systemd/system/aadp-anvil-watchdog.service` + `.timer` — installed and enabled; fires every 15 minutes (first fire 5 min after boot)
- `BACKLOG.md` — B-022–B-031 all archived; file now 3 lines (down from 43)
- `TRAJECTORY.md` — Destination 5 updated to reflect B-031 complete; Parked Directions updated

## What Was Learned
- The health endpoint (localhost:9101) is the right layer for the watchdog — it detects both process death and Supabase connectivity loss without needing to call an Anvil callable from the Pi side (which would require a second uplink connection).
- The keepalive thread provides the liveness signal: process alive + Supabase reachable = healthy. If the Anvil websocket silently disconnects but the process is alive, systemd won't help — but Anvil's built-in auto-reconnect handles that case. If reconnect fails, the keepalive eventually goes stale and the watchdog restarts the service.
- B-022–B-029 were already archived by Bill in the `bae8e6f` commit pulled at session start — the card's context was slightly stale. Only B-030 and B-031 needed to be removed from BACKLOG.md.

## Boot-chain file sizes (post-archive)
PROTECTED.md: 34 | DIRECTIVES.md: 2 | CATALOG.md: 10 | CONTEXT.md: 70 | TRAJECTORY.md: ~97 | BACKLOG.md: 3 | Total: ~216

## Unfinished
Nothing. All "Done when" items verified. Next card: B-032 when Bill writes one.
Candidate: agent that reads agent_feedback table and surfaces patterns to Bill.
