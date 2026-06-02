#!/usr/bin/env python3
"""AADP Anvil Uplink — read-only and control callables for the Claude Dashboard."""
import json
import logging
import os
import re
import subprocess
import threading
import time
import requests
import anvil.server
import anthropic
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
log = logging.getLogger(__name__)

# anvil-uplink 0.7.0 requires a tracer provider to be set before any call is dispatched
from anvil_downlink_util.tracing import set_internal_tracer_provider, TracerProvider
set_internal_tracer_provider(TracerProvider())


def _load_env(path: str) -> dict:
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    return env


_ENV = _load_env(os.path.expanduser('~/aadp/mcp-server/.env'))
_SUPABASE_URL = _ENV['SUPABASE_URL']
_SUPABASE_KEY = _ENV['SUPABASE_SERVICE_KEY']
_STATS_URL = 'http://localhost:9100'
_CHROMADB_URL = 'http://localhost:8000'
_HEADERS = {
    'apikey': _SUPABASE_KEY,
    'Authorization': f'Bearer {_SUPABASE_KEY}',
    'Content-Type': 'application/json',
}
_CLAUDIS_DIR = os.path.expanduser('~/aadp/claudis')


def _get_chromadb_collection_id(name: str) -> str:
    r = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{name}', timeout=5)
    r.raise_for_status()
    return r.json()['id']


# ── Health server (localhost:9101) ───────────────────────────────────────────
# Watchdog hits /ping to verify the process and Supabase connectivity are alive.

_last_keepalive = time.monotonic()
_keepalive_lock = threading.Lock()


def _keepalive_worker():
    """Background thread: Supabase liveness probe every 10 minutes."""
    global _last_keepalive
    time.sleep(30)  # let the uplink connect first
    while True:
        try:
            r = requests.get(
                f'{_SUPABASE_URL}/rest/v1/agent_registry',
                headers=_HEADERS,
                params={'select': 'agent_name', 'limit': '1'},
                timeout=10,
            )
            r.raise_for_status()
            with _keepalive_lock:
                _last_keepalive = time.monotonic()
            log.info('Keepalive OK')
        except Exception as e:
            log.warning('Keepalive failed: %s', e)
        time.sleep(600)  # 10 minutes


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping':
            with _keepalive_lock:
                age = time.monotonic() - _last_keepalive
            conn = anvil.server._connection
            ws_ok = conn is not None and conn.is_ready()
            supabase_ok = age < 1200  # 20 minutes — 2 keepalive cycles
            if ws_ok and supabase_ok:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'ok')
            else:
                self.send_response(503)
                self.end_headers()
                reasons = []
                if not ws_ok:
                    reasons.append('ws_disconnected')
                if not supabase_ok:
                    reasons.append('supabase_stale')
                self.wfile.write(','.join(reasons).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/write_thread_gather_entries':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length))
                thread_id = body.get('thread_id')
                article_ids = body.get('article_ids', [])
                if not thread_id or not isinstance(article_ids, list):
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'missing thread_id or article_ids')
                    return
                result = _write_thread_gather_entries_impl(thread_id, article_ids)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            except Exception as e:
                log.warning('write_thread_gather_entries HTTP error: %s', e)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # suppress per-request logging


threading.Thread(
    target=lambda: HTTPServer(('0.0.0.0', 9101), _HealthHandler).serve_forever(),
    daemon=True,
    name='health-server',
).start()
threading.Thread(target=_keepalive_worker, daemon=True, name='keepalive').start()
log.info('Health server listening on localhost:9101')


# ── Read-only callables ──────────────────────────────────────────────────────

@anvil.server.callable
def ping():
    global _last_keepalive
    with _keepalive_lock:
        _last_keepalive = time.monotonic()
    return {'pong': True}


@anvil.server.callable
def get_system_status():
    r = requests.get(f'{_STATS_URL}/system_status', timeout=5)
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_agent_fleet():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers=_HEADERS,
        params={
            'select': 'agent_name,display_name,description,status,schedule,protected,updated_at,webhook_url',
            'order': 'agent_name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def set_agent_status(agent_name, status):
    if status not in ('active', 'paused'):
        raise Exception(f'Invalid status "{status}". Only active or paused allowed.')
    # Read current status to enforce active↔paused only
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers=_HEADERS,
        params={'select': 'status', 'agent_name': f'eq.{agent_name}'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Agent "{agent_name}" not found.')
    current = rows[0]['status']
    if current not in ('active', 'paused'):
        raise Exception(f'Cannot toggle agent with status "{current}" from dashboard.')
    now = datetime.now(timezone.utc).isoformat()
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'agent_name': f'eq.{agent_name}'},
        json={'status': status, 'updated_at': now},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Agent %s status set to %s', agent_name, status)
    return {'status': status}


@anvil.server.callable
def invoke_agent(agent_name):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers=_HEADERS,
        params={'select': 'webhook_url,status', 'agent_name': f'eq.{agent_name}'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Agent "{agent_name}" not found.')
    row = rows[0]
    if row.get('status') != 'active':
        raise Exception(f'Agent "{agent_name}" is not active.')
    webhook_url = row.get('webhook_url')
    if not webhook_url:
        raise Exception(f'Agent "{agent_name}" has no webhook URL configured.')
    def _fire():
        try:
            resp = requests.post(webhook_url, json={}, timeout=120)
            log.info('Agent %s webhook completed: %d', agent_name, resp.status_code)
        except Exception as e:
            log.warning('Agent %s webhook error: %s', agent_name, e)

    threading.Thread(target=_fire, daemon=True, name=f'invoke-{agent_name}').start()
    log.info('Agent %s invoke fired (fire-and-forget)', agent_name)
    return {'triggered': True, 'agent': agent_name}


@anvil.server.callable
def submit_agent_feedback(agent_name, rating, comment=None):
    # LEGACY — thumbs-up/down buttons removed from Fleet tab 2026-05-09 (B-114).
    # No callers remain. Kept to avoid breaking any stale client versions.
    if rating not in (1, -1):
        raise Exception('Rating must be 1 (thumbs up) or -1 (thumbs down).')
    payload = {'agent_name': agent_name, 'rating': rating}
    if comment:
        payload['comment'] = comment.strip()[:500]
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    log.info('Feedback submitted for %s: rating=%d', agent_name, rating)
    return {'submitted': True}


@anvil.server.callable
def get_work_queue():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/work_queue',
        headers=_HEADERS,
        params={
            'select': 'id,task_type,status,priority,created_at,created_by,assigned_agent,input_data',
            'status': 'neq.complete',
            'order': 'priority.asc,created_at.asc',
            'limit': '30',
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_inbox():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/inbox',
        headers=_HEADERS,
        params={
            'select': 'id,from_agent,subject,body,priority,created_at',
            'status': 'eq.pending',
            'order': 'created_at.desc',
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


# ── Control callables ────────────────────────────────────────────────────────

@anvil.server.callable
def approve_inbox_item(item_id):
    now = datetime.now(timezone.utc).isoformat()
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/inbox',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{item_id}'},
        json={'status': 'approved', 'responded_at': now},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Inbox item %s approved', item_id)
    return {'status': 'approved'}


@anvil.server.callable
def deny_inbox_item(item_id):
    now = datetime.now(timezone.utc).isoformat()
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/inbox',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{item_id}'},
        json={'status': 'rejected', 'responded_at': now},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Inbox item %s denied', item_id)
    return {'status': 'rejected'}


@anvil.server.callable
def trigger_lean_session():
    r = requests.post(f'{_STATS_URL}/trigger_lean', timeout=15)
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_lean_status():
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
        procs = [l for l in result.stdout.splitlines() if 'claude -p' in l and 'grep' not in l]
        if procs:
            return {'running': True, 'pid': int(procs[0].split()[1])}
        return {'running': False, 'pid': None}
    except Exception as e:
        log.warning('get_lean_status error: %s', e)
        return {'running': False, 'pid': None}


@anvil.server.callable
def write_directive(text):
    text = (text or '').strip()
    if not text:
        raise Exception('Directive text cannot be empty.')
    directives_path = os.path.join(_CLAUDIS_DIR, 'DIRECTIVES.md')
    with open(directives_path, 'w') as f:
        f.write(text + '\n')
    for cmd in [
        ['git', '-C', _CLAUDIS_DIR, 'add', 'DIRECTIVES.md'],
        ['git', '-C', _CLAUDIS_DIR, 'commit', '-m', 'directive: written from Anvil dashboard'],
        ['git', '-C', _CLAUDIS_DIR, 'push', 'origin', 'main'],
    ]:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f'{cmd[2]} failed: {result.stderr.strip()}')
    log.info('Directive written and pushed: %s', text[:80])
    return {'status': 'written', 'message': 'Directive written and pushed to claudis.'}


# ── Autonomous mode callables ────────────────────────────────────────────────

_N8N_SCHEDULER_ID = 'Lm68vpmIyLfeFawa'
_N8N_BASE = 'http://localhost:5678/api/v1'


def _n8n_headers():
    return {'X-N8N-API-KEY': _ENV.get('N8N_API_KEY', ''), 'Content-Type': 'application/json'}


@anvil.server.callable
def get_autonomous_mode():
    """Returns scheduler_active (bool|None) and auto_cycle_enabled (bool)."""
    try:
        r = requests.get(f'{_N8N_BASE}/workflows/{_N8N_SCHEDULER_ID}', headers=_n8n_headers(), timeout=10)
        r.raise_for_status()
        scheduler_active = r.json().get('active', False)
    except Exception as e:
        log.warning('get_autonomous_mode n8n error: %s', e)
        scheduler_active = None

    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/system_config',
            headers=_HEADERS,
            params={'key': 'eq.auto_cycle_enabled', 'select': 'value'},
            timeout=5,
        )
        r.raise_for_status()
        rows = r.json()
        auto_cycle = rows[0]['value'] if rows else False
    except Exception:
        auto_cycle = False

    return {'scheduler_active': scheduler_active, 'auto_cycle_enabled': auto_cycle}


@anvil.server.callable
def set_autonomous_mode(enabled):
    """Enable or disable the autonomous growth scheduler and auto-cycle."""
    enabled = bool(enabled)
    errors = []

    action = 'activate' if enabled else 'deactivate'
    try:
        r = requests.post(
            f'{_N8N_BASE}/workflows/{_N8N_SCHEDULER_ID}/{action}',
            headers=_n8n_headers(),
            timeout=10,
        )
        r.raise_for_status()
    except Exception as e:
        errors.append(f'n8n: {e}')

    try:
        r = requests.patch(
            f'{_SUPABASE_URL}/rest/v1/system_config',
            headers={**_HEADERS, 'Prefer': 'return=minimal'},
            params={'key': 'eq.auto_cycle_enabled'},
            json={'value': enabled},
            timeout=5,
        )
        r.raise_for_status()
    except Exception as e:
        errors.append(f'auto_cycle: {e}')

    log.info('Autonomous mode set to %s', enabled)
    return {'enabled': enabled, 'errors': errors}


@anvil.server.callable
def retire_agent(agent_name, reason=''):
    """Retire an agent: set status=retired in agent_registry, write annotation."""
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'agent_name': f'eq.{agent_name}'},
        json={'status': 'retired', 'workflow_id': None},
        timeout=5,
    )
    r.raise_for_status()
    requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json={
            'target_type': 'agent',
            'target_id': agent_name,
            'content': f'Agent retired by Bill. Reason: {reason}' if reason else 'Agent retired by Bill.',
            'action_session': 'uplink_retire_agent',
            'processed': True,
            'metadata': {'intent_type': 'state_change', 'new_status': 'retired'},
        },
        timeout=5,
    )
    log.info('Agent %s retired: %s', agent_name, reason)
    return {'status': 'retired', 'agent_name': agent_name}


@anvil.server.callable
def retire_skill(skill_name, reason=''):
    """Retire a skill: set status=retired in skills_registry, write annotation."""
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/skills_registry',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'name': f'eq.{skill_name}'},
        json={'status': 'retired'},
        timeout=5,
    )
    r.raise_for_status()
    requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json={
            'target_type': 'skill',
            'target_id': skill_name,
            'content': f'Skill retired by Bill. Reason: {reason}' if reason else 'Skill retired by Bill.',
            'action_session': 'uplink_retire_skill',
            'processed': True,
            'metadata': {'intent_type': 'state_change', 'new_status': 'retired'},
        },
        timeout=5,
    )
    log.info('Skill %s retired: %s', skill_name, reason)
    return {'status': 'retired', 'skill_name': skill_name}


@anvil.server.callable
def confirm_project_complete(project_id, notes=''):
    """Mark a project complete after Bill's explicit confirmation."""
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/aadp_projects',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{project_id}'},
        json={'status': 'complete'},
        timeout=5,
    )
    r.raise_for_status()
    requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json={
            'target_type': 'project_completion',
            'target_id': project_id,
            'content': f'Project marked complete by Bill. Notes: {notes}' if notes else 'Project marked complete by Bill.',
            'action_session': 'uplink_confirm_project_complete',
            'metadata': {'intent_type': 'state_change', 'new_status': 'complete'},
        },
        timeout=5,
    )
    log.info('Project %s confirmed complete', project_id)
    return {'status': 'complete', 'project_id': project_id}


@anvil.server.callable
def reject_project_completion(project_id, reason=''):
    """Reject an auto-cycle completion request — project stays active."""
    requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json={
            'target_type': 'project_completion',
            'target_id': project_id,
            'content': f'Project completion rejected. Reason: {reason}' if reason else 'Project completion rejected.',
            'action_session': 'uplink_reject_project_completion',
            'metadata': {'intent_type': 'state_change', 'action': 'rejected', 'reason': reason},
        },
        timeout=5,
    )
    log.info('Project %s completion rejected: %s', project_id, reason)
    return {'status': 'rejected', 'project_id': project_id, 'reason': reason}


# ── Lesson callables ─────────────────────────────────────────────────────────

@anvil.server.callable
def get_lesson_stats():
    """Lesson utilization summary — total, never-applied, mean times_applied, top categories."""
    r = requests.get(f'{_STATS_URL}/lesson_stats', timeout=15)
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_lessons(filter='recent', limit=25, age_threshold_days=7):
    params = {
        'select': 'id,title,category,times_applied,confidence,chromadb_id,created_at',
        'limit': str(limit),
    }
    if filter == 'most_applied':
        params['order'] = 'times_applied.desc'
    elif filter == 'never_applied':
        params['times_applied'] = 'eq.0'
        cutoff = (datetime.now(timezone.utc) - timedelta(days=age_threshold_days)).isoformat()
        params['created_at'] = f'lt.{cutoff}'
        params['order'] = 'created_at.desc'
    elif filter == 'broken':
        params['chromadb_id'] = 'is.null'
        params['order'] = 'created_at.desc'
    else:  # recent (default)
        params['order'] = 'created_at.desc'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def search_lessons(query):
    collection_id = _get_chromadb_collection_id('lessons_learned')
    r = requests.post(
        f'{_CHROMADB_URL}/api/v1/collections/{collection_id}/query',
        json={'query_texts': [query], 'n_results': 20, 'include': ['documents', 'metadatas', 'distances']},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get('ids') or not data['ids'][0]:
        return []
    chromadb_ids = data['ids'][0]
    distances = dict(zip(chromadb_ids, data['distances'][0]))
    ids_csv = ','.join(f'"{cid}"' for cid in chromadb_ids)
    r2 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers=_HEADERS,
        params={
            'select': 'id,title,category,times_applied,confidence,chromadb_id,created_at',
            'chromadb_id': f'in.({ids_csv})',
        },
        timeout=10,
    )
    r2.raise_for_status()
    rows = {row['chromadb_id']: row for row in r2.json()}
    results = []
    for cid in chromadb_ids:
        row = dict(rows.get(cid, {
            'chromadb_id': cid, 'id': None, 'title': '(not in Supabase)',
            'category': None, 'times_applied': None, 'confidence': None, 'created_at': None,
        }))
        row['distance'] = distances.get(cid)
        results.append(row)
    return results


@anvil.server.callable
def update_lesson(lesson_id, delta):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers=_HEADERS,
        params={'select': 'confidence', 'id': f'eq.{lesson_id}'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Lesson {lesson_id} not found.')
    current = float(rows[0].get('confidence') or 0.5)
    new_conf = round(max(0.0, min(1.0, current + float(delta))), 4)
    now = datetime.now(timezone.utc).isoformat()
    r2 = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{lesson_id}'},
        json={'confidence': new_conf, 'updated_at': now},
        timeout=10,
    )
    r2.raise_for_status()
    log.info('Lesson %s confidence: %.4f → %.4f', lesson_id, current, new_conf)
    return {'confidence': new_conf}


@anvil.server.callable
def delete_lesson(lesson_id, chromadb_id=None):
    r = requests.delete(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{lesson_id}'},
        timeout=10,
    )
    r.raise_for_status()
    if chromadb_id:
        try:
            coll_id = _get_chromadb_collection_id('lessons_learned')
            rd = requests.post(
                f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/delete',
                json={'ids': [chromadb_id]},
                timeout=10,
            )
            rd.raise_for_status()
        except Exception as e:
            log.warning('ChromaDB delete failed for %s: %s', chromadb_id, e)
    log.info('Lesson deleted: %s (chromadb_id=%s)', lesson_id, chromadb_id)
    return {'deleted': True}


# ── Session callables ────────────────────────────────────────────────────────

@anvil.server.callable
def get_session_status():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/session_status',
        headers=_HEADERS,
        params={'order': 'updated_at.desc', 'limit': '1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


@anvil.server.callable
def get_session_artifacts(limit=10):
    sessions_dir = os.path.join(_CLAUDIS_DIR, 'sessions', 'lean')
    if not os.path.isdir(sessions_dir):
        return []
    files = sorted(
        [f for f in os.listdir(sessions_dir) if f.endswith('.md')],
        reverse=True,
    )[:limit]
    results = []
    for fname in files:
        path = os.path.join(sessions_dir, fname)
        try:
            with open(path) as f:
                content = f.read()
            title = fname
            for line in content.splitlines():
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            date = fname[:10] if len(fname) >= 10 else ''
            results.append({'filename': fname, 'title': title, 'date': date, 'content': content})
        except Exception:
            pass
    return results


# ── Boot briefing callables ───────────────────────────────────────────────────

@anvil.server.callable
def post_boot_briefing(content, directive_seen=None):
    payload = {'content': content}
    if directive_seen:
        payload['directive_seen'] = directive_seen
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/boot_briefings',
        headers={**_HEADERS, 'Prefer': 'return=representation'},
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    row = r.json()[0]
    log.info('Boot briefing posted: %s', row.get('id'))
    return {'id': row.get('id')}


@anvil.server.callable
def get_boot_briefings(limit=10):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/boot_briefings',
        headers=_HEADERS,
        params={'order': 'created_at.desc', 'limit': str(limit)},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def acknowledge_boot_briefing(briefing_id):
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/boot_briefings',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{briefing_id}'},
        json={'acknowledged': True},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Boot briefing %s acknowledged', briefing_id)
    return {'acknowledged': True}


# ── Memory callables ─────────────────────────────────────────────────────────

@anvil.server.callable
def get_collection_stats():
    r = requests.get(f'{_CHROMADB_URL}/api/v1/collections', timeout=5)
    r.raise_for_status()
    collections = r.json()
    result = []
    for coll in collections:
        rc = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{coll["id"]}/count', timeout=5)
        count = rc.json() if rc.ok else 0
        result.append({'name': coll['name'], 'id': coll['id'], 'count': count})
    result.sort(key=lambda x: x['name'])
    return result


@anvil.server.callable
def browse_collection(name, limit=15, offset=0):
    coll_id = _get_chromadb_collection_id(name)
    rc = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/count', timeout=5)
    rc.raise_for_status()
    total = rc.json()
    r = requests.post(
        f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/get',
        json={'limit': limit, 'offset': offset, 'include': ['documents', 'metadatas']},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    ids = data.get('ids') or []
    documents = data.get('documents') or []
    metadatas = data.get('metadatas') or []
    docs = [
        {
            'id': ids[i],
            'document': (documents[i] if i < len(documents) else '')[:600],
            'metadata': metadatas[i] if i < len(metadatas) else {},
        }
        for i in range(len(ids))
    ]
    return {'total': total, 'offset': offset, 'limit': limit, 'docs': docs}


@anvil.server.callable
def search_collection(name, query, n_results=15):
    coll_id = _get_chromadb_collection_id(name)
    r = requests.post(
        f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/query',
        json={
            'query_texts': [query],
            'n_results': n_results,
            'include': ['documents', 'metadatas', 'distances'],
        },
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if not data.get('ids') or not data['ids'][0]:
        return []
    ids = data['ids'][0]
    documents = (data.get('documents') or [[]])[0]
    metadatas = (data.get('metadatas') or [[]])[0]
    distances = (data.get('distances') or [[]])[0]
    return [
        {
            'id': ids[i],
            'document': (documents[i] if i < len(documents) else '')[:600],
            'metadata': metadatas[i] if i < len(metadatas) else {},
            'distance': distances[i] if i < len(distances) else None,
        }
        for i in range(len(ids))
    ]


@anvil.server.callable
def delete_document(collection, doc_id):
    coll_id = _get_chromadb_collection_id(collection)
    r = requests.post(
        f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/delete',
        json={'ids': [doc_id]},
        timeout=10,
    )
    r.raise_for_status()
    if collection == 'lessons_learned':
        try:
            rd = requests.delete(
                f'{_SUPABASE_URL}/rest/v1/lessons_learned',
                headers={**_HEADERS, 'Prefer': 'return=minimal'},
                params={'chromadb_id': f'eq.{doc_id}'},
                timeout=10,
            )
            rd.raise_for_status()
        except Exception as e:
            log.warning('Supabase delete for chromadb_id %s failed: %s', doc_id, e)
    log.info('Deleted document %s from %s', doc_id, collection)
    return {'deleted': True}


@anvil.server.callable
def get_table_rows(table, limit=25):
    _curated = {
        'research_papers': {
            'select': 'id,title,relevance_score,status,discovered_at',
            'order': 'discovered_at.desc',
        },
        'error_logs': {
            'select': 'id,workflow_name,error_message,timestamp',
            'resolved': 'eq.false',
            'order': 'timestamp.desc',
        },
    }
    if table not in _curated:
        raise Exception(f'Table "{table}" is not in curated views.')
    params = dict(_curated[table])
    params['limit'] = str(limit)
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/{table}',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def resolve_error_log(error_id, notes=None):
    now = datetime.now(timezone.utc).isoformat()
    payload = {'resolved': True, 'resolved_by': 'bill', 'resolved_at': now}
    if notes:
        payload['resolution_notes'] = notes.strip()[:500]
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/error_logs',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{error_id}'},
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    log.info('Error log %s resolved', error_id)
    return {'resolved': True}


# ── Site callables ───────────────────────────────────────────────────────────

_SITE_DIR = os.path.expanduser('~/aadp/thompsmanlearn.github.io')
_CLAUDIS_SESSIONS_DIR = os.path.join(_CLAUDIS_DIR, 'sessions', 'lean')


@anvil.server.callable
def get_site_status():
    """Return compact project state for status.json and desktop session fetch."""
    sessions = []
    try:
        files = sorted(
            [f for f in os.listdir(_CLAUDIS_SESSIONS_DIR) if f.endswith('.md')],
            reverse=True,
        )[:3]
        for fname in files:
            path = os.path.join(_CLAUDIS_SESSIONS_DIR, fname)
            with open(path) as f:
                content = f.read()
            title = fname
            outcome = ''
            for line in content.splitlines():
                if line.startswith('# '):
                    title = line[2:].strip()
                for section in ('## What Changed', '## Summary'):
                    if line.startswith(section):
                        pass
            # Extract first bullet from What Changed as outcome
            in_changed = False
            for line in content.splitlines():
                if line.startswith('## What Changed'):
                    in_changed = True
                    continue
                if in_changed and line.startswith('##'):
                    break
                if in_changed and line.strip().startswith('-'):
                    outcome = line.strip().lstrip('- ').strip()[:120]
                    break
            sessions.append({
                'date': fname[:10],
                'descriptor': fname[11:-3] if len(fname) > 14 else fname,
                'outcome': outcome,
            })
    except Exception:
        pass

    directive = ''
    try:
        with open(os.path.join(_CLAUDIS_DIR, 'DIRECTIVES.md')) as f:
            directive = f.read().strip()
    except Exception:
        pass

    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/agent_registry',
            headers=_HEADERS,
            params={'select': 'agent_name', 'status': 'eq.active'},
            timeout=5,
        )
        agent_count = len(r.json()) if r.ok else 0
    except Exception:
        agent_count = 0

    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'system': 'online',
        'mode': 'lean',
        'agent_count': agent_count,
        'last_sessions': sessions,
        'current_directive': directive,
    }


@anvil.server.callable
def update_site():
    """Regenerate status.json from live data and push to GitHub Pages repo."""
    if not os.path.isdir(_SITE_DIR):
        raise Exception(f'Site directory not found: {_SITE_DIR}')

    status = get_site_status()

    import json as _json
    status_path = os.path.join(_SITE_DIR, 'status.json')
    with open(status_path, 'w') as f:
        _json.dump(status, f, indent=2, default=str)

    cmds = [
        ['git', '-C', _SITE_DIR, 'add', 'status.json'],
        ['git', '-C', _SITE_DIR, 'commit', '-m', f'site update: {status["generated_at"][:10]}'],
        ['git', '-C', _SITE_DIR, 'push', 'origin', 'main'],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0 and 'nothing to commit' not in result.stdout:
            raise Exception(f'{cmd[2]} failed: {result.stderr.strip()}')

    log.info('Site updated and pushed')
    return {'updated': True, 'generated_at': status['generated_at']}


# ── Artifacts callables ──────────────────────────────────────────────────────

@anvil.server.callable
def get_artifacts(agent_name=None, artifact_type=None, limit=30):
    params = {
        'select': 'id,agent_name,artifact_type,summary,confidence,reviewed_by_bill,bill_rating,created_at',
        'order': 'created_at.desc',
        'limit': str(limit),
    }
    if agent_name:
        params['agent_name'] = f'eq.{agent_name}'
    if artifact_type:
        params['artifact_type'] = f'eq.{artifact_type}'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_artifacts',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_artifact(artifact_id):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_artifacts',
        headers=_HEADERS,
        params={'select': '*', 'id': f'eq.{artifact_id}'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Artifact {artifact_id} not found.')
    return rows[0]


@anvil.server.callable
def rate_artifact(artifact_id, rating, comment=None):
    if rating not in (1, -1):
        raise Exception('Rating must be 1 or -1.')
    payload = {'reviewed_by_bill': True, 'bill_rating': rating}
    if comment:
        payload['bill_comment'] = comment.strip()[:500]
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/agent_artifacts',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{artifact_id}'},
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    log.info('Artifact %s rated %d', artifact_id, rating)
    return {'rated': True}


@anvil.server.callable
def get_artifact_agents():
    """Return distinct agent names and artifact types for filter UI."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_artifacts',
        headers=_HEADERS,
        params={'select': 'agent_name,artifact_type', 'order': 'agent_name.asc'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    agents = sorted({row['agent_name'] for row in rows if row.get('agent_name')})
    types = sorted({row['artifact_type'] for row in rows if row.get('artifact_type')})
    return {'agents': agents, 'types': types}


# ── Research callables ───────────────────────────────────────────────────────

@anvil.server.callable
def get_research_articles(limit=50):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers=_HEADERS,
        params={
            'select': 'id,agent_run_id,title,url,source,query_used,summary,retrieved_at,rating,comment,status',
            'order': 'retrieved_at.desc',
            'limit': str(limit),
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def rate_research_article(article_id, rating):
    if rating not in (1, -1, 0):
        raise Exception('Rating must be 1, -1, or 0.')
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'return=representation'},
        params={'id': f'eq.{article_id}'},
        json={'rating': rating},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    log.info('Article %s rated %d', article_id, rating)
    return rows[0] if rows else {'rating': rating}


@anvil.server.callable
def comment_research_article(article_id, comment):
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{article_id}'},
        json={'comment': (comment or '').strip()[:500]},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Article %s comment saved', article_id)
    return {'saved': True}


@anvil.server.callable
def set_research_article_status(article_id, status):
    if status not in ('new', 'reviewed', 'archived'):
        raise Exception(f'Invalid status "{status}". Must be new, reviewed, or archived.')
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{article_id}'},
        json={'status': status},
        timeout=10,
    )
    r.raise_for_status()
    log.info('Article %s status → %s', article_id, status)
    return {'status': status}


@anvil.server.callable
def submit_agent_feedback_v2(target_type, target_id, content):
    content = (content or '').strip()
    if not content:
        raise Exception('Feedback content cannot be empty.')
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        json={'target_type': target_type, 'target_id': target_id, 'content': content[:2000]},
        timeout=10,
    )
    r.raise_for_status()
    log.info('agent_feedback_v2: target_type=%s target_id=%s', target_type, target_id)
    return {'submitted': True}


@anvil.server.callable
def get_feedback_threads():
    """Return pending and recently resolved feedback for thread display in the Research tab."""
    r1 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'id,target_type,target_id,content,created_at,action_summary,action_session,action_result_url',
            'or': '(processed.is.null,processed.eq.false)',
            'order': 'created_at.asc',
        },
        timeout=10,
    )
    r1.raise_for_status()
    pending = r1.json()

    r2 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'id,target_type,target_id,content,created_at,action_summary,action_session,action_result_url,processed_at',
            'processed': 'eq.true',
            'order': 'processed_at.desc',
            'limit': '10',
        },
        timeout=10,
    )
    r2.raise_for_status()
    resolved = r2.json()

    log.info('get_feedback_threads: pending=%d resolved=%d', len(pending), len(resolved))
    return {'pending': pending, 'resolved': resolved}


@anvil.server.callable
def get_research_counters():
    """Return total articles, unreviewed count, and articles added in last 24h."""
    # Total
    r_total = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id'},
        timeout=10,
    )
    r_total.raise_for_status()
    total = int(r_total.headers.get('Content-Range', '*/0').split('/')[-1])

    # Unreviewed (status = 'new')
    r_new = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'status': 'eq.new'},
        timeout=10,
    )
    r_new.raise_for_status()
    unreviewed = int(r_new.headers.get('Content-Range', '*/0').split('/')[-1])

    # New in last 24h
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    r_recent = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'count=exact'},
        params={'select': 'id', 'retrieved_at': f'gte.{cutoff}'},
        timeout=10,
    )
    r_recent.raise_for_status()
    last_24h = int(r_recent.headers.get('Content-Range', '*/0').split('/')[-1])

    return {'total': total, 'unreviewed': unreviewed, 'last_24h': last_24h}


@anvil.server.callable
def get_research_run_summary():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers=_HEADERS,
        params={'select': 'agent_run_id,retrieved_at', 'order': 'retrieved_at.desc', 'limit': '1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return {'agent_run_id': None, 'count': 0, 'retrieved_at': None}
    latest_run_id = rows[0]['agent_run_id']
    latest_ts = rows[0]['retrieved_at']
    r2 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers={**_HEADERS, 'Prefer': 'count=exact'},
        params={'agent_run_id': f'eq.{latest_run_id}', 'select': 'id'},
        timeout=10,
    )
    r2.raise_for_status()
    content_range = r2.headers.get('Content-Range', '*/0')
    count = int(content_range.split('/')[-1]) if '/' in content_range else 0
    return {'agent_run_id': latest_run_id, 'count': count, 'retrieved_at': latest_ts}


@anvil.server.callable
def get_research_bundle(agent_run_id=None):
    """Return markdown bundle of a research run — ready to paste into a desktop session."""
    if agent_run_id is None:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/research_articles',
            headers=_HEADERS,
            params={'select': 'agent_run_id', 'order': 'retrieved_at.desc', 'limit': '1'},
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return '# Research Bundle\n\nNo articles found.\n'
        agent_run_id = rows[0]['agent_run_id']

    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_articles',
        headers=_HEADERS,
        params={
            'select': 'title,url,source,query_used,summary,retrieved_at,rating,comment',
            'agent_run_id': f'eq.{agent_run_id}',
            'order': 'retrieved_at.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    articles = r.json()

    if not articles:
        return f'# Research Bundle\n\nNo articles found for run `{agent_run_id}`.\n'

    run_timestamp = (articles[0].get('retrieved_at') or '')[:19].replace('T', ' ') + ' UTC'
    article_count = len(articles)
    query_set = sorted({a['query_used'] for a in articles if a.get('query_used')})

    lines = [
        '---',
        f'run_id: {agent_run_id}',
        f'run_timestamp: {run_timestamp}',
        f'article_count: {article_count}',
        'query_set:',
    ]
    for q in query_set:
        lines.append(f'  - {q}')
    lines += ['---', '']

    for article in articles:
        title = article.get('title') or '(no title)'
        source = article.get('source') or ''
        url = article.get('url') or ''
        query_used = article.get('query_used') or ''
        summary = article.get('summary') or ''
        rating = article.get('rating') or 0
        comment = (article.get('comment') or '').strip()

        lines.append(f'## {title}')
        if source:
            lines.append(f'**Source:** {source}')
        if url:
            lines.append(f'**URL:** {url}')
        if query_used:
            lines.append(f'**Query:** {query_used}')
        lines.append('')
        if summary:
            lines.append(summary)
            lines.append('')
        if rating == 1:
            lines.append('**Rating:** 👍')
        elif rating == -1:
            lines.append('**Rating:** 👎')
        if comment:
            lines.append(f'**Comment:** {comment}')
        lines.append('')

    # Pending feedback (target_type in agent/anvil_view, not yet processed)
    r2 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'target_type,target_id,content,created_at,action_summary,action_session,action_result_url',
            'target_type': 'in.(agent,anvil_view)',
            'or': '(processed.is.null,processed.eq.false)',
            'order': 'created_at.asc',
        },
        timeout=10,
    )
    r2.raise_for_status()
    pending = r2.json()

    if pending:
        lines += ['## Pending Feedback', '']
        for fb in pending:
            fb_type = fb.get('target_type') or ''
            fb_target = fb.get('target_id') or ''
            fb_content = fb.get('content') or ''
            fb_summary = fb.get('action_summary')
            fb_session = fb.get('action_session')
            fb_url = fb.get('action_result_url')
            lines.append(f'- [{fb_type}: {fb_target}] {fb_content}')
            if fb_summary is not None:
                icon = '⏸' if fb_summary.startswith('Deferred:') else '✅'
                lines.append(f'  {icon} {fb_summary}')
                if fb_session:
                    lines.append(f'  Session: {fb_session}')
                if fb_url:
                    lines.append(f'  Result: {fb_url}')
        lines.append('')

    # Recently resolved feedback (last 10 processed items)
    r3 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'target_type,target_id,content,action_summary,action_session,action_result_url,processed_at',
            'processed': 'eq.true',
            'order': 'processed_at.desc',
            'limit': '10',
        },
        timeout=10,
    )
    r3.raise_for_status()
    resolved = r3.json()

    if resolved:
        lines += ['## Recently Resolved Feedback', '']
        for fb in resolved:
            fb_type = fb.get('target_type') or ''
            fb_target = fb.get('target_id') or ''
            fb_content = fb.get('content') or ''
            fb_summary = fb.get('action_summary')
            fb_session = fb.get('action_session')
            fb_url = fb.get('action_result_url')
            lines.append(f'- [{fb_type}: {fb_target}] {fb_content}')
            if fb_summary is not None:
                icon = '⏸' if fb_summary.startswith('Deferred:') else '✅'
                lines.append(f'  {icon} {fb_summary}')
                if fb_session:
                    lines.append(f'  Session: {fb_session}')
                if fb_url:
                    lines.append(f'  Result: {fb_url}')
        lines.append('')

    log.info('get_research_bundle: run_id=%s articles=%d pending_feedback=%d resolved_feedback=%d',
             agent_run_id, article_count, len(pending), len(resolved))
    return '\n'.join(lines)


@anvil.server.callable
def run_research_synthesis():
    r = requests.post(f'{_STATS_URL}/run_paper_synthesis', timeout=55)
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_latest_briefing():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/research_briefings',
        headers=_HEADERS,
        params={'order': 'created_at.desc', 'limit': '1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


# ── Export bundle callables ─────────────────────────────────────────────────

def _bundle_header(bundle_type, view_filter, row_count):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return [
        '---',
        f'bundle_type: {bundle_type}',
        f'generated_at: {now}',
        f'view_filter: {view_filter}',
        f'row_count: {row_count}',
        '---',
        '',
    ]


def _bundle_resolved_feedback(target_type, target_ids=None):
    params = {
        'select': 'target_type,target_id,content,action_summary,action_session,action_result_url,processed_at',
        'processed': 'eq.true',
        'target_type': f'eq.{target_type}',
        'order': 'processed_at.desc',
        'limit': '10',
    }
    if target_ids:
        ids_csv = ','.join(f'"{t}"' for t in target_ids)
        params['target_id'] = f'in.({ids_csv})'
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/agent_feedback',
            headers=_HEADERS,
            params=params,
            timeout=10,
        )
        r.raise_for_status()
        rows = r.json()
    except Exception:
        return []
    if not rows:
        return []
    lines = ['## Recently Resolved Feedback', '']
    for fb in rows:
        fb_target = fb.get('target_id') or ''
        fb_content = fb.get('content') or ''
        fb_summary = fb.get('action_summary')
        fb_session = fb.get('action_session')
        fb_url = fb.get('action_result_url')
        lines.append(f'- [{fb_target}] {fb_content}')
        if fb_summary is not None:
            icon = '⏸' if fb_summary.startswith('Deferred:') else '✅'
            lines.append(f'  {icon} {fb_summary}')
            if fb_session:
                lines.append(f'  Session: {fb_session}')
            if fb_url:
                lines.append(f'  Result: {fb_url}')
    lines.append('')
    return lines


@anvil.server.callable
def get_lessons_bundle(filter='recent', limit=50, age_threshold_days=7):
    """Return markdown bundle of lessons_learned — ready to paste into a desktop session."""
    params = {
        'select': 'id,title,category,content,confidence,times_applied,created_at,chromadb_id',
        'limit': str(limit),
    }
    if filter == 'most_applied':
        params['order'] = 'times_applied.desc'
    elif filter == 'never_applied':
        params['times_applied'] = 'eq.0'
        cutoff = (datetime.now(timezone.utc) - timedelta(days=age_threshold_days)).isoformat()
        params['created_at'] = f'lt.{cutoff}'
        params['order'] = 'created_at.desc'
    elif filter == 'broken':
        params['chromadb_id'] = 'is.null'
        params['order'] = 'created_at.desc'
    else:
        params['order'] = 'created_at.desc'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/lessons_learned',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    lessons = r.json()

    now_dt = datetime.now(timezone.utc)
    lines = _bundle_header('lessons', filter, len(lessons))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(lessons)} lesson(s) from the lessons_learned store, '
        f'filtered by: {filter}. Use these to identify lessons that are stale, duplicated, '
        'poorly worded, or never relevant. "Never Applied" lessons may not be reaching '
        'retrieval — check category/title clarity. "Broken" lessons are missing from '
        'ChromaDB and will not be retrieved semantically.',
        '',
        '## Lessons',
        '',
    ]
    for lesson in lessons:
        title = lesson.get('title') or '(no title)'
        lid = lesson.get('id') or ''
        category = lesson.get('category') or ''
        content = lesson.get('content') or ''
        confidence = lesson.get('confidence')
        times_applied = lesson.get('times_applied') or 0
        created_at = (lesson.get('created_at') or '')[:10]
        chromadb_id = lesson.get('chromadb_id')
        in_chromadb = 'yes' if chromadb_id else 'no'
        age_days = '?'
        if created_at:
            try:
                age_days = (now_dt.date() - datetime.strptime(created_at, '%Y-%m-%d').date()).days
            except Exception:
                pass
        if len(content) > 500:
            content = content[:500] + ' [truncated]'
        lines.append(f'### {title}')
        lines.append(
            f'**id:** {lid} | **category:** {category} | **confidence:** {confidence} | '
            f'**times_applied:** {times_applied} | **age_days:** {age_days} | **chromadb:** {in_chromadb}'
        )
        lines.append('')
        lines.append(content)
        lines.append('')

    lines += _bundle_resolved_feedback('anvil_view', ['lessons_tab'])
    log.info('get_lessons_bundle: filter=%s count=%d', filter, len(lessons))
    return '\n'.join(lines)


@anvil.server.callable
def get_memory_bundle(collection=None, limit=100):
    """Return markdown bundle of ChromaDB memory state — ready to paste into a desktop session."""
    if collection is None:
        try:
            r = requests.get(f'{_CHROMADB_URL}/api/v1/collections', timeout=10)
            r.raise_for_status()
            colls = r.json()
        except Exception as e:
            return f'# Memory Bundle\n\nFailed to fetch collections: {e}\n'

        lines = _bundle_header('memory', 'all_collections', len(colls))
        lines += [
            '## Summary',
            '',
            f'This bundle contains stats for {len(colls)} ChromaDB collection(s). '
            'Use this to assess collection health, detect unexpected growth or shrinkage, '
            'and identify collections that may have stale or misclassified content.',
            '',
            '## Collections',
            '',
        ]
        for coll in colls:
            name = coll.get('name') or ''
            coll_id = coll.get('id') or ''
            doc_count = '?'
            try:
                r2 = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/count', timeout=5)
                if r2.ok:
                    doc_count = r2.json()
            except Exception:
                pass
            samples = []
            try:
                r3 = requests.post(
                    f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/get',
                    json={'limit': 3, 'include': ['documents']},
                    timeout=5,
                )
                if r3.ok:
                    docs = r3.json().get('documents') or []
                    for d in docs[:3]:
                        excerpt = (d or '')[:100].replace('\n', ' ')
                        samples.append(excerpt)
            except Exception:
                pass
            lines.append(f'**{name}** — {doc_count} documents')
            for s in samples:
                lines.append(f'  - {s}')
            lines.append('')
    else:
        try:
            coll_id = _get_chromadb_collection_id(collection)
            r = requests.post(
                f'{_CHROMADB_URL}/api/v1/collections/{coll_id}/get',
                json={'limit': limit, 'include': ['documents', 'metadatas']},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            return f'# Memory Bundle\n\nFailed to fetch {collection}: {e}\n'

        ids = data.get('ids') or []
        docs = data.get('documents') or []
        metas = data.get('metadatas') or []

        lines = _bundle_header('memory', f'collection:{collection}', len(ids))
        lines += [
            '## Summary',
            '',
            f'This bundle contains up to {limit} documents from ChromaDB collection "{collection}". '
            'Use this to assess retrieval quality, identify stale or poorly-labelled content, '
            'and spot duplicates.',
            '',
            f'## Documents ({len(ids)})',
            '',
        ]
        for i, doc_id in enumerate(ids):
            doc = (docs[i] if i < len(docs) else '') or ''
            meta = (metas[i] if i < len(metas) else {}) or {}
            excerpt = doc[:600].replace('\n', ' ')
            if len(doc) > 600:
                excerpt += ' [truncated]'
            lines.append(f'**[{doc_id}]**')
            if meta:
                meta_str = ', '.join(f'{k}={v}' for k, v in list(meta.items())[:4])
                lines.append(f'meta: {meta_str}')
            lines.append(excerpt)
            lines.append('')

    lines += _bundle_resolved_feedback('anvil_view', ['memory_tab'])
    log.info('get_memory_bundle: collection=%s', collection)
    return '\n'.join(lines)


@anvil.server.callable
def get_sessions_bundle(limit=10):
    """Return markdown bundle of recent session artifacts — ready to paste into a desktop session."""
    root = os.path.join(_CLAUDIS_DIR, 'sessions')
    if not os.path.isdir(root):
        return '# Sessions Bundle\n\nNo sessions directory found.\n'
    # Collect from sessions/ root and sessions/lean/ subdirectory
    all_files = []
    for dirpath, _dirs, fnames in os.walk(root):
        for f in fnames:
            if f.endswith('.md') and not f.startswith('B-'):
                all_files.append(os.path.join(dirpath, f))
    all_files.sort(key=lambda p: os.path.basename(p), reverse=True)
    all_files = all_files[:limit]
    if not all_files:
        return '# Sessions Bundle\n\nNo session files found.\n'

    sessions = []
    for path in all_files:
        fname = os.path.basename(path)
        try:
            with open(path) as f:
                raw_lines = f.read().splitlines()
        except Exception:
            continue
        title = fname
        date = fname[:10] if len(fname) >= 10 else ''
        card = ''
        tasks = []
        capability = []
        current_section = None
        for line in raw_lines:
            stripped = line.strip()
            stripped_lower = stripped.lower()
            if line.startswith('# '):
                title = line[2:].strip()
            elif line.startswith('**Card:**'):
                card = line.replace('**Card:**', '').strip()
            elif stripped_lower in ('## tasks completed', '## tasks'):
                current_section = 'tasks'
            elif stripped_lower == '## capability delta':
                current_section = 'capability'
            elif stripped.startswith('## '):
                current_section = None
            elif current_section == 'tasks' and line.startswith('- ') and len(tasks) < 3:
                tasks.append(line[2:].strip()[:150])
            elif current_section == 'capability' and len(capability) < 4:
                for prefix in ('Before:', 'After:', 'Reader of this change:', 'Reader:'):
                    if stripped.startswith(prefix):
                        capability.append(stripped[:200])
                        break
        sessions.append({'filename': fname, 'date': date, 'title': title,
                         'card': card, 'tasks': tasks, 'capability': capability})

    lines = _bundle_header('sessions', f'recent_{limit}', len(sessions))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(sessions)} recent session artifact(s). '
        'Use these to identify sessions that ran well, sessions that got stuck, '
        'and recurring patterns (repeated failures, scope creep, lessons not applied).',
        '',
    ]
    for s in sessions:
        lines.append(f'## {s["date"]} — {s["title"]}')
        if s['card']:
            lines.append(f'**Card:** {s["card"]}')
        lines.append('')
        if s['tasks']:
            lines.append('**What changed:**')
            for t in s['tasks']:
                lines.append(f'- {t}')
            lines.append('')
        if s['capability']:
            lines.append('**Capability delta:**')
            for c in s['capability']:
                lines.append(f'- {c}')
            lines.append('')

    lines += _bundle_resolved_feedback('anvil_view', ['sessions_tab'])
    log.info('get_sessions_bundle: count=%d', len(sessions))
    return '\n'.join(lines)


@anvil.server.callable
def get_fleet_bundle():
    """Return markdown bundle of agent fleet state — ready to paste into a desktop session."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_registry',
        headers=_HEADERS,
        params={
            'select': 'agent_name,display_name,description,status,schedule,updated_at',
            'order': 'status.asc,agent_name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    agents = r.json()

    r2 = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'target_id,content,action_summary,created_at',
            'target_type': 'eq.agent',
            'order': 'created_at.desc',
            'limit': '50',
        },
        timeout=10,
    )
    r2.raise_for_status()
    fb_by_agent = {}
    for fb in r2.json():
        agent_n = fb.get('target_id') or ''
        fb_by_agent.setdefault(agent_n, [])
        if len(fb_by_agent[agent_n]) < 3:
            fb_by_agent[agent_n].append(fb)

    by_status = {}
    for agent in agents:
        st = agent.get('status') or 'unknown'
        by_status.setdefault(st, []).append(agent)

    lines = _bundle_header('fleet', 'all', len(agents))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(agents)} agent(s) grouped by status. '
        'Use this for fleet health review: identify dead-weight agents (low activity, no purpose), '
        'agents with repeated unactioned feedback, and candidates for retirement.',
        '',
    ]
    status_order = ['active', 'paused', 'building', 'sandbox', 'broken', 'retired']
    for st in status_order + [s for s in by_status if s not in status_order]:
        if st not in by_status:
            continue
        group = by_status[st]
        lines.append(f'## {st.title()} ({len(group)})')
        lines.append('')
        for agent in group:
            name = agent.get('agent_name') or ''
            desc = (agent.get('description') or '').strip()[:200]
            schedule = agent.get('schedule') or 'unscheduled'
            updated = (agent.get('updated_at') or '')[:10]
            lines.append(f'**{name}**')
            lines.append(f'Schedule: {schedule} | Last updated: {updated}')
            if desc:
                lines.append(desc)
            fbs = fb_by_agent.get(name, [])
            if fbs:
                lines.append('Recent feedback:')
                for fb in fbs:
                    content = (fb.get('content') or '')[:120]
                    summary = fb.get('action_summary')
                    date = (fb.get('created_at') or '')[:10]
                    lines.append(f'  - [{date}] {content}')
                    if summary:
                        icon = '⏸' if summary.startswith('Deferred:') else '✅'
                        lines.append(f'    {icon} {summary}')
            lines.append('')

    log.info('get_fleet_bundle: agents=%d', len(agents))
    return '\n'.join(lines)


@anvil.server.callable
def get_errors_bundle():
    """Return markdown bundle of unresolved error logs — ready to paste into a desktop session."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/error_logs',
        headers=_HEADERS,
        params={
            'select': 'id,workflow_name,workflow_id,node_name,error_type,error_message,timestamp',
            'resolved': 'eq.false',
            'order': 'timestamp.desc',
        },
        timeout=10,
    )
    r.raise_for_status()
    errors = r.json()

    now_dt = datetime.now(timezone.utc)
    lines = _bundle_header('errors', 'unresolved', len(errors))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(errors)} unresolved error(s). '
        'Use this for triage: identify which errors need immediate attention, '
        'which are noise/transient, and which cluster around a single workflow.',
        '',
        '## Errors',
        '',
    ]
    for err in errors:
        wf = err.get('workflow_name') or err.get('workflow_id') or '(unknown workflow)'
        node = err.get('node_name') or ''
        etype = err.get('error_type') or ''
        msg = (err.get('error_message') or '').strip()
        ts = err.get('timestamp') or ''
        age_h = '?'
        if ts:
            try:
                ts_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                age_h = round((now_dt - ts_dt).total_seconds() / 3600, 1)
            except Exception:
                pass
        lines.append(f'**{wf}**' + (f' / {node}' if node else ''))
        if etype:
            lines.append(f'Type: {etype} | Age: {age_h}h')
        lines.append(msg[:300] + ('[truncated]' if len(msg) > 300 else ''))
        lines.append('')

    log.info('get_errors_bundle: count=%d', len(errors))
    return '\n'.join(lines)


@anvil.server.callable
def get_skills_bundle():
    """Return markdown bundle of skills registry — ready to paste into a desktop session."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/skills_registry',
        headers=_HEADERS,
        params={
            'select': 'id,name,description,trigger_keywords,file_path,times_loaded,last_loaded',
            'order': 'name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    skills = r.json()

    lines = _bundle_header('skills', 'all', len(skills))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(skills)} skill(s) from the skills registry. '
        'Use this to assess skill coverage and retrieval triggering quality: '
        'are the trigger keywords specific enough? Are any skills never loaded? '
        'Are any skills obsolete given current system state?',
        '',
        '## Skills',
        '',
    ]
    for skill in skills:
        name = skill.get('name') or ''
        description = skill.get('description') or ''
        keywords = skill.get('trigger_keywords') or []
        times_loaded = skill.get('times_loaded') or 0
        last_loaded = (skill.get('last_loaded') or '')[:10] or 'never'
        file_path = skill.get('file_path') or ''
        content_excerpt = ''
        if file_path:
            path = file_path.replace('~', os.path.expanduser('~'))
            try:
                with open(path) as f:
                    raw = f.read()
                content_excerpt = raw[:500].replace('\n', ' ')
                if len(raw) > 500:
                    content_excerpt += ' [truncated]'
            except Exception:
                pass
        kw_str = ', '.join(keywords) if isinstance(keywords, list) else str(keywords)
        lines.append(f'**{name}**')
        lines.append(f'Times loaded: {times_loaded} | Last loaded: {last_loaded}')
        if description:
            lines.append(description[:200])
        if kw_str:
            lines.append(f'Triggers: {kw_str}')
        if content_excerpt:
            lines.append(f'Excerpt: {content_excerpt}')
        lines.append('')

    lines += _bundle_resolved_feedback('anvil_view', ['skills_tab'])
    log.info('get_skills_bundle: count=%d', len(skills))
    return '\n'.join(lines)


@anvil.server.callable
def get_artifacts_bundle(agent_name=None, artifact_type=None, limit=30):
    """Return markdown bundle of agent artifacts — ready to paste into a desktop session."""
    params = {
        'select': 'id,agent_name,artifact_type,summary,content,confidence,bill_rating,bill_comment,reviewed_by_bill,created_at',
        'order': 'created_at.desc',
        'limit': str(limit),
    }
    if agent_name:
        params['agent_name'] = f'eq.{agent_name}'
    if artifact_type:
        params['artifact_type'] = f'eq.{artifact_type}'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_artifacts',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    artifacts = r.json()

    filter_desc = 'all'
    if agent_name and artifact_type:
        filter_desc = f'{agent_name}/{artifact_type}'
    elif agent_name:
        filter_desc = f'agent:{agent_name}'
    elif artifact_type:
        filter_desc = f'type:{artifact_type}'

    lines = _bundle_header('artifacts', filter_desc, len(artifacts))
    lines += [
        '## Summary',
        '',
        f'This bundle contains {len(artifacts)} artifact(s). Filter: {filter_desc}. '
        'Use this for output quality review: are artifacts well-structured? '
        'Do rated artifacts reveal quality patterns? '
        'Are any artifact types consistently low-confidence?',
        '',
        '## Artifacts',
        '',
    ]
    for art in artifacts:
        agent_n = art.get('agent_name') or ''
        atype = art.get('artifact_type') or ''
        summary = (art.get('summary') or '').strip()[:200]
        content = (art.get('content') or '').strip()
        confidence = art.get('confidence')
        rating = art.get('bill_rating')
        comment = (art.get('bill_comment') or '').strip()
        reviewed = art.get('reviewed_by_bill', False)
        created_at = (art.get('created_at') or '')[:10]
        content_excerpt = content[:300]
        if len(content) > 300:
            content_excerpt += ' [truncated]'
        rating_str = '\U0001f44d' if rating == 1 else '\U0001f44e' if rating == -1 else 'unrated'
        reviewed_str = '✅ reviewed' if reviewed else 'pending'
        lines.append(f'**{agent_n}** / {atype} — {created_at}')
        lines.append(f'Confidence: {confidence} | Rating: {rating_str} | {reviewed_str}')
        if summary:
            lines.append(summary)
        if content_excerpt:
            lines.append(content_excerpt)
        if comment:
            lines.append(f'Comment: {comment}')
        lines.append('')

    lines += _bundle_resolved_feedback('anvil_view', ['artifacts_tab'])
    log.info('get_artifacts_bundle: filter=%s count=%d', filter_desc, len(artifacts))
    return '\n'.join(lines)


# ── Skills callables ─────────────────────────────────────────────────────────

@anvil.server.callable
def get_skills():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/skills_registry',
        headers=_HEADERS,
        params={
            'select': 'id,name,description,trigger_keywords,file_path,times_loaded,last_loaded',
            'order': 'name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_skill(name):
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/skills_registry',
        headers=_HEADERS,
        params={'select': 'file_path', 'name': f'eq.{name}'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Skill "{name}" not found in registry.')
    file_path = rows[0]['file_path'].replace('~', os.path.expanduser('~'))
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        raise Exception(f'Skill file not found at {file_path}')
    return {'name': name, 'file_path': file_path, 'content': content}


# ── Cycle grader (B-097) ─────────────────────────────────────────────────────

@anvil.server.callable
def get_grader_reviews_by_type(review_type='card', limit=20):
    """Return grader reviews filtered by type: 'card' or 'research_cycle'."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/grader_reviews',
        headers=_HEADERS,
        params={
            'select': 'id,card_id,target_id,review_type,verdict,rationale,criteria_results,created_at,reviewed_by_bill,bill_override',
            'review_type': f'eq.{review_type}',
            'order': 'created_at.desc',
            'limit': str(limit),
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_latest_cycle_verdict(thread_id):
    """Return the most recent grader verdict for a thread's research cycles."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/grader_reviews',
        headers=_HEADERS,
        params={
            'select': 'verdict,rationale,created_at,reviewed_by_bill,bill_override',
            'target_id': f'eq.{thread_id}',
            'review_type': 'eq.research_cycle',
            'order': 'created_at.desc',
            'limit': '1',
        },
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else {}


# ── Grader evaluation export (B-102) ─────────────────────────────────────────

@anvil.server.callable
def export_grader_review(review_id):
    """Return a structured markdown block for desktop AI analysis of a grader verdict."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/grader_reviews',
        headers=_HEADERS,
        params={
            'id': f'eq.{review_id}',
            'select': 'id,card_id,target_id,review_type,verdict,rationale,criteria_results,input_snapshot,created_at,reviewed_by_bill,bill_override',
        },
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise Exception(f'Review {review_id} not found.')
    rv = rows[0]

    # Format criteria_results
    criteria = rv.get('criteria_results') or []
    if isinstance(criteria, str):
        import json as _j
        try:
            criteria = _j.loads(criteria)
        except Exception:
            criteria = []
    criteria_lines = []
    for c in criteria:
        met = c.get('met', False)
        badge = '✅' if met else '❌'
        ev = c.get('evidence', '')
        crit_text = c.get('criterion', '')
        criteria_lines.append(f'{badge} **{crit_text}**')
        if ev:
            criteria_lines.append(f'   Evidence: {ev}')

    # Format input_snapshot
    snapshot = rv.get('input_snapshot') or {}
    if isinstance(snapshot, str):
        try:
            snapshot = _j.loads(snapshot)
        except Exception:
            snapshot = {}
    snap_lines = []
    for k, v in snapshot.items():
        snap_lines.append(f'- **{k}:** {str(v)[:300]}')

    # Build markdown
    ts = (rv.get('created_at') or '')[:19].replace('T', ' ')
    review_type = rv.get('review_type', 'card')
    target = rv.get('card_id') or rv.get('target_id') or '?'
    verdict = rv.get('verdict', '?').upper()
    verdict_icons = {'PASS': '✅', 'PAUSE': '⚠️', 'FAIL': '❌',
                     'CONTINUE': '🔄', 'COMPLETE': '✅'}
    icon = verdict_icons.get(verdict, '❓')

    # Extract commit_sha from input_snapshot if available
    snapshot = rv.get('input_snapshot') or {}
    if isinstance(snapshot, str):
        try:
            import json as _jsn
            snapshot = _jsn.loads(snapshot)
        except Exception:
            snapshot = {}
    commit_sha = snapshot.get('commit_sha', 'HEAD~3 fallback (no SHA recorded)')

    lines = [
        f'# Grader Review Export',
        f'',
        f'## Metadata',
        f'- **Review ID:** {rv["id"]}',
        f'- **Target:** {target} ({review_type})',
        f'- **Verdict:** {icon} {verdict}',
        f'- **Graded at:** {ts} UTC',
        f'- **Commit SHA used:** {commit_sha}',
        f'- **Reviewed by Bill:** {rv.get("reviewed_by_bill", False)}',
        f'',
        f'## Verdict',
        f'**{verdict}**',
        f'',
        f'## Rationale',
        rv.get('rationale') or '(none)',
        f'',
        f'## Criteria Assessment',
    ]
    lines.extend(criteria_lines or ['(no criteria recorded)'])
    lines += [
        f'',
        f'## What the Grader Saw (Input Snapshot)',
    ]
    lines.extend(snap_lines or ['(no snapshot recorded)'])
    if rv.get('bill_override'):
        lines += ['', f'## Bill Override', rv['bill_override']]

    lines += [
        f'',
        f'---',
        f'*Paste into a desktop AI session and ask:*',
        f'*"Was this verdict correct? If not, what about the input or rubric should change to fix it?"*',
    ]

    markdown = '\n'.join(lines)
    log.info('export_grader_review: id=%s verdict=%s', review_id, verdict)
    return {'review_id': review_id, 'verdict': verdict, 'markdown': markdown}


# ── Capability index (B-089) ─────────────────────────────────────────────────

@anvil.server.callable
def get_capabilities(status_filter=None, limit=200):
    """Return the capabilities registry. status_filter: 'active'|'deprecated'|'retired'|None."""
    params = {
        'select': 'id,name,category,description,confidence,status,times_used,last_used,authorization_tier',
        'order': 'category.asc,name.asc',
        'limit': str(limit),
    }
    if status_filter:
        params['status'] = f'eq.{status_filter}'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/capabilities',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    log.info('get_capabilities: returned %d rows (filter=%s)', len(rows), status_filter)
    return rows


@anvil.server.callable
def get_skills_registry():
    """Return the skills registry — all skills with applies_when, provides, status."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/skills_registry',
        headers=_HEADERS,
        params={
            'select': 'name,description,applies_when,also_triggers_when,provides,file_path,status,times_used,last_used',
            'order': 'name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    log.info('get_skills_registry: returned %d rows', len(rows))
    return rows


# ── Grader reviews (B-087) ───────────────────────────────────────────────────

@anvil.server.callable
def get_grader_reviews(limit=20, unreviewed_only=False):
    """Return recent grader reviews for dashboard display."""
    params = {
        'select': 'id,card_id,session_artifact_path,verdict,rationale,criteria_results,created_at,reviewed_by_bill,bill_override',
        'order': 'created_at.desc',
        'limit': str(limit),
    }
    if unreviewed_only:
        params['reviewed_by_bill'] = 'eq.false'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/grader_reviews',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    log.info('get_grader_reviews: returned %d rows', len(rows))
    return rows


@anvil.server.callable
def bill_override_grader_review(review_id, override_verdict, override_reason):
    """Bill overrides a grader verdict (pass a paused card or fail a passed one)."""
    if override_verdict not in ('pass', 'pause', 'fail'):
        raise Exception(f'Invalid override verdict "{override_verdict}".')
    override_note = f'Bill override → {override_verdict}: {(override_reason or "").strip()[:300]}'
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/grader_reviews',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{review_id}'},
        json={'reviewed_by_bill': True, 'bill_override': override_note},
        timeout=10,
    )
    r.raise_for_status()
    log.info('bill_override_grader_review: id=%s override=%s', review_id, override_verdict)
    return {'overridden': True, 'verdict': override_verdict}


# ── Annotation backbone (B-085) ─────────────────────────────────────────────
# agent_feedback is the unified annotation table for the whole system.
# See architecture/decisions/annotation-pattern.md for target_type vocabulary.

@anvil.server.callable
def annotate(target_type, target_id, content, source='bill'):
    """File an annotation against any target. Classifier (B-086) enriches async."""
    VALID_TYPES = {'agent', 'anvil_view', 'lesson', 'skill', 'session', 'card',
                   'capability', 'thread', 'approval_request'}
    if target_type not in VALID_TYPES:
        raise Exception(f'Invalid target_type "{target_type}". Valid: {sorted(VALID_TYPES)}')
    content = (content or '').strip()
    if not content:
        raise Exception('Annotation content cannot be empty.')
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=representation'},
        json={
            'target_type': target_type,
            'target_id': str(target_id),
            'content': content[:2000],
            'action_session': source,
        },
        timeout=10,
    )
    r.raise_for_status()
    row = r.json()[0] if r.json() else {}
    feedback_id = row.get('id', '')
    log.info('annotate: type=%s id=%s source=%s feedback_id=%s', target_type, target_id, source, feedback_id)

    # Classification — synchronous so we can read intent before card-generation decision
    classification = {}
    if feedback_id:
        try:
            cr = requests.post(
                f'{_STATS_URL}/classify_annotation',
                json={
                    'feedback_id': feedback_id,
                    'target_type': target_type,
                    'target_id': str(target_id),
                    'content': content[:2000],
                },
                timeout=30,
            )
            if cr.ok:
                classification = cr.json()
        except Exception as e:
            log.warning('classify_annotation failed (non-fatal): %s', e)

    # Card generation trigger (B-114): correction/gap + high confidence + scoped target type
    _CARD_GEN_INTENTS = {'correction', 'gap'}
    _CARD_GEN_TARGET_TYPES = {'agent', 'skill', 'capability'}
    intent = classification.get('intent_type', '')
    conf = float(classification.get('confidence', 0.0))
    if (intent in _CARD_GEN_INTENTS and conf >= 0.8
            and target_type in _CARD_GEN_TARGET_TYPES and feedback_id):
        def _fire_card_gen(fid):
            try:
                requests.post(
                    f'{_STATS_URL}/generate_card_from_comment',
                    json={'feedback_id': fid},
                    timeout=90,
                )
            except Exception as ge:
                log.warning('generate_card_from_comment failed (non-fatal): %s', ge)
        import threading as _threading
        _threading.Thread(target=_fire_card_gen, args=(feedback_id,), daemon=True).start()
        log.info('card generation triggered for feedback_id=%s intent=%s conf=%.2f', feedback_id, intent, conf)

    return {'id': feedback_id, 'created': True, 'intent': intent, 'card_gen_triggered': (
        intent in _CARD_GEN_INTENTS and conf >= 0.8 and target_type in _CARD_GEN_TARGET_TYPES
    )}


@anvil.server.callable
def get_annotations(target_type, target_id, processed=None):
    """Retrieve annotations for a target. processed=None returns all."""
    params = {
        'select': 'id,target_type,target_id,content,created_at,processed,action_summary,action_session,action_result_url',
        'target_type': f'eq.{target_type}',
        'target_id': f'eq.{target_id}',
        'order': 'created_at.asc',
    }
    if processed is True:
        params['processed'] = 'eq.true'
    elif processed is False:
        params['or'] = '(processed.is.null,processed.eq.false)'
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    log.info('get_annotations: type=%s id=%s → %d rows', target_type, target_id, len(rows))
    return rows


@anvil.server.callable
def mark_annotation_processed(feedback_id, action_summary, action_session, action_result_url=None):
    """Mark an annotation as processed with action notes."""
    payload = {
        'processed': True,
        'processed_at': datetime.now(timezone.utc).isoformat(),
        'action_summary': (action_summary or '').strip()[:500],
        'action_session': (action_session or '').strip()[:200],
    }
    if action_result_url:
        payload['action_result_url'] = action_result_url.strip()[:500]
    r = requests.patch(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers={**_HEADERS, 'Prefer': 'return=minimal'},
        params={'id': f'eq.{feedback_id}'},
        json=payload,
        timeout=10,
    )
    r.raise_for_status()
    log.info('mark_annotation_processed: id=%s session=%s', feedback_id, action_session)
    return {'processed': True}


@anvil.server.callable
def export_comment_driven_results(since_date='', agent_name=''):
    """Bundle comment-driven card results for desktop review (B-114)."""
    r = requests.post(
        f'{_STATS_URL}/export_comment_driven_results',
        json={'since_date': since_date, 'agent_name': agent_name},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


@anvil.server.callable
def get_comment_driven_activity():
    """Return {agent_name: {card_id, date}} for agents with recent comment-driven cards."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/agent_feedback',
        headers=_HEADERS,
        params={
            'select': 'target_id,metadata,created_at',
            'target_type': 'eq.agent',
            'order': 'created_at.desc',
            'limit': '200',
        },
        timeout=10,
    )
    r.raise_for_status()
    result = {}
    for row in r.json():
        meta = row.get('metadata') or {}
        if isinstance(meta, str):
            import json as _j
            try:
                meta = _j.loads(meta)
            except Exception:
                meta = {}
        card_id = meta.get('generated_card_id', '')
        if card_id and row.get('target_id') not in result:
            result[row['target_id']] = {
                'card_id': card_id,
                'date': (row.get('created_at') or '')[:10],
            }
    return result


@anvil.server.callable
def run_consumer_audit():
    """Run the consumer audit against the manifest and return findings."""
    r = requests.post(f'{_STATS_URL}/consumer_audit', json={}, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Bill's mind / working bundle (B-120) ────────────────────────────────────

@anvil.server.callable
def get_working_bundle():
    """Return markdown with Bill's unaddressed notes, flagged session artifacts, and recent activity.

    Flagged = artifacts within last 14 days where the **After:** line contains
    'failed', 'stuck', 'blocked', 'unresolved', or 'error' (case-insensitive).
    Only the After line is searched — searching full text caused false positives
    from historical references in artifact bodies.

    Artifacts with no **After:** line are excluded from both sections. They have
    no recorded outcome and add no signal to the bundle.
    """
    import glob
    import os as _os

    def _clean_summary(text, max_chars=120):
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > int(max_chars * 0.7):
            truncated = truncated[:last_space]
        return truncated.rstrip('.,;:') + '…'

    lines = []

    # Sections 1 & 2: session artifacts
    sessions_dir = _os.path.expanduser('~/aadp/claudis/sessions/lean')
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).date()
    FLAG_WORDS = ('failed', 'stuck', 'blocked', 'unresolved', 'error')
    all_artifacts = []  # (date, title, after_line, flagged)

    for path in sorted(glob.glob(f'{sessions_dir}/*.md'), reverse=True):
        name = _os.path.basename(path)
        try:
            file_date = datetime.strptime(name[:10], '%Y-%m-%d').date()
        except ValueError:
            continue
        try:
            with open(path) as f:
                text = f.read()
        except Exception:
            continue
        title = name[:-3]
        for line in text.splitlines():
            if line.startswith('# '):
                title = line[2:].strip()
                break
        after_line = ''
        for line in text.splitlines():
            if line.startswith('**After:**'):
                after_line = line.replace('**After:**', '').strip()
                break
        if not after_line:
            continue
        flagged = file_date >= cutoff and any(w in after_line.lower() for w in FLAG_WORDS)
        all_artifacts.append((file_date, title, after_line, flagged))

    lines.append('\n## What Claude Code flagged\n')
    flagged_arts = [(d, t, a) for d, t, a, f in all_artifacts if f]
    if flagged_arts:
        for d, t, a in flagged_arts:
            lines.append(f"- [{d}] {t}: {_clean_summary(a)}")
    else:
        lines.append("_Nothing flagged in the last 14 days._")

    lines.append('\n## Recent activity\n')
    for d, t, a, _ in all_artifacts[:5]:
        lines.append(f"- [{d}] {t}: {_clean_summary(a)}")

    return '\n'.join(lines)


# ── Audit bundle (B-122) ─────────────────────────────────────────────────────

@anvil.server.callable
def get_audit_bundle():
    """Return markdown system snapshot for design and review sessions.

    Sections: store sizes/activity (last 14d), agent fleet, recent sessions
    (last 14d, all, no filter), open work, delta since last_audit_at.
    Bigger than working bundle; read when doing design work or periodic review.
    """
    import glob
    import os as _os

    def _clean_summary(text, max_chars=120):
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_space = truncated.rfind(' ')
        if last_space > int(max_chars * 0.7):
            truncated = truncated[:last_space]
        return truncated.rstrip('.,;:') + '…'

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=14)
    cutoff_iso = cutoff.isoformat()
    lines = []

    # ── Store sizes and activity ─────────────────────────────────────────────
    lines.append('## Store sizes and activity (last 14 days)\n')
    lines.append('| Store | Total | +14d | Last write |')
    lines.append('|---|---|---|---|')

    # (table_name, timestamp_column)
    SUPABASE_STORES = [
        ('lessons_learned', 'created_at'),
        ('research_articles', 'retrieved_at'),
        ('threads', 'created_at'),
        ('thread_entries', 'created_at'),
        ('agent_feedback', 'created_at'),
    ]
    store_totals = {}

    for table, ts_col in SUPABASE_STORES:
        try:
            r = requests.get(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers={**_HEADERS, 'Prefer': 'count=exact'},
                params={'select': ts_col, 'order': f'{ts_col}.desc', 'limit': '1'},
                timeout=10,
            )
            r.raise_for_status()
            cr = r.headers.get('Content-Range', '*/0')
            total = int(cr.split('/')[-1]) if '/' in cr and cr.split('/')[-1].isdigit() else 0
            rows_body = r.json()
            last_write = rows_body[0][ts_col][:16].replace('T', ' ') if rows_body else 'never'
            r2 = requests.head(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers={**_HEADERS, 'Prefer': 'count=exact'},
                params={'select': '*', ts_col: f'gte.{cutoff_iso}'},
                timeout=10,
            )
            r2.raise_for_status()
            cr2 = r2.headers.get('Content-Range', '*/0')
            added = int(cr2.split('/')[-1]) if '/' in cr2 and cr2.split('/')[-1].isdigit() else 0
            store_totals[table] = total
            lines.append(f'| supabase:{table} | {total} | +{added} | {last_write} |')
        except Exception as e:
            lines.append(f'| supabase:{table} | error | — | {str(e)[:60]} |')

    CHROMADB_STORES = ['lessons_learned', 'research_findings', 'session_memory', 'reference_material']
    for col_name in CHROMADB_STORES:
        try:
            col_id = _get_chromadb_collection_id(col_name)
            r = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{col_id}/count', timeout=5)
            r.raise_for_status()
            total = r.json()
            lines.append(f'| chromadb:{col_name} | {total} | N/A | N/A |')
        except Exception as e:
            lines.append(f'| chromadb:{col_name} | error | — | {str(e)[:60]} |')

    # ── Agent fleet ──────────────────────────────────────────────────────────
    lines.append('\n## Agent fleet\n')
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/agent_registry',
            headers=_HEADERS,
            params={'select': 'agent_name,description,status,updated_at', 'order': 'agent_name'},
            timeout=10,
        )
        r.raise_for_status()
        agents = r.json()
        status_counts = {}
        for a in agents:
            s = a.get('status', 'unknown')
            status_counts[s] = status_counts.get(s, 0) + 1
        status_summary = ', '.join(f'{v} {k}' for k, v in sorted(status_counts.items()))
        lines.append(f'Total: {len(agents)} ({status_summary})\n')
        lines.append('**Active agents:**')
        for a in agents:
            if a.get('status') == 'active':
                last = (a.get('updated_at') or '')[:10]
                desc = (a.get('description') or '—')[:80]
                lines.append(f'- {a["agent_name"]} [{last}]: {desc}')
    except Exception as e:
        lines.append(f'_Error: {e}_')

    # ── Recent sessions (last 14 days, all) ──────────────────────────────────
    lines.append('\n## Recent sessions (last 14 days, all)\n')
    sessions_dir = _os.path.expanduser('~/aadp/claudis/sessions/lean')
    try:
        session_lines = []
        for path in sorted(glob.glob(f'{sessions_dir}/*.md'), reverse=True):
            name = _os.path.basename(path)
            try:
                file_date = datetime.strptime(name[:10], '%Y-%m-%d').date()
            except ValueError:
                continue
            if file_date < cutoff.date():
                continue
            try:
                with open(path) as f:
                    text = f.read()
            except Exception:
                continue
            title = name[:-3]
            for line in text.splitlines():
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            after_line = ''
            for line in text.splitlines():
                if line.startswith('**After:**'):
                    after_line = line.replace('**After:**', '').strip()
                    break
            outcome = _clean_summary(after_line) if after_line else '(no outcome recorded)'
            session_lines.append(f'- [{file_date}] {title}: {outcome}')
        lines.extend(session_lines if session_lines else ['_No session artifacts in the last 14 days._'])
    except Exception as e:
        lines.append(f'_Error reading sessions: {e}_')

    # ── Open work ────────────────────────────────────────────────────────────
    lines.append('\n## Open work\n')
    directives_path = _os.path.expanduser('~/aadp/claudis/DIRECTIVES.md')
    try:
        with open(directives_path) as f:
            directives_text = f.read().strip()
        lines.append(f'**DIRECTIVES.md:**\n```\n{directives_text}\n```\n')
    except Exception as e:
        lines.append(f'**DIRECTIVES.md:** _Error: {e}_\n')
    try:
        r = requests.head(
            f'{_SUPABASE_URL}/rest/v1/work_queue',
            headers={**_HEADERS, 'Prefer': 'count=exact'},
            params={'select': '*', 'status': 'in.(pending,claimed)'},
            timeout=10,
        )
        r.raise_for_status()
        cr = r.headers.get('Content-Range', '*/0')
        wq_count = int(cr.split('/')[-1]) if '/' in cr and cr.split('/')[-1].isdigit() else 0
        lines.append(f'work_queue pending+claimed: {wq_count}')
    except Exception as e:
        lines.append(f'work_queue: _Error: {e}_')
    # ── Delta since last audit ───────────────────────────────────────────────
    lines.append('\n## What\'s changed since last audit\n')
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/system_config',
            headers=_HEADERS,
            params={'select': 'value,updated_at', 'key': 'eq.last_audit_at'},
            timeout=10,
        )
        r.raise_for_status()
        cfg_rows = r.json()
        if not cfg_rows:
            lines.append('_No prior audit recorded._')
        else:
            last_audit_ts = cfg_rows[0]['value']
            last_audit_label = (cfg_rows[0].get('updated_at') or str(last_audit_ts))[:16].replace('T', ' ')
            lines.append(f'Last audit: {last_audit_label} UTC\n')
            grew = []
            for table, ts_col in SUPABASE_STORES:
                try:
                    r2 = requests.head(
                        f'{_SUPABASE_URL}/rest/v1/{table}',
                        headers={**_HEADERS, 'Prefer': 'count=exact'},
                        params={'select': '*', ts_col: f'gte.{last_audit_ts}'},
                        timeout=10,
                    )
                    r2.raise_for_status()
                    cr2 = r2.headers.get('Content-Range', '*/0')
                    added_since = int(cr2.split('/')[-1]) if '/' in cr2 and cr2.split('/')[-1].isdigit() else 0
                    if added_since > 0:
                        grew.append(f'- supabase:{table}: +{added_since}')
                except Exception:
                    pass
            lines.extend(grew if grew else ['_No Supabase stores grew since last audit._'])
    except Exception as e:
        lines.append(f'_Error checking last_audit_at: {e}_')

    return '\n'.join(lines)


@anvil.server.callable
def mark_audit_taken():
    """Write/update last_audit_at in system_config to now(). Call manually after exporting audit bundle."""
    now_iso = datetime.now(timezone.utc).isoformat()
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/system_config',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'key': 'last_audit_at', 'value': now_iso, 'updated_at': now_iso},
        timeout=10,
    )
    r.raise_for_status()
    return {'marked_at': now_iso}


# ── Desktop Claude export (B-131) ────────────────────────────────────────────

@anvil.server.callable
def get_desktop_bundle():
    """Return markdown export shaped for Desktop Claude as the named reader.

    Sections:
    1. Active threads with most recent summary entry expanded
    2. Up to 3 recent research artifacts (full content) from ~/aadp/research_artifacts/
    3. Up to 10 recent research articles — title, full URL, source, summary
    4. Up to 5 recent session artifacts — Capability delta expanded
    5. Known fragilities — unprocessed agent_feedback for agents/skills/capabilities
    6. Store counts (at a glance)
    """
    import glob
    import os as _os

    now_label = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    lines = [f'# Desktop Claude Export — {now_label} UTC\n']
    lines.append('_Paste into a take-stock conversation. Desktop Claude cannot load files autonomously._\n')

    # ── 1. Active threads ────────────────────────────────────────────────────
    lines.append('## Active threads\n')
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/threads',
            headers=_HEADERS,
            params={
                'select': 'id,title,state,last_activity_at,charter',
                'state': 'eq.active',
                'order': 'last_activity_at.desc',
            },
            timeout=10,
        )
        r.raise_for_status()
        threads = r.json()
        if not threads:
            lines.append('_No active threads._\n')
        else:
            for t in threads:
                title = t.get('title') or '(untitled)'
                last_act = (t.get('last_activity_at') or '')[:10]
                charter = t.get('charter') or {}
                question = charter.get('question', '') if isinstance(charter, dict) else ''
                lines.append(f'### {title} [{last_act}]')
                if question:
                    lines.append(f'**Question:** {question}')
                try:
                    re2 = requests.get(
                        f'{_SUPABASE_URL}/rest/v1/thread_entries',
                        headers=_HEADERS,
                        params={
                            'select': 'content,created_at',
                            'thread_id': f'eq.{t["id"]}',
                            'entry_type': 'eq.summary',
                            'order': 'created_at.desc',
                            'limit': '1',
                        },
                        timeout=10,
                    )
                    re2.raise_for_status()
                    entries = re2.json()
                    if entries:
                        ets = (entries[0].get('created_at') or '')[:10]
                        content = (entries[0].get('content') or '').strip()
                        lines.append(f'**Latest summary [{ets}]:** {content}')
                    else:
                        lines.append('_No summary entries yet._')
                except Exception as e2:
                    lines.append(f'_Error fetching entries: {e2}_')
                lines.append('')
    except Exception as e:
        lines.append(f'_Error fetching threads: {e}_\n')

    # ── 2. Recent Research artifacts ─────────────────────────────────────────
    lines.append('## Recent Research\n')
    research_dir = os.path.expanduser('~/aadp/research_artifacts')
    try:
        if os.path.isdir(research_dir):
            art_files = sorted(
                [f for f in os.listdir(research_dir) if f.endswith('.md')],
                key=lambda f: os.path.getmtime(os.path.join(research_dir, f)),
                reverse=True,
            )[:3]
            if art_files:
                for af in art_files:
                    try:
                        with open(os.path.join(research_dir, af)) as f:
                            lines.append(f.read())
                        lines.append('')
                    except Exception:
                        pass
            else:
                lines.append('_No research artifacts yet._\n')
        else:
            lines.append('_No research artifacts yet._\n')
    except Exception as e:
        lines.append(f'_Error reading research artifacts: {e}_\n')

    # ── 3. Recent research articles ──────────────────────────────────────────
    lines.append('## Recent research (up to 10 articles)\n')
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/research_articles',
            headers=_HEADERS,
            params={
                'select': 'title,url,source,summary,retrieved_at',
                'order': 'retrieved_at.desc',
                'limit': '10',
            },
            timeout=10,
        )
        r.raise_for_status()
        articles = r.json()
        if not articles:
            lines.append('_No research articles found._\n')
        else:
            for a in articles:
                ts = (a.get('retrieved_at') or '')[:10]
                title = a.get('title') or '(no title)'
                url = a.get('url') or ''
                source = a.get('source') or ''
                summary = (a.get('summary') or '').strip()
                lines.append(f'**[{ts}] {title}**')
                if url:
                    lines.append(f'URL: {url}')
                if source:
                    lines.append(f'Source: {source}')
                if summary:
                    lines.append(f'Summary: {summary}')
                lines.append('')
    except Exception as e:
        lines.append(f'_Error fetching research articles: {e}_\n')

    # ── 4. Recent session artifacts ──────────────────────────────────────────
    lines.append('## Recent sessions (up to 5)\n')
    sessions_dir = _os.path.expanduser('~/aadp/claudis/sessions/lean')
    try:
        count = 0
        for path in sorted(glob.glob(f'{sessions_dir}/*.md'), reverse=True):
            if count >= 5:
                break
            name = _os.path.basename(path)
            try:
                file_date = datetime.strptime(name[:10], '%Y-%m-%d').date()
            except ValueError:
                continue
            try:
                with open(path) as f:
                    text = f.read()
            except Exception:
                continue
            title = name[:-3]
            for line in text.splitlines():
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            delta_lines = []
            in_delta = False
            for line in text.splitlines():
                if re.match(r'^#+\s+Capability delta', line):
                    in_delta = True
                    continue
                if in_delta:
                    if re.match(r'^#+\s+', line):
                        break
                    delta_lines.append(line)
            delta_text = '\n'.join(delta_lines).strip()
            lines.append(f'### [{file_date}] {title}')
            if delta_text:
                lines.append(f'**Capability delta:**\n{delta_text}')
            else:
                lines.append('**Capability delta:** (no delta recorded)')
            lines.append('')
            count += 1
        if count == 0:
            lines.append('_No session artifacts found._\n')
    except Exception as e:
        lines.append(f'_Error reading sessions: {e}_\n')

    # ── 5. Known fragilities ─────────────────────────────────────────────────
    lines.append('## Known fragilities (unprocessed feedback)\n')
    try:
        r = requests.get(
            f'{_SUPABASE_URL}/rest/v1/agent_feedback',
            headers=_HEADERS,
            params={
                'select': 'target_type,target_id,content,created_at',
                'processed': 'eq.false',
                'target_type': 'in.(agent,skill,capability)',
                'order': 'created_at.desc',
                'limit': '10',
            },
            timeout=10,
        )
        r.raise_for_status()
        fragilities = r.json()
        if not fragilities:
            lines.append('_No unprocessed fragility feedback._\n')
        else:
            for fb in fragilities:
                ts = (fb.get('created_at') or '')[:10]
                target = f'{fb.get("target_type", "?")}:{fb.get("target_id", "?")}'
                content = (fb.get('content') or '').strip()
                lines.append(f'- [{ts}] **{target}**: {content}')
            lines.append('')
    except Exception as e:
        lines.append(f'_Error fetching fragilities: {e}_\n')

    # ── 6. Store counts ──────────────────────────────────────────────────────
    lines.append('## Store counts\n')
    lines.append('| Store | Total |')
    lines.append('|---|---|')
    SUPABASE_STORES = [
        ('lessons_learned', 'created_at'),
        ('research_articles', 'retrieved_at'),
        ('threads', 'created_at'),
        ('thread_entries', 'created_at'),
        ('agent_feedback', 'created_at'),
    ]
    for table, _ts_col in SUPABASE_STORES:
        try:
            r = requests.head(
                f'{_SUPABASE_URL}/rest/v1/{table}',
                headers={**_HEADERS, 'Prefer': 'count=exact'},
                params={'select': '*'},
                timeout=10,
            )
            r.raise_for_status()
            cr = r.headers.get('Content-Range', '*/0')
            total = int(cr.split('/')[-1]) if '/' in cr and cr.split('/')[-1].isdigit() else '?'
            lines.append(f'| supabase:{table} | {total} |')
        except Exception as e:
            lines.append(f'| supabase:{table} | error ({str(e)[:40]}) |')
    CHROMADB_STORES = ['lessons_learned', 'research_findings', 'session_memory', 'reference_material']
    for col_name in CHROMADB_STORES:
        try:
            col_id = _get_chromadb_collection_id(col_name)
            r = requests.get(f'{_CHROMADB_URL}/api/v1/collections/{col_id}/count', timeout=5)
            r.raise_for_status()
            lines.append(f'| chromadb:{col_name} | {r.json()} |')
        except Exception as e:
            lines.append(f'| chromadb:{col_name} | error ({str(e)[:40]}) |')

    return '\n'.join(lines)


# ── Deep Research Pipeline (B-137) ───────────────────────────────────────────

_deep_research_jobs = {}  # job_id → {status, result, error}
_RESEARCH_ARTIFACTS_DIR = os.path.expanduser('~/aadp/research_artifacts')


def _gemini_generate(prompt, timeout=90):
    """Call Gemini 2.5 Flash. Returns (text, tokens_in, tokens_out). Retries once on 503."""
    gemini_key = _ENV.get('GEMINI_API_KEY', '')
    if not gemini_key:
        raise Exception('GEMINI_API_KEY not set')
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}'
    payload = {'contents': [{'parts': [{'text': prompt}]}]}
    for attempt in range(3):
        resp = requests.post(url, json=payload, timeout=timeout)
        if resp.status_code == 503 and attempt < 2:
            log.warning('_gemini_generate: 503, retrying in %ds (attempt %d)', 10 * (attempt + 1), attempt + 1)
            time.sleep(10 * (attempt + 1))
            continue
        resp.raise_for_status()
        break
    data = resp.json()
    text = data['candidates'][0]['content']['parts'][0]['text']
    usage = data.get('usageMetadata', {})
    return text, usage.get('promptTokenCount', 0), usage.get('candidatesTokenCount', 0)


def _gemini_json(prompt, timeout=90):
    """Call Gemini and parse JSON. Returns (parsed_obj, tokens_in, tokens_out)."""
    text, tin, tout = _gemini_generate(prompt, timeout=timeout)
    # Strip markdown code fences if present
    stripped = re.sub(r'^```(?:json)?\s*\n?', '', text.strip())
    stripped = re.sub(r'\n?```\s*$', '', stripped.strip())
    try:
        return json.loads(stripped), tin, tout
    except json.JSONDecodeError as e:
        raise Exception(f'Gemini JSON parse failure: {e}\nRaw: {text[:200]}')


def _haiku_json(system_prompt, user_content, timeout=30):
    """Call claude-haiku-4-5. Returns (parsed_obj, tokens_in, tokens_out)."""
    client = anthropic.Anthropic(api_key=_ENV.get('ANTHROPIC_API_KEY', ''))
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=2048,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_content}],
    )
    text = msg.content[0].text
    stripped = re.sub(r'^```(?:json)?\s*\n?', '', text.strip())
    stripped = re.sub(r'\n?```\s*$', '', stripped.strip())
    try:
        return json.loads(stripped), msg.usage.input_tokens, msg.usage.output_tokens
    except json.JSONDecodeError as e:
        raise Exception(f'Haiku JSON parse failure: {e}\nRaw: {text[:200]}')


def _fetch_semantic_scholar(query):
    """Return list of result dicts from Semantic Scholar."""
    api_key = _ENV.get('SEMANTIC_SCHOLAR_API_KEY', '')
    headers = {}
    if api_key:
        headers['x-api-key'] = api_key
    try:
        resp = requests.get(
            'https://api.semanticscholar.org/graph/v1/paper/search',
            headers=headers,
            params={
                'query': query,
                'fields': 'title,abstract,year,citationCount,isOpenAccess,openAccessPdf,externalIds',
                'limit': 5,
            },
            timeout=20,
        )
        resp.raise_for_status()
        papers = resp.json().get('data', [])
        results = []
        for p in papers:
            eid = p.get('externalIds') or {}
            corpus_id = eid.get('CorpusId')
            url = p.get('openAccessPdf', {}).get('url') if p.get('isOpenAccess') else None
            abstract_url = f'https://www.semanticscholar.org/paper/{corpus_id}' if corpus_id else None
            results.append({
                'source': 'semantic_scholar',
                'title': p.get('title', ''),
                'url': url or abstract_url or '',
                'snippet': (p.get('abstract') or '')[:400],
                'year': p.get('year'),
                'citation_count': p.get('citationCount'),
                'is_open_access': p.get('isOpenAccess'),
                'pdf_url': url,
            })
        return results
    except Exception as e:
        log.warning('_fetch_semantic_scholar error: %s', e)
        return []


def _fetch_arxiv(query, cat_prefix=None):
    """Return list of result dicts from arXiv Atom feed.
    cat_prefix: optional arXiv category filter string, e.g. '(cat:q-bio.NC OR cat:q-bio.QM)'
    """
    import xml.etree.ElementTree as ET
    try:
        search_q = f'{cat_prefix} AND all:{query}' if cat_prefix else f'all:{query}'
        resp = requests.get(
            'https://export.arxiv.org/api/query',
            params={'search_query': search_q, 'max_results': 5},
            timeout=20,
        )
        resp.raise_for_status()
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(resp.text)
        results = []
        for entry in root.findall('atom:entry', ns):
            title = (entry.findtext('atom:title', '', ns) or '').strip().replace('\n', ' ')
            abstract = (entry.findtext('atom:summary', '', ns) or '').strip().replace('\n', ' ')
            abs_url = (entry.findtext('atom:id', '', ns) or '').strip()
            pdf_url = abs_url.replace('/abs/', '/pdf/') if '/abs/' in abs_url else None
            authors = [a.findtext('atom:name', '', ns) for a in entry.findall('atom:author', ns)]
            results.append({
                'source': 'arxiv',
                'title': title,
                'url': abs_url,
                'snippet': abstract[:400],
                'pdf_url': pdf_url,
                'is_open_access': True,
                'authors': authors[:3],
            })
        return results
    except Exception as e:
        log.warning('_fetch_arxiv error: %s', e)
        return []


_WIKIPEDIA_UA = {'User-Agent': 'AADP-Research/1.0 (thompsman@gmail.com)'}

# arXiv category filters for pass two — restrict by gap type to avoid domain mismatches
_ARXIV_CAT_PREFIX = {
    # 'academic' omitted — no category filter; academic gaps span all domains
    'technical': '(cat:cs.AI OR cat:cs.LG OR cat:eess)',
    # 'conceptual' → not included; conceptual gaps route to Wikipedia, not arXiv
}

# Clinical terms in gap.query → skip arXiv entirely; Semantic Scholar covers these journals
_ARXIV_CLINICAL_TERMS = {
    'clinical trial', 'randomized controlled', 'fda',
    'drug application', 'dosing', 'adverse effects', 'contraindication',
}


def _fetch_wikipedia(query):
    """Two-step Wikipedia fetch. Returns list with 0 or 1 result."""
    try:
        from urllib.parse import quote
        s1 = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params={'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': 1},
            headers=_WIKIPEDIA_UA,
            timeout=10,
        )
        s1.raise_for_status()
        hits = s1.json().get('query', {}).get('search', [])
        if not hits:
            log.info('_fetch_wikipedia: no results for "%s"', query[:60])
            return []
        title = hits[0]['title']
        s2 = requests.get(
            f'https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}',
            headers=_WIKIPEDIA_UA,
            timeout=10,
        )
        s2.raise_for_status()
        data = s2.json()
        return [{
            'source': 'wikipedia',
            'title': data.get('title', title),
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
            'snippet': (data.get('extract') or '')[:400],
        }]
    except Exception as e:
        log.warning('_fetch_wikipedia error: %s', e)
        return []


def _fetch_guardian(query):
    """Return list of result dicts from The Guardian API."""
    api_key = _ENV.get('GUARDIAN_API_KEY', '')
    if not api_key:
        log.warning('_fetch_guardian: GUARDIAN_API_KEY not set')
        return []
    try:
        resp = requests.get(
            'https://content.guardianapis.com/search',
            params={
                'q': query,
                'show-fields': 'headline,bodyText,webUrl,webPublicationDate,sectionName',
                'api-key': api_key,
                'page-size': 5,
            },
            timeout=20,
        )
        resp.raise_for_status()
        items = resp.json().get('response', {}).get('results', [])
        results = []
        for item in items:
            fields = item.get('fields') or {}
            body = (fields.get('bodyText') or '')[:400]
            results.append({
                'source': 'guardian',
                'title': fields.get('headline') or item.get('webTitle', ''),
                'url': item.get('webUrl') or fields.get('webUrl', ''),
                'snippet': body,
                'publication_date': (item.get('webPublicationDate') or '')[:10],
                'section': fields.get('sectionName', ''),
            })
        return results
    except Exception as e:
        log.warning('_fetch_guardian error: %s', e)
        return []


def _fetch_brave_dr(query, max_results=5):
    try:
        resp = requests.post(
            f'{_STATS_URL}/web_search',
            json={'query': query, 'max_results': max_results},
            timeout=20,
        )
        if not resp.ok:
            return []
        return resp.json().get('results', [])
    except Exception as e:
        log.warning('_fetch_brave_dr error: %s', e)
        return []


def _fetch_tavily_dr(query, max_results=5):
    try:
        resp = requests.post(
            f'{_STATS_URL}/search_tavily',
            json={'query': query, 'max_results': max_results},
            timeout=25,
        )
        if not resp.ok:
            return []
        return resp.json().get('results', [])
    except Exception as e:
        log.warning('_fetch_tavily_dr error: %s', e)
        return []


def _fetch_github_dr(query, per_page=8):
    # Keyword-only for GitHub; strip stop words
    _stop = {'what','how','why','when','where','who','which','are','is','was','were',
              'do','does','did','can','could','would','should','will','the','a','an',
              'and','or','but','not','for','of','with','to','in','on','at','by','from',
              'about','like','some','any','have','has','had','i','we','you','they','it',
              'be','been','being','people','doing','trying','using','running','making',
              'building','working','getting','looking','there','their','this','that',
              'just','get','run','into','its','more','also','now','even'}
    words = re.sub(r'[^\w\s]', ' ', query.lower()).split()
    kws = [w for w in words if w not in _stop and len(w) > 2][:6]
    gh_query = ' '.join(kws) if len(kws) >= 2 else query[:60]
    try:
        resp = requests.post(
            f'{_STATS_URL}/search_github',
            json={'query': gh_query, 'per_page': per_page},
            timeout=15,
        )
        if not resp.ok:
            return []
        return resp.json().get('results', [])
    except Exception as e:
        log.warning('_fetch_github_dr error: %s', e)
        return []


def _dr_log_error(source, error_msg):
    """Log a single-source failure to error_logs."""
    try:
        requests.post(
            f'{_SUPABASE_URL}/rest/v1/error_logs',
            headers={**_HEADERS, 'Prefer': 'return=minimal'},
            json={
                'workflow_id': 'workpad_deep_research',
                'node_name': source,
                'error_message': str(error_msg)[:500],
                'resolved': False,
            },
            timeout=5,
        )
    except Exception:
        pass


def _deep_research_worker(job_id, query):
    """Background thread: runs the full B-137 two-pass pipeline."""
    t0 = time.monotonic()
    token_log = {}

    try:
        os.makedirs(_RESEARCH_ARTIFACTS_DIR, exist_ok=True)

        # ── Call 1: Gemini query expansion ────────────────────────────────────
        exp_prompt = (
            f'The user is researching: {query}\n\n'
            'Generate optimized search queries for each source. Return JSON only:\n'
            '{\n'
            '  "semantic_scholar": "query for academic paper search",\n'
            '  "arxiv": "query for preprint search — use ti: abs: notation if helpful",\n'
            '  "guardian": "concrete news-framing query",\n'
            '  "wikipedia": "1-3 word entity or concept name",\n'
            '  "default": "query for Brave, Tavily, GitHub"\n'
            '}'
        )
        expanded, tin, tout = _gemini_json(exp_prompt)
        token_log['expansion'] = (tin, tout)
        log.info('DR[%s] expansion done: %s', job_id, list(expanded.keys()))

        def_q = expanded.get('default', query)

        # ── Pass 1: Fire all 7 sources in parallel ────────────────────────────
        p1_results = {
            'semantic_scholar': [], 'arxiv': [], 'wikipedia': [],
            'guardian': [], 'brave': [], 'tavily': [], 'github': [],
        }
        p1_errors = {}

        def _run_source(name, fn, *args):
            try:
                p1_results[name] = fn(*args) or []
            except Exception as e:
                p1_results[name] = []
                p1_errors[name] = str(e)
                _dr_log_error(name, e)

        p1_threads = [
            threading.Thread(target=_run_source, args=('semantic_scholar', _fetch_semantic_scholar, expanded.get('semantic_scholar', def_q))),
            threading.Thread(target=_run_source, args=('arxiv', _fetch_arxiv, expanded.get('arxiv', def_q))),
            threading.Thread(target=_run_source, args=('wikipedia', _fetch_wikipedia, expanded.get('wikipedia', def_q))),
            threading.Thread(target=_run_source, args=('guardian', _fetch_guardian, expanded.get('guardian', def_q))),
            threading.Thread(target=_run_source, args=('brave', _fetch_brave_dr, def_q)),
            threading.Thread(target=_run_source, args=('tavily', _fetch_tavily_dr, def_q)),
            threading.Thread(target=_run_source, args=('github', _fetch_github_dr, def_q)),
        ]
        for t in p1_threads:
            t.start()
        for t in p1_threads:
            t.join(timeout=30)
        log.info('DR[%s] pass 1 done: %s results', job_id, {k: len(v) for k, v in p1_results.items()})

        # Build source summary for Gemini calls
        def _result_summary(source_name, items):
            lines = []
            for item in items[:5]:
                title = item.get('title', '')
                url = item.get('url', '')
                snippet = item.get('snippet', '')[:200]
                year = item.get('year', '')
                cites = item.get('citation_count', '')
                pub_date = item.get('publication_date', '')
                line = f'- [{source_name}] {title} | {url}'
                if year:
                    line += f' | {year}'
                if cites is not None and cites != '':
                    line += f' | {cites} citations'
                if pub_date:
                    line += f' | {pub_date}'
                if snippet:
                    line += f'\n  {snippet}'
                lines.append(line)
            return '\n'.join(lines)

        all_p1_text = '\n\n'.join(
            _result_summary(src, p1_results[src])
            for src in ['brave', 'tavily', 'github', 'semantic_scholar', 'arxiv', 'wikipedia', 'guardian']
            if p1_results[src]
        )

        # ── Call 2: Relevance screening and clustering ────────────────────────
        screen_prompt = (
            f'The user is researching: {query}\n\n'
            'Below are raw results from 7 sources. Your jobs:\n'
            '1. Drop results that are noise, tangential, or duplicate.\n'
            '2. Group remaining results into 3-6 topic clusters.\n'
            '3. Identify direct factual contradictions between sources.\n'
            '   State each as: "Source A says X. Source B says Y." Do not resolve.\n\n'
            'Return JSON only:\n'
            '{\n'
            '  "clusters": [\n'
            '    {\n'
            '      "topic": "cluster name",\n'
            '      "findings": [\n'
            '        {\n'
            '          "claim": "specific claim or finding",\n'
            '          "source_name": "brave|tavily|github|semantic_scholar|arxiv|wikipedia|guardian",\n'
            '          "title": "result title",\n'
            '          "url": "url",\n'
            '          "year": null,\n'
            '          "citation_count": null,\n'
            '          "is_open_access": null,\n'
            '          "pdf_url": null,\n'
            '          "publication_date": null\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ],\n'
            '  "conflicts": [\n'
            '    {\n'
            '      "topic": "what the conflict is about",\n'
            '      "source_a": {"title": "", "url": "", "claim": ""},\n'
            '      "source_b": {"title": "", "url": "", "claim": ""}\n'
            '    }\n'
            '  ]\n'
            '}\n\n'
            f'Raw results:\n{all_p1_text}'
        )
        screened, tin, tout = _gemini_json(screen_prompt)
        token_log['screening'] = (tin, tout)
        clusters = screened.get('clusters', [])
        conflicts = screened.get('conflicts', [])
        log.info('DR[%s] screening done: %d clusters %d conflicts', job_id, len(clusters), len(conflicts))

        # ── Call 3: Gap identification ────────────────────────────────────────
        clusters_text = json.dumps(clusters, indent=2)
        gap_prompt = (
            f'You have just synthesized a first-pass research summary on the following topic: {query}\n\n'
            'Review the synthesis and identify gaps, unanswered questions, and claims that need\n'
            'deeper sourcing. Return a JSON array only — no preamble, no markdown fences.\n\n'
            'Schema:\n'
            '[\n'
            '  {\n'
            '    "gap": "concise description of what is missing or unresolved",\n'
            '    "type": "academic | conceptual | current | technical | practitioner",\n'
            '    "priority": "high | medium | low",\n'
            '    "query": "3-5 keyword search string for academic APIs"\n'
            '  }\n'
            ']\n\n'
            'Type definitions:\n'
            '- academic: needs peer-reviewed sourcing or citation evidence\n'
            '- conceptual: needs definitional grounding or relationship clarification\n'
            '- current: needs recent news or developments\n'
            '- technical: needs implementation detail, code, or applied examples\n'
            '- practitioner: needs community knowledge, implementation patterns, or tooling\n'
            '  comparisons from practitioners building similar systems — blogs, GitHub repos,\n'
            '  community forums. Use for personal AI, knowledge management, workflow design,\n'
            '  and emerging practice questions where no peer-reviewed literature exists.\n\n'
            'The "query" field must be short — 3 to 5 keywords maximum. It will be sent directly\n'
            'to arXiv and Semantic Scholar search endpoints. Do not use full sentences, question\n'
            'marks, or filler words. Extract the core topic terms only.\n\n'
            'Examples of good query values:\n'
            '- "MDMA PTSD long-term outcomes"\n'
            '- "psilocybin phase 3 remission trial"\n'
            '- "psychedelic therapy neuroplasticity mechanisms"\n'
            '- "psychedelic therapy non-clinical digital delivery"\n\n'
            'Do not use abbreviations in the "query" field. Always spell out domain terms in full.\n'
            'For example: "psychedelic assisted therapy" not "PAT", "post-traumatic stress disorder"\n'
            'not "PTSD", "major depressive disorder" not "MDD".\n\n'
            'If total gaps exceed 6, return only high and medium priority items.\n\n'
            'Return only the JSON array.\n\n'
            f'Clustered findings:\n{clusters_text}'
        )
        gap_result, tin, tout = _gemini_json(gap_prompt)
        token_log['gaps'] = (tin, tout)
        gaps = gap_result if isinstance(gap_result, list) else gap_result.get('gaps', [])
        log.info('DR[%s] gaps done: %d gaps', job_id, len(gaps))

        # ── Haiku call: gap routing ───────────────────────────────────────────
        haiku_system = (
            'You are a routing classifier. Assign each gap to one or more sources by type.\n'
            'Route: academic → semantic_scholar, arxiv\n'
            '       conceptual → wikipedia\n'
            '       current → guardian\n'
            '       technical → github, arxiv\n'
            '       practitioner → brave, github\n'
            'Return the input JSON array with a "sources" field added to each item.\n'
            'For any gap assigned to wikipedia, also return a "wiki_title" field containing\n'
            'the most likely Wikipedia article title for this concept — 1 to 3 words,\n'
            'title-cased, as it would appear in a Wikipedia URL.\n'
            'Example: "wiki_title": "Psychedelic therapy"\n'
            'Return only the JSON array.'
        )
        try:
            routed_gaps, h_in, h_out = _haiku_json(haiku_system, json.dumps(gaps))
            token_log['haiku_routing'] = (h_in, h_out)
        except Exception as haiku_err:
            # Fallback: assign all gaps to all sources
            log.warning('DR[%s] Haiku routing failed, using fallback: %s', job_id, haiku_err)
            _dr_log_error('haiku_routing', f'JSON parse failure — using fallback: {haiku_err}')
            all_sources = ['semantic_scholar', 'arxiv', 'wikipedia', 'guardian', 'github']
            routed_gaps = [{**g, 'sources': all_sources} for g in gaps]
            token_log['haiku_routing'] = (0, 0)
        log.info('DR[%s] routing done', job_id)

        # ── Plan review pause ─────────────────────────────────────────────────
        approval_event = threading.Event()
        _deep_research_jobs[job_id].update({
            'status': 'awaiting_review',
            'plan': {
                'gaps': routed_gaps,
                'cluster_count': len(clusters),
                'pass1_source_counts': {k: len(v) for k, v in p1_results.items()},
            },
            '_approval_event': approval_event,
        })
        log.info('DR[%s] awaiting plan review (%d gaps)', job_id, len(routed_gaps))
        approval_event.wait(timeout=3600)  # auto-proceed after 1 hour
        routed_gaps = _deep_research_jobs[job_id].get('_approved_gaps', routed_gaps)
        _deep_research_jobs[job_id]['status'] = 'running'
        log.info('DR[%s] plan approved, proceeding to pass 2 (%d gaps)', job_id, len(routed_gaps))

        # ── Pass 2: Retrieve for each gap ─────────────────────────────────────
        _SOURCE_FETCHERS = {
            'semantic_scholar': _fetch_semantic_scholar,
            'arxiv': _fetch_arxiv,
            'wikipedia': _fetch_wikipedia,
            'guardian': _fetch_guardian,
            'brave': _fetch_brave_dr,
            'tavily': _fetch_tavily_dr,
            'github': _fetch_github_dr,
        }
        p2_results = {}       # gap_idx → {source: [results]}
        p2_arxiv_queries = {} # gap_idx → constructed arXiv query string (for artifact table)

        def _fetch_gap_source(gap_idx, gap, source_name):
            fetcher = _SOURCE_FETCHERS.get(source_name)
            if not fetcher:
                return
            try:
                gap_desc = gap.get('gap', '')          # full natural language description
                gap_query = gap.get('query', gap_desc) # 3-5 keyword string for academic APIs
                gap_type = gap.get('type', '')

                # Routing rule:
                #   gap.query (short keywords) → semantic_scholar, arxiv
                #   gap.gap   (full NL desc)   → guardian, brave, tavily, github
                if source_name in ('semantic_scholar', 'arxiv'):
                    search_q = gap_query
                elif source_name == 'wikipedia':
                    # wiki_title is a 1-3 word concept term added by Haiku routing
                    search_q = gap.get('wiki_title', gap_query)
                else:
                    # Guardian, Brave, Tavily, GitHub: natural language gets better results
                    search_q = gap_desc

                # practitioner gaps belong to web sources; skip academic APIs regardless of routing
                if gap_type == 'practitioner' and source_name in ('semantic_scholar', 'arxiv'):
                    p2_results.setdefault(gap_idx, {})[source_name] = []
                    if source_name == 'arxiv':
                        p2_arxiv_queries[gap_idx] = 'skipped — practitioner'
                    return

                # arXiv: category filtering + clinical-only skip
                if source_name == 'arxiv':
                    # conceptual gaps belong to Wikipedia, not arXiv
                    if gap_type == 'conceptual':
                        p2_results.setdefault(gap_idx, {})[source_name] = []
                        p2_arxiv_queries[gap_idx] = 'skipped — conceptual (use Wikipedia)'
                        return
                    # clinical-only queries return garbage on arXiv; Semantic Scholar covers these
                    q_lower = search_q.lower()
                    if any(term in q_lower for term in _ARXIV_CLINICAL_TERMS):
                        p2_results.setdefault(gap_idx, {})[source_name] = []
                        p2_arxiv_queries[gap_idx] = f'skipped — clinical ({search_q})'
                        log.info('DR[%s] arXiv skipped for clinical gap: %s', job_id, search_q[:60])
                        return
                    # apply category filter based on gap type
                    cat_prefix = _ARXIV_CAT_PREFIX.get(gap_type)
                    if cat_prefix:
                        cats = [c.split(':')[1] for c in cat_prefix.strip('()').split(' OR ')]
                        p2_arxiv_queries[gap_idx] = f'[{", ".join(cats)}] {search_q}'
                    else:
                        p2_arxiv_queries[gap_idx] = search_q
                    items = _fetch_arxiv(search_q, cat_prefix=cat_prefix) or []
                    p2_results.setdefault(gap_idx, {})[source_name] = items
                    return

                items = fetcher(search_q) or []
                p2_results.setdefault(gap_idx, {})[source_name] = items
            except Exception as e:
                p2_results.setdefault(gap_idx, {})[source_name] = []
                _dr_log_error(f'p2_{source_name}', e)

        p2_threads = []
        for idx, gap in enumerate(routed_gaps):
            for src in (gap.get('sources') or []):
                t = threading.Thread(target=_fetch_gap_source, args=(idx, gap, src))
                p2_threads.append(t)

        for t in p2_threads:
            t.start()
        for t in p2_threads:
            t.join(timeout=30)
        log.info('DR[%s] pass 2 done: %d gaps addressed', job_id, len(p2_results))

        # ── Build artifact ────────────────────────────────────────────────────
        runtime = round(time.monotonic() - t0)
        now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        p2_src_count = sum(len(v) for v in p2_results.values())

        slug = re.sub(r'\s+', '-', re.sub(r'[^\w\s]', '', query.lower().strip()))[:40].rstrip('-')
        filename = f'{datetime.now(timezone.utc).strftime("%Y-%m-%d")}-{slug}.md'
        artifact_path = os.path.join(_RESEARCH_ARTIFACTS_DIR, filename)

        def _inline_attr(item):
            src = item.get('source', '')
            title = item.get('title', '')
            url = item.get('url', '')
            year = item.get('year')
            cites = item.get('citation_count')
            pdf = item.get('pdf_url')
            pub_date = item.get('publication_date', '')
            parts = []
            if url:
                parts.append(f'[{title}]({url})')
            else:
                parts.append(title)
            if src in ('semantic_scholar', 'arxiv'):
                if year:
                    parts.append(f'[{src}] [{year}]')
                if cites is not None:
                    parts.append(f'[{cites} citations]')
                if pdf:
                    parts.append(f'[[PDF]]({pdf})')
                elif url:
                    parts.append(f'[[Abstract]]({url})')
            elif src == 'guardian':
                date_str = pub_date or ''
                parts.append(f'[Guardian, {date_str}]' if date_str else '[Guardian]')
            elif src in ('brave', 'tavily'):
                parts.append(f'[{src.capitalize()}]')
            elif src == 'github':
                parts.append('[GitHub]')
            elif src == 'wikipedia':
                parts.append('[Wikipedia]')
            return ' '.join(parts)

        lines = [
            '---',
            f'# Research: {query}',
            f'{now_iso} | {runtime}s | 7 sources pass one | {p2_src_count} sources pass two',
            '',
            '## Query Expansion',
            f'Original: {query}',
            f'Semantic Scholar: {expanded.get("semantic_scholar", def_q)}',
            f'arXiv: {expanded.get("arxiv", def_q)}',
            f'Guardian: {expanded.get("guardian", def_q)}',
            f'Wikipedia: {expanded.get("wikipedia", def_q)}',
            f'Brave / Tavily / GitHub: {def_q}',
            '',
            '## Pass One Findings',
            '',
        ]

        for cluster in clusters:
            lines.append(f'### {cluster.get("topic", "Cluster")}')
            for finding in cluster.get('findings', []):
                claim = finding.get('claim', '')
                attr = _inline_attr(finding)
                lines.append(f'- {claim} — {attr}')
            lines.append('')

        # Gap table
        lines += [
            '## Gap Analysis',
            '| Gap | Type | Priority | Sources Assigned | Pass Two Query |',
            '|-----|------|----------|-----------------|----------------|',
        ]
        for idx, gap in enumerate(routed_gaps):
            g = gap.get('gap', '')
            t_type = gap.get('type', '')
            priority = gap.get('priority', '')
            sources = ', '.join(gap.get('sources') or [])
            # Show arXiv constructed query (with category prefix) if available
            if 'arxiv' in (gap.get('sources') or []) and idx in p2_arxiv_queries:
                p2_query = p2_arxiv_queries[idx]
            else:
                p2_query = gap.get('query', g)
            lines.append(f'| {g} | {t_type} | {priority} | {sources} | {p2_query} |')
        lines.append('')

        # Pass 2 findings
        lines.append('## Pass Two Findings')
        lines.append('')
        for idx, gap in enumerate(routed_gaps):
            gap_desc = gap.get('gap', '')
            src_results = p2_results.get(idx, {})
            lines.append(f'### Gap: {gap_desc}')
            queried_srcs = ', '.join(src_results.keys()) if src_results else 'none'
            lines.append(f'Queried: {queried_srcs}')
            any_result = False
            for src_name, items in src_results.items():
                for item in items:
                    lines.append(f'- {item.get("snippet", item.get("title", ""))[:150]} — {_inline_attr(item)}')
                    any_result = True
            if not any_result:
                lines.append('*No relevant results returned.*')
            lines.append('')

        # Conflicts
        if conflicts:
            lines.append('## Conflicts')
            for i, c in enumerate(conflicts, 1):
                topic = c.get('topic', '')
                sa = c.get('source_a', {})
                sb = c.get('source_b', {})
                a_title = sa.get('title', 'Source A')
                a_url = sa.get('url', '')
                a_claim = sa.get('claim', '')
                b_title = sb.get('title', 'Source B')
                b_url = sb.get('url', '')
                b_claim = sb.get('claim', '')
                a_link = f'[{a_title}]({a_url})' if a_url else a_title
                b_link = f'[{b_title}]({b_url})' if b_url else b_title
                lines.append(f'{i}. **{topic}**: {a_link} says {a_claim}. {b_link} says {b_claim}.')
            lines.append('')

        # Unresolved (pass 2 returned 0 results)
        unresolved = [
            (routed_gaps[idx], src_results)
            for idx, src_results in p2_results.items()
            if all(len(v) == 0 for v in src_results.values())
        ]
        unresolved += [
            (routed_gaps[idx], {})
            for idx in range(len(routed_gaps))
            if idx not in p2_results
        ]
        if unresolved:
            lines.append('## Unresolved After Two Passes')
            for gap, src_results in unresolved:
                gap_desc = gap.get('gap', '')
                lines.append(f'- **{gap_desc}**: 0 results returned.')
            lines.append('')

        # Footer
        p1_counts = ' | '.join(f'{src} {len(p1_results[src])}' for src in
                                ['brave', 'tavily', 'github', 'semantic_scholar', 'arxiv', 'wikipedia', 'guardian'])
        p2_detail = ' | '.join(
            f'{src} {sum(len(v.get(src, [])) for v in p2_results.values())}'
            for src in ['semantic_scholar', 'arxiv', 'wikipedia', 'guardian', 'brave', 'tavily', 'github']
        )

        def _tok(key):
            tin, tout = token_log.get(key, (0, 0))
            return f'{tin}/{tout}tok'

        lines += [
            '---',
            f'Query: {query} | {now_iso}',
            f'Pass one: {p1_counts}',
            f'Pass two: {p2_detail}',
            f'Gemini: expansion {_tok("expansion")} | screening {_tok("screening")} | gaps {_tok("gaps")}',
            f'Haiku: routing {_tok("haiku_routing")}',
            '---',
        ]

        artifact_content = '\n'.join(lines)
        with open(artifact_path, 'w') as f:
            f.write(artifact_content)
        log.info('DR[%s] artifact written: %s', job_id, artifact_path)

        # Append to workpad_state output_entries
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            'action': 'deep_research',
            'query': query,
            'timestamp': now,
            'artifact_path': artifact_path,
            'artifact_content': artifact_content,
        }
        try:
            r = requests.get(
                f'{_SUPABASE_URL}/rest/v1/workpad_state',
                headers=_HEADERS,
                params={'select': 'output_entries', 'id': 'eq.1'},
                timeout=10,
            )
            r.raise_for_status()
            rows = r.json()
            current = (rows[0].get('output_entries') or []) if rows else []
            current.append(entry)
            requests.post(
                f'{_SUPABASE_URL}/rest/v1/workpad_state',
                headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
                json={'id': 1, 'output_entries': current, 'updated_at': now},
                timeout=10,
            ).raise_for_status()
        except Exception as wb_err:
            log.warning('DR[%s] workpad_state write failed: %s', job_id, wb_err)

        _deep_research_jobs[job_id] = {
            'status': 'done',
            'result': {
                'artifact_path': artifact_path,
                'artifact_content': artifact_content,
                'runtime_s': runtime,
                'query': query,
            },
            'error': None,
        }

    except Exception as e:
        log.error('DR[%s] pipeline error: %s', job_id, e)
        _deep_research_jobs[job_id] = {'status': 'error', 'result': None, 'error': str(e)}


@anvil.server.callable
def run_deep_research(query):
    """Start the two-pass deep research pipeline. Returns {job_id, status} immediately."""
    import uuid
    query = (query or '').strip()
    if not query:
        raise Exception('Query is required.')
    job_id = str(uuid.uuid4())[:8]
    _deep_research_jobs[job_id] = {'status': 'running', 'result': None, 'error': None}
    threading.Thread(
        target=_deep_research_worker,
        args=(job_id, query),
        daemon=True,
        name=f'deep-research-{job_id}',
    ).start()
    log.info('run_deep_research: job_id=%s query=%s', job_id, query[:60])
    return {'job_id': job_id, 'status': 'running'}


@anvil.server.callable
def get_deep_research_status(job_id):
    """Poll the status of a deep research job."""
    job = _deep_research_jobs.get(job_id)
    if not job:
        raise Exception(f'Deep research job {job_id} not found.')
    return job


@anvil.server.callable
def approve_deep_research_plan(job_id, approved_gaps=None):
    """Approve the pass-1 plan and resume pass 2. Optionally pass edited gaps list."""
    job = _deep_research_jobs.get(job_id)
    if not job:
        raise Exception(f'Deep research job {job_id} not found.')
    if job.get('status') != 'awaiting_review':
        raise Exception(f'Job {job_id} is not awaiting review (status: {job.get("status")}).')
    if approved_gaps is not None:
        job['_approved_gaps'] = approved_gaps
    event = job.get('_approval_event')
    if event:
        event.set()
    log.info('approve_deep_research_plan: job_id=%s gaps=%s', job_id,
             len(approved_gaps) if approved_gaps is not None else 'unchanged')
    return {'ok': True}


# ── Workpad ───────────────────────────────────────────────────────────────────

_WORKPAD_EMPTY = {'input_text': '', 'attach_url': '', 'output_entries': []}


@anvil.server.callable
def get_workpad_state():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers=_HEADERS,
        params={'select': '*', 'id': 'eq.1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return dict(_WORKPAD_EMPTY)
    row = rows[0]
    return {
        'input_text': row.get('input_text', ''),
        'attach_url': row.get('attach_url', ''),
        'output_entries': row.get('output_entries') or [],
    }


@anvil.server.callable
def save_workpad_input(input_text, attach_url):
    now = datetime.now(timezone.utc).isoformat()
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'id': 1, 'input_text': input_text or '', 'attach_url': attach_url or '', 'updated_at': now},
        timeout=10,
    )
    r.raise_for_status()
    return {'saved_at': now}


@anvil.server.callable
def _extract_article_text(raw_html, url):
    """Extract clean human-readable article text from raw HTML.

    Removes script/style blocks and their entire content, HTML tags,
    CSS, JS, and structured data. Returns (text, failed) where
    failed=True means clean text could not be extracted.
    """
    import html as _html_mod

    # 1. Remove entire content of non-prose blocks before touching tags
    _BLOCK_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<style[^>]*>.*?</style>',
        r'<noscript[^>]*>.*?</noscript>',
        r'<svg[^>]*>.*?</svg>',
        r'<head[^>]*>.*?</head>',      # head contains no readable content
        r'<iframe[^>]*>.*?</iframe>',
        r'<!--.*?-->',                  # HTML comments
    ]
    text = raw_html
    for pat in _BLOCK_PATTERNS:
        text = re.sub(pat, ' ', text, flags=re.DOTALL | re.IGNORECASE)

    # 2. Strip all remaining HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # 3. Decode HTML entities
    text = _html_mod.unescape(text)

    # 4. Remove curly-brace blocks of any length (CSS rules that leaked through)
    #    Use re.DOTALL so multi-line blocks are caught. No char-count limit.
    text = re.sub(r'\{[^{}]*\}', ' ', text, flags=re.DOTALL)
    # Second pass catches nested or adjacent blocks
    text = re.sub(r'\{[^{}]*\}', ' ', text, flags=re.DOTALL)

    # 5. Line-level filtering — drop lines that look like CSS/JS artifacts
    _JS_CSS_LINE = re.compile(
        r'^\s*('
        r'var |const |let |function |return |import |export |module\.|window\.|document\.|'
        r'\.[\w-]+\s*[\({]|'          # .selector( or .selector{
        r'[@#][\w-]|'                  # @media, #id selectors
        r'[\w-]+\s*:\s*[\w\d#\'"%-].*?;|'  # CSS property: value;
        r'[;{}]'                        # bare semicolons or braces
        r')',
        re.IGNORECASE
    )
    clean_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _JS_CSS_LINE.match(stripped):
            continue
        # Drop lines that are >60% punctuation/symbols
        alpha = sum(1 for c in stripped if c.isalpha())
        if len(stripped) > 10 and alpha / len(stripped) < 0.4:
            continue
        clean_lines.append(stripped)
    text = '\n'.join(clean_lines)

    # 6. Collapse whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    # 7. Quality gate: need at least 50 prose words, >50% word-like tokens
    prose_words = [w for w in text.split() if re.search(r'[a-zA-Z]{3,}', w)]
    total_tokens = len(text.split()) or 1
    if len(prose_words) < 50 or (len(prose_words) / total_tokens) < 0.5:
        return text, True  # failed — insufficient clean prose
    return text, False


def fetch_url_content(url):
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'AADP/1.0'})
        resp.raise_for_status()
        raw = resp.text
        # Extract page title for fallback
        title_match = re.search(r'<title[^>]*>(.*?)</title>', raw, re.IGNORECASE | re.DOTALL)
        page_title = title_match.group(1).strip() if title_match else url
        text, failed = _extract_article_text(raw, url)
        if failed:
            text = f'{page_title}\n{url}\n[FETCH FAILED - markup only]'
    except Exception as e:
        text = f'Error fetching URL: {e}'
        failed = True
    now = datetime.now(timezone.utc).isoformat()
    entry = {'action': 'read_url', 'result': text, 'timestamp': now}
    # Read current entries, append, then upsert
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers=_HEADERS,
        params={'select': 'output_entries', 'id': 'eq.1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    current = (rows[0].get('output_entries') or []) if rows else []
    current.append(entry)
    r2 = requests.post(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'id': 1, 'output_entries': current, 'updated_at': now},
        timeout=10,
    )
    r2.raise_for_status()
    log.info('fetch_url_content: url=%s chars=%d', url[:80], len(text))
    return entry


@anvil.server.callable
def clear_workpad():
    now = datetime.now(timezone.utc).isoformat()
    r = requests.post(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'id': 1, 'input_text': '', 'attach_url': '', 'output_entries': [], 'updated_at': now},
        timeout=10,
    )
    r.raise_for_status()
    log.info('clear_workpad: cleared at %s', now)
    return {'cleared_at': now}


@anvil.server.callable
def search_brave(query, max_results=5):
    """Legacy single-engine search. Kept for backward compat; Workpad now uses search_all."""
    query = (query or '').strip()
    if not query:
        raise Exception('Query is required.')
    now = datetime.now(timezone.utc).isoformat()
    try:
        resp = requests.post(
            'http://localhost:9100/web_search',
            json={'query': query, 'max_results': max_results},
            timeout=20,
        )
    except Exception as e:
        raise Exception(f'Search unavailable: {e}')
    if resp.status_code == 429:
        raise Exception('Brave rate limit hit, try again in a moment')
    if not resp.ok:
        data = resp.json() if resp.content else {}
        raise Exception(f'Search error: {data.get("error", resp.status_code)}')
    data = resp.json()
    results = data.get('results', [])
    entry = {
        'action': 'search',
        'query': query,
        'results': results,
        'timestamp': now,
    }
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers=_HEADERS,
        params={'select': 'output_entries', 'id': 'eq.1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    current = (rows[0].get('output_entries') or []) if rows else []
    current.append(entry)
    r2 = requests.post(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'id': 1, 'output_entries': current, 'updated_at': now},
        timeout=10,
    )
    r2.raise_for_status()
    log.info('search_brave: query=%s results=%d', query[:60], len(results))
    return entry


def _normalize_query(q):
    """Normalize query for deduplication: lowercase, collapse whitespace, strip punctuation ends."""
    q = q.lower().strip()
    q = re.sub(r'\s+', ' ', q)
    q = q.strip('.,!?;:')
    return q


@anvil.server.callable
def search_all(query, max_results=10):
    """Run Brave+Tavily in parallel, then Gemini synthesis. Deduplicates identical queries."""
    import threading
    query = (query or '').strip()
    if not query:
        raise Exception('Query is required.')

    # ── 1. Deduplication: read current entries before executing ──────────────
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers=_HEADERS,
        params={'select': 'output_entries', 'id': 'eq.1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    current = (rows[0].get('output_entries') or []) if rows else []

    norm_query = _normalize_query(query)
    for existing in reversed(current):
        if (existing.get('action') == 'search_all'
                and _normalize_query(existing.get('query', '')) == norm_query
                and existing.get('github_searched', False)):  # only reuse entries created with github support
            log.info('search_all: duplicate query "%s" — reusing existing entry', query[:60])
            return existing  # skip search and Gemini; return cached result

    # ── 2. Run Brave + Tavily + GitHub in parallel ────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    brave_data = {}
    tavily_data = {}
    github_data = {}
    gemini_data = {}

    def _call_brave():
        try:
            resp = requests.post(
                'http://localhost:9100/web_search',
                json={'query': query, 'max_results': max_results},
                timeout=20,
            )
            brave_data.update(resp.json() if resp.ok else {'results': [], 'error': resp.text[:200]})
        except Exception as e:
            brave_data['error'] = str(e)
            brave_data['results'] = []

    def _call_tavily():
        try:
            resp = requests.post(
                'http://localhost:9100/search_tavily',
                json={'query': query, 'max_results': max_results},
                timeout=25,
            )
            tavily_data.update(resp.json() if resp.ok else {'results': [], 'answer': '', 'error': resp.text[:200]})
        except Exception as e:
            tavily_data['error'] = str(e)
            tavily_data['results'] = []
            tavily_data['answer'] = ''

    def _call_github():
        # GitHub repo search works on keywords, not natural language.
        # Strip question/stop words to extract technical terms.
        _stopwords = {
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'are', 'is', 'was',
            'were', 'do', 'does', 'did', 'can', 'could', 'would', 'should', 'will',
            'the', 'a', 'an', 'and', 'or', 'but', 'not', 'for', 'of', 'with', 'to',
            'in', 'on', 'at', 'by', 'from', 'about', 'like', 'some', 'any', 'have',
            'has', 'had', 'i', 'we', 'you', 'they', 'it', 'be', 'been', 'being',
            'people', 'doing', 'trying', 'using', 'running', 'making', 'building',
            'working', 'getting', 'looking', 'there', 'their', 'this', 'that',
            'just', 'get', 'run', 'into', 'its', 'more', 'also', 'now', 'even',
        }
        words = re.sub(r'[^\w\s]', ' ', query.lower()).split()
        kws = [w for w in words if w not in _stopwords and len(w) > 2][:6]
        gh_query = ' '.join(kws) if len(kws) >= 2 else query[:60]
        try:
            resp = requests.post(
                'http://localhost:9100/search_github',
                json={'query': gh_query, 'per_page': 8},
                timeout=15,
            )
            github_data.update(resp.json() if resp.ok else {'results': [], 'error': resp.text[:200]})
            github_data['gh_query'] = gh_query  # store for debugging
        except Exception as e:
            github_data['error'] = str(e)
            github_data['results'] = []

    threads = [
        threading.Thread(target=_call_brave),
        threading.Thread(target=_call_tavily),
        threading.Thread(target=_call_github),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    # ── 3. Gemini synthesizes Brave+Tavily+GitHub results (sequential, after all done) ──
    def _call_gemini():
        try:
            resp = requests.post(
                'http://localhost:9100/search_gemini',
                json={
                    'query': query,
                    'brave_results': brave_data.get('results', []),
                    'tavily_results': tavily_data.get('results', []),
                    'tavily_answer': tavily_data.get('answer', ''),
                    'github_results': github_data.get('results', []),
                },
                timeout=45,
            )
            if resp.ok:
                data = resp.json()
                gemini_data['answer'] = data.get('answer', '')
                if not gemini_data['answer']:
                    gemini_data['error_reason'] = 'api_returned_empty'
            else:
                try:
                    err = resp.json().get('error', resp.text[:200])
                except Exception:
                    err = resp.text[:200]
                gemini_data['answer'] = ''
                gemini_data['error_reason'] = f'api_error: {err}'
        except requests.exceptions.Timeout:
            gemini_data['answer'] = ''
            gemini_data['error_reason'] = 'timeout'
        except Exception as e:
            gemini_data['answer'] = ''
            gemini_data['error_reason'] = f'exception: {e}'

    _call_gemini()

    entry = {
        'action': 'search_all',
        'query': query,
        'timestamp': now,
        'brave': brave_data.get('results', []),
        'tavily': {
            'results': tavily_data.get('results', []),
            'answer': tavily_data.get('answer', ''),
        },
        'github': github_data.get('results', []),
        'github_searched': True,  # marks entry as created after github feature — enables dedup
        'gemini': {
            'answer': gemini_data.get('answer', ''),
            'error_reason': gemini_data.get('error_reason', ''),
        },
        'errors': {k: v for k, v in {
            'brave': brave_data.get('error'),
            'tavily': tavily_data.get('error'),
            'github': github_data.get('error'),
        }.items() if v},
    }

    # ── 4. Append to workpad_state ───────────────────────────────────────────
    current.append(entry)
    r2 = requests.post(
        f'{_SUPABASE_URL}/rest/v1/workpad_state',
        headers={**_HEADERS, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
        json={'id': 1, 'output_entries': current, 'updated_at': now},
        timeout=10,
    )
    r2.raise_for_status()
    log.info('search_all: query=%s brave=%d tavily=%d github=%d gemini_chars=%d gemini_error=%s',
             query[:60], len(entry['brave']), len(entry['tavily']['results']),
             len(entry['github']),
             len(entry['gemini'].get('answer', '')),
             entry['gemini'].get('error_reason', 'none'))
    return entry


@anvil.server.callable
def submit_bill_input(mode, text):
    mode = (mode or '').strip()
    text = (text or '').strip()
    if mode not in ('Question', 'Comment', 'Command'):
        raise Exception(f'Invalid mode: {mode}')
    if not text:
        raise Exception('Text is required.')
    # Overwrite any existing row — table holds at most one entry at a time
    requests.delete(
        f'{_SUPABASE_URL}/rest/v1/bill_input',
        headers=_HEADERS,
        params={'id': 'neq.00000000-0000-0000-0000-000000000000'},
        timeout=10,
    ).raise_for_status()
    requests.post(
        f'{_SUPABASE_URL}/rest/v1/bill_input',
        headers=_HEADERS,
        json={'mode': mode, 'text': text, 'status': 'pending'},
        timeout=10,
    ).raise_for_status()
    log.info('submit_bill_input: mode=%s text_len=%d', mode, len(text))
    return {'status': 'ok'}


@anvil.server.callable
def get_bill_input_response():
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/bill_input',
        headers=_HEADERS,
        params={'select': 'status,response,mode,text', 'order': 'created_at.desc', 'limit': '1'},
        timeout=10,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return {'status': 'none', 'response': None}
    row = rows[0]
    return {
        'status': row.get('status', 'pending'),
        'response': row.get('response'),
        'mode': row.get('mode'),
        'text': row.get('text'),
    }


log.info('Connecting to Anvil uplink...')
anvil.server.connect(_ENV['ANVIL_UPLINK_KEY'])
log.info('Uplink connected — waiting for calls.')
anvil.server.wait_forever()
