---
date: 2026-05-03
session_type: bill-initiated
card: B-080a
title: Fix fetch→helpers.httpRequest regression in context_engineering_research callback
---

## Tasks completed

- Replaced `fetch()` with `helpers.httpRequest()` in the Write Thread Entries Code node (workflow gzCSocUFNxTGIzSD) — same payload contract, same conditional firing logic (thread_id present and articles > 0)
- Updated workflow via `workflow_update`; verified via re-fetch that the active version (f0deee6e) contains the fix
- Retroactive backfill: called `write_thread_gather_entries` directly against uplink port 9101 for all three orphaned runs:
  - run `a77805d8` → thread `e6f7f118` (Configure vs. create): **10 written**
  - run `65622741` → thread `1b3a5cd9` (Consumer AI): **7 written**
  - run `36b6ee2d` → thread `e6f7f118` (Configure vs. create): **14 written** (card said 13; one article added since diagnostic)
  - Total: **31 thread entries recovered**
- Smoke test: triggered gather on Configure vs. create thread with one query; response included `thread_entries_written: 6`; thread_entries count rose 32 → 45. Fix confirmed.
- Lesson written to lessons_learned + ChromaDB: `lesson_n8n_code_node_helpers_http_2026-05-03`

## Key decisions

- **Lesson conflict flagged, card followed:** Existing lessons `lesson_n8n_code_node_no_http_2026-03-25` and `lesson_n8n_code_node_fetch_silent_failure_2026-03-31` say `$helpers` (with `$`) is undefined in Code node v2 sandbox. Card prescribed `helpers.httpRequest` (no `$`). These are distinct — `helpers` without `$` is the in-scope utility n8n provides for Code nodes; `$helpers` with `$` is the expression-context accessor. Smoke test confirmed `helpers.httpRequest` works. New lesson corrects the gap in the existing ones.
- **Retroactive backfill via direct uplink call:** The Card authorized calling `write_thread_gather_entries` directly rather than re-triggering the full research pipeline, which would have been slower and added noise to the article table.

## Capability delta

- **Fixed:** Thread-triggered gather runs now correctly write thread entries via the callback — the silent failure is closed
- **Recovered:** 31 orphaned thread entries from three prior runs now linked to their threads
- **New lesson:** `helpers.httpRequest` (no `$`) is the correct HTTP utility for n8n Code node v2 — corrects two prior lessons that identified the problem but not the working alternative

## Lessons written

1. `lesson_n8n_code_node_helpers_http_2026-05-03` — Supabase id: `3a8f8563-c42c-4331-9547-115dcfdbaa11`

## Branches

None — workflow-only fix, no code files modified.

## Usage

~% session, ~% weekly (unknown at artifact write time)
