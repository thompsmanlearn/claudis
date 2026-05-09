# Session: 2026-05-08 — B-096: Research orchestrator core loop

## Directive
Build the orchestrator that runs a research cycle against a charter.

## What Changed
- **stats_server.py** (live + canonical): Added `/run_research_cycle` endpoint with full 8-step pipeline:
  1. Read charter (_parse_charter by section headers)
  2. Memory pass (ChromaDB: research_findings, lessons_learned, reference_material + Supabase research_articles + prior thread entries)
  3. Plan searches (Haiku: 3-7 queries with rationale + source_type)
  4. Execute searches (Brave via /web_search, disqualifying filter applied)
  5. Fetch URLs (/web_fetch, scored by source type preference, cap 8)
  6. Synthesize (Sonnet: synthesis + criteria assessment + sub-questions + summary + self-assessment)
  7. Write entries (gather, analysis, summary, sub_question_candidates, cycle_metadata)
  8. Call grader (stub; B-097 completes this)
- **architecture/decisions/research-orchestrator.md** (new): Cycle structure, model choices, cost discipline, extension guide.

## Smoke Test
Thread id: e0560a85 (TEST: Charter smoke test)
- Cycle 1: 7 searches, 32 results, 8 URLs fetched
- charter_advancement: partial ✓
- grader_verdict: continue (stub, /grade_research_cycle 404 → defaulted to continue) ✓
- Entry IDs written: gather, analysis, summary, cycle_metadata — all 4 ✓

## What Was Learned
stats_server.py uses urllib throughout — not the `requests` library. Internal calls to /web_search, /web_fetch, and /grade_research_cycle must use urllib.request. The `requests` import error only surfaces at runtime; the server starts fine but fails on the first internal call. Lesson: use stdlib urllib consistently within stats_server.

The metadata column on thread_entries stores JSON as a string (JSONB column). The orchestrator dumps the dict to a JSON string before writing — this is correct; Supabase PostgREST handles the string→JSONB cast.

## Unfinished
/grade_research_cycle (B-097) returns 404 — grader stub defaults to "continue." B-097 will complete this path. Sub-question candidates written this cycle can be spawned as child threads via B-100.
