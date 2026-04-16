# Skill: Triage

## Purpose
Cross-layer diagnostic reasoning when something is broken and the 
failing layer is unclear. This skill is for diagnosis, not repair — 
once you know what's broken, switch to the relevant skill 
(system-ops for runbooks, agent-development for agent/API fixes).

## When to Load
- An execution failed and the error doesn't clearly point to one layer
- A tool call returns unexpected results (wrong data, silent success, 
  empty response)
- An agent stopped producing expected output after a system change
- error_log has entries without an obvious owner
- You're about to debug something and aren't sure where to start

## Core Instructions

### Session-start probes (every session, not per-task)
Run these two before beginning any work:
- `diag_agent_stuck_tasks` — work_queue items claimed >2 hours
- `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` 
  — real store sync gap (not COUNT comparison, which misses NULLs)

### The layer stack (check in this order)
1. **Infrastructure** — Is the service running? Pi resources OK?
   (n8n, ChromaDB, MCP server, Supabase connectivity)
2. **Tool/API** — Did the tool call actually succeed? Check for 
   silent failures — tools can return 200 while rejecting unknown 
   columns or writing nothing. Surface OK ≠ actual OK.
3. **Data** — Is the data correct? Schema match? Enum values exact? 
   Check for NULL foreign keys, JSONB nesting issues, metrics that 
   measure the wrong thing.
4. **Agent logic** — Is the prompt right? Is output going where 
   expected? Is the evaluator looking in the right place for output?

### The core principle: don't trust surface signals
Almost every triage failure in this system traces to a metric or 
tool reporting OK when the underlying state was wrong. Before 
concluding something works:
- Verify the actual row/state, not the tool's return code
- Ask: does this metric measure what I think it measures?
- If a tool "succeeds" but the expected change didn't happen, 
  use supabase_exec_sql to check directly

### Read-only during diagnosis
While triaging, do not modify system state except to write 
diagnostic findings to error_log. No "quick fixes," no config 
changes, no data patches. Diagnosis and repair are separate steps. 
Find the layer, log what you found, then hand off to the right 
skill for the fix.

### What to log
Triage that doesn't leave a trace is invisible to future sessions.
- Root cause identified → write to error_log before switching skills
- Fix confirmed after handoff → write to audit_log
- Unresolved → write what you tried and what was ruled out to 
  error_log so the next session doesn't repeat the same probes

### When to stop and escalate
Three signals mean you're stuck in a loop — alert Bill via Telegram 
and stop:
- Same error 3+ times in error_log
- Work queue item claimed >2 hours without completing
- API budget approaching limit

Do not retry past these thresholds. Write what you found, send 
the Telegram alert, stop.

## Cross-Skill Warnings
- If triage reveals an agent problem → load agent-development. 
  Do not patch agent issues during diagnosis.
- If triage reveals a service problem → load system-ops for the 
  runbook. Triage finds the layer; system-ops has the procedure.
- See skills/PROTECTED.md before modifying anything.

## Known Failure Modes
- Metrics that measure the wrong thing (see references/lessons.md: 
  store sync gap)
- Tools that report success without performing the operation 
  (see references/lessons.md: work_queue_update silent 400s)
- Evaluators that can't see output sent to external channels 
  (see references/lessons.md: 4-Pillars blind spots)
- Historical ratios that reflect pre-monitoring state, not failures 
  (see references/lessons.md: evaluator audit ratio)
