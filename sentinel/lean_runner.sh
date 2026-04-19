#!/bin/bash
# lean_runner.sh — spawned by stats_server /trigger_lean
# Runs a non-interactive Claude Code lean session via LEAN_BOOT.md.
# Injects relevant lessons from lesson_injector before starting.
# Manages its own lock, timeout, and Telegram notifications.

LOCK_FILE="/tmp/oslean.lock"
LOG_DIR="/home/thompsman/aadp/logs"
VENV_DIR="/home/thompsman/aadp/mcp-server/venv"
CLAUDIS_DIR="/home/thompsman/aadp/claudis"
MCP_DIR="/home/thompsman/aadp/mcp-server"
LEAN_BOOT="/home/thompsman/aadp/LEAN_BOOT.md"
DIRECTIVES="${CLAUDIS_DIR}/DIRECTIVES.md"
CLAUDE_BIN="/home/thompsman/.local/bin/claude"
INJECT_WEBHOOK="http://localhost:5678/webhook/inject-context"
BACKLOG="${CLAUDIS_DIR}/BACKLOG.md"
MAX_TURNS=200
TIMEOUT_SECS=7200   # 2 hours
TG_WEBHOOK="http://localhost:5678/webhook/telegram-quick-send"

# Load Supabase credentials for session_status writes
SUPABASE_URL=$(grep '^SUPABASE_URL=' "${MCP_DIR}/.env" | cut -d= -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
SUPABASE_KEY=$(grep '^SUPABASE_SERVICE_KEY=' "${MCP_DIR}/.env" | cut -d= -f2 | tr -d '"' | tr -d "'" | tr -d ' ')
SESSION_ID="lean_$(date '+%Y%m%d_%H%M%S')_$$"
CARD_ID=""

write_phase() {
    local phase="$1"
    local action="${2:-}"
    python3 -c "
import sys, requests, datetime
url, key, sid, cid, phase, action = sys.argv[1:]
r = requests.post(
    url + '/rest/v1/session_status',
    headers={'apikey': key, 'Authorization': 'Bearer ' + key,
             'Content-Type': 'application/json',
             'Prefer': 'resolution=merge-duplicates,return=minimal'},
    json={'session_id': sid, 'card_id': cid or None, 'phase': phase,
          'current_action': action,
          'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat()},
    timeout=5)
" "${SUPABASE_URL}" "${SUPABASE_KEY}" "${SESSION_ID}" "${CARD_ID}" "${phase}" "${action}" 2>/dev/null || true
}

send_telegram() {
    curl -s -X POST "${TG_WEBHOOK}" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$1\"}" > /dev/null 2>&1 || true
}

mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_DIR}/lean_$(date '+%Y%m%d_%H%M%S').log"
START_TIME=$(date +%s)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "START: lean_runner invoked"

# Create lock — stats_server already checked it isn't stale
echo "$$" > "${LOCK_FILE}"
PROMPT_FILE=$(mktemp /tmp/lean_prompt_XXXXXX.md)
trap 'rm -f "${LOCK_FILE}" "${PROMPT_FILE}"; log "Cleanup done."' EXIT

# Git pull
log "GIT: pulling claudis"
if ! git -C "${CLAUDIS_DIR}" pull >> "${LOG_FILE}" 2>&1; then
    send_telegram "Lean session failed: git pull error. Check ${LOG_FILE}"
    exit 1
fi

# Build directive description for lesson injection.
# If DIRECTIVES.md is a single-line pointer "Run: B-NNN", resolve the backlog card.
DIRECTIVE_RAW=$(cat "${DIRECTIVES}" 2>/dev/null | tr -d '\r')
if echo "${DIRECTIVE_RAW}" | grep -qE '^Run: B-[0-9]+$'; then
    CARD_ID=$(echo "${DIRECTIVE_RAW}" | grep -oE 'B-[0-9]+')
    DIRECTIVE_DESC=$(awk "/^## ${CARD_ID}:/{found=1} found{print; if(found && NF==0) count++; if(count>3) exit}" "${BACKLOG}" 2>/dev/null \
        | head -20 | tr '\n' ' ' | sed 's/["\\/]//g' | cut -c1-300)
    [ -z "${DIRECTIVE_DESC}" ] && DIRECTIVE_DESC="lean session ${CARD_ID}"
    log "INJECT: resolved ${CARD_ID} from BACKLOG.md"
else
    DIRECTIVE_DESC=$(echo "${DIRECTIVE_RAW}" | head -20 | tr '\n' ' ' | sed 's/["\\/]//g' | cut -c1-300)
fi
[ -z "${DIRECTIVE_DESC}" ] && DIRECTIVE_DESC="lean session directive"

write_phase "started" "booting: ${CARD_ID:-directive}"
log "STATUS: wrote started phase to session_status"

# Fetch lesson context from injector (25s timeout — endpoint takes ~15s)
log "INJECT: fetching lesson context"
INJECT_PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'task_type': 'general',
    'task_id': '',
    'description': sys.argv[1]
}))" "${DIRECTIVE_DESC}" 2>/dev/null)

CONTEXT_BLOCK=$(curl -s --max-time 25 -X POST "${INJECT_WEBHOOK}" \
    -H "Content-Type: application/json" \
    -d "${INJECT_PAYLOAD}" \
    2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('context_block', ''))" 2>/dev/null || echo "")

# Assemble prompt: context block + quality signal instruction + LEAN_BOOT trigger
if [ -n "${CONTEXT_BLOCK}" ]; then
    echo "${CONTEXT_BLOCK}" > "${PROMPT_FILE}"
    log "INJECT: context block received ($(echo "${CONTEXT_BLOCK}" | wc -l) lines)"
else
    log "INJECT: no context returned — proceeding without enrichment"
fi

cat >> "${PROMPT_FILE}" << 'EOF'

LESSON TRACKING: If any pre-loaded lessons above directly influenced a decision or saved you from a mistake during this session, list them by lesson ID in the session artifact under a "Lessons Applied" section. If none were relevant, omit the section. This tracks lesson injector effectiveness.

EOF

echo "Read ${LEAN_BOOT}" >> "${PROMPT_FILE}"

# Activate venv and run Claude
source "${VENV_DIR}/bin/activate"
cd "${MCP_DIR}"

write_phase "executing" "running ${CARD_ID:-directive}"
log "CLAUDE: starting"
EXIT_CODE=0
timeout "${TIMEOUT_SECS}" "${CLAUDE_BIN}" -p \
    --dangerously-skip-permissions \
    --max-turns "${MAX_TURNS}" \
    < "${PROMPT_FILE}" \
    >> "${LOG_FILE}" 2>&1 || EXIT_CODE=$?

END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))
MINS=$(( DURATION / 60 ))
SECS=$(( DURATION % 60 ))

if [ "${EXIT_CODE}" -eq 0 ]; then
    log "END: success (${DURATION}s)"
    write_phase "complete" "finished in ${MINS}m ${SECS}s"

    # Regenerate GitHub Pages site from live data
    log "SITE: regenerating"
    "${VENV_DIR}/bin/python3" /home/thompsman/aadp/thompsmanlearn.github.io/generate_site.py \
        >> "${LOG_FILE}" 2>&1 && log "SITE: updated" || log "SITE: update failed (non-fatal)"

    send_telegram "Lean session complete (${MINS}m ${SECS}s). Artifact in claudis/sessions/lean/"
elif [ "${EXIT_CODE}" -eq 124 ]; then
    log "TIMEOUT: killed after ${TIMEOUT_SECS}s"
    write_phase "timeout" "timed out after ${MINS}m"
    send_telegram "Lean session timed out after 2 hours. Check ${LOG_FILE}"
else
    log "ERROR: exit code ${EXIT_CODE} after ${DURATION}s"
    write_phase "error" "exit ${EXIT_CODE} after ${MINS}m ${SECS}s"
    send_telegram "Lean session error (exit ${EXIT_CODE}, ${MINS}m ${SECS}s). Check ${LOG_FILE}"
fi
