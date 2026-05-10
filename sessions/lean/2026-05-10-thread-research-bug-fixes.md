# Session: Thread Research Pipeline Bug Fixes
Date: 2026-05-10
Type: lean
Card: unplanned (bug fixes)
Code commits: bac6b44, merged ce7b99e (claudis)

## Tasks Completed
- Fixed three bugs in the thread research pipeline reported by Bill

## Bug 1: Duplicate findings
`run_thread_research` used `seen_urls` only within a single call. The same URL could be written as a finding across multiple research cycles. Fix: fetch all existing `finding` source URLs for the thread from Supabase before the write loop; skip any URL already present; add to the local set as each new finding is written. Added `skipped_duplicates` to cycle_summary content and JSON response. Smoke test: 12 skipped, 0 new on the smoke test thread.

## Bug 2: Memory consultation wrong query
`consult_memory` trusted the `question` parameter from the caller. A prior test call had passed "ChromaDB vector store embedding retrieval" as the question, which was written as the consultation query. Fix: when `thread_id` is provided, fetch `threads.charter['question']` directly from Supabase before building `query_text`. The DB is authoritative; the caller-supplied question is overridden. Smoke test: passing "WRONG QUESTION PLACEHOLDER" produced the correct charter question in the consultation.

## Bug 3: Last gather output not wired to thread
Root cause: thread_research_agent n8n workflow (KIq8lkEjmyUqFc7d) was inactive. Production webhook only registers for active workflows. n8n recorded execution 2762 as error with zero nodes running. `trigger_thread_gather._fire()` had no `raise_for_status()` and logged all status codes at INFO — completely silent. Fix: activated the workflow via n8n API, `docker restart n8n` (required for webhook registration), added non-200 `log.warning` in `_fire()`. Smoke test: webhook returns 200.

## Key Decisions
- `consult_memory` owns query derivation — callers cannot be trusted. DB is authoritative.
- Added `skipped_duplicates` to the cycle_summary entry (visible in Anvil) so Bill can see dedup counts.
- Kept sandbox status on thread_research_agent; only activated the n8n workflow (not a full promotion).

## Capability Delta
**Before:** Duplicate findings written across cycles; memory consultation could use wrong query; gather failures silent.
**After:** Dedup enforced at write time; consultation always uses correct charter question; non-200 webhook responses surfaced in journald.

## Lessons Written
2 new:
1. consult_memory: always fetch query from threads.charter, not from caller
2. n8n inactive sandbox workflow: silent webhook failure, must activate before gather works

## Branches
- attempt/fix-thread-research-bugs → merged to main, deleted

## Usage
~18% session / weekly TBD
