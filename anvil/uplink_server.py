#!/usr/bin/env python3
"""AADP Anvil Uplink — read-only and control callables for the Claude Dashboard."""
import logging
import os
import subprocess
import threading
import time
import requests
import anvil.server
from datetime import datetime, timezone
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
            if age < 1200:  # 20 minutes — 2 keepalive cycles
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'ok')
            else:
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'stale')
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
            'select': 'agent_name,display_name,description,status,schedule,protected,updated_at',
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
            'select': 'id,task_type,status,priority,created_at',
            'status': 'neq.complete',
            'order': 'created_at.desc',
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
        'error_log': {
            'select': 'id,workflow_name,error_message,created_at',
            'resolved': 'eq.false',
            'order': 'created_at.desc',
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


log.info('Connecting to Anvil uplink...')
anvil.server.connect(_ENV['ANVIL_UPLINK_KEY'])
log.info('Uplink connected — waiting for calls.')
anvil.server.wait_forever()
