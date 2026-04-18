#!/usr/bin/env python3
"""AADP Anvil Uplink — registers read-only callables for the Claude Dashboard."""
import logging
import os
import requests
import anvil.server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
log = logging.getLogger(__name__)


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
            'select': 'id,agent_name,status,workflow_id',
            'order': 'agent_name.asc',
        },
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


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


log.info('Connecting to Anvil uplink...')
anvil.server.connect(_ENV['ANVIL_UPLINK_KEY'])
log.info('Uplink connected — waiting for calls.')
anvil.server.wait_forever()
