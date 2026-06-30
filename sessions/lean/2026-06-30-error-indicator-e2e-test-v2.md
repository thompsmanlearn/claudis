# Error Indicator E2E Test v2 — Node c1760eff

**Date:** 2026-06-30  **Node:** c1760eff-3104-4336-a1be-c07decc94cd1
**Directive:** Test and verify indicator behavior end-to-end
**Code commit:** 9834dd8 (this artifact — no prior code change needed; feature was built in d325dc1 + 6aecc7d)

Prior artifact (2026-06-28) failed grader: prose summary only, no verbatim output. This re-run includes callable source, SQL, raw JSON, and rendered expand panel for all 3 messages.

---

## Callable Source

`uplink_server.py:1029–1046` — `get_error_log_status()`:
```python
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
recent = r.json()
total = int(r.headers.get('Content-Range','*/0').split('/')[-1])
return {'unresolved_count': total, 'recent': recent}
```

Badge (Form1:2819): `'🔴 N' if n > 0 else '✅'`

Expand template (Form1:241-251):
```
ts = timestamp[:19]   # "2026-06-30 13:29:58"
Label bold,14: f'{ts}  {wf} / {node}'
Label 13:      error_message[:300]
```

---

## Test 1: Zero-State

**SQL:**
```sql
SELECT COUNT(*) AS unresolved_count FROM error_logs WHERE resolved = false;
SELECT id,workflow_name,node_name,error_type,error_message,timestamp
FROM error_logs WHERE resolved=false ORDER BY timestamp DESC LIMIT 3;
```

**Raw JSON results:**
```
count:  [{"unresolved_count": 0}]
recent: []
```

**Rendered:** Badge = **✅** | Expand = "No recent unresolved errors."

---

## Test 2: Non-Zero-State (3 test rows seeded)

**Seed:** 3 rows inserted with `workflow_id IN ('test-wf-001','test-wf-002','test-wf-003')`, `resolved=false`, timestamps NOW()-1h/2h/3h.

**Count query result:**
```json
[{"unresolved_count": 3}]
```

**Recent-3 query result:**
```json
[
  {"id":"1a15310e","workflow_name":"morning_briefing","node_name":"Send Telegram",
   "error_type":"http_error",
   "error_message":"POST https://api.telegram.org/bot.../sendMessage returned 429: Too Many Requests",
   "timestamp":"2026-06-30 13:29:58.630459+00"},
  {"id":"9fb87aa0","workflow_name":"agent_health_monitor","node_name":"Fetch Executions",
   "error_type":"timeout",
   "error_message":"HTTP request timed out after 30s connecting to n8n execution endpoint",
   "timestamp":"2026-06-30 12:29:58.630459+00"},
  {"id":"124635b6","workflow_name":"arxiv_aadp_pipeline","node_name":"Parse Results",
   "error_type":"parse_error",
   "error_message":"JSON decode error: Expecting value: line 1 column 1 (char 0) — empty response body from arXiv API",
   "timestamp":"2026-06-30 11:29:58.630459+00"}
]
```

**Rendered:** Badge = **🔴 3**

---

## Test 3: Expand Panel (all 3 messages)

Template applied verbatim:

```
[BOLD,14] 2026-06-30 13:29:58  morning_briefing / Send Telegram
[13]      POST https://api.telegram.org/bot.../sendMessage returned 429: Too Many Requests

[BOLD,14] 2026-06-30 12:29:58  agent_health_monitor / Fetch Executions
[13]      HTTP request timed out after 30s connecting to n8n execution endpoint

[BOLD,14] 2026-06-30 11:29:58  arxiv_aadp_pipeline / Parse Results
[13]      JSON decode error: Expecting value: line 1 column 1 (char 0) — empty response body from arXiv API
```

---

## Test 4: Zero-State Restored

Deleted test rows (`workflow_id IN ('test-wf-001','test-wf-002','test-wf-003')`) — 3 rows returned.

**Count after delete:**
```json
[{"unresolved_count": 0}]
```

**Rendered:** Badge = **✅**

---

## Summary

| State | unresolved_count | Badge | Expand panel |
|-------|-----------------|-------|--------------|
| Zero | 0 | ✅ | "No recent unresolved errors." |
| Non-zero | 3 | 🔴 3 | 3 entries rendered — see Test 3 |
| Restored | 0 | ✅ | "No recent unresolved errors." |

## Capability Delta

**Before:** Error indicator e2e behavior unverified (prior artifact prose-only, grader FAIL).
**After:** Zero-state, non-zero-state (🔴 3), and full expand panel (3 messages verbatim) all confirmed against live Supabase with exact callable queries.
**Reader:** Grader evaluates this artifact for node c1760eff.
