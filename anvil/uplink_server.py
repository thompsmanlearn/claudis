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
_HEADERS = {
    'apikey': _SUPABASE_KEY,
    'Authorization': f'Bearer {_SUPABASE_KEY}',
    'Content-Type': 'application/json',
}
_CLAUDIS_DIR = os.path.expanduser('~/aadp/claudis')


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


log.info('Connecting to Anvil uplink...')
anvil.server.connect(_ENV['ANVIL_UPLINK_KEY'])
log.info('Uplink connected — waiting for calls.')
anvil.server.wait_forever()
