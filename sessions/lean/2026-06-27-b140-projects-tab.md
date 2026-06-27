# Session Artifact — B-140: Projects tab — Anvil UI
Date: 2026-06-27
Directive: Run: B-140
Code commits: claudis e8073bc (attempt), 8433bc7 (merge to main); claude-dashboard a0830ac (attempt), 52d4b57 (merge to master)

## Capability Delta

**Before:** Anvil dashboard had 3 tabs (Home / Workpad / System). No UI to decompose, start, monitor, or stop autonomous projects. `get_project_progress`, `get_active_project`, `start_project`, `abandon_project` callables did not exist.

**After:** Dashboard has 4 tabs (Home / Workpad / Projects / System). Projects tab renders three states: Draft (decompose + start), Running (node badges + stop), Stopped (grader rationale + resume/abandon). Four new callables live on uplink.

**Reader:** Bill via Anvil dashboard at claude-dashboard.anvil.app.

## What was built

### uplink_server.py — 4 new callables

**`get_project_progress(project_id)`** — returns `{project, nodes[], session, auto_cycle_enabled}`. Nodes include `grader_verdict` and `grader_rationale` (populated from latest `grader_reviews` row per node). Queries 4 tables: `aadp_projects`, `aadp_project_nodes`, `grader_reviews` (by `card_id in (node_ids)`), `session_status`, `system_config`.

**`get_active_project()`** — returns first `aadp_projects` row with `status='active'`, or `None`.

**`start_project(project_id)`** — reads node 1 (earliest `created_at`), writes directive to `DIRECTIVES.md`, commits + pushes claudis, sets project `status='active'`, POSTs to `/trigger_lean`.

**`abandon_project(project_id)`** — patches project `status='abandoned'`.

### Form1/__init__.py — Projects tab

Tab order: Home / Workpad / **Projects** / System. Tab added to `_build_layout`, `_set_tab`, and new `_show_projects_tab` handler.

Three state panels (only one visible at a time):
- **Draft**: goal textarea, optional revision notes (hidden until first decompose), Decompose / Regenerate / Start buttons, node list rendered by `_proj_render_node_list`
- **Running**: project name, node list with status badges, session phase label, Stop button (`set_auto_cycle_only(False)`)
- **Stopped**: project name, node list with grader rationale for failed nodes, Resume button (`set_auto_cycle_only(True)` + `trigger_lean_session`), Abandon button

15s poll timer via Anvil `Timer(interval=15)` — calls `get_project_progress` when Projects tab is visible.

## Verification

### B-141 get_project_progress verified against test project cb457489-878f-4aad-a385-3b0dc44bc3bc:

```json
{
  "project": {"id": "cb457489-...", "name": "Grader-Gated Node Completion Test", "status": "complete"},
  "nodes": [
    {"name": "Node 3: Must never fire", "status": "pending", "grader_verdict": null, "grader_rationale": null},
    {"name": "Node 2: Rigged to fail", "status": "pending", "grader_verdict": "fail",
     "grader_rationale": "The task required including the FULL command output verbatim..."},
    {"name": "Node 1: Passing control", "status": "done", "grader_verdict": "pass", "grader_rationale": null}
  ],
  "session": {"phase": "close_session", "current_action": "running close-session", "updated_at": "2026-06-26T20:34:09..."},
  "auto_cycle_enabled": true
}
```
- Node 1: done, verdict=pass ✅
- Node 2: pending, verdict=fail, rationale present ✅
- Node 3: pending, no grader entry ✅
- auto_cycle_enabled reflects live Supabase value ✅

### Anvil uplink
- Service restarted and reconnected: `Connected to "Default Environment" as SERVER` confirmed in journalctl

### Code committed and pushed
- claudis main: 8433bc7
- claude-dashboard master: 52d4b57
- Anvil auto-syncs from master branch on GitHub push

## Not tested (browser-only)
- Decompose button → node list render (requires Anvil browser session)
- Start button → DIRECTIVES.md write + lean trigger (requires browser + live project)
- Running state → node badge polling in browser
