B-028: Add Anvil Uplink key to .env and verify connection
Status: ready
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
