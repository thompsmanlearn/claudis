# PROJECT_STATE.md — Anvil UI Decomposition

*Read when the active project is Anvil UI. Updated by Claude Code at session close when Anvil work was done.*

**Last verified:** 2026-04-25

---

## What exists

Six tabs. All built programmatically in `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (~1370 lines). Uplink server at `~/aadp/claudis/anvil/uplink_server.py` (35 callables).

| Tab | What works |
|-----|------------|
| Fleet | System status; agent fleet grouped/searchable with expand, status toggle, feedback, Run button (on-demand agents only); work queue expandable cards (input_data, created_by, assigned_agent, priority sort); inbox approve/deny; controls (lean trigger, directive writer, autonomous mode toggle) |
| Sessions | Live session status card; Site Status + Regenerate button; last 15 session artifacts as expandable cards |
| Lessons | Filter views (Recent/Top Used/Never Applied/Broken/Search); lesson cards with confidence thumbs + delete |
| Memory | ChromaDB collection browser (browse/search/delete); Supabase: Research Papers read-only; Error Log with notes TextBox + Resolve button |
| Skills | Skills list with View Content button |
| Artifacts | Agent/type filter buttons; artifact cards with lazy-load expand, rating + comment input |

---

## No open gaps

All gaps from the original project arc are closed as of 2026-04-25:
- ~~Work queue detail~~ — expandable cards with payload, sorted by priority
- ~~Error log resolve~~ — Resolve button + notes, `resolve_error_log` callable
- ~~Site status + regenerate~~ — Sessions tab, wired before this session
- ~~Artifact comments~~ — comment TextBox wired to `rate_artifact`
- ~~Per-agent invocation~~ — Run button on active agents with `webhook_url`; `invoke_agent` callable; `webhook_url` column added to `agent_registry`

---

## Schema additions (2026-04-25)

| Table | Column | Type | Purpose |
|-------|--------|------|---------|
| `agent_registry` | `webhook_url` | text, nullable | n8n webhook URL for on-demand invocation; populated for `agent_health_monitor`, `lesson_injector`, `session_health_reporter` |

---

## Uplink callable inventory (35)

Those NOT wired to any UI tab are marked *.

`ping`* · `get_system_status` · `get_agent_fleet` · `set_agent_status` · `invoke_agent` · `submit_agent_feedback` · `get_work_queue` · `get_inbox` · `approve_inbox_item` · `deny_inbox_item` · `trigger_lean_session` · `get_lean_status` · `write_directive` · `get_autonomous_mode` · `set_autonomous_mode` · `get_lessons` · `search_lessons` · `update_lesson` · `delete_lesson` · `get_session_status` · `get_session_artifacts` · `get_collection_stats` · `browse_collection` · `search_collection` · `delete_document` · `get_table_rows` · `resolve_error_log` · `get_site_status` · `update_site` · `get_artifacts` · `get_artifact` · `rate_artifact` · `get_artifact_agents` · `get_skills` · `get_skill`

---

## Known bugs (all fixed)

| Location | Bug | Fixed |
|----------|-----|-------|
| `uplink_server.py` | `get_table_rows` error_logs: `select`/`order` used `created_at` (col is `timestamp`) | 2026-04-25 |
| `Form1` | Rendered `row.get('created_at')` for error_logs | 2026-04-25 |
