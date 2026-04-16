# Lessons — System Ops

Curated from ChromaDB lessons_learned 2026-04-15. Actionable only — known-procedure execution.

---

## Supabase

**Supabase Management API (api.supabase.com) returns HTTP 403 from the Pi (Cloudflare block).**
Always use PostgREST (`SUPABASE_URL/rest/v1/`) with `SUPABASE_SERVICE_KEY` for all data operations. The Management API is only accessible from non-Pi environments. This affects bulk inserts, backfills, and any operation that doesn't fit a standard CRUD call.
*(2026-04-13)*

**DDL requires `supabase_exec_sql` MCP tool, not PostgREST.**
`CREATE TABLE`, `ALTER TABLE`, and other DDL cannot be executed via the REST API. PostgREST is CRUD only. Use `supabase_exec_sql` (which calls the Supabase Management API SQL endpoint) for all schema changes.
*(2026-03-29)*

**INSERT with array columns: use cast syntax, not ARRAY[] constructor.**
`ARRAY['a','b']` in SQL sent via `supabase_exec_sql` fails silently — no exception, no row. Always use: `'{"value1","value2"}'::text[]`. This applies to all INSERT/UPDATE statements with text[], integer[], or other array-typed columns.
*(2026-03-22)*

**Atomic counter increments require an RPC function.**
PostgREST PATCH cannot do `col = col + 1`. Pattern: `CREATE OR REPLACE FUNCTION fn(arr text[]) RETURNS void AS $$ UPDATE table SET col = col + 1 WHERE match_col = ANY(arr); $$ LANGUAGE sql SECURITY DEFINER`. Call via `POST /rest/v1/rpc/fn_name` with service key. Works for any atomic increment/decrement.
*(2026-03-31)*

---

## n8n

**n8n test webhooks and production webhooks are completely different paths.**
Test: `/webhook-test/` — fires when the workflow editor is open, even for inactive workflows. Production: `/webhook/` — only registers when the workflow is explicitly activated. If a webhook works in the editor but 404s in production, the workflow is not activated.
*(2026-03-23)*

**Activate workflows via `POST /activate`, never `PATCH {active: true}`.**
`PATCH` with `{active: true}` returns null for the active field and does nothing. Use `POST /api/v1/workflows/{id}/activate` to activate. `POST /api/v1/workflows/{id}/deactivate` to deactivate. These are the only reliable methods.
*(2026-03-29)*

---

## Store Sync

**Store sync gap repair procedure (ChromaDB > Supabase).**
When `SELECT COUNT(*) FROM lessons_learned` in Supabase is lower than ChromaDB count:
1. Get ChromaDB collection UUID: `GET /api/v1/collections` → find lessons_learned id
2. Fetch all IDs: `POST /api/v1/collections/{id}/get` with `limit=300, include=["documents","metadatas"]`
3. Get all Supabase chromadb_ids: `SELECT chromadb_id FROM lessons_learned WHERE chromadb_id IS NOT NULL`
4. Set diff in Python: `chromadb_ids - supabase_ids` → missing entries
5. Bulk INSERT via PostgREST with `SUPABASE_SERVICE_KEY` (NOT Management API — Cloudflare blocks from Pi)
6. Clean up orphaned NULL chromadb_id Supabase entries that are now duplicates
*(2026-04-13)*

**The real store sync gap metric is `chromadb_id IS NULL` in Supabase, not COUNT comparison.**
`COUNT(ChromaDB) ≈ COUNT(Supabase)` can look healthy while 29% of lessons have `chromadb_id=NULL` — those lessons exist in Supabase but are completely invisible to `memory_search`. Correct query: `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL`. Repair: run `memory_add` with UUID as doc_id for each NULL record, then `UPDATE lessons_learned SET chromadb_id = id::text WHERE chromadb_id IS NULL`.
*(2026-04-09)*
