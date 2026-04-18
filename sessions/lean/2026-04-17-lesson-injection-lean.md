# Session: 2026-04-17 — lesson-injection-lean

## Directive
Wire the lesson_injector into lean sessions so /oslean gets the same pre-loaded context that autonomous sentinel sessions receive. Add a quality signal so we can measure whether injected lessons actually influenced decisions.

## What Changed
- **~/aadp/sentinel/lean_runner.sh** (updated):
  - Reads DIRECTIVES.md before starting. If directive is a pointer ("Run: B-NNN"), resolves the full card description from BACKLOG.md via awk — gives the injector a meaningful description for semantic search.
  - Calls inject-context webhook (task_type='general', 25s timeout — endpoint takes ~15s) and prepends context_block to the prompt file.
  - Appends LESSON TRACKING instruction telling Claude to list applied lesson IDs in the session artifact under "Lessons Applied" if any were relevant.
  - Falls back gracefully (empty context block, no error) if injector is unavailable.

## What Was Learned
- `task_type='lean'` is not a recognized routing type in inject_context_v3.1 — it returns empty. Use `task_type='general'` which routes to the default path and returns full context.
- The inject-context webhook takes ~15 seconds to respond (ChromaDB queries + expansion). 10s timeout was silently cutting it off. 25s is safe.
- "Run: B-024" as a description is too short for meaningful semantic search. Resolving the full backlog card description before calling the injector gives the search the vocabulary it needs.

## Quality Signal Design
Each lean session artifact should now include a "Lessons Applied" section listing lesson IDs that were retrieved and actually used during the session. Absence of the section means no injected lessons were relevant. Presence with IDs means the injection influenced real decisions. Over 10+ sessions this becomes a signal on injector quality — not just retrieval rate but application rate.

## Lessons Applied
- None (this session was the build, not an execution using injected lessons)
