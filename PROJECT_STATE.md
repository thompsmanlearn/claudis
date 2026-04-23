# PROJECT_STATE.md — Anvil UI Decomposition

*Read when the active project is Anvil UI. Updated by Claude Code at session close when Anvil work was done.*

---

## What exists

Six tabs. All built programmatically in `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (1267 lines). Uplink server at `~/aadp/claudis/anvil/uplink_server.py` (874 lines, 33 callables).

| Tab | Status | What works |
|-----|--------|------------|
| Fleet | Working | Agent list (grouped active/paused/retired), expandable cards with status toggle + feedback, work queue (count + list), inbox (approve/deny), controls panel (lean trigger, directive writer, autonomous mode toggle) |
| Sessions | Working | Live session status, last 15 session artifacts as expandable cards |
| Lessons | Working | Filter (recent/all/low-confidence), semantic search, thumbs up/down, delete |
| Memory | Working | ChromaDB collection browser (browse/search/delete docs), Supabase views (Research Papers, Error Log) |
| Skills | Working | List all skills, expand to read full content |
| Artifacts | Working | Filter by agent/type, expand to see content + rate (👍/👎) |

---

## Gaps (project arc next)

### 1 — Work queue detail
**What's missing:** Queue rows show `[status] task_type (p:priority)` only. No description, no payload, no actions.

**What to build:**
- Expand the `get_work_queue` callable (`uplink_server.py:202`) — add `description,payload` to the `select` param.
- Render expandable queue cards in `_load_queue` (`Form1:451`) — show description and a truncated payload preview on expand.
- Optional: add Claim/Cancel buttons calling `work_queue_update` via a new uplink callable.

**Complexity:** Low (backend: 1-line select change; UI: replace Label rows with card builder).

---

### 2 — Error log resolve
**What's missing:** Error log is read-only. No way to mark an error resolved from the UI.

**Backend state:**
- `error_logs` table has `resolved` (bool), `resolution_notes` (text), `resolved_by`, `resolved_at`.
- `get_table_rows('error_logs')` works but has two bugs:
  - `select` includes `created_at` — column is actually `timestamp`. Fix: change to `id,workflow_name,error_message,error_type,timestamp`.
  - `order` is `created_at.desc` — fix to `timestamp.desc`.
- UI renders `row.get('created_at')` at `Form1:966` — fix to `row.get('timestamp')`.
- No `resolve_error` callable exists in the uplink server.

**What to build:**
- Add `resolve_error(error_id, notes=None)` callable to `uplink_server.py` — PATCH `resolved=true`, `resolved_by='bill'`, `resolved_at=now()`, `resolution_notes`.
- Add "Resolve" button to each error card in `_load_supabase_table` (`Form1:940`), wired to the new callable.
- Fix the `get_table_rows` bugs above.

**Complexity:** Medium (new callable + UI card builder for error rows).

---

### 3 — Site status + regenerate
**What's missing:** `get_site_status()` and `update_site()` callables exist (`uplink_server.py:665,733`) but are not wired to any UI panel.

**What to build:**
- Add a "Site" section to the Sessions tab or Fleet controls panel.
- On load: call `get_site_status()` — display `generated_at`, `agent_count`, `mode`, `current_directive`, last 3 session summaries.
- Add a "Regenerate Site" button — calls `update_site()` (runs `generate_site.py` + git push); show confirmation or error.

**Complexity:** Low (callables are complete; pure UI wiring).

---

### 4 — Artifact comments
**What's missing:** `rate_artifact(artifact_id, rating, comment=None)` already accepts a comment (`uplink_server.py:799`), but the UI rating buttons (`Form1:1120`) don't pass one. Existing `bill_comment` is displayed if present, but there's no input to write a new one.

**What to build:**
- In `_make_load_detail` (`Form1:1097`), add a `TextBox(placeholder='Comment…', width=200)` above the rating buttons.
- Pass `comment_box.text or None` as the third arg to `rate_artifact`.

**Complexity:** Trivial (3-line UI change; backend already handles it).

---

### 5 — Per-agent invocation
**What's missing:** Agent cards have status toggle and feedback, but no way to trigger an agent run. No callable exists for this.

**Context:** Most agents are n8n workflows triggered by webhook. Some are sentinel-driven. "Invocation" means posting to the agent's n8n webhook.

**What to build:**
- Add `invoke_agent(agent_name)` callable to `uplink_server.py` — look up the agent's `webhook_url` from `agent_registry`, POST to it with a minimal payload, return `{'triggered': True}`.
- Add "Run" button to each agent card detail panel — only shown if agent is active and has a webhook_url.
- Handle missing webhook_url gracefully (button hidden or shows "no webhook configured").

**Complexity:** Medium (new callable needs webhook_url column in agent_registry; verify column exists).

---

## Known bugs (found during decomposition, not yet fixed)

| Location | Bug |
|----------|-----|
| `uplink_server.py:639` | `get_table_rows` error_logs: `select` has `created_at` (col is `timestamp`), `order` is `created_at.desc` |
| `Form1:966` | Renders `row.get('created_at')` for error_logs — returns None (col is `timestamp`) |
| `LEAN_BOOT.md:109` | Lists table as `error_log` — actual table name is `error_logs` |

---

## Uplink callable inventory

33 callables total. Those NOT wired to any UI tab are marked *.

`ping`* · `get_system_status` · `get_agent_fleet` · `set_agent_status` · `submit_agent_feedback` · `get_work_queue` · `get_inbox` · `approve_inbox_item` · `deny_inbox_item` · `trigger_lean_session` · `get_lean_status` · `write_directive` · `get_autonomous_mode` · `set_autonomous_mode` · `get_lessons` · `search_lessons` · `update_lesson` · `delete_lesson` · `get_session_status` · `get_session_artifacts` · `get_collection_stats` · `browse_collection` · `search_collection` · `delete_document` · `get_table_rows` · `get_site_status`* · `update_site`* · `get_artifacts` · `get_artifact` · `rate_artifact` · `get_artifact_agents` · `get_skills` · `get_skill`

---

## Implementation order (suggested)

1. **Site status + regenerate** — lowest effort, highest visibility. Pure wiring.
2. **Artifact comments** — trivial, completes a half-built feature.
3. **Error log resolve** — medium effort, requires bug fix + new callable + UI card builder.
4. **Work queue detail** — medium effort, high operational value.
5. **Per-agent invocation** — medium effort, requires verifying agent_registry schema.
