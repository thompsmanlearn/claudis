# Session: 2026-05-08 — B-106: Retire context_engineering_research fully

## What Changed
- **n8n**: Workflow gzCSocUFNxTGIzSD deleted (was deactivated since B-101). Webhook route
  POST /webhook/context-engineering-research returns 404 — confirmed.
- **agent_registry**: status='retired', workflow_id=null.
- **stats-server/stats_server.py** (canonical + live):
  - `_log_research_error`: workflow_id changed from hardcoded "gzCSocUFNxTGIzSD" to None
    (comment explaining deletion). workflow_name kept for log traceability.
  - `/run_context_research`: Added DEPRECATED docstring (B-106, 2026-05-08). Endpoint
    kept to prevent 500s from any stale callers; no n8n workflow routes to it.
  - Line 3613 provenance field left as-is — intentional historical reference for existing articles.
- **agents/INDEX.md**: context_engineering_research entry updated to RETIRED with strikethrough.
- **DEEP_DIVE_BRIEF.md**: Section 8 (Capabilities), agent fleet table, and section 11
  desktop session description all updated to reflect retirement.

## Smoke Test
- n8n API GET gzCSocUFNxTGIzSD: returns id=None (workflow deleted).
- POST /webhook/context-engineering-research: 404 "not registered" — confirmed gone.
- stats server restarted cleanly (aadp-stats active).
- agent_registry: status=retired, workflow_id=null — confirmed.

## Notes
- No agent code folder existed at agents/production/context_engineering_research/ — the
  agent's logic lived entirely in stats_server.py (/run_context_research) and n8n.
  Nothing to move to agents/retired/.
- research_articles table history preserved (170+ articles from all prior runs intact).
- The research orchestrator (B-096) is the replacement. Smoke test: /run_research_cycle
  on any thread with a charter.

## Lessons Applied
None pre-loaded were directly triggered.
