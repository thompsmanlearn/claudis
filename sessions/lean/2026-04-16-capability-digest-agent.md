# Session: 2026-04-16 — Capability Digest Agent

## Directive
B-019: Build an n8n workflow that queries newly scouted resources from Supabase, groups them by inquiry thread, and sends a formatted Telegram digest to Bill. Daily schedule + manual webhook trigger.

## What Changed

**n8n workflow created and activated:**
- Name: Capability Digest Agent
- ID: `Lt6kMhhVxMetMpcp`
- Webhook: GET `/capability-digest`
- Schedule: daily at 08:00 UTC (`0 8 * * *`)
- Status: active

**Workflow structure (6 nodes):**
1. Schedule Trigger (daily 8am) + Webhook Trigger → both feed Fetch Resources
2. Fetch Resources — PostgREST query: `resources` where `status=scouted` and `scouted_at >= now()-24h`, ordered by `relevance_score desc`
3. Fetch Threads — PostgREST query: `inquiry_threads` where `status=active`
4. Format Digest (Code node, runOnceForAllItems) — groups by thread_id, top 3 per thread, 4000 char hard max
5. Send Telegram (parallel branch) — Telegram node, chatId 8513796837, Life OS Bot credentials
6. Write Audit Log (parallel branch) — POST to audit_log with `actor=capability_digest_agent`

**Audit/delivery branching:** Format Digest → [Send Telegram, Write Audit Log] in parallel. Audit fires regardless of Telegram delivery.

**First run results (exec 2353, 2352):**
- Status: success (both)
- Resources in digest: 5 (all from game-development thread)
- Audit log confirmed: `details.resources_in_digest = 5`
- Telegram message delivered

**Sample message structure:**
```
Capability Digest — Apr 16

[game-development]
* Importing AI Generated Models into UE5...
  AI-generated 3D models into UE5 workflow directly matches interests
  https://reddit.com/...
* Blender Geometry Nodes to Unreal
  Blender Geometry Nodes to UE5 plugin directly bridges both engines
  https://reddit.com/...
...
```

## What Was Learned

- Used Telegram node directly (not Quick Send webhook) — avoids Docker self-calling complexity and is more reliable within n8n
- `responseFormat: text` + `$('Node Name').item.json.data` parse pattern works cleanly for multi-node Supabase data access
- Webhook registration requires `docker restart n8n` after activation — confirmed via 200 on webhook test
- The `active` field must be omitted from workflow creation JSON (400 otherwise); activate separately via activate API

## Unfinished

- Agent not yet registered in `agent_registry` (B-019 scope excluded other Supabase tables)
- Digest currently shows all scouted items from last 24h regardless of whether they've already been digested; if Scout runs twice in 24h, duplicates could appear. Future: mark resources as `digested` after sending, query only un-digested.
- Message format uses plain text (no Markdown parse_mode) — intentional to avoid formatting issues with URLs and special chars
