#!/bin/bash
# lean_runner.sh — spawned by stats_server /trigger_lean
# Runs a non-interactive Claude Code lean session via LEAN_BOOT.md.
# Manages its own lock, timeout, and Telegram notifications.

LOCK_FILE="/tmp/oslean.lock"
LOG_DIR="/home/thompsman/aadp/logs"
VENV_DIR="/home/thompsman/aadp/mcp-server/venv"
CLAUDIS_DIR="/home/thompsman/aadp/claudis"
MCP_DIR="/home/thompsman/aadp/mcp-server"
LEAN_BOOT="/home/thompsman/aadp/LEAN_BOOT.md"
DIRECTIVES="${CLAUDIS_DIR}/DIRECTIVES.md"
CLAUDE_BIN="/home/thompsman/.local/bin/claude"
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

# Extract CARD_ID if DIRECTIVES.md is a single-line pointer "Run: B-NNN"
DIRECTIVE_RAW=$(cat "${DIRECTIVES}" 2>/dev/null | tr -d '\r')
if echo "${DIRECTIVE_RAW}" | grep -qE '^Run: B-[0-9]+$'; then
    CARD_ID=$(echo "${DIRECTIVE_RAW}" | grep -oE 'B-[0-9]+')
fi

write_phase "started" "booting: ${CARD_ID:-directive}"
log "STATUS: wrote started phase to session_status"


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

    # GRADER: grade the completed card if auto_cycle is enabled and CARD_ID is known (B-087)
    # Only auto-cycle sessions get graded — manual single-card sessions skip this.
    if [ -n "${CARD_ID}" ]; then
        AUTO_CYCLE_ENABLED=$(curl -s \
            -H "apikey: ${SUPABASE_KEY}" \
            -H "Authorization: Bearer ${SUPABASE_KEY}" \
            "${SUPABASE_URL}/rest/v1/system_config?key=eq.auto_cycle_enabled&select=value" \
            2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0].get('value','false') if d else 'false')" 2>/dev/null || echo "false")

        if [ "${AUTO_CYCLE_ENABLED}" = "true" ]; then
            # Find most recent session artifact for this card
            ARTIFACT=$(ls -t "${CLAUDIS_DIR}/sessions/lean/"*"${CARD_ID}"*.md 2>/dev/null | head -1)
            ARTIFACT_NAME=$(basename "${ARTIFACT}" 2>/dev/null || echo "")
            # Capture HEAD SHA immediately after card commit (B-104)
            CARD_COMMIT_SHA=$(git -C "${CLAUDIS_DIR}" rev-parse HEAD 2>/dev/null || echo "")
            log "GRADER: grading ${CARD_ID} artifact=${ARTIFACT_NAME} sha=${CARD_COMMIT_SHA:0:8}"

            GRADE_RESULT=$(curl -s --max-time 90 -X POST "http://localhost:9100/grade_card" \
                -H "Content-Type: application/json" \
                -d "{\"card_id\": \"${CARD_ID}\", \"session_artifact_path\": \"${ARTIFACT_NAME}\", \"commit_sha\": \"${CARD_COMMIT_SHA}\"}" \
                2>/dev/null)
            VERDICT=$(echo "${GRADE_RESULT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('verdict','pause'))" 2>/dev/null || echo "pause")
            log "GRADER: verdict=${VERDICT}"

            if [ "${VERDICT}" = "pass" ]; then
                log "GRADER: pass — auto-cycle may proceed"
            else
                # pause or fail: file annotation, stop chain
                RATIONALE=$(echo "${GRADE_RESULT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('rationale','')[:400])" 2>/dev/null || echo "")
                curl -s -X POST "${SUPABASE_URL}/rest/v1/agent_feedback" \
                    -H "apikey: ${SUPABASE_KEY}" \
                    -H "Authorization: Bearer ${SUPABASE_KEY}" \
                    -H "Content-Type: application/json" \
                    -H "Prefer: return=minimal" \
                    -d "{\"target_type\": \"card\", \"target_id\": \"${CARD_ID}\", \"content\": \"Grader verdict: ${VERDICT}. ${RATIONALE}\", \"action_session\": \"lean_runner_grader\"}" \
                    >> "${LOG_FILE}" 2>&1
                send_telegram "⚠️ Grader: ${CARD_ID} verdict=${VERDICT}. Auto-cycle stopped. Review grader_reviews in Anvil."
                log "GRADER: chain stopped at ${CARD_ID} — ${VERDICT}"
                exit 0
            fi
        else
            log "GRADER: auto_cycle not enabled — skipping grader"
        fi
    fi

    # AUTO-CYCLE: if enabled and an unblocked project node exists, trigger the next session
    CYCLE_SCRIPT=$(mktemp /tmp/cycle_XXXXXX.py)
    cat > "${CYCLE_SCRIPT}" << 'PYEOF'
import sys, os, json, urllib.request

url = os.environ.get('SUPABASE_URL', '')
key = os.environ.get('SUPABASE_KEY', '')
if not url or not key:
    sys.exit(0)
headers = {'apikey': key, 'Authorization': 'Bearer ' + key}

def get(path):
    req = urllib.request.Request(url + path, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

try:
    cfg = get('/rest/v1/system_config?key=eq.auto_cycle_enabled&select=value')
    if not cfg or not cfg[0].get('value'):
        sys.exit(0)

    projects = get('/rest/v1/aadp_projects?status=eq.active&select=id,name')
    if not projects:
        sys.exit(0)
    proj_ids = {p['id'] for p in projects}
    proj_names = {p['id']: p.get('name', p['id']) for p in projects}

    nodes = get('/rest/v1/aadp_project_nodes?select=id,name,status,dependencies,context,acceptance_criteria,project_id')
    nodes = [n for n in nodes if n['project_id'] in proj_ids]
    done_ids = {n['id'] for n in nodes if n['status'] == 'done'}

    for node in sorted([n for n in nodes if n['status'] == 'pending'], key=lambda x: x['id']):
        deps = node.get('dependencies') or []
        if all(d in done_ids for d in deps):
            print(json.dumps(node))
            sys.exit(0)

    # No pending nodes — request Bill's confirmation before marking complete (B-107)
    if not any(n['status'] != 'done' for n in nodes) and nodes:
        try:
            ac_cfg = get('/rest/v1/system_config?key=eq.auto_cycle_completion&select=value')
            auto_complete = ac_cfg[0].get('value', False) if ac_cfg else False
        except Exception:
            auto_complete = False

        if auto_complete:
            # Explicit opt-in: auto-PATCH to complete (legacy behavior)
            for pid in proj_ids:
                req = urllib.request.Request(
                    url + f'/rest/v1/aadp_projects?id=eq.{pid}',
                    data=json.dumps({'status': 'complete'}).encode(),
                    headers={**headers, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'},
                    method='PATCH'
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
            print('PROJECT_COMPLETE', file=sys.stderr)
        else:
            # Safe default: write annotation and wait for Bill's confirmation
            for pid in proj_ids:
                proj_name = proj_names.get(pid, pid)
                annotation = {
                    'target_type': 'project_completion',
                    'target_id': pid,
                    'content': f"Project '{proj_name}' has no remaining unblocked pending nodes. Confirm completion or identify missing work.",
                    'action_session': 'lean_runner_auto_cycle',
                    'metadata': {'intent_type': 'question', 'project_name': proj_name},
                }
                req = urllib.request.Request(
                    url + '/rest/v1/agent_feedback',
                    data=json.dumps(annotation).encode(),
                    headers={**headers, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=10):
                    pass
            print('PROJECT_COMPLETION_PENDING', file=sys.stderr)

except Exception as e:
    print(f'CYCLE_ERROR: {e}', file=sys.stderr)
PYEOF

    export SUPABASE_URL SUPABASE_KEY
    NEXT_NODE=$(python3 "${CYCLE_SCRIPT}" 2>> "${LOG_FILE}")
    rm -f "${CYCLE_SCRIPT}"

    if [ -n "${NEXT_NODE}" ]; then
        NODE_LABEL=$(echo "${NEXT_NODE}" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])")
        echo "${NEXT_NODE}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
lines = ['# Project Node: ' + d['name'], '',
         '## Goal', d.get('acceptance_criteria', ''), '',
         '## Context', d.get('context', ''), '',
         '## Node ID', d['id'], '']
with open('${DIRECTIVES}', 'w') as f:
    f.write('\n'.join(lines))
" && log "CYCLE: wrote directive for node: ${NODE_LABEL}"

        git -C "${CLAUDIS_DIR}" add "${DIRECTIVES}" \
            && git -C "${CLAUDIS_DIR}" commit -m "auto-cycle: directive → ${NODE_LABEL}" \
            && git -C "${CLAUDIS_DIR}" push >> "${LOG_FILE}" 2>&1 \
            && log "CYCLE: DIRECTIVES.md committed" \
            || log "CYCLE: git commit failed (non-fatal)"

        # Release lock before triggering — next session creates its own
        rm -f "${LOCK_FILE}"
        trap 'rm -f "${PROMPT_FILE}"; log "Cleanup done."' EXIT

        sleep 2
        curl -s http://localhost:9100/trigger_lean >> "${LOG_FILE}" 2>&1
        send_telegram "Auto-cycle → '${NODE_LABEL}'"
        log "CYCLE: triggered next session"
    else
        log "CYCLE: no unblocked nodes — session chain complete"
    fi

elif [ "${EXIT_CODE}" -eq 124 ]; then
    log "TIMEOUT: killed after ${TIMEOUT_SECS}s"
    write_phase "timeout" "timed out after ${MINS}m"
    send_telegram "Lean session timed out after 2 hours. Check ${LOG_FILE}"
else
    log "ERROR: exit code ${EXIT_CODE} after ${DURATION}s"
    write_phase "error" "exit ${EXIT_CODE} after ${MINS}m ${SECS}s"
    send_telegram "Lean session error (exit ${EXIT_CODE}, ${MINS}m ${SECS}s). Check ${LOG_FILE}"
fi
