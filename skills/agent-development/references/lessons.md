# Lessons — Agent Development

Curated from ChromaDB lessons_learned 2026-04-15. Actionable only — things that change build decisions.

---

## Agent Lifecycle

**Pre-promotion duplicate check is mandatory.**
Before promoting any sandbox agent: `SELECT agent_name, status, workflow_id FROM agent_registry WHERE agent_name LIKE '%keyword%' AND status='active'`. If anything returns, stop. Sandbox names don't always match prod names (e.g. `serendipity_engine` vs `serendipity_engine_prod`). INDEX.md Production table is the authoritative list of what's running.
*(2026-03-29)*

**When agent_registry shows status=building + workflow_id=null, check n8n workflow list first.**
The workflow may already exist but was never linked. In 2026-04-14, Research Synthesis Agent had been active in n8n since 2026-04-05 but never linked in the registry. Inspect the existing workflow, upgrade if needed, then update agent_registry with workflow_id and status=active. Don't build from scratch until confirmed the workflow truly doesn't exist.
*(2026-04-14)*

**Health monitoring must cover building/sandbox agents separately.**
n8n execution-log monitors are blind to building/sandbox agents (no workflow_id, not active). Add a parallel branch querying `status=in.(building,sandbox)` with `updated_at > 7 days` as stale threshold. Use a normalize/guard Code node (`runOnceForAllItems`) returning a sentinel item when input is empty — otherwise the empty-array chain-halt bug silently kills the branch.
*(2026-04-13)*

**Stats server delegation beats complex n8n logic when:**
logic requires ChromaDB subprocess, API keys should stay in .env (not in workflow JSON), or the endpoint needs CLI testability. Pattern: add endpoint to `stats_server.py`, replace complex n8n nodes with a single HTTP Request to `host.docker.internal:9100/your_endpoint`, keep schedule/webhook triggers in n8n.
*(2026-04-14)*

---

## n8n Workflow Building

**HTTP Request node unwraps JSON array responses into multiple items.**
A response `[{...},{...}]` creates one workflow item per element, breaking sequential chains — `.item` references fail for items beyond index 0. Fix at the API layer: wrap in a container object `{"results": [...], "count": N}`.
*(2026-03-25)*

**workflow_create: omit the `active` field entirely.**
Including `active: false` causes 400 "active is read-only". Workflows are always created inactive. Activate separately via `POST /api/v1/workflows/{id}/activate`. Never use `PATCH {active: true}` — it returns null and does nothing.
*(2026-03-25)*

**Webhook node requires `webhookId` at the node level matching the path.**
Without it, n8n silently fails to register the route and returns 404. Always include `webhookId` as a top-level node property equal to the path value. Undocumented in n8n 2.6.4 but required for API-built workflows.
*(2026-03-30)*

**API-created workflows have a different webhook URL format than UI-created ones.**
UI-created: `/webhook/{path}`. API-created: `/webhook/{workflowId}/webhook/{path}`. Never guess. Look up the actual path from the n8n SQLite: `SELECT webhookPath FROM webhook_entity WHERE workflowId = '{id}'`.
*(2026-03-22)*

**Newly-activated workflows return 404 webhooks until n8n restarts.**
n8n doesn't register webhooks for workflows activated via API after server startup. Activation returns success and `active=true`, but the webhook 404s. Fix: `docker restart n8n`. For sandbox testing without restart, write directly to Supabase via PostgREST instead.
*(2026-04-01)*

**Sandbox agents must use webhook trigger, not manual trigger.**
The n8n execute API returns 405 for manual-trigger workflows. The `agent_test` task type triggers via HTTP webhook. Always use `n8n-nodes-base.webhook` as trigger with `responseMode: onReceived`. Leave DEACTIVATED after testing.
*(2026-03-24)*

**Never hardcode credentials in n8n workflow JSON. Always update both headers simultaneously.**
Keys rotate; stale keys cause misleading auth failures. Read from `.env` at build time. Replace both `apikey` header AND `Authorization: Bearer` header using `str.replace(OLD, NEW)` on the full workflow JSON string to catch all occurrences at once.
*(2026-03-31)*

**`finished: false` on error executions — check status field, not just `finished`.**
Polling `exec.finished == True` loops forever when a workflow errors because `finished` stays false. Correct terminal check: `exec.finished OR exec.status in ("success", "error", "crashed")`.
*(2026-04-06)*

**`$json` refers to the PREVIOUS node's output, not any arbitrary upstream node.**
In chain A → B → C, node C's `$json` is B's output. To reference non-adjacent upstream data: `$('Node Name').item.json`. Critical when intermediate nodes (e.g. Telegram send) sit between a data source and a write node.
*(2026-03-31)*

**Audit log nodes must branch from the data node, not from the delivery node.**
Chain: Filter → Telegram → Write Audit means a Telegram failure drops the audit record. Correct structure: Filter → Telegram (terminal) AND Filter → Write Audit (parallel branch). Delivery failure must never prevent audit from firing.
*(2026-04-01)*

**HTTP Request nodes that don't consume the response need `responseFormat: text`.**
Without it, unexpected response bodies cause "Empty or invalid JSON" failures. Also: use `Prefer: return=minimal` (not `return=representation`) for INSERT nodes where the returned row isn't used.
*(2026-04-05)*

---

## API Integration

**Prompt caching: Haiku 4.5 silently fails; Sonnet 4.6 requires ~2048-token system block.**
Haiku 4.5 returns `cache_creation_input_tokens: 0` with no error regardless of prompt length — do not attempt caching. Sonnet 4.6 caches correctly but actual minimum is ~2048 tokens (documented threshold is 1024 — wrong). Target 2200+ tokens in the system block to clear with margin. Confirmed working in 4-Pillars Evaluator (workflow kQ5OALBwexLQS7in, exec 1892/1893).
*(2026-03-31)*

**Agent evaluation requires 4 pillars, not binary pass/fail.**
Score: (1) core LLM behavior consistency, (2) memory accuracy, (3) tool use correctness, (4) environment interaction. Status-aware recommendation enums: active agents get `maintain|needs_work|retire`; sandbox/paused get `promote|keep_sandbox|needs_work|retire`. Inject valid options as a `VALID RECOMMENDATION VALUES` block in the Haiku prompt — otherwise Haiku picks invalid options.
*(2026-03-25)*
