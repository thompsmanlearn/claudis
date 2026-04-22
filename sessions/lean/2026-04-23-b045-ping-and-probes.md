# Session: 2026-04-22 — B-045: /ping websocket fix + §13 probes

## Directive
B-045: Fix `localhost:9101/ping` to reflect Anvil websocket state; complete three deferred §13 probes (Telegram webhook, n8n API key, lean_runner.sh drift).

## What Changed

- **`~/aadp/claudis/anvil/uplink_server.py`** — `_HealthHandler.do_GET` now checks `anvil.server._connection is not None and conn.is_ready()` in addition to the existing `_last_keepalive` age. Returns 503 with body `ws_disconnected`, `supabase_stale`, or `ws_disconnected,supabase_stale` when unhealthy. Committed `31eee68` and pushed to main.
- `aadp-anvil.service` restarted; `/ping` confirmed HTTP 200 `ok` on healthy connection.

## /ping Before / After

**Before:** `_HealthHandler` checked only `_last_keepalive` age (< 1200s). `_last_keepalive` is refreshed by a Supabase background probe every 10 minutes, independent of websocket state. A dead websocket with a live process returned 200 as long as Supabase was reachable.

**After:** Also checks `anvil.server._connection is not None and conn.is_ready()`. The library sets `_connection = None` in `reconnect()` the moment `closed()` fires. The library's `heartbeat_until_reopened()` sends `call("anvil.private.echo", "keep-alive")` every 10 seconds, so silent disconnects are detected within ~10–20s. False-positive window: **20 minutes → ~10–20 seconds**.

503 body names the failing check(s), making watchdog log triage easier.

## Probe Results

| Probe | Result |
|-------|--------|
| **Telegram webhook** | `kddIKvA37UDw4x6e` (Telegram Command Agent) — `active: true`. POST `/webhook/telegram-quick-send` → HTTP 200, message delivered. |
| **n8n API key** | `workflow_list` returned 51 workflows with HTTP 200. API key valid. |
| **lean_runner.sh drift** | `diff ~/aadp/sentinel/lean_runner.sh ~/aadp/claudis/sentinel/lean_runner.sh` → exit 0. Files identical. |

## Incidental Finding: telegram-quick-send field is `message`, not `text`

The diagnostic probe sent `{"text": "..."}` but the workflow's Send Telegram node reads `{{ $json.body.message }}`. Bill received the message body as literal "undefined". **This is not a systemic bug** — all production callers use the correct field:
- `stats_server.py` line 432: `{"chat_id": ..., "message": message}` ✓
- `lean_runner.sh` line 48: `{"message": "$1"}` ✓

The "undefined" delivery was caused by the diagnostic probe using the wrong field. No fix needed; worth noting so the next session using this webhook sends `{"message": "..."}`.

## Open Questions for Desktop

- None blocking. The `/ping` fix is live and tested. All three probes are closed.
- The Telegram webhook field mismatch (`text` vs `message`) is documented above for awareness. If desktop wants a fix card to add input validation or a field alias, that would be a standalone card.

## Unfinished

Nothing. All B-045 done-when conditions are met.
