# Session: 2026-04-18 — Anvil Uplink Key

## Directive
B-028: Add the Anvil Uplink key to .env and verify connection to anvil.works.

## What Changed
- `~/aadp/mcp-server/.env`: added `ANVIL_UPLINK_KEY=server_BYUWVDIOIIZOT65Y46QEDLQ7-PUCVGRU3KBBGPNPH`
- `anvil-uplink 0.7.0` installed in `~/aadp/mcp-server/venv` (also pulled: ws4py-sslupdate, future, argparse)
- `~/aadp/mcp-server/anvil_test.py`: minimal test — connects, prints confirmation, disconnects cleanly
- `~/aadp/claudis/tools/anvil_test.py`: copy committed to repo
- `BACKLOG.md`: B-028 marked complete

## What Was Learned
- `anvil-uplink` has no clean `on_connect` callback in v0.7.0 — calling `anvil.server.connect()` then checking that no exception was raised is sufficient to confirm a live Uplink connection
- The mcp-server venv is the right install target; system Python lacks the package and the server process uses the venv

## Unfinished
- B-027: build the Uplink service (systemd + Anvil app UI) — next card
