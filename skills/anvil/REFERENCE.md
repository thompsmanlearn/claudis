# Anvil Uplink & Server Callable Reference

## Error Propagation (Uplink → Browser)
- Exceptions raised in @anvil.server.callable functions propagate directly to the client as Python exceptions
- Client-side try/except catches them normally — the current dashboard pattern is correct
- Anvil defines specific exception types: TimeoutError, UplinkDisconnectedError, NoServerFunctionError, AppOfflineError, SerializationError, InternalError
- If the uplink process is down or disconnected, client gets UplinkDisconnectedError
- If a callable raises any Exception, it propagates to the browser as-is with the message string

## Timeout Behavior
- Free plan has approximately 30-second timeout on server calls (varies by plan)
- No built-in way for a callable to detect or extend its timeout
- For long-running work, the recommended pattern is: return an ID immediately, do work in a background thread, provide a second callable to poll for results
- anvil.server.call() in client code automatically shows a loading spinner — suppress with `with anvil.server.no_loading_indicator:` context manager

## Connection Stability
- Uplink websocket can silently disconnect after days of running — multiple forum reports of this
- anvil.server.connect() auto-reconnects on disconnect, but may not always succeed
- Recommended: periodic health check or daily restart via cron/systemd timer
- The systemd Restart=always in aadp-anvil.service handles crash recovery but not silent disconnects
- Consider adding a watchdog: a scheduled task or timer that calls a no-op callable to verify liveness

## anvil.server.call() Client-Side API
- anvil.server.call('function_name', arg1, arg2, kwarg=value) — args pass through
- Returns whatever the callable returns (must be "portable types": str, int, float, bool, None, list, dict, datetime, Media)
- Return data size limit: 4MB excluding Media objects
- Displays loading spinner by default — suppress with no_loading_indicator context manager
- Keyword arguments pass through to the callable

## Portable Types (what callables can accept/return)
- Strings, numbers, booleans, None
- Lists, dicts, tuples (of portable types)
- datetime objects
- anvil.Media objects (for large data/files)
- No circular references allowed

## Key Gotchas
- anvil-uplink 0.7.0 requires set_internal_tracer_provider(TracerProvider()) before any RPC dispatch or handler thread crashes (lesson already captured)
- Server Uplink has full server-side privileges — treat it like trusted code
- connect() init_session parameter runs after connection but before any calls — useful for setup verification
- quiet=True on connect() suppresses output but still shows errors
- The claude-dashboard repo uses master branch, not main

## Anvil App Structure (for Claude Code builds)
- App code lives in thompsmanlearn/claude-dashboard (master branch)
- client_code/Form1/__init__.py — UI built programmatically with add_component()
- server_code/ — server modules (not currently used, uplink handles everything)
- theme/assets/theme.css — styling
- anvil.yaml — app config
- Push to GitHub and Anvil syncs automatically
- Material Design 3 theme — use roles like 'outlined-card', 'filled-button', 'tonal-button', 'headline', 'title', 'body'

## Uplink Server Location
- ~/aadp/claudis/anvil/uplink_server.py
- Runs as systemd service: aadp-anvil.service
- Uses mcp-server venv for Python environment
- Reads credentials from ~/aadp/mcp-server/.env
