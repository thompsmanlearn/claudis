# Session Artifact — 2026-05-03 — Pre-card cleanup pass

## Directive

Unnumbered pre-card cleanup: update reference docs to reflect B-076–B-083, verify 6 recent lessons in both stores, classify 19 unresolved errors.

## What was done

**Step 1 — DEEP_DIVE_BRIEF.md sections 4, 5, 7, 8, 12 (date → 2026-05-03):**
- Section 4: added thread architecture features to "What's working now" (B-070–B-083); added 13 thread callables to callable table
- Section 5: added Thread Architecture capability subsection; added thread-aware gather note under Research
- Section 7: added threads and thread_entries to Database Schema; noted research_articles.thread_id column
- Section 8: updated context_engineering_research row — thread-aware query derivation + gather output wiring
- Section 12: added n8n webhook v2 body nesting gotcha (`$json.body.field`, not `$json.field`)

**Step 2 — anvil-redesign-principles-and-plan.md:**
- Built: added B-079/B-080 (thread-aware gather + regression fix), B-083 (standing summary), B-081 (neutral summaries), B-082 (company RSS)
- Not yet built: removed "Standing summary rendered at the top of the thread page" (done)
- Thread page layout spec: standing summary slot updated to "(B-083 live)"

**Step 3 — TRAJECTORY.md:**
- "Where we are": thread architecture complete B-070–B-083; use-period; no card pending
- Handoff: new cleanup entry at top; retained B-082/B-081; dropped B-078 (3-entry cap)

**Step 4 — Lesson verification:**
- Queried Supabase: 6 lessons created in last 72h, all with chromadb_id set
- Queried ChromaDB directly (`/api/v1/collections/{id}/get` with 6 IDs): all 6 returned
- All 6 exist in both stores. No writes needed.

**Step 5 — Error log classification:**
- 19 unresolved errors: all `fetch_error`, all from `context_engineering_research` (gzCSocUFNxTGIzSD)
- All are URL page-fetch failures: Medium bot-blocking, SSL timeout on one external URL, job site redirect, GitHub blob redirect
- The agent's skip-on-empty logic already handled these gracefully — they are operational noise, not bugs
- All 19 marked resolved with note: "Expected operational noise: URL page fetch returned empty or timed out. Article was skipped per design — no thin rows inserted."

## Classification note

`error_logs` is accumulating fetch attempt failures that the agent already handles silently. These should be resolved on sight rather than allowed to accumulate. Consider whether this logging level is worth the operational clutter — a future card could change the agent to only log on unexpected failures.

## Commits

- `1e99fb0` — docs: DEEP_DIVE_BRIEF + anvil redesign plan (claudis main)
- `0d1d801` — trajectory: redesign chapter complete, use-period handoff (claudis main)
