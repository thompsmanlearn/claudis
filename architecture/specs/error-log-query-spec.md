# Error Log Query Spec — Home Tab Error Log Indicator

Project: Home Tab Error Log Indicator (ea278e62)
Node: Define error log data schema and query (5939bc2b)
Written: 2026-06-27

---

## Table: error_logs

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | uuid | NO | Primary key |
| workflow_id | text | NO | Source workflow |
| workflow_name | text | NO | Human-readable workflow name |
| node_name | text | YES | Failing node within workflow |
| error_type | text | NO | Error category |
| error_message | text | NO | Error detail text |
| execution_id | text | YES | n8n execution reference |
| timestamp | timestamptz | YES | When the error occurred |
| resolved | boolean | NO | False = unresolved |
| resolution_notes | text | YES | Free-text resolution detail |
| resolved_by | text | YES | Who resolved it |
| resolved_at | timestamptz | YES | When it was resolved |

---

## Query 1 — Unresolved error count

Used for the badge value. Returns a single integer.

**SQL:**
```sql
SELECT COUNT(*) AS unresolved_count
FROM error_logs
WHERE resolved = false;
```

**MCP tool fallback:**
```
mcp__aadp__error_log_query({ resolved: false })
```
Returns all unresolved rows; caller counts `result.length`. Use the SQL form when only the count is needed — avoids fetching full rows.

---

## Query 2 — 3 most recent errors

Used for the expanded error list. Returns up to 3 rows, newest first.

**SQL:**
```sql
SELECT id, workflow_name, node_name, error_type, error_message, timestamp
FROM error_logs
WHERE resolved = false
ORDER BY timestamp DESC
LIMIT 3;
```

**MCP tool fallback:**
```
mcp__aadp__error_log_query({ resolved: false, hours_back: 720 })
```
The tool does not support LIMIT or ORDER BY — caller must sort and slice client-side. Use the SQL form for the UI path to avoid over-fetching.

---

## UI contract

- **Badge:** zero → green checkmark; non-zero → red badge with count
- **Expanded panel:** 3 rows max — `workflow_name`, `node_name` (if set), `error_message`, `timestamp`
- **Data source:** `mcp__aadp__supabase_exec_sql` with the SQL forms above
- **Callable name (uplink):** TBD in next node — spec only
