#!/bin/bash
# Polls /ping on the Anvil uplink server. Restarts aadp-anvil.service on non-200.

PING_URL="http://localhost:9101/ping"
TIMEOUT=5
TMP=$(mktemp)

status=$(curl -s --max-time "$TIMEOUT" -o "$TMP" -w "%{http_code}" "$PING_URL" 2>/dev/null || echo "000")
body=$(cat "$TMP")
rm -f "$TMP"

if [ "$status" = "200" ]; then
    echo "$(date -Iseconds): anvil-watchdog: /ping OK"
else
    echo "$(date -Iseconds): anvil-watchdog: /ping returned ${status} (body: ${body}) — restarting aadp-anvil.service"
    systemctl restart aadp-anvil.service
    echo "$(date -Iseconds): anvil-watchdog: aadp-anvil.service restarted"
fi

exit 0
