# Session Artifact — Home Tab Error Log Indicator: status strip badge
Date: 2026-06-27
Node ID: 3c1d70dd-89ea-41fc-8505-0a8b1e1af9ba
Code commits: claudis c49c00f (attempt), 2a6113d (merge to main); claude-dashboard 0cc80e0 (attempt), b87d6a4 (merge to master)

## Capability Delta

**Before:** Home tab status strip showed health, agents, queue, and inbox badge. No visibility into `error_logs` table from the dashboard. `get_error_log_status` callable did not exist.

**After:** Status strip has an Errors badge — `✅` when unresolved count is 0, `🔴 N` when non-zero. `get_error_log_status` callable returns `{unresolved_count, recent[3]}` via a single PostgREST call with `Prefer: count=exact`. Badge refreshes on every `refresh_data()` call via `_load_error_status()`.

**Reader:** Bill via Anvil dashboard Home tab status strip.

## What was built

### uplink_server.py — `get_error_log_status` callable

```python
@anvil.server.callable
def get_error_log_status():
    """Return unresolved error count and the 3 most recent unresolved errors."""
    r = requests.get(
        f'{_SUPABASE_URL}/rest/v1/error_logs',
        headers={**_HEADERS, 'Prefer': 'count=exact'},
        params={
            'select': 'id,workflow_name,node_name,error_type,error_message,timestamp',
            'resolved': 'eq.false',
            'order': 'timestamp.desc',
            'limit': '3',
        },
        timeout=10,
    )
    r.raise_for_status()
    recent = r.json()
    content_range = r.headers.get('Content-Range', '*/0')
    total = int(content_range.split('/')[-1]) if '/' in content_range else len(recent)
    return {'unresolved_count': total, 'recent': recent}
```

Single request via `Prefer: count=exact` returns total count in `Content-Range` header and top-3 rows in body. Consistent with existing `Content-Range` pattern used elsewhere in uplink_server.py.

### Form1/__init__.py — error badge component

**Init (`__init__`):** Added `self._home_error_count = 0`.

**Status strip (`_build_home_layout`):**
```python
self._home_error_lbl = Label(text='—', font_size=24, bold=True)
# ...
strip.add_component(Label(text='  Errors: ', font_size=18))
strip.add_component(self._home_error_lbl)
```

**Loader (`_load_error_status`):**
```python
def _load_error_status(self):
    try:
        with anvil.server.no_loading_indicator:
            data = anvil.server.call('get_error_log_status')
        self._home_error_count = data.get('unresolved_count', 0)
    except Exception:
        self._home_error_count = 0
    self._update_home_status_strip()
```

**Refresh wiring (`refresh_data`):** `_load_error_status()` called after `_load_inbox()`.

**Badge rendering (`_update_home_status_strip`):**
```python
n_errors = self._home_error_count
self._home_error_lbl.text = f'🔴 {n_errors}' if n_errors > 0 else '✅'
```

## Verified state at boot

- `error_logs` table: 0 unresolved errors (confirmed by live query in boot step 9)
- `architecture/specs/error-log-query-spec.md`: SQL queries verified in Node 1 (commit d325dc1)
- `Content-Range` pattern: matches existing usage at lines 1349, 1359, 1370, 1396, 2716, 2727, 2822 of uplink_server.py
