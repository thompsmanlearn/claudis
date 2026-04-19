#!/bin/bash
# =============================================================================
# Sentinel Scheduler — ~/aadp/sentinel/scheduler.sh
# Invoked by systemd timer every 8 hours.
# Launches Claude Code in headless mode (-p) with the Sentinel prompts.
# =============================================================================

set -euo pipefail

# --- Configuration ---
SENTINEL_DIR="/home/thompsman/aadp/sentinel"
VENV_DIR="/home/thompsman/aadp/mcp-server/venv"
LOG_DIR="/home/thompsman/aadp/logs"
LOCK_FILE="/tmp/sentinel.lock"
STALE_LOCK_SECONDS=7200  # 2 hours
MAX_TURNS=200            # Max Claude Code iterations per invocation
TELEGRAM_CHAT_ID="8513796837"
DISK_PROMPT="${SENTINEL_DIR}/disk_prompt.md"
WAKE_PROMPT="${SENTINEL_DIR}/wake_prompt.md"

# --- Ensure directories exist ---
mkdir -p "${LOG_DIR}"
mkdir -p "/home/thompsman/aadp/prompts"

# --- Timestamp for logging ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="${LOG_DIR}/sentinel_$(date '+%Y%m%d').log"

log() {
    echo "[${TIMESTAMP}] $1" >> "${LOG_FILE}"
}

# --- Send Telegram alert (best effort, no dependency on n8n) ---
send_telegram_alert() {
    local message="$1"
    # Read the bot token from n8n's SQLite DB is complex;
    # instead, store it in .env or a dedicated file.
    # For now, use curl via n8n webhook as fallback.
    # This can be enhanced later with a direct bot token.
    log "ALERT: ${message}"
}

# --- Lock check ---
if [ -f "${LOCK_FILE}" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "${LOCK_FILE}") ))
    if [ "${LOCK_AGE}" -lt "${STALE_LOCK_SECONDS}" ]; then
        log "SKIP: Lock file exists (age: ${LOCK_AGE}s). Another instance is running."
        exit 0
    else
        log "WARNING: Stale lock detected (age: ${LOCK_AGE}s). Removing and proceeding."
        rm -f "${LOCK_FILE}"
    fi
fi

# --- Create lock ---
echo "$$" > "${LOCK_FILE}"
trap 'rm -f "${LOCK_FILE}"' EXIT

log "START: Sentinel invocation beginning"

# --- Activate virtual environment (needed for MCP server dependencies) ---
source "${VENV_DIR}/bin/activate"

# --- Change to the MCP server directory (Claude Code expects this) ---
cd /home/thompsman/aadp/mcp-server

# --- Lesson Injector: fetch pre-loaded context for the pending task ---
INJECT_WEBHOOK="http://localhost:5678/webhook/inject-context"
ENRICHED_PROMPT=$(mktemp /tmp/sentinel_prompt_XXXXXX.md)
trap 'rm -f "${LOCK_FILE}" "${ENRICHED_PROMPT}"' EXIT

# Look up highest-priority pending task from work_queue via Supabase REST
SUPABASE_URL=$(grep SUPABASE_URL .env | cut -d= -f2)
SUPABASE_KEY=$(grep SUPABASE_SERVICE_KEY .env | cut -d= -f2)
TASK_JSON=$(curl -s \
    -H "apikey: ${SUPABASE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_KEY}" \
    "${SUPABASE_URL}/rest/v1/work_queue?status=eq.pending&order=priority.asc,created_at.asc&limit=1&select=id,task_type,input_data" \
    2>/dev/null || echo "[]")

TASK_TYPE=$(echo "${TASK_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['task_type'] if d else 'general')" 2>/dev/null || echo "general")
TASK_ID=$(echo "${TASK_JSON}"   | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d[0]['id']) if d else '')" 2>/dev/null || echo "")
TASK_DESC=$(echo "${TASK_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d[0].get('input_data',{}).get('description','')) if d else '')" 2>/dev/null || echo "")

# --- Atomically claim the task at shell level before Claude starts ---
if [ -n "${TASK_ID}" ]; then
    CLAIM_NOW=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    curl -s -X PATCH \
        -H "apikey: ${SUPABASE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"status\":\"claimed\",\"claimed_at\":\"${CLAIM_NOW}\",\"assigned_agent\":\"sentinel\"}" \
        "${SUPABASE_URL}/rest/v1/work_queue?id=eq.${TASK_ID}&status=eq.pending" \
        > /dev/null 2>&1 \
        && log "CLAIM: task ${TASK_ID} (${TASK_TYPE}) marked claimed" \
        || log "WARNING: failed to claim task ${TASK_ID} — proceeding anyway"
fi

# Call lesson_injector webhook (5s timeout, fail gracefully)
INJECT_PAYLOAD=$(python3 -c "import json,sys; print(json.dumps({'task_type': sys.argv[1], 'task_id': sys.argv[2], 'description': sys.argv[3]}))" "${TASK_TYPE}" "${TASK_ID}" "${TASK_DESC}" 2>/dev/null)
CONTEXT_BLOCK=$(curl -s --max-time 10 -X POST "${INJECT_WEBHOOK}" \
    -H "Content-Type: application/json" \
    -d "${INJECT_PAYLOAD}" \
    2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('context_block',''))" 2>/dev/null || echo "")

# Assemble enriched prompt: CONTEXT BLOCK + wake_prompt
if [ -n "${CONTEXT_BLOCK}" ]; then
    echo "${CONTEXT_BLOCK}" > "${ENRICHED_PROMPT}"
    log "INJECT: lesson_injector returned context (task_type=${TASK_TYPE})"
else
    log "INJECT: lesson_injector unavailable or no context — proceeding without enrichment"
fi
cat "${WAKE_PROMPT}" >> "${ENRICHED_PROMPT}"

# --- Run Claude Code in headless mode ---
EXIT_CODE=0
CLAUDE_OUTPUT=$(claude -p \
    --dangerously-skip-permissions \
    --max-turns "${MAX_TURNS}" \
    --system-prompt-file "${DISK_PROMPT}" \
    < "${ENRICHED_PROMPT}" \
    2>&1) || EXIT_CODE=$?
echo "${CLAUDE_OUTPUT}" >> "${LOG_FILE}"

# --- Handle exit ---
if [ "${EXIT_CODE}" -eq 0 ]; then
    log "END: Sentinel invocation completed successfully"
else
    # Check if failure was a rate limit — if so, un-claim the task so next wake can retry
    if echo "${CLAUDE_OUTPUT}" | grep -q "You've hit your limit\|rate limit\|Rate limit" 2>/dev/null && [ -n "${TASK_ID}" ]; then
        log "RATE_LIMIT: usage limit hit — releasing task ${TASK_ID} back to pending"
        curl -s -X PATCH \
            -H "apikey: ${SUPABASE_KEY}" \
            -H "Authorization: Bearer ${SUPABASE_KEY}" \
            -H "Content-Type: application/json" \
            -d "{\"status\":\"pending\",\"claimed_at\":null,\"assigned_agent\":null}" \
            "${SUPABASE_URL}/rest/v1/work_queue?id=eq.${TASK_ID}" \
            > /dev/null 2>&1 \
            && log "RATE_LIMIT: task ${TASK_ID} released" \
            || log "WARNING: failed to release task ${TASK_ID}"
    else
        log "ERROR: Sentinel exited with code ${EXIT_CODE}"
        send_telegram_alert "Sentinel exited with error code ${EXIT_CODE}. Check ${LOG_FILE}"
    fi
fi

# --- Session Health Reporter: fire-and-forget after every session ---
curl -s --max-time 10 -X POST "http://localhost:5678/webhook/5x6G8gFlCxX0YKdM/webhook/session-health-report" \
    -H "Content-Type: application/json" \
    -d "{\"exit_code\": ${EXIT_CODE}, \"triggered_by\": \"sentinel\"}" \
    >> "${LOG_FILE}" 2>&1 || log "WARNING: session-health-report webhook failed (non-fatal)"

# --- Rotate logs: keep last 7 days ---
find "${LOG_DIR}" -name "sentinel_*.log" -mtime +7 -delete 2>/dev/null || true

log "---"
