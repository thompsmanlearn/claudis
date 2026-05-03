# B-080: Wire thread-triggered gather output back into originating thread

**Date:** 2026-05-02  
**Card:** B-080  
**Duration:** ~1 session  
**Status:** Complete

## What Changed

- **DDL:** `ALTER TABLE public.research_articles ADD COLUMN thread_id uuid` (nullable, no FK)
- **`stats-server/stats_server.py`:** `run_context_research` now accepts `thread_id` from payload, includes it in article inserts (only when present), queries article IDs by `agent_run_id` at run-end and returns them in response
- **`anvil/uplink_server.py`:** Added `_write_thread_gather_entries_impl` helper and `@anvil.server.callable write_thread_gather_entries(thread_id, article_ids)`; added HTTP POST handler at `/write_thread_gather_entries` on the health server; changed health server binding from `127.0.0.1` to `0.0.0.0` (required for Docker/n8n reachability)
- **n8n workflow `gzCSocUFNxTGIzSD`:** Added `Write Thread Entries` Code node between `Run Context Research` and `Respond to Webhook`; Code node calls uplink HTTP endpoint conditionally (only when `thread_id` and `article_ids.length > 0`), always returns 1 item

## Judgment Calls

- Added `/write_thread_gather_entries` as HTTP endpoint on the uplink health server (port 9101) rather than the stats server, to keep all thread entry write logic co-located with other thread callables in `uplink_server.py`. Required changing the health server binding to `0.0.0.0` so Docker containers can reach it via `host.docker.internal:9101`.
- Code node reads `thread_id` from the stats server response rather than the Webhook node output — cleaner because the stats server already extracts and validates it.
- `write_thread_gather_entries` also registered as an Anvil callable so it's accessible from the dashboard for future use.

## Bug Fixed (pre-existing, B-079)

The `Run Context Research` n8n node was using `$json.queries` to read the thread-derived queries from the webhook payload. In n8n webhook v2, body fields are nested at `$json.body`, not `$json` directly. This meant thread-specific queries were never reaching the stats server — all runs used default queries. Fixed as part of this card: changed to `$json.body.queries` and `$json.body.thread_id`.

## Smoke Test Results

- `thread_id` column: confirmed `uuid`, nullable via `information_schema`
- Stats server direct call: `{"thread_id": "e6f7f118...", "inserted": 1, "article_ids": ["4b368a5c..."]}` — article row confirmed with `thread_id = e6f7f118...`
- HTTP endpoint: `POST :9101/write_thread_gather_entries` → `{"written": 1}`, then `{"written": 0}` on retry (idempotent)
- Thread entry verified: `entry_type=gather`, `source=research_articles:4b368a5c...`, content `**title**\nurl\n\nsummary`
- n8n workflow round-trip: `thread_id` flows through execution correctly (confirmed via execution data inspection)
- Non-thread run: `thread_id: null`, `article_ids: []`, `thread_entries_written: null` — no entries written

**Note:** Full end-to-end via n8n webhook → stats server → article insert with thread_id → Code node callback → thread entries was verified as components. A live n8n workflow run with new articles was not possible in-session because all source queries returned dupes (60 articles already in DB from prior runs). The path is functionally complete.

## Applied Lessons

- `lesson_n8n_no_run_endpoint_2026-04-25`
- `7febbc27` (POST /activate)
- `lesson_n8n_merge_deadlock_2026-03-25` — avoided by using single Code node with conditional fetch() instead of branching
- `7b16d0a6` (empty array kills chain) — avoided: stats server returns object not array, Code node always returns 1 item
- `lesson_sandbox_webhook_trigger_required_2026-03-24`
