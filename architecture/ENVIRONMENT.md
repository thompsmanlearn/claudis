# ENVIRONMENT

Operational facts about the AADP platform. Read this file at session start, same priority as the master prompt.

**Convention:** Append-only. New entries added freely. Retired entries marked with date and reason — never silently deleted. A retired constraint is itself signal.

---

## Service Endpoints

| Service | Internal (host) | From n8n (Docker) | Notes |
|---|---|---|---|
| Supabase | https://cihbfubghytzqrpffgcq.supabase.co | same | REST + Management API |
| n8n | http://localhost:5678 | — | API key in .env |
| ChromaDB | http://localhost:8000 | http://host.docker.internal:8000 | v0.5.20 — do NOT upgrade |
| Stats Server | http://localhost:9100 | http://host.docker.internal:9100 | systemd aadp-stats.service, always-on |
| Credentials | ~/aadp/mcp-server/.env | — | Never commit |

Wake trigger: `GET http://host.docker.internal:9100/trigger_sentinel` — fires from n8n to wake Sentinel.

---

## Supabase

**Table name gotcha:** `error_logs` (plural), not `error_log`. MCP server fixed 2026-03-17.

**work_queue status values:** `pending`, `claimed`, `complete`, `failed` — never `completed`, `in_progress`, or `processing`. Using an invalid status causes a constraint violation.

**work_queue.priority is INTEGER:** 1 = normal, 2 = high, 3 = critical. Not strings.

**Array columns — NEVER use ARRAY[] constructor syntax:**
```sql
-- WRONG (silent failure, blank error string):
INSERT INTO foo (tags) VALUES (ARRAY['a','b'])

-- CORRECT:
INSERT INTO foo (tags) VALUES ('{"a","b"}'::text[])
```
The Supabase Management API rejects the ARRAY[] form silently — no clear parse error, no 400 response. Diagnosed 2026-03-22.

**UPSERT with non-PK unique key:**
```
POST /rest/v1/{table}?on_conflict={unique_col}
Prefer: resolution=merge-duplicates,return=representation
```
Without `?on_conflict=<col>`, PostgREST uses PK as conflict target.

**DDL requires Management API PAT:** `SUPABASE_MGMT_PAT` in .env. The REST API (PostgREST) cannot execute DDL.

**session_notes valid categories:** `todo`, `observation` — not `note`, `lesson`, `session_summary`.

**inbox valid message_types:** `help_request`, `approval_request`, `recommendation`, `observation`, `question`, `alert`

**inbox valid status values:** `pending`, `approved`, `denied`, `deferred`, `replied`

**agent_registry valid status values:** `active`, `paused`, `retired`, `building`, `broken`, `sandbox` (added 2026-03-23)

---

## ChromaDB

**Version:** v0.5.20 running in Docker. Client must be `chromadb==0.5.20`. Do NOT upgrade — v1.x client uses /api/v2 which is incompatible with the server.

**memory_add parameter:** Use `doc_id` not `id`. Using `id` causes silent failure with confusing metadata error. Correct: `memory_add(collection, doc_id, content, metadata)`. Metadata must be a JSON object, not a string. Discovered 2026-03-23.

**Bulk-get gotcha:** `/get` with `"embeddings"` in include fails with IndexError at scale. Use `["documents", "metadatas"]` only.

**Distance thresholds:** Below 0.8 = high confidence. 0.8–1.2 = review carefully. Above 1.2 = weak match, search again from different angle.

**Collections:** `reference_material`, `agent_templates`, `lessons_learned`, `error_patterns`, `research_findings`, `session_memory`, `self_diagnostics`, `ag_research_data`

**Writing quality matters:** Lessons written as `"n8n Webhook URL Format"` (tool-name first) search poorly. Write with failure mode first: `"When a webhook 404s even though the workflow exists"`. See `chromadb_lesson_writing_quality_2026_03_22` for full guidance.

**Dual-store rule:** Every lesson to BOTH Supabase `lessons_learned` AND ChromaDB `lessons_learned`. Writing to only one store makes the lesson invisible to either SQL queries or semantic search.

---

## n8n

**Activation:** `POST /api/v1/workflows/{id}/activate` — NOT `PATCH {active: true}` (returns `active: null`, does nothing).

**Workflow creation:** Omit `active` field entirely — including `active: false` causes `400: request/body/active is read-only`. Workflows always start inactive.

**Workflow PUT body:** Only 4 keys allowed: `name`, `nodes`, `connections`, `settings`. Any other key causes `400: must NOT have additional properties`. Strip before PUT.

**Empty array chain stop (CRITICAL):** When an HTTP Request node returns `[]`, it creates 0 output items and silently stops all downstream nodes. No error raised. Fix: set `responseFormat: "text"`, parse JSON in downstream Code node.

**Code node sandbox (v2.6.4):** `fetch()` is NOT available. `$http` is NOT available. Use HTTP Request nodes for ALL external HTTP. Code nodes are for data transformation only.

*Note: The agent_control handler in Build Write Req uses `try{await fetch(...)}catch(e){}` for auto-wake. If fetch() is unavailable in the sandbox, the call is caught silently and the work_queue insert still succeeds. The auto-wake may not fire; Sentinel picks up the task on next scheduled wake.*

**Anthropic API response in n8n:** Response fields are at `$json` top level — NOT `$json.body`. The body wrapper is the most common mistake parsing Haiku/Claude responses.

**Webhook body access:** `$json.FIELD_NAME` not `$json.body.FIELD_NAME`. The `.body` wrapper does not exist for POST webhook data.

**Telegram trigger node:** NEVER use spaces in node name. Spaces cause URL-encoded path (`telegram%20trigger`) → lookup fails → zero executions. Name: `TelegramTrigger` not `Telegram Trigger`. After renaming: deactivate → PUT → activate.

**Node rename:** Update BOTH the node `name` field AND all `target.node` references in the connections dict.

**Telegram credential:** ID `y4YfKWpm20Z9sw7G` ("Life OS Telegram Bot"). Bill's chat_id: `8513796837`.

**RSS CDATA stripping:** `<![CDATA[...]]>` wrappers must be stripped before regex. `<!\[CDATA\[` is a regex character class issue. Pattern:
```javascript
const clean = xml.replace(/<!\[CDATA\[/g, '').replace(/\]\]>/g, '');
```

**HTTP Request body expressions:** Use `$json.prompt` not `.prompt`. Bare `.prompt` is invalid JS syntax.

**Script output:** In `python3 -c` commands, ALL `print()` goes to stdout and corrupts JSON output. Use `print(..., file=sys.stderr)` for debug.

**Workflow execution:** `workflow_execute` MCP tool is not supported — n8n public API has no execution endpoint. To run a workflow on demand: create with webhook trigger, activate, POST to webhook, deactivate, delete.

**host.docker.internal:** Added via `extra_hosts: ["host.docker.internal:host-gateway"]` in `/home/thompsman/n8n/docker-compose.yml`. Use instead of hardcoded Docker IP.

---

## Active Workflow IDs

| workflow_id | agent_name | trigger |
|---|---|---|
| kddIKvA37UDw4x6e | telegram_command_agent | Telegram long-poll |
| 1YaIxHK7kqARgaja | daily_briefing_agent | cron 0 14 * * * (6AM Pacific) |
| F3khynqQBUXSnadu | weather_agent | GET /webhook/weather |
| IYaj3zv9xj79h9jg | wiki_attention_monitor | cron 0 15 * * * (7AM Pacific) |
| AGCfhllXOksxhQRC | coast_intelligence | GET /webhook/coast, cron 30 14 * * * |
| VarOOpgZ4XIsIMBY | ai_frontier_scout | GET /webhook/frontier, cron 0 15 * * * |
| tM22yOa0RpCSA0tV | cosmos_report | GET /webhook/cosmos, cron 15 14 * * * |
| 8VXxDD3JUi1sI2h3 | serendipity_engine | GET /webhook/today, cron 30 15 * * * |
| nvILr4bSsgmGISsv | macro_pulse | GET /webhook/macro, cron 45 15 * * 1-5 |
| 2IrUemstlA4K6EIS | heritage_watch | GET /webhook/heritage, cron 0 16 * * * |

---

## External API Notes

**Wikimedia On This Day:** WORKING: `https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{MM}/{DD}` (zero-padded, User-Agent header required). BROKEN: `https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{M}/{D}` → 404.

**NASA NEO:** Uses `DEMO_KEY` — rate limited. For production use, Bill should register for a real API key.

**FRED API:** Free, no key required for basic series. Series used: T10Y2Y (yield curve), UNRATE (unemployment), M2SL (money supply).

---

*Bootstrapped 2026-03-24 from ChromaDB lessons_learned and disk memory files. Append as new facts are discovered.*
