# Session: 2026-04-22 — B-046 Anvil uplink watchdog

## Directive
B-046: Create a systemd timer that polls `localhost:9101/ping` every 30 seconds and restarts `aadp-anvil.service` on non-200 response, closing the §13 "Anvil uplink silent disconnects" item.

## What Changed

### Files created
- `~/aadp/sentinel/anvil_watchdog.sh` — check script; captures HTTP status code and body; logs both on failure; restarts `aadp-anvil.service` on non-200; exits 0 always
- `~/aadp/claudis/sentinel/anvil_watchdog.sh` — versioned copy (same content)
- `~/aadp/claudis/sentinel/aadp-anvil-watchdog.service` — versioned copy of systemd service unit
- `~/aadp/claudis/sentinel/aadp-anvil-watchdog.timer` — versioned copy of systemd timer unit

### Files updated (in /etc/systemd/system/)
- `aadp-anvil-watchdog.service` — ExecStart updated to new script path (`~/aadp/sentinel/anvil_watchdog.sh`)
- `aadp-anvil-watchdog.timer` — interval changed from 15min to 30s; OnBootSec changed from 5min to 60s; `Persistent=true` added

**Prior state note:** A previous session (prior to B-044) had created the watchdog files with a 15-minute interval and the script at `~/aadp/claudis/anvil/anvil_watchdog.sh`. This session brought all three files to B-046 spec.

### Systemd
- `sudo systemctl daemon-reload` — done
- `sudo systemctl enable --now aadp-anvil-watchdog.timer` — already enabled; reloaded

## Verification

**Timer active:**
```
Wed 2026-04-22 11:03:39 PDT  aadp-anvil-watchdog.timer → aadp-anvil-watchdog.service
```

**Journal (healthy-state check, new script):**
```
Apr 22 11:03:06 raspberrypi systemd[1]: Starting aadp-anvil-watchdog.service
Apr 22 11:03:06 raspberrypi aadp-anvil-watchdog[514036]: 2026-04-22T11:03:06-07:00: anvil-watchdog: /ping OK
Apr 22 11:03:07 raspberrypi systemd[1]: Finished aadp-anvil-watchdog.service
```

**aadp-anvil.service NOT restarted** by watchdog during verification — confirmed, /ping returned 200.

## What Was Learned
- A partial implementation already existed from a prior session (watchdog active at 15-minute interval). B-046 brought it to the specified 30-second interval and moved the script to the `sentinel/` canonical location.
- The `Persistent=true` timer flag ensures a missed fire (e.g., during suspend or reboot gap) triggers immediately on next opportunity — important for a watchdog.
- `set -euo pipefail` in the old script was inappropriate for a watchdog — a failed `systemctl restart` would have caused the service to exit non-zero, making systemd think the watchdog itself failed, not the target service. Removed in new script.

## Unfinished
- No disconnect test was performed (per B-046 directive: do not simulate). Real disconnect will exercise restart path on its own.
- The old script at `~/aadp/claudis/anvil/anvil_watchdog.sh` still exists. It's no longer referenced by the service unit but could cause confusion. Safe to delete but not in scope for this card.
