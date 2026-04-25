# PROJECT_STATE.md — Anvil UI Decomposition

*Read when the active project is Anvil UI. Updated by Claude Code at session close when Anvil work was done.*

**Last verified:** 2026-04-25

---

## What exists

Six tabs. All built programmatically in `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (1325 lines). Uplink server at `~/aadp/claudis/anvil/uplink_server.py` (874 lines, 34 callables).

| Tab | Status | What works |
|-----|--------|------------|
| Fleet | Working | Agent list (grouped active/paused/retired), expandable cards with status toggle + feedback, work queue (count + list), inbox (approve/deny), controls panel (lean trigger, directive writer, autonomous mode toggle) |
| Sessions | Working | Live session status, Site Status card + Regenerate button, last 15 session artifacts as expandable cards |
| Lessons | Working | Filter (recent/all/low-confidence), semantic search, thumbs up/down, delete |
| Memory | Working | ChromaDB collection browser (browse/search/delete docs), Supabase views (Research Papers, Error Log) |
| Skills | Working | List all skills, expand to read full content |
| Artifacts | Working | Filter by agent/type, expand to see content + rate (👍/👎) with comment input |
| Memory (Error Log) | Working | Error log rows now have notes TextBox + Resolve button → `resolve_error_log` callable |
| Fleet (Work Queue) | Working | Expandable cards with input_data preview, created_by, assigned_agent; sorted by priority |

---

## Gaps (project arc next)

### 1 — Per-agent invocation
**What's missing:** Agent cards have status toggle and feedback, but no way to trigger an agent run. No callable exists for this.

**Context:** Most agents are n8n workflows triggered by webhook. Some are sentinel-driven. "Invocation" means posting to the agent's n8n webhook.

**What to build:**
- Add `invoke_agent(agent_name)` callable to `uplink_server.py` — look up the agent's `webhook_url` from `agent_registry`, POST to it with a minimal payload, return `{'triggered': True}`.
- Add "Run" button to each agent card detail panel — only shown if agent is active and has a webhook_url.
- Handle missing webhook_url gracefully (button hidden or shows "no webhook configured").

**Complexity:** Medium (new callable needs webhook_url column in agent_registry; verify column exists).

---

## Known bugs

| Location | Bug | Status |
|----------|-----|--------|
| `uplink_server.py:639` | `get_table_rows` error_logs: `select`/`order` used `created_at` (col is `timestamp`) | Fixed 2026-04-25 |
| `Form1:966` | Rendered `row.get('created_at')` for error_logs | Fixed 2026-04-25 |

---

## Uplink callable inventory

34 callables total. Those NOT wired to any UI tab are marked *.

`ping`* · `get_system_status` · `get_agent_fleet` · `set_agent_status` · `submit_agent_feedback` · `get_work_queue` · `get_inbox` · `approve_inbox_item` · `deny_inbox_item` · `trigger_lean_session` · `get_lean_status` · `write_directive` · `get_autonomous_mode` · `set_autonomous_mode` · `get_lessons` · `search_lessons` · `update_lesson` · `delete_lesson` · `get_session_status` · `get_session_artifacts` · `get_collection_stats` · `browse_collection` · `search_collection` · `delete_document` · `get_table_rows` · `resolve_error_log` · `get_site_status` · `update_site` · `get_artifacts` · `get_artifact` · `rate_artifact` · `get_artifact_agents` · `get_skills` · `get_skill`

---

## Implementation order (suggested)

1. **Per-agent invocation** — medium effort, requires verifying agent_registry schema.
