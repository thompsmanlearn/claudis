# Skill: Agent Development

## Purpose
Building, promoting, and retiring agents in the AADP fleet. 
Writing and versioning agent prompts. Calling external APIs and 
integrations from agents and n8n workflows. This skill covers 
the full agent lifecycle and the API patterns needed to support it.

## When to Load
- Designing, scaffolding, promoting, or retiring agents
- Writing or updating agent prompts, versioning via prompt_update
- Building or debugging n8n workflows
- Writing Supabase queries, ChromaDB operations, or Claude API 
  calls within agent context
- Connecting agents to external APIs (Telegram, GitHub, Gmail, 
  Google Calendar)

## Core Instructions

### Part 1: Agent Lifecycle

#### Before building anything
Check if it already exists:
`SELECT agent_name, status, workflow_id FROM agent_registry 
WHERE agent_name LIKE '%keyword%' AND status='active'`
Sandbox names don't always match prod names. INDEX.md Production 
table is authoritative. If the workflow exists in n8n but isn't 
linked in agent_registry, link it — don't rebuild.

#### Sandbox → Active promotion checklist
1. Pre-promotion duplicate check (above)
2. Behavioral health check passes
3. Workflow uses webhook trigger, not manual trigger (execute API 
   returns 405 for manual-trigger workflows)
4. workflow_id linked in agent_registry
5. Audit log node branches from data node, not delivery node
6. Leave sandbox workflow DEACTIVATED after testing

#### Health monitoring
n8n execution monitors are blind to building/sandbox agents 
(no workflow_id). Monitor these separately: query 
`status=in.(building,sandbox)` with `updated_at > 7 days` as 
stale threshold. Use a normalize/guard Code node 
(`runOnceForAllItems`) returning a sentinel item when input is 
empty — the empty-array bug silently kills branches otherwise.

#### When to delegate to stats server
Move logic out of n8n and into stats_server.py when: it requires 
ChromaDB subprocess calls, API keys should stay in .env not 
workflow JSON, or the endpoint needs CLI testability. Pattern: 
add endpoint to stats_server.py, replace complex n8n nodes with 
HTTP Request to `host.docker.internal:9100/your_endpoint`, keep 
schedule/webhook triggers in n8n.

### Part 2: n8n Workflow Patterns

#### Webhook setup (critical — undocumented in n8n 2.6.4)
- webhookId must be a top-level node property matching the path 
  value. Without it, n8n silently fails to register the route.
- API-created webhook URLs differ from UI-created. Never guess. 
  Look up: `SELECT webhookPath FROM webhook_entity WHERE 
  workflowId = '{id}'`
- Newly-activated workflows return 404 until n8n restarts. 
  `docker restart n8n` after activation. For sandbox testing 
  without restart, write directly to Supabase via PostgREST.

#### Workflow creation
- Omit the `active` field entirely — including `active: false` 
  causes 400. Workflows are always created inactive.
- Activate separately: `POST /api/v1/workflows/{id}/activate`
- Never use `PATCH {active: true}` — returns null, does nothing.

#### Data flow gotchas
- HTTP Request node unwraps JSON arrays into multiple items, 
  breaking sequential chains. Fix at API layer: wrap in 
  `{"results": [...], "count": N}`.
- `$json` refers to the PREVIOUS node's output only. For 
  non-adjacent data: `$('Node Name').item.json`
- `finished: false` on error executions — check 
  `exec.finished OR exec.status in ("success","error","crashed")`, 
  not just `finished`.
- HTTP Request nodes that don't consume the response need 
  `responseFormat: text`. Use `Prefer: return=minimal` for 
  INSERT nodes where the returned row isn't used.

#### Credentials
Never hardcode in workflow JSON. Read from .env at build time. 
When rotating, replace both `apikey` header AND 
`Authorization: Bearer` using str.replace on the full JSON 
string to catch all occurrences.

#### Audit logging
Audit node must branch from the data node, not the delivery 
node. Filter → Telegram AND Filter → Write Audit as parallel 
branches. Delivery failure must never prevent audit from firing.

### Part 3: Claude API Patterns

#### Prompt caching
- Haiku 4.5: silently fails. Returns 
  cache_creation_input_tokens: 0 with no error. Do not attempt.
- Sonnet 4.6: works, but actual minimum is ~2048 tokens in the 
  system block (documented threshold of 1024 is wrong). Target 
  2200+ tokens to clear with margin.

#### Agent evaluation (4-Pillars)
Score on four axes, not binary pass/fail:
1. Core LLM behavior consistency
2. Memory accuracy
3. Tool use correctness
4. Environment interaction

Status-aware recommendations: active agents get 
`maintain|needs_work|retire`; sandbox/paused get 
`promote|keep_sandbox|needs_work|retire`. Inject valid options 
as a VALID RECOMMENDATION VALUES block in the Haiku prompt — 
Haiku picks invalid options otherwise.

## Cross-Skill Warnings
- If a build fails and you can't tell which layer broke → 
  load triage. Don't debug infrastructure from this skill.
- If the task involves Telegram message formatting → check 
  communication skill for 750-char limit and format rules.
- See skills/PROTECTED.md — TCA workflow (kddIKvA37UDw4x6e) 
  must never be modified without Bill's explicit approval.

## Known Failure Modes
- Building an agent that already exists under a different name 
  (see references/lessons.md: pre-promotion duplicate check)
- Webhook 404 after activation without n8n restart 
  (see references/lessons.md: webhook registration)
- Silent branch death from empty arrays in monitoring workflows 
  (see references/lessons.md: health monitoring)
- Prompt caching appearing to work but doing nothing on Haiku 
  (see references/lessons.md: prompt caching)
