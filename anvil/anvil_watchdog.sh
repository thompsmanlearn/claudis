#!/bin/bash
# Watchdog: verify aadp-anvil health and restart if unresponsive.
# Runs every 15 minutes via aadp-anvil-watchdog.timer.
set -euo pipefail

HEALTH_URL="http://localhost:9101/ping"
SERVICE="aadp-anvil.service"

if curl -sf --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
    echo "$(date -Iseconds): anvil health OK"
    exit 0
fi

echo "$(date -Iseconds): anvil health check FAILED — restarting $SERVICE"
systemctl restart "$SERVICE"
echo "$(date -Iseconds): $SERVICE restarted"
