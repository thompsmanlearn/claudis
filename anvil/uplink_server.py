#!/usr/bin/env python3
"""AADP Anvil Uplink — read-only and control callables for the Claude Dashboard."""
import logging
import os
import subprocess
import threading
import time
import requests
import anvil.server
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

    def log_message(self, *args):
        pass  # suppress per-request logging


threading.Thread(
    target=lambda: HTTPServer(('127.0.0.1', 9101), _HealthHandler).serve_forever(),
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


# ── Lesson callables ─────────────────────────────────────────────────────────

@anvil.server.callable
def get_lessons(filter='recent', limit=25):
    params = {
        'select': 'id,title,category,times_applied,confidence,chromadb_id,created_at',
        'limit': str(limit),
    }
    if filter == 'most_applied':
        params['order'] = 'times_applied.desc'
    elif filter == 'never_applied':
        params['times_applied'] = 'eq.0'
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
            'document': (documents[i] if i < len(documents) else '')[:300],
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
            'document': (documents[i] if i < len(documents) else '')[:300],
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
            'select': 'target_type,target_id,content,created_at',
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
            lines.append(f'- [{fb_type}: {fb_target}] {fb_content}')
        lines.append('')

    log.info('get_research_bundle: run_id=%s articles=%d pending_feedback=%d',
             agent_run_id, article_count, len(pending))
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


log.info('Connecting to Anvil uplink...')
anvil.server.connect(_ENV['ANVIL_UPLINK_KEY'])
log.info('Uplink connected — waiting for calls.')
anvil.server.wait_forever()
