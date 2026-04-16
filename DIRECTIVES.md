## Goal
Write the system-ops SKILL.md with reviewed content.

## Context
Content drafted on desktop using lessons from references/lessons.md.
Write exactly as provided.

## Done when
- skills/system-ops/SKILL.md replaced with content below
- Committed and pushed
- Session artifact written

## Scope
Touch: skills/system-ops/SKILL.md, sessions/lean/
Do not touch: everything else

## Content to write

# Skill: System Ops

## Purpose
Operating and maintaining AADP infrastructure on the Pi. Running 
known procedures for service management, data operations, and 
store synchronization. This skill is for executing runbooks when 
you know what's wrong — if you don't know what layer is failing, 
load triage first.

## When to Load
- Restarting or managing Pi services (n8n, ChromaDB, MCP server, 
  Supabase connectivity, stats server, sentinel)
- Handling disk, memory, or temperature alerts
- Running Supabase DDL or data operations
- Performing store sync repair between ChromaDB and Supabase
- Activating, deactivating, or debugging n8n workflow state

## Core Instructions

### Supabase Operations

#### API access from the Pi
The Management API (api.supabase.com) returns 403 from the Pi — 
Cloudflare blocks it. Always use PostgREST 
(`SUPABASE_URL/rest/v1/`) with `SUPABASE_SERVICE_KEY` for all 
data operations. This affects bulk inserts, backfills, and 
anything beyond standard CRUD.

#### DDL (schema changes)
PostgREST is CRUD only. `CREATE TABLE`, `ALTER TABLE`, and all 
DDL require the `supabase_exec_sql` MCP tool (which calls the 
Management API SQL endpoint, not PostgREST).

#### Array column syntax
`ARRAY['a','b']` in SQL via supabase_exec_sql fails silently — 
no exception, no row inserted. Always use cast syntax: 
`'{"value1","value2"}'::text[]`. Applies to all array-typed 
columns (text[], integer[], etc.).

#### Atomic counter increments
PostgREST PATCH cannot do `col = col + 1`. Create an RPC function:
`CREATE OR REPLACE FUNCTION fn(arr text[]) RETURNS void AS $$ 
UPDATE table SET col = col + 1 WHERE match_col = ANY(arr); 
$$ LANGUAGE sql SECURITY DEFINER`
Call via `POST /rest/v1/rpc/fn_name` with service key.

### n8n Service Operations

#### Webhook paths
Test webhooks (`/webhook-test/`) fire when the editor is open, 
even for inactive workflows. Production webhooks (`/webhook/`) 
only register when the workflow is explicitly activated. If a 
webhook works in the editor but 404s in production, the workflow 
is not activated.

#### Activation
Activate via `POST /api/v1/workflows/{id}/activate` only. 
`PATCH {active: true}` returns null and does nothing. Deactivate 
via `POST /api/v1/workflows/{id}/deactivate`. These are the only 
reliable methods.

### Store Sync Repair

#### Measuring the gap correctly
Do not use COUNT comparison between ChromaDB and Supabase — it 
hides the real problem. The correct metric: 
`SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL`
Lessons with NULL chromadb_id exist in Supabase but are invisible 
to memory_search.

#### Repair procedure (ChromaDB > Supabase)
1. Get ChromaDB collection UUID: `GET /api/v1/collections` → 
   find lessons_learned id
2. Fetch all IDs: `POST /api/v1/collections/{id}/get` with 
   `limit=300, include=["documents","metadatas"]`
3. Get all Supabase chromadb_ids: `SELECT chromadb_id FROM 
   lessons_learned WHERE chromadb_id IS NOT NULL`
4. Set diff: `chromadb_ids - supabase_ids` → missing entries
5. Bulk INSERT via PostgREST with SUPABASE_SERVICE_KEY (not 
   Management API — Cloudflare blocks from Pi)
6. Clean up orphaned NULL chromadb_id entries that are duplicates

#### Repair procedure (NULL chromadb_ids in Supabase)
Run `memory_add` with UUID as doc_id for each NULL record, then:
`UPDATE lessons_learned SET chromadb_id = id::text 
WHERE chromadb_id IS NULL`

## Cross-Skill Warnings
- If a service won't start and you can't tell why → load triage. 
  System-ops has runbooks for known procedures, not diagnostic 
  reasoning.
- Store sync repair touches both ChromaDB and Supabase — verify 
  both sides after any repair, not just the side you wrote to.
- See skills/PROTECTED.md before modifying any service 
  configuration or restarting protected workflows.

## Known Failure Modes
- Silent INSERT failure from ARRAY[] constructor syntax 
  (see references/lessons.md: array column syntax)
- Management API 403 when accidentally using api.supabase.com 
  instead of PostgREST (see references/lessons.md: API access)
- Store sync appearing healthy by COUNT while 29% of lessons 
  have NULL chromadb_ids (see references/lessons.md: gap metric)
- Workflow activation via PATCH doing nothing silently 
  (see references/lessons.md: n8n activation)
