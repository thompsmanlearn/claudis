# Session: 2026-04-17 — documentation-and-version-control

## Directive
Two directives executed this session:
1. Write DEEP_DIVE_BRIEF.md — comprehensive technical reference built from direct inspection of all source files and live system queries.
2. B-025: Add stats_server.py and supporting infrastructure to version control.

Plus: COLLABORATOR_BRIEF.md updated with card format guide, TRAJECTORY.md updated with Anvil direction.

## What Changed
- **DEEP_DIVE_BRIEF.md** — 776-line technical reference covering all 12 sections (infrastructure, data flows, MCP tools, stats_server endpoints, agent fleet, DB schema, ChromaDB collections, lesson system, session mechanics, git conventions, config files, known gaps). Written from direct file reads and live SQL/ChromaDB queries. Commit 0889686.
- **claudis/stats-server/stats_server.py** — production file (3,205 lines) now in git, unmodified. Highest system fragility eliminated.
- **claudis/stats-server/aadp-stats.service** — systemd unit file captured.
- **claudus/stats-server/supabase_rpcs.sql** — DDL for both increment_lessons_applied_by_id and increment_lessons_applied, queried from live DB.
- **claudis/stats-server/.gitignore** — prevents .env, __pycache__, venv from being committed.
- **BACKLOG.md** — B-025 card added; card format now consistent.
- **COLLABORATOR_BRIEF.md** — card format guide added at end: structure, writing rules, two-hour ceiling, context cost explanation.
- **TRAJECTORY.md** — updated with Anvil dashboard direction (Parked), /oslean broken status noted, session timestamp updated.
- **DIRECTIVES.md** — set to investigate /oslean for next session.

## What Was Learned
- stats_server.py had no inline secrets. All credentials read from .env. Only hardcoded value is Bill's Telegram chat_id (line 432) — not a credential, no change needed.
- The FastAPI sidecar in mcp-server/server.py (port 9100 endpoints) is legacy/unreachable — the real stats server is the standalone systemd process.
- Full BACKLOG.md loads on every Run: B-NNN directive. Archiving old cards is load-bearing, not cosmetic.
- Rebase conflict on DIRECTIVES.md: Opus had written the prose directive directly to remote while we were working locally. Resolved to card-pointer format.
- aadp-stats restart verified: /healthz ok, /inject_context_v3 returns confidence:medium, 5 lessons, 940-token context block.

## Known Issues
- **/oslean is broken.** Bill confirmed the Telegram command is not triggering lean sessions. Root cause unknown — could be TCA routing, /trigger_lean endpoint, lock file state, or lean_runner.sh. Next session investigates and fixes.

## Anvil Direction (from Bill/Opus)
Anvil (anvil.works) is under evaluation as a dashboard and UI layer. Key capability: Uplink feature maintains a persistent websocket from Pi to Anvil cloud — no port forwarding needed. Pi uplink script wraps existing infrastructure (stats_server, Supabase, git). Anvil app serves as browser/PWA dashboard accessible from any device. Solves: real monitoring UI, interactive lean session launch, inbox approval UI, phone capabilities. First milestone: read-only dashboard. Blocked on Bill creating an Anvil account. Not yet a backlog card. Captured in TRAJECTORY.md Parked Directions.

## Unfinished
- /oslean fix (next directive)
- architecture_review agent behavioral_health_check (pending from prior sessions)
