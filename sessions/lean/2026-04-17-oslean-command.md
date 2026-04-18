# Session: 2026-04-17 — oslean-command

## Directive
Build a /oslean Telegram command that triggers a non-interactive lean boot session. Bill edits DIRECTIVES.md on GitHub first, then sends /oslean to kick it off from his phone.

## What Changed
- **~/aadp/sentinel/lean_runner.sh** (new, executable): Shell script spawned by stats_server. Creates /tmp/oslean.lock, does git pull on claudis, runs `claude -p --dangerously-skip-permissions --max-turns 200 <<< "Read /home/thompsman/aadp/LEAN_BOOT.md"`, sends Telegram on completion (success/timeout/error). 2-hour timeout via `timeout` command (exit 124). Cleans lock on exit via trap.
- **stats_server.py**: Added `/trigger_lean` endpoint (GET or POST). Checks /tmp/oslean.lock — if fresh (<2h), returns "already in progress" message without spawning. If stale, kills orphaned claude process and removes lock. Otherwise spawns lean_runner.sh as a detached background process (start_new_session=True) and returns immediately with "Session starting" message.
- **TCA (kddIKvA37UDw4x6e)**: Added `/oslean` to queryCommands in parse-command node — routes to `http://host.docker.internal:9100/trigger_lean`, label "Lean Session", ack "Checking…". Also added to help text. No other TCA changes.

## What Was Learned
- `claude` binary is at `/home/thompsman/.local/bin/claude` — not in PATH when spawned from a systemd-managed stats_server subprocess. Must use full path.
- Lock guard needs to live in stats_server.py (not just lean_runner.sh) so the "already running" message comes back through TCA as a proper response, not a separate Telegram fire-and-forget.
- `subprocess.Popen(..., start_new_session=True)` is the right pattern for spawning a detached background process from FastAPI without blocking the request.
- The query_agent TCA path (Prep Ack → Send Ack → Call Webhook → Handle Response → Send Response) gives two Telegram messages per /oslean: immediate ack ("Checking…") + webhook response ("Session starting…"). lean_runner.sh then sends a third on completion. Total: 3 messages across the session lifetime — acceptable.

## Unfinished
Nothing. /oslean is fully operational. To use:
1. Edit ~/aadp/claudis/DIRECTIVES.md on GitHub with the directive
2. Send /oslean in Telegram
3. Receive "Checking… / Session starting" immediately
4. Receive completion ping when done (minutes to ~2 hours later)
