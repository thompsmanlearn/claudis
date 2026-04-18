# DEEP_DIVE_BRIEF.md — AADP Comprehensive Technical Reference

*Written 2026-04-17 by Claude Sonnet 4.6 (lean session). Source: direct inspection of all files, live SQL queries, live ChromaDB queries. For onboarding fresh sessions and reconstruction from scratch.*

---

## 1. Infrastructure and Services Map

### Hardware
Raspberry Pi 5, 16GB RAM, always-on. All compute is local. External API calls are rate-limited resources.

### Running Services

| Service | Container/Process | Port | Start mechanism | Config location |
|---|---|---|---|---|
| n8n 2.6.4 | Docker container `n8n` | 5678 | Docker (auto-restart) | `~/n8n/docker-compose.yml`, `~/n8n/n8n_data/` |
| ChromaDB v0.5.20 | Docker container | 8000 | Docker (auto-restart) | Do NOT upgrade — v1.x client uses /api/v2, incompatible |
| Stats Server | systemd `aadp-stats.service` | 9100 | systemd (always-on) | `~/aadp/stats-server/stats_server.py`, `~/aadp/mcp-server/.env` |
| MCP Server | Claude Code stdio subprocess | stdio | Claude Code spawns it | `~/aadp/mcp-server/server.py`, `~/aadp/mcp-server/.env` |
| Sentinel | systemd `aadp-sentinel.service` (oneshot) | — | `aadp-sentinel.timer` every 8h | `/etc/systemd/system/aadp-sentinel.{service,timer}` |
| Supabase | Remote (cihbfubghytzqrpffgcq.supabase.co) | 443 | External SaaS | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_MGMT_PAT` in .env |

### n8n docker-compose (`~/n8n/docker-compose.yml`)
```yaml
image: n8nio/n8n:latest
container_name: n8n
ports: 5678:5678
volumes: ./n8n_data:/home/node/.n8n
environment:
  N8N_HOST: n8n.thompslife.com
  WEBHOOK_URL: https://n8n.thompslife.com/
  TZ: America/Los_Angeles
extra_hosts:
  - "host.docker.internal:host-gateway"   # critical — lets n8n reach Pi services
```

The `host.docker.internal:host-gateway` extra_hosts entry is what lets n8n workflows call `http://host.docker.internal:9100` to reach the stats server.

### Stats Server systemd (`/etc/systemd/system/aadp-stats.service`)
```
Type=simple, User=thompsman
WorkingDirectory=/home/thompsman/aadp/stats-server
ExecStart=/home/thompsman/aadp/stats-server/venv/bin/python stats_server.py
Restart=always, RestartSec=5
```

### Sentinel systemd (`/etc/systemd/system/aadp-sentinel.{service,timer}`)
- **Service:** `Type=oneshot`, runs `~/aadp/sentinel/scheduler.sh`, `TimeoutStartSec=3600`
- **Timer:** `OnBootSec=2min`, `OnUnitActiveSec=8h`, `Persistent=true` (fires immediately on boot if missed)
- **Current state (2026-04-15):** Stopped and disabled — Lean Mode active

### Credentials (`~/aadp/mcp-server/.env`) — NEVER commit
Keys present (do not expose values):
- `CHROMADB_HOST`, `CHROMADB_PORT`
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_MGMT_PAT`
- `N8N_BASE_URL`, `N8N_API_KEY`
- `ANTHROPIC_API_KEY`
- `GITHUB_TOKEN`
- `STATS_PORT` (default 9100)

---

## 2. Data Flow Architecture

### Autonomous Mode Session (sentinel)

```
aadp-sentinel.timer (8h)
  → aadp-sentinel.service
    → scheduler.sh
      1. Read .env for SUPABASE_URL, SUPABASE_SERVICE_KEY
      2. Supabase REST: GET work_queue?status=eq.pending&order=priority.asc&limit=1
      3. PATCH work_queue: set status=claimed, claimed_at, assigned_agent=sentinel
      4. POST http://localhost:5678/webhook/inject-context
           → lesson_injector (n8n workflow MFmk28ijs1wMig7h)
           → stats_server /inject_context_v3 (via webhook body)
           → ChromaDB: 3-5 semantic queries across collections
           → Supabase RPC: increment_lessons_applied_by_id
           → returns context_block (PRE-LOADED CONTEXT markdown)
      5. Assemble: context_block + wake_prompt.md → ENRICHED_PROMPT temp file
      6. claude -p --dangerously-skip-permissions --max-turns 200
           --system-prompt-file disk_prompt.md
           < ENRICHED_PROMPT
      7. After session exit:
           POST /webhook/5x6G8gFlCxX0YKdM/webhook/session-health-report
           (session_health_reporter writes GitHub artifact)
```

### Lean Mode Session (TCA → lean_runner)

```
Telegram: /oslean
  → TCA (kddIKvA37UDw4x6e) — long-poll Telegram
    → /trigger_lean command matched
    → POST http://host.docker.internal:9100/trigger_lean
      → stats_server /trigger_lean
        → if /tmp/oslean.lock exists: return {"status":"locked"}
        → subprocess: ~/aadp/sentinel/lean_runner.sh
          1. git -C claudis pull
          2. Read DIRECTIVES.md — if "Run: B-NNN" format, resolve from BACKLOG.md
          3. POST http://localhost:5678/webhook/inject-context (task_type=general, 25s timeout)
          4. Assemble: context_block + LESSON TRACKING + "Read LEAN_BOOT.md" → PROMPT_FILE
          5. claude -p --dangerously-skip-permissions --max-turns 200 < PROMPT_FILE
          6. On completion: Telegram via /webhook/telegram-quick-send
```

### When Claude Code reads LEAN_BOOT.md
Claude Code's startup sequence (triggered by reading LEAN_BOOT.md):
1. git pull claudis → abort if fails
2. cp claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md
3. Read PROTECTED.md
4. Read DIRECTIVES.md → resolve B-NNN pointer if needed
5. Read CATALOG.md → match skills
6. Read CONTEXT.md
7. Read TRAJECTORY.md
8. Execute directive

### When an agent writes a lesson
```
Session produces lesson
  → memory_add MCP tool
      → ChromaDB HttpClient.add(collection=lessons_learned, doc_id=uuid, document, metadata)
  → supabase_exec_sql or sb_post
      → Supabase lessons_learned INSERT (title, content, category, chromadb_id=uuid)
Both stores must be written. chromadb_id links the two records.
```

### When lesson_injector fires
```
POST /webhook/inject-context (lesson_injector workflow MFmk28ijs1wMig7h)
  → Webhook node receives {task_type, task_id, description}
  → HTTP Request → POST http://host.docker.internal:9100/inject_context_v3
    (v3 is current; v2 endpoint preserved for backward compat)
    → Haiku intent expansion: 3-4 specific search phrases
    → Per-task-type collection routing (see _V3_TASK_ROUTING table)
    → ChromaDB subprocess queries (mcp-server venv, chromadb 0.5.20)
    → Staleness penalty on lessons >4 weeks old (+0.05/week)
    → zero_applied wildcard: 2 random never-retrieved lessons injected
    → Supabase RPC: increment_lessons_applied_by_id(lesson_ids)
    → Returns JSON: {context_block, lesson_ids, confidence_tier, ...}
  → n8n returns context_block to scheduler.sh caller
```

### n8n execution monitoring
```
agent_health_monitor (w5vypq4vb2rSrwdl) — webhook triggered
  Branch 1: active agents
    → GET /api/v1/executions?workflowId={id} for each active agent
    → flag agents with consecutive errors ≥1, auto-pause ≥3
  Branch 2: building/sandbox agents
    → Supabase: SELECT stale agents (status=building/sandbox, updated_at > 7 days)
    → experimental_outputs: INSERT stale_build_scan
    → sandbox_notify Telegram alert
  Guard node: returns sentinel item when input empty (prevents array-chain-halt)
```

---

## 3. MCP Server (`~/aadp/mcp-server/server.py`)

Transport: stdio (stdin/stdout). Claude Code spawns it as a subprocess per session.

Startup self-test: ChromaDB heartbeat → Supabase REST GET / → n8n GET /workflows.

The FastAPI stats sidecar (port 9100, exposing `/system_status` and `/healthz`) is defined in server.py but **not running there** — the real stats server is the standalone `stats_server.py` managed by systemd. The server.py sidecar code appears to be legacy or not reached.

### All Exposed Tools

**Memory (ChromaDB)**

| Tool | What it does |
|---|---|
| `memory_search` | Semantic query on a collection. Logs to audit_log (fire-and-forget) and retrieval_log. Params: query, collection, n_results (default 5), where_filters |
| `memory_add` | Add document to collection. Generates UUID doc_id if not provided. Handles metadata-as-string defensive parsing. |
| `memory_delete` | Delete document by doc_id from collection. |
| `memory_list_collections` | List all ChromaDB collections with counts. |

**Prompts (Supabase `agent_prompts` table)**

| Tool | What it does |
|---|---|
| `prompt_get` | Fetch active prompt for agent_name (is_active=true, highest version) |
| `prompt_update` | Deactivate old versions, INSERT new version, audit_log entry |
| `prompt_history` | All versions for agent_name ordered by version desc |
| `prompt_rollback` | Deactivate all, activate target version |

**Config (Supabase `agent_config` table)**

| Tool | What it does |
|---|---|
| `config_get` | Fetch config record for agent_name |
| `config_set` | UPSERT config with on_conflict=agent_name |

**Agent Registry (Supabase `agent_registry` table)**

| Tool | What it does |
|---|---|
| `agent_register` | INSERT new agent, audit_log entry |
| `agent_update` | PATCH agent by agent_name, audit_log entry |

**Error Log (Supabase `error_logs` table)**

| Tool | What it does |
|---|---|
| `error_log_query` | Filter by workflow_id, resolved, hours_back (default 48) |
| `error_log_resolve` | PATCH resolved=true, resolution_notes, resolved_at |

**Ideas (Supabase `ideas` table)**

| Tool | What it does |
|---|---|
| `idea_capture` | INSERT idea with content, tags (array), source, status=new |
| `idea_list` | Filter by status, tags (cs. array overlap), limit |

**Work Queue (Supabase `work_queue` table)**

| Tool | What it does |
|---|---|
| `work_queue_add` | INSERT task: task_type, input_data, priority, created_by, status=pending |
| `work_queue_query` | Filter by status, task_type, assigned_agent. Ordered by priority.asc, created_at.asc |
| `work_queue_update` | PATCH by task_id: status, output_data, error_message, assigned_agent. Sets completed_at on complete/failed. |

Valid work_queue statuses: `pending`, `claimed`, `processing`, `complete`, `failed`

**Audit Log (Supabase `audit_log` table)**

| Tool | What it does |
|---|---|
| `audit_log_query` | Filter by actor, action, hours_back (default 24), limit (default 50) |

**Session Notes (Supabase `session_notes` table)**

| Tool | What it does |
|---|---|
| `session_notes_save` | INSERT note: content, category, consumed=false |
| `session_notes_load` | GET unconsumed notes. consume=true marks them consumed (default false — safe read) |

**Workflows (n8n REST API)**

| Tool | What it does |
|---|---|
| `workflow_list` | GET /api/v1/workflows, optional active filter |
| `workflow_get` | GET /api/v1/workflows/{id} — full JSON |
| `workflow_create` | POST /api/v1/workflows |
| `workflow_update` | PUT /api/v1/workflows/{id} — strips versionId, active, id before sending |
| `workflow_activate` | POST /api/v1/workflows/{id}/activate |
| `workflow_deactivate` | POST /api/v1/workflows/{id}/deactivate |
| `workflow_execute` | **Always raises ValueError** — n8n public API has no execution endpoint. Use work_queue instead. |
| `execution_list` | GET /api/v1/executions, optional workflowId filter |
| `execution_get` | GET /api/v1/executions/{id} |

**System**

| Tool | What it does |
|---|---|
| `system_status` | psutil: cpu_percent, memory, disk, temperature (Pi thermal sensor), uptime |
| `service_status` | `docker ps` — checks if service container is running, returns port |
| `logs_fetch` | `docker logs --tail N container` |

**DDL**

| Tool | What it does |
|---|---|
| `supabase_exec_sql` | POST to Management API `api.supabase.com/v1/projects/{ref}/database/query`. Requires SUPABASE_MGMT_PAT. Note: Management API is Cloudflare-blocked from Pi for most operations — this endpoint specifically works for DDL. For CRUD data ops always use PostgREST. |

**Composite**

| Tool | What it does |
|---|---|
| `developer_context_load` | Concurrent: agent_registry + pending work_queue + unresolved errors + session_notes (cap 5) + claude_code_master config + system_status. master_prompt and recent_work excluded (on-demand via individual tools). |

**Key implementation details:**
- n8n API key is re-read from .env on every call (`get_n8n_headers()`) — key rotations require no server restart
- All Supabase ops use PostgREST (`SUPABASE_URL/rest/v1/`) with service key
- ChromaDB client is lazily created and shared (`chromadb.HttpClient`, port from .env)
- `memory_search` fires `log_retrieval()` as `asyncio.ensure_future` — never blocks search
- `retrieval_log` accumulates query-document pairs for eventual adapter training (goal: 1500 labeled pairs → +70% retrieval accuracy)

---

## 4. Stats Server (`~/aadp/stats-server/stats_server.py`)

FastAPI app, 3205 lines, systemd-managed, port 9100. Callable from n8n via `http://host.docker.internal:9100`. Claude Code calls it at `http://localhost:9100`.

ChromaDB access: stats_server spawns subprocesses using `mcp-server/venv/bin/python` with inline scripts. It cannot import chromadb directly because it runs in its own venv.

### All Endpoints

**System**

| Endpoint | Method | What it does |
|---|---|---|
| `/system_status` | GET | psutil snapshot: cpu, memory, disk, temperature, uptime |
| `/healthz` | GET | `{"status": "ok"}` |

**Sentinel Control**

| Endpoint | Method | What it does |
|---|---|---|
| `/trigger_sentinel` | GET/POST | Checks `systemctl is-active aadp-sentinel.service`. If active+mid-task: returns `{"status":"mid_task"}` with task info (unless `?force=1`). Else: `sudo systemctl start --no-block aadp-sentinel.service` |
| `/trigger_lean` | (inferred from lean_runner.sh) | TCA calls this to start lean sessions |

**GitHub Operations**

| Endpoint | Method | What it does |
|---|---|---|
| `/gh` | GET | Dispatch `cmd` + `args` to `gh_cmd_dispatch()`. Commands: gh_status, gh_becoming, gh_attempts, gh_log, gh_review, gh_keep, gh_redirect, gh_close, gh_report |

`gh_cmd_dispatch` operates on `~/aadp/claudis` repo. git pull/push use stored credentials (no `gh` CLI — uses GitHub REST API via GITHUB_TOKEN).

**Data Operations**

| Endpoint | Method | What it does |
|---|---|---|
| `/append_experiment` | POST | Append content to `experiments/{path}`, git add+commit+push. Body: `{path, content}` |
| `/write_experiment` | POST | Write session artifact to `experiments/sessions/{filename}`, commit+push. Filename must match `[\w\-]+\.md`. |
| `/get_outputs` | GET | Fetch `experimental_outputs` from Supabase for agent_name. Wrapped in `{outputs, count}` (prevents n8n array-unwrap). Params: agent_name, limit, exclude_type |
| `/get_audit` | GET | Fetch `audit_log` for actor=agent_name. Wrapped object. Params: agent_name, limit |

**Research**

| Endpoint | Method | What it does |
|---|---|---|
| `/run_daily_research` | POST | Fetch arXiv + HN for 3 rotating topics. Haiku scores relevance ≥7/10. Write to experiments/research/ (GitHub) + ChromaDB research_findings + Supabase research_papers. Also fetches Reddit r/ClaudeAI + Anthropic GitHub releases (Anthropic signals). Idempotent: skips if today's file exists (override with force=true). |
| `/run_research_synthesis` | POST | Weekly synthesis of ChromaDB research_findings over 21-day window. Delegates all logic. Two modes: accumulation (runs 1-3) / synthesis (run 4+). Idempotency guard (skips if ran <5 days ago). Calls Sonnet for synthesis. Writes to experimental_outputs + Telegram digest. |
| `/get_research_window` | POST | Return ChromaDB research_findings filtered by date. Body: `{days_back, collection}`. Returns `{entries, count, date_range}` |

**ChromaDB Proxy**

| Endpoint | Method | What it does |
|---|---|---|
| `/memory_query` | POST | Semantic query via subprocess. Body: `{collection, query_text, n_results, distance_threshold}`. Returns `{results, count}` wrapped (n8n safety). |

**Lesson Injection**

| Endpoint | Method | What it does |
|---|---|---|
| `/inject_context_v2` | POST | Intent-expanded context with tiered memory (v2.1). Haiku expansion → 5 collections (lessons, errors, patterns, session_memory, research). Staleness penalty. 2000-token cap. Increments times_applied. |
| `/inject_context_v3` | POST | **Current version (v3.1).** Task-type routing + confidence signal + zero_applied wildcards. Same interface as v2 plus: routing_applied, confidence_tier, min_distance, retrieve_recommendation. See routing table below. |
| `/lessons_applied` | POST | Increment `times_applied` for lesson IDs. Called by n8n after lesson injection. Two RPCs: `increment_lessons_applied_by_id` (chromadb_id match) and `increment_lessons_applied` (content match fallback). |

### inject_context_v3 Routing Table

```python
_V3_TASK_ROUTING = {
    "agent_build":      [lessons, error_patterns, reference_material, session_memory, research_findings],
    "research_cycle":   [research_findings, lessons, reference_material, session_memory],
    "explore":          [lessons, session_memory, research_findings],
    "self_diagnostic":  [self_diagnostics, error_patterns, lessons],
    "directive":        [lessons, error_patterns, reference_material, session_memory],
    "gh_weekly_search": [research_findings],
    "gh_report":        [session_memory, lessons],
    "gh_task":          [lessons, reference_material],
    "agent_control":    [lessons, error_patterns],
    "agent_test":       [lessons, error_patterns, reference_material],
    # unknown → all 5 tiers
}
```

Confidence signal thresholds: `min_dist < 0.8` → high/retrieve; `0.8–1.1` → medium/retrieve; `1.1+` → low/reason_with_context; no results → none/reason.

Zero-applied wildcard: 2 random lessons with `times_applied=0 AND created_at < 3 days ago AND chromadb_id IS NOT NULL` are appended as "Uncirculated Lessons" section (trimmed first if budget tight). This ensures eventual coverage of niche lessons that never match semantic queries.

---

## 5. Agent Fleet

**Lifecycle:** `building` → `sandbox` → (behavioral_health_check + 4-Pillars evaluation) → `active` OR `retired/paused`

**~25 active + sandbox agents** as of 2026-04-14. Full source at `~/aadp/claudis/agents/`.

### Production Agents

| agent_name | workflow_id | trigger | key behavior |
|---|---|---|---|
| telegram_command_agent | kddIKvA37UDw4x6e | Telegram long-poll | Routes /commands → work_queue or webhooks. **PROTECTED — never modify without explicit approval.** |
| daily_briefing_agent | 1YaIxHK7kqARgaja | cron 0 14 * * * (6AM Pacific) | Daily digest: system health, agent status, errors, work queue |
| weather_agent | F3khynqQBUXSnadu | GET /webhook/weather | Open-Meteo forecast for CA |
| wiki_attention_monitor | IYaj3zv9xj79h9jg | cron 0 15 * * * (7AM Pacific) | Wikimedia pageview velocity spikes → Haiku clusters → Telegram |
| serendipity_engine_prod | ROhfvqO3yJW6j955 | cron 30 15 * * * | Wikipedia On This Day → Haiku synthesis → Telegram |
| github_issue_tracker | F2lRufWUOXAGv5GB | GET /webhook/github-issue-tracker | GitHub API scan for open issues >3 days unactioned |
| morning_briefing | xt8Prqvi7iJlhrVG | /webhook/morning-briefing | No LLM. Work queue + agent counts + system health Telegram |
| behavioral_health_check | kdzJPyZtchNA3Seq | GET /webhook/behavioral-health-check | Last 10 n8n executions → Haiku 0-10 reliability score + recommendation |
| agent_health_monitor | w5vypq4vb2rSrwdl | /webhook/agent-health-monitor | Two branches: active agent error scan + building/sandbox stale scan |
| research_synthesis_agent | JUBCbXJe3TwwpB2T | /webhook/research-synthesis | Delegates to stats_server /run_research_synthesis. Idempotency guard (<5 days). |
| arxiv_aadp_pipeline | bZ35VinkRjRT7gYi | /webhook/arxiv-aadp | arXiv preprints Mon/Wed/Fri. Haiku scores AADP implications. Writes research_papers + research_findings. |
| github_weekly_search | — | Sunday 6AM UTC | GitHub API search for MCP/agent repos |

### Platform Infrastructure Agents

| agent_name | workflow_id | trigger | key behavior |
|---|---|---|---|
| lesson_injector | MFmk28ijs1wMig7h | POST /webhook/inject-context | Called by scheduler.sh before every claude -p. Calls /inject_context_v3. |
| session_health_reporter | 5x6G8gFlCxX0YKdM | POST /webhook/session-health-report | After every sentinel session. No Anthropic API. Commits to experiments/sessions/ on GitHub. |
| daily_research_scout | xNbmcFrNvqbmhlJW | cron 14:00 UTC + /webhook | Delegates to stats_server /run_daily_research |
| autonomous_growth_scheduler | Lm68vpmIyLfeFawa | every 6h | If work_queue empty: insert explore/agent_build/research_cycle task (rotating). **Currently deactivated (Lean Mode).** |
| usage_stats | NeVI0bEB6WsJEf6I | GET /webhook/usage-stats | On-demand Telegram: Claudis state, heartbeat, agent counts |
| agent_evaluator_4pillars | kQ5OALBwexLQS7in | GET /webhook/evaluate-agent | Haiku 4-pillar scoring: behavior_consistency, output_quality, reliability, integration_fit |

### Sandbox Agents
- `architecture_review` (7mVc61pDCIObJFos) — biweekly research-to-architecture review, next promotion candidate

### Retired
- `haiku_self_critic` (1v0JFPdtVte5MJrO) — deactivated
- `serendipity_engine` (ToMG7Y5hkp9UlyJM) — superseded by prod version

### TCA Command Routing
TCA (`kddIKvA37UDw4x6e`) handles all Telegram commands. Key commands:
- `/oslean` → POST `host.docker.internal:9100/trigger_lean` → lean_runner.sh
- `/wake` → trigger_sentinel
- `/weather`, `/wiki`, `/usage`, `/gh_issues`, `/health_check`, `/evaluate` → route to respective webhook
- `/approve`, `/reject` → inbox approval flow (PATCH inbox by `id=eq.{inbox_id}`)
- `/gh_status`, `/gh_log`, etc. → GET `host.docker.internal:9100/gh?cmd=...`

---

## 6. Database Schema

### Active Tables (queried in production)

**`work_queue`**
- id (uuid PK), task_type (text), status (text, default pending), priority (integer, default 3)
- assigned_agent, input_data (jsonb), output_data (jsonb), created_by
- created_at, claimed_at, completed_at, error_message
- Valid statuses: `pending`, `claimed`, `processing`, `complete`, `failed`
- Priority: 1=normal, 2=high, 3=critical (INTEGER — not strings)
- Reads: sentinel scheduler.sh, developer_context_load
- Writes: autonomous_growth_scheduler, TCA command routing, Claude Code via MCP

**`agent_registry`**
- id (uuid), agent_name (text, unique), display_name, agent_type, description, status (default building)
- input_types/output_types/data_sources (text[]), schedule, workflow_id, performance_metrics (jsonb)
- protected (bool), telegram_command, created_at, updated_at
- Valid statuses: `active`, `paused`, `retired`, `building`, `broken`, `sandbox`
- Reads: developer_context_load, behavioral_health_check, agent_health_monitor
- Writes: agent_register/agent_update MCP tools

**`lessons_learned`**
- id (uuid), title, category, content, confidence (float, default 0.5), times_applied (int, default 0)
- source (default sentinel), created_at, updated_at, chromadb_id (text)
- `chromadb_id` links to ChromaDB document. NULL = invisible to semantic search.
- Reads: lesson_injector, wisdom-review, diagnose
- Writes: memory_add (via session) + lessons_learned INSERT (dual-store rule)

**`session_notes`**
- id (uuid), content, category (default todo), created_at, consumed (bool, default false)
- Valid categories: `todo`, `observation`
- Reads: session_notes_load MCP tool (cap 5 in developer_context_load)
- Writes: session_notes_save MCP tool, session close ritual

**`audit_log`**
- id (uuid), actor, action, target, details (jsonb), timestamp
- Written by: every MCP tool operation (fire-and-forget, never blocks)

**`error_logs`** (note: plural, not `error_log`)
- id (uuid), workflow_id, workflow_name, node_name, error_type, error_message, execution_id
- timestamp, resolved (bool, default false), resolution_notes, resolved_by, resolved_at

**`experimental_outputs`**
- id, agent_name, experiment_id, output_type, content (jsonb), confidence, promoted, reviewed_by_bill, created_at, api_usage (jsonb)
- Written by: behavioral_health_check, agent_evaluator_4pillars, wiki_attention_monitor, etc.

**`agent_prompts`**
- id, agent_name, prompt_text, version (int), is_active (bool), created_at, created_by, change_notes
- Versioned. Only one active per agent_name.

**`agent_config`**
- id, agent_name (unique), model (default claude-haiku-4-5-20251001), temperature (default 0.3), max_tokens (default 1024), metadata (jsonb), updated_at

**`retrieval_log`**
- id, query, collection, doc_id, distance, was_relevant (bool, nullable), session_id, created_at
- Written by: memory_search MCP tool (fire-and-forget via log_retrieval())
- Purpose: training data for ChromaDB linear adapter (goal: 1500 labeled pairs)

**`research_papers`**
- id, title, authors, abstract, publication_date, citation_count, source, source_id, url, pdf_url
- topic_tags (text[]), relevance_score, status, discovered_at, reviewed_at, notes
- component_tag, action_type, already_addressed_since, addressed_by
- Written by: arxiv_aadp_pipeline, daily_research_scout, run_daily_research

**`system_config`**
- key (text PK), value (jsonb), updated_at
- Stores: research_rotation_index, heartbeat state, etc.

**`inbox`**
- id, from_agent, message_type, subject, body, context (jsonb), status (default pending)
- bill_reply, priority, created_at, responded_at
- Valid message_types: `help_request`, `approval_request`, `recommendation`, `observation`, `question`, `alert`
- Valid statuses: `pending`, `approved`, `denied`, `deferred`, `replied`

**`capabilities`**
- id, name, category, description, confidence (default 0.5), times_used (default 0), last_used, created_at, updated_at

### Supporting Tables (present, less active)
`agent_outputs`, `daily_digests`, `data_sources`, `directives`, `environmental_observations`, `experiments`, `feedback_log`, `ideas`, `inquiry_threads`, `projects`, `refinements`, `research_evidence`, `research_questions`, `research_topics`, `resources`, `wiki_monitor_config`, `wiki_page_baselines`

---

## 7. ChromaDB Collections

All collections use the default `all-MiniLM-L6-v2` embedding model. ChromaDB v0.5.20 at localhost:8000.

**Live counts as of 2026-04-17:**

| Collection | Count | Purpose | What writes to it |
|---|---|---|---|
| `lessons_learned` | 224 | Technical lessons from sessions | Session close dual-store writes |
| `reference_material` | 173 | Architecture patterns, runbooks | Session writes |
| `research_findings` | 141 | arXiv/HN research items | run_daily_research, arxiv_aadp_pipeline |
| `session_memory` | 71 | Episodic session context | Session close writes |
| `error_patterns` | 15 | Known failure modes | Session writes |
| `self_diagnostics` | 11 | Diagnostic procedures | Session writes |
| `agent_templates` | 4 | Agent scaffolding templates | Session writes |
| `ag_research_data` | 8 | (appears to be legacy) | Unknown |

**Distance thresholds (from ENVIRONMENT.md):**
- < 0.8: high confidence match
- 0.8–1.2: review carefully
- > 1.2: weak match

**Critical gotcha:** Never include `"embeddings"` in the `include` list for bulk-get operations — causes IndexError at scale. Use `["documents", "metadatas"]` only.

**Store sync validation:** `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` — any value > 0 means lessons are invisible to semantic search. The correct sync metric is not COUNT comparison but NULL chromadb_ids.

---

## 8. Lesson System End-to-End

### Creation
Any session (autonomous or lean) can write a lesson. The close ritual requires:
1. `memory_add(collection="lessons_learned", content=..., metadata={date, category, source, permanent?})` → returns ChromaDB doc_id
2. INSERT into Supabase `lessons_learned` with chromadb_id = ChromaDB doc_id

Both writes are required. Either alone is a broken lesson.

**Writing quality:** Lead with failure mode, not tool name. "When a webhook 404s even though the workflow exists" retrieves well. "n8n Webhook URL Format" does not.

### Retrieval (inject_context_v3.1)
1. scheduler.sh / lean_runner.sh calls `POST /webhook/inject-context` before `claude -p`
2. lesson_injector workflow proxies to `POST host.docker.internal:9100/inject_context_v3`
3. stats_server:
   - Resolves task-type routing (which collections to query)
   - Expands intent via Haiku: 3-4 specific technical phrases from task_type+description
   - Queries `lessons_learned`: multi-phrase, threshold 1.4, n=8
   - Applies staleness penalty: +0.05/week beyond 4 weeks (unless metadata.permanent=true)
   - Queries other collections per routing table (single-phrase, lower thresholds)
   - Deduplicates across all collections
   - Fetches 2 zero_applied wildcards from Supabase (random, >3 days old, never retrieved)
   - Assembles context block with section headers and distance scores
   - Trims to 2000-token budget (cuts from bottom — research trimmed before lessons)
   - Returns context_block + confidence signal

### Injection
Context block prepended as `## PRE-LOADED CONTEXT` before the session prompt.

### Tracking
`increment_lessons_applied_by_id(lesson_ids)` Supabase RPC fires after every injection — increments `times_applied` for each retrieved lesson including wildcards.

**Quality signal (added 2026-04-17):** Session artifacts now include a "Lessons Applied" section listing lesson IDs that actually influenced decisions. This tracks application rate separately from retrieval rate.

### Current Health
- 224 lessons in ChromaDB, 224 in Supabase (gap = 0 as of 2026-04-13 sync repair)
- zero_applied = 126 as of 2026-04-15, trending down. Validation: stay below 130 for 3 consecutive sessions.

---

## 9. Session Mechanics

### Autonomous Mode (`scheduler.sh`)

```bash
# Configuration
MAX_TURNS=200
STALE_LOCK_SECONDS=7200 (2h)
LOG_FILE: ~/aadp/logs/sentinel_YYYYMMDD.log

# Lock management
/tmp/sentinel.lock — PID file, stale after 2h

# Task claiming
1. Supabase REST: GET work_queue (pending, priority.asc, limit=1)
2. PATCH: status=claimed, claimed_at, assigned_agent=sentinel
3. On rate-limit exit: PATCH back to pending (task preserved for next wake)

# Lesson injection
POST localhost:5678/webhook/inject-context → 10s timeout
context_block prepended to wake_prompt.md

# Claude invocation
claude -p --dangerously-skip-permissions --max-turns 200 \
  --system-prompt-file disk_prompt.md \
  < ENRICHED_PROMPT

# Post-session
POST /webhook/session-health-report (fire-and-forget, non-fatal)
Log rotation: keep 7 days

# System prompt: ~/aadp/sentinel/disk_prompt.md (v29, ~407 lines, ~3500 tokens)
# Wake prompt: ~/aadp/sentinel/wake_prompt.md
```

### Lean Mode (`lean_runner.sh`)

```bash
# Configuration
MAX_TURNS=200, TIMEOUT_SECS=7200 (2h)
LOCK_FILE=/tmp/oslean.lock

# Sequence
1. git -C claudis pull (abort+Telegram if fails)
2. Read DIRECTIVES.md:
   - If "Run: B-NNN": awk-extract card from BACKLOG.md
   - Else: use DIRECTIVES.md content directly
3. POST /webhook/inject-context (task_type=general, 25s timeout, graceful fail)
4. Assemble: context_block + LESSON TRACKING instruction + "Read LEAN_BOOT.md"
5. timeout 7200 claude -p --dangerously-skip-permissions --max-turns 200 < PROMPT_FILE
6. Telegram: complete/timeout/error notification

# No system-prompt-file — LEAN_BOOT.md serves as the operational frame
# LEAN_BOOT.md triggers the full startup sequence upon Claude reading it
```

### Close Ritual (lean sessions)
Write artifact to `~/aadp/claudis/sessions/lean/YYYY-MM-DD-descriptor.md`:
```
# Session: [date] — [descriptor]
## Directive
## What Changed
## What Was Learned
## Lessons Applied   ← lesson IDs that influenced decisions
## Unfinished
```
Commit: `session artifact: YYYY-MM-DD-descriptor`

### Close Ritual (autonomous sessions)
10-step skill (`/close-session`):
1. Close attempt branches
2. Commit agents
3. Update TRAJECTORY.md
4. Archive prompt version
5. Commit session artifact with capability delta
6. Check wisdom-review cadence
7. Write lessons to Supabase + ChromaDB
8. Update capabilities counters
9. Write session narrative to ChromaDB session_memory
10. Write handoff note with intent queue check to Supabase session_notes

---

## 10. Git and File Conventions

### Repo: `thompsmanlearn/claudis` → `~/aadp/claudis/`

Git uses stored credentials. `gh` CLI not installed — use GitHub REST API via GITHUB_TOKEN if needed.

```
claudis/
  agents/
    INDEX.md          — lightweight manifest, read at session start
    production/       — active agent workflow JSONs (credentials replaced with {{PLACEHOLDER}})
    sandbox/
    retired/
    critics/
  architecture/
    decisions/        — ADRs (inject-context-v3.md, arch-review-backward-loop-fix.md, etc.)
    ENVIRONMENT.md    — operational facts, API gotchas, endpoint catalog. Append-only.
    BECOMING.md       — aspirations/redirects from Bill via /gh_redirect
  sessions/
    lean/             — lean session artifacts (YYYY-MM-DD-descriptor.md)
    monthly/
    YYYY-MM-DD-HHMM.md — autonomous session artifacts
  skills/
    CATALOG.md        — skill routing table
    PROTECTED.md      — resources requiring explicit approval
    agent-development/SKILL.md
    system-ops/SKILL.md
    communication/SKILL.md
    research/SKILL.md
    triage/SKILL.md
  experiments/
    research/         — daily_research_scout outputs (YYYY-MM-DD.md + INDEX.md)
    sessions/         — session_health_reporter outputs
  CONTEXT.md          — system facts, bootstrap context
  CONVENTIONS.md      — operational procedures
  TRAJECTORY.md       — destinations + active vectors + operational state
  DIRECTIVES.md       — Bill's standing instructions (only Bill edits). Can contain "Run: B-NNN" pointer.
  BACKLOG.md          — lean session card queue, referenced for B-NNN pointers. Cards B-001 through B-021 archived 2026-04-16.
  LEAN_BOOT.md        — lean mode startup protocol
  COLLABORATOR_BRIEF.md, INQUIRIES.md — supporting docs
  roblox/             — Lune pipeline artifacts
  attempts/           — attempt branch close notes
  archive/, processed/, docs/, experiments/ — supporting dirs
```

### DIRECTIVES.md and BACKLOG.md — How Lean Tasks Are Specified

`DIRECTIVES.md` holds the current lean session task in one of two forms:

**Form 1 — Inline prose.** The full directive written directly. Claude Code reads and executes it.

**Form 2 — Card pointer.** A single line:
```
Run: B-025
```
Claude Code reads `BACKLOG.md`, finds the card with that ID, and executes it. `lean_runner.sh` also extracts the first 300 characters of the card description for lesson injection before Claude starts.

**Context cost of BACKLOG.md:** The full file is loaded every time the pointer form is used. Cards should be archived periodically once completed — the archive note at the top of BACKLOG.md is load-bearing, not cosmetic.

### Backlog Card Format

All cards follow this structure. Opus writes them; Claude Code executes them.

```markdown
## B-NNN: Short descriptive title

**Status:** ready
**Depends on:** B-MMM      ← omit if none

### Goal
One paragraph. What this session should accomplish and why it matters now.
Not how — just what and why.

### Context
Background Claude Code needs before starting. Reference prior sessions,
system state, design constraints, known gotchas relevant to this task.
Enough to execute without back-and-forth — not a tutorial.

### Done when
- Specific verifiable criterion (file at path, curl response, DB row)
- Specific verifiable criterion
- Commit pushed to main

### Scope
Touch: explicit list of files, tables, workflows, services Claude Code may modify
Do not touch: explicit list of things off-limits this session
```

**Writing rules:**
- **Goal**: what and why, not how. One paragraph.
- **Context**: what Claude Code won't find by reading the code — prior decisions, active gotchas, related work from other sessions.
- **Done when**: every item must be checkable. "Works correctly" is not a criterion. "curl localhost:9100/healthz returns `{\"status\":\"ok\"}`" is.
- **Scope / Do not touch**: explicit guardrails prevent scope creep. Name the specific things that are off-limits.
- **Two-hour ceiling**: if a card can't reasonably complete in one lean session, split it. Incomplete sessions leave the system in an unknown state and produce no artifact.
- **Card numbers are sequential** and never reused. Archive completed cards in batches; add a note at the top of BACKLOG.md indicating the archived range.

### Branching Convention
- Main work: `main` branch
- Non-trivial builds: `attempt/description` branch before starting
- Commit outcome on attempt branches (including failures)
- Close attempt branches at session end (`/close-session` step 1)

### What Gets Committed
- Sessions commit to `sessions/lean/` or `sessions/YYYY-MM-DD-HHMM.md`
- Research writes to `experiments/research/`
- Stats server changes go to disk only (NOT currently in git — fragility noted below)
- Bill commits DIRECTIVES.md directly

---

## 11. Key Configuration Files to Recreate

| File | Purpose | Notes |
|---|---|---|
| `~/aadp/mcp-server/.env` | All credentials | Never commit. Keys: CHROMADB_HOST/PORT, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_MGMT_PAT, N8N_BASE_URL, N8N_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN, STATS_PORT |
| `/etc/systemd/system/aadp-stats.service` | Systemd unit for stats server | Type=simple, ExecStart=mcp-server venv python stats_server.py, Restart=always |
| `/etc/systemd/system/aadp-sentinel.service` | Systemd unit for sentinel (oneshot) | ExecStart=scheduler.sh, TimeoutStartSec=3600, WorkingDirectory=mcp-server |
| `/etc/systemd/system/aadp-sentinel.timer` | Timer — fires every 8h | OnUnitActiveSec=8h, Persistent=true |
| `~/n8n/docker-compose.yml` | n8n container | image n8nio/n8n:latest, port 5678, extra_hosts host.docker.internal |
| `~/.claude/` | Claude Code settings | MCP server config pointing to server.py |
| n8n credential: `y4YfKWpm20Z9sw7G` | Telegram bot ("Life OS Telegram Bot") | Bill's chat_id: 8513796837 |

### n8n Credential IDs
- Telegram credential ID: `y4YfKWpm20Z9sw7G`
- Anthropic API: stored in n8n credential store (also in .env for stats_server)

### Supabase RPC Functions (must exist for lesson system)
```sql
-- Required: increment times_applied by chromadb_id
CREATE FUNCTION increment_lessons_applied_by_id(lesson_ids text[]) ...

-- Required: increment by content (legacy fallback)  
CREATE FUNCTION increment_lessons_applied(lesson_contents text[]) ...
```

These are called by inject_context_v3 and /lessons_applied endpoint. If they're missing, the system degrades gracefully (tries, fails silently) but tracking is broken.

---

## 12. Known Gaps, Fragilities, and Undocumented Dependencies

### Fragilities

**stats_server.py is now in git** (added 2026-04-17, commit 56ba358). Production file committed to `claudis/stats-server/stats_server.py` exactly as-is. Systemd unit and Supabase RPC DDL also committed. This fragility is closed.

**n8n API key expires silently.** The key in .env is read fresh on every call (fixed 2026-04-15), but the key itself has a TTL. When it expires, all workflow management fails. No monitoring exists for key expiration. The 2026-04-14 session was blocked by an expired key discovered by accident.

**No Telegram alert for sentinel failures.** `send_telegram_alert()` in scheduler.sh logs to file but doesn't actually send a Telegram message — the function body just calls `log()`. Sentinel failures are only discoverable by checking logs manually.

**ChromaDB version pinned at v0.5.20.** Client and server must match exactly. `chromadb==0.5.20` in mcp-server venv. v1.x client uses /api/v2 API path — incompatible. Do not upgrade without testing both sides.

**stats_server ChromaDB access uses subprocess.** stats_server cannot import chromadb directly (different venv). Every ChromaDB operation spawns a Python subprocess using `mcp-server/venv/bin/python`. This adds ~200-500ms latency per ChromaDB call in stats_server.

**Array column syntax must use cast form.** `ARRAY['a','b']` in SQL fails silently in Supabase Management API. Always use `'{"a","b"}'::text[]`. Failing to use this produces no error and no inserted row.

**Management API Cloudflare-blocked from Pi.** `api.supabase.com` returns 403 for most operations from the Pi. The DDL endpoint (`/v1/projects/{ref}/database/query`) works. All CRUD must go through PostgREST (`SUPABASE_URL/rest/v1/`).

**workflow_execute MCP tool always fails.** n8n public API has no execution endpoint. The MCP tool raises ValueError. To run a workflow: ensure it has a webhook trigger, activate it, POST to webhook. Or use work_queue for schedule-triggered workflows.

**n8n webhooks need restart after activation.** Newly-activated workflows return 404 until n8n restarts (`docker restart n8n`). For sandbox testing without restart: write directly to Supabase via PostgREST.

**Prompt caching only works on Sonnet 4.6+.** Haiku 4.5 silently ignores `cache_control` (returns cache_creation_input_tokens: 0, no error). Sonnet 4.6 requires ~2048 tokens in the system block to actually cache.

### Undocumented Dependencies

**Supabase RPC functions.** The RPCs `increment_lessons_applied_by_id` and `increment_lessons_applied` are called by inject_context_v3 and stats_server /lessons_applied. Their DDL is not checked into the repo (see `~/aadp/sentinel/supabase_tables.sql` for original schema, but RPCs may be more recent).

**n8n credential IDs hardcoded in workflows.** All workflow JSONs in `agents/production/` have credentials replaced with `{{CREDENTIAL_NAME}}` placeholders. Recreating on a fresh n8n instance requires recreating credentials and updating all placeholder references.

**Telegram chat_id hardcoded.** Bill's chat_id `8513796837` is in scheduler.sh, lean_runner.sh, stats_server.py, and many n8n workflow payloads.

**`/webhook/telegram-quick-send` assumed always active.** Both scheduler.sh and lean_runner.sh call this webhook for notifications. If TCA is deactivated or the webhook changes, all Telegram notifications from sentinel/lean sessions silently fail.

**Bill's Roblox account needed for pipeline.** Lune v0.10.4 is installed at `/usr/local/bin/lune` and can produce valid .rbxl files (verified: 888 bytes, magic bytes confirmed). Full pipeline completion requires a Roblox account + Studio session (Windows/Mac, ~15 minutes) to create a base game and get Universe ID + Place ID for Open Cloud API. This is blocked on Bill — not an automated task.

---

## 13. Where We're Going — Anvil Dashboard

*Captured 2026-04-17. Status: evaluating. Not yet a backlog card.*

### The Problem Anvil Solves

The current interface is Telegram-only. That works for alerts and commands but has real limits: no visual overview of system state, no way to browse the resource inbox comfortably, no interactive session control beyond typed commands, and no phone-native capabilities (camera, geolocation, push notifications). The monitoring agents (cosmos_report, daily_briefing_agent, session_health_reporter) produce output but there's no good place to look at it.

### What Anvil Is

Anvil (anvil.works) is a Python-only web app platform. The key capability for AADP is **Uplink**: a persistent websocket connection that the Pi initiates outbound to Anvil's cloud. Once connected, Anvil's server-side Python can call functions defined in the Pi-side uplink script directly.

Why this matters for a Pi behind a home router:
- No port forwarding required
- No reverse proxy or nginx config
- Auto-reconnects on failure
- The Pi is always the initiator — firewall-friendly

The resulting Anvil web app is accessible from any browser and installable as a PWA on a phone.

### Proposed Architecture

```
Pi uplink script (systemd service)
  ↕ websocket (outbound from Pi)
Anvil cloud
  ↕
Anvil web app (browser / phone PWA)
```

The uplink script is a thin wrapper — it doesn't contain business logic, just exposes existing infrastructure:

| Uplink function | Delegates to |
|---|---|
| `get_system_status()` | stats_server `/system_status` |
| `get_agent_fleet()` | Supabase `agent_registry` |
| `get_work_queue()` | Supabase `work_queue` |
| `get_session_notes()` | Supabase `session_notes` |
| `get_resource_inbox()` | Supabase `resources` |
| `approve_inbox_item(id)` | Supabase `inbox` PATCH |
| `trigger_lean_session()` | stats_server `/trigger_lean` |
| `write_directive(text)` | claudis git → DIRECTIVES.md |

### Phone Capabilities Anvil Unlocks

Anvil apps running in the browser on a phone can access:
- **Camera** — Bill could photograph something and route the image into the system
- **Geolocation** — location-aware agents (weather, local context)
- **Web push notifications** — replace Telegram alerts with native phone notifications

### Planned First Milestone

Read-only dashboard:
- System status (CPU, RAM, disk, temp)
- Agent fleet health (active count, any paused/broken)
- Work queue (pending tasks)
- Last 5 session notes

This proves the uplink architecture before adding interactive controls. No writes, no session launching — just visibility.

### What's Needed Before Claude Code Can Build

1. **Bill creates an Anvil account** at anvil.works (free tier)
2. **Bill prototypes the uplink connection** — installs `anvil-uplink` Python package on the Pi, runs the minimal hello-world uplink to confirm the websocket connects from behind the home router
3. **Bill shares the uplink key** (Anvil generates one per app) — goes in `.env` as `ANVIL_UPLINK_KEY`
4. **Backlog card written** once the connection is proven

Until steps 1-3 are done, Claude Code has nothing to build against. This is a Bill action.

### What Doesn't Change

The Anvil layer is additive. Telegram commands keep working. The MCP server, stats_server, n8n, and all existing agents are unchanged. Anvil is a new read/write surface on top of existing infrastructure, not a replacement.

---

*This document was written from direct inspection. Every claim traces to a file read, a SQL query result, or a live system query. As of 2026-04-17. Anvil section added 2026-04-18.*
