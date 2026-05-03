B-080a: Fix B-080 callback regression — fetch undefined in n8n Code node sandbox

## Goal

B-080 shipped with a silent failure: the run-end callback in the context_engineering_research workflow uses `fetch`, which doesn't exist in n8n's Code node VM sandbox. Articles get inserted with thread_id correctly, but the callback to write_thread_gather_entries throws ReferenceError, gets swallowed, and no thread entries are written. Three thread-triggered gather runs landed 30 articles into research_articles with thread_id set but produced zero gather entries in the corresponding threads.

Replace `fetch` with `helpers.httpRequest` in the n8n Code node, then run the existing write_thread_gather_entries callable retroactively to load the orphaned articles into their threads.

## Context

n8n Code nodes execute inside a vm.createContext({}) sandbox. Node 22's global `fetch` is not inherited into that sandbox. n8n provides `helpers.httpRequest()` as the in-scope HTTP utility for Code nodes — same JSON-payload semantics as fetch but uses n8n's HTTP machinery.

write_thread_gather_entries is already idempotent on (thread_id, source). Running it retroactively against the existing orphaned articles will not duplicate entries.

Orphaned article groups (from diagnostic):
- agent_run_id a77805d8: 10 articles, thread_id e6f7f118 (Configure vs. create)
- agent_run_id 65622741: 7 articles, thread_id 1b3a5cd9 (Consumer AI)
- agent_run_id 36b6ee2d: 13 articles, thread_id e6f7f118 (Configure vs. create)

## Done when

- The Code node in workflow gzCSocUFNxTGIzSD that fires the callback uses helpers.httpRequest instead of fetch. Same payload contract, same target endpoint, same conditional firing logic (only when thread_id present and articles > 0).
- Workflow updated via workflow_update; smoke test it by triggering one new gather on the Configure vs. create thread and confirming gather entries land within ~60s.
- Retroactive load of the three orphaned runs: for each (agent_run_id, thread_id) pair above, gather the article IDs from research_articles and call write_thread_gather_entries(thread_id, [article_ids]). Report counts written per call. Idempotency means re-running is safe.
- Lesson written: "n8n Code node VM sandbox does not inherit Node globals like fetch — use helpers.httpRequest for HTTP calls from Code nodes. ReferenceError gets swallowed by try/catch, leaves no journald trace."
- Session artifact written.

## Scope

Touch:
- n8n workflow gzCSocUFNxTGIzSD (Code node fix)
- research_articles read (retroactive backfill: read article IDs by run_id, no writes to research_articles)
- thread_entries write (via existing write_thread_gather_entries; no schema change)
- session artifact

Do not touch:
- The uplink callable (already correct)
- The trigger_thread_gather flow (already correct)
- Schema (no changes needed)
- Any other workflow

If a different sandbox issue surfaces during the retroactive load — stop and surface it. Don't paper over additional silent failures.
