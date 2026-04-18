# Session: 2026-04-18 — Anvil Uplink Key

## Directive
B-028: Add the Anvil Uplink key to .env and verify connection to anvil.works.

## What Changed
- `~/aadp/mcp-server/.env`: added `ANVIL_UPLINK_KEY=server_BYUWVDIOIIZOT65Y46QEDLQ7-PUCVGRU3KBBGPNPH`
- `anvil-uplink 0.7.0` installed in `~/aadp/mcp-server/venv` (also pulled: ws4py-sslupdate, future, argparse)
- `~/aadp/mcp-server/anvil_test.py`: minimal test — connects, prints confirmation, disconnects cleanly
- `~/aadp/claudis/tools/anvil_test.py`: copy committed to repo
- `BACKLOG.md`: B-028 marked complete; B-027 context corrected (Section 13 not 4, master branch noted, read-only scope clarified)
- `DIRECTIVES.md`: already pointed to Run: B-027 (no change needed)

## What Was Learned
- `anvil-uplink` has no clean `on_connect` callback in v0.7.0 — calling `anvil.server.connect()` then checking that no exception was raised is sufficient to confirm a live Uplink connection
- The mcp-server venv is the right install target; system Python lacks the package and the server process uses the venv
- `thompsmanlearn/claude-dashboard` uses `master` branch (not `main`) — GITHUB_TOKEN verified working against it

## Lessons Applied
None — session was too short and mechanical to draw on the lesson store.

## Unfinished
- B-027: build the Uplink service (systemd + Anvil app UI) — next card
- Write functions (approve_inbox_item, write_directive, trigger_lean_session) deferred to a card after B-027
