# BACKLOG.md

---

## B-138: Decouple auto_cycle toggle from growth scheduler

**Context:** `set_autonomous_mode(enabled)` in `uplink_server.py` (around line 405) currently toggles two unrelated things in one call: `auto_cycle_enabled` in `system_config` AND the `autonomous_growth_scheduler` n8n workflow (ID `Lm68vpmIyLfeFawa`). Starting an autonomous project requires `auto_cycle_enabled=true` but must NOT activate the growth scheduler, which injects unrelated work_queue items on a 6-hour timer. The Projects tab (B-140) needs to control `auto_cycle_enabled` independently.

Add a `set_auto_cycle_only(enabled: bool)` callable to `uplink_server.py` that patches only `system_config.auto_cycle_enabled` via Supabase REST — no n8n call, no growth scheduler side effect. The existing `set_autonomous_mode` callable is left unchanged (it still controls both, for the Home tab button).

**Done when:**
- `set_auto_cycle_only(enabled: bool)` exists in `uplink_server.py` as an `@anvil.server.callable`
- It patches `system_config` where `key = 'auto_cycle_enabled'` and returns `{"enabled": enabled}`
- It does NOT touch the n8n growth scheduler workflow
- Verified: calling `set_auto_cycle_only(True)` sets `auto_cycle_enabled=true` in Supabase; calling `set_auto_cycle_only(False)` sets it back to false; n8n workflow `Lm68vpmIyLfeFawa` active state is unchanged in both cases

---

## B-139: Decompose callable — goal → project + nodes

**Context:** Core of the autonomous project system. Takes a goal string from Bill and uses Opus 4.8 to decompose it into a linear `aadp_project` with `aadp_project_nodes`. Returns the plan (project id + ordered node list) for display in the Projects tab (B-140). Supports a `revision_notes` parameter so Bill can regenerate with corrections without retyping the goal.

Node acceptance criteria must follow the convention established in this session: Claude must print verbatim evidence in its response (tool outputs, file contents, command results) so the grader can evaluate based on the log. The Opus prompt must enforce this.

**Implementation:**

Add `decompose_goal(goal: str, revision_notes: str = "")` to `uplink_server.py`:

1. Build an Opus 4.8 prompt that includes: the goal, any revision notes, a description of what lean sessions can do (Bash, MCP tools, Supabase, file writes, Python), the node type vocabulary (`write`, `build`, `polish`), and the acceptance-criteria convention (print evidence verbatim in response).
2. Instruct Opus to produce a linear chain of 3–7 nodes. Each node: `name`, `type`, `context` (why this step, what inputs it has), `acceptance_criteria` (what to do + what to print as evidence).
3. Parse Opus's JSON response.
4. INSERT into `aadp_projects`: `name` (short title derived from goal), `goal`, `status='draft'`.
5. INSERT nodes into `aadp_project_nodes` in order, each depending on the previous (linear chain). `status='pending'`.
6. Return `{"project_id": "...", "project_name": "...", "nodes": [{id, name, type, context, acceptance_criteria}, ...]}`

If `revision_notes` is provided, include the prior decomposition in the prompt and ask Opus to revise it.

**Done when:**
- `decompose_goal(goal, revision_notes="")` callable exists in `uplink_server.py`
- Calling it with a test goal (e.g. "research and summarize the three most cited papers on transformer attention mechanisms published in 2024") returns a valid project_id and a list of 3–7 nodes with names, context, and acceptance_criteria
- The inserted project has `status='draft'` in `aadp_projects`
- Nodes are inserted with sequential dependencies (node N depends on node N-1); node 1 has no deps
- Acceptance criteria in every node includes explicit instruction to print evidence verbatim
- A second call with the same goal + `revision_notes="make the first node just find paper titles, not full summaries"` returns a revised plan and inserts a NEW project (does not mutate the first)
- Print the node list in your response so the grader can verify the structure

---

## B-140: Projects tab — Anvil UI

**Context:** New "Projects" tab in the Anvil dashboard (`claude-dashboard/client_code/Form1/__init__.py`). Wires the decompose callable (B-139), `set_auto_cycle_only` (B-138), and the progress callable (B-141) into a usable interface. The tab has three visual states driven by project status.

**Draft state** (project status = `draft`, no session running):
- Goal text area (multiline, placeholder: "Describe the goal or problem…")
- Optional "Revision notes" text field (single line, hidden until first decompose)
- "Decompose" button → calls `decompose_goal(goal, revision_notes)`, displays node list
- Node list: each node shows name, type badge, acceptance_criteria (collapsed to 2 lines, expandable)
- "Start" button → calls `set_auto_cycle_only(True)`, writes node 1 directive to DIRECTIVES.md via a new `start_project(project_id)` callable (see Notes), calls `/trigger_lean` via stats server, sets project status = `active`
- "Regenerate" button → shows revision notes field, re-calls `decompose_goal`, replaces displayed plan (old draft project marked `status='abandoned'`)

**Running state** (project status = `active`, session running or between sessions):
- Node list with status badges: `pending` (grey) / `running` (blue) / `done` (green) / `failed` (red)
- Current session phase from `get_project_progress()` (B-141): shown below the node list
- "Stop after current session" button → calls `set_auto_cycle_only(False)`

**Stopped state** (project status = `active`, `auto_cycle_enabled=false` or grader stopped chain):
- Node list with final statuses
- If a node has `status='failed'` (grader stopped): show grader rationale below that node
- "Resume" button → calls `set_auto_cycle_only(True)`, re-triggers
- "Abandon" button → sets project `status='abandoned'`

**Notes:**
- Add a `start_project(project_id)` callable to `uplink_server.py` that: reads node 1 from `aadp_project_nodes`, writes it to `DIRECTIVES.md` in the lean_runner format (`# Project Node: ...`), commits + pushes to claudis, calls `http://localhost:9100/trigger_lean`, sets `aadp_projects.status='active'`.
- Add a `get_active_project()` callable that returns the active project + nodes (used to determine which state the tab renders).
- The Projects tab is the 5th tab. Current tabs: Home / Workpad / Sessions / System. Add Projects between Workpad and Sessions (new order: Home / Workpad / Projects / Sessions / System).

**Done when:**
- Projects tab renders in the Anvil dashboard
- Draft state: typing a goal and clicking Decompose shows a node list returned from `decompose_goal`
- Start button triggers a lean session and sets the project active (verify via session_status and lock file appearing)
- Running state: node badges update when polled (use a 15s timer, same pattern as the lean status poller on Home tab)
- Stop button sets `auto_cycle_enabled=false` (verify via Supabase query)
- Stopped state renders when a chain has stopped (simulate by manually setting `auto_cycle_enabled=false` mid-project)
- Print a summary of what was built and verified in your response so the grader can assess

---

## B-141: Project-progress callable

**Context:** Anvil callable that returns enough state for the Projects tab (B-140) to render the Running and Stopped views without making multiple round-trips. Reads `aadp_project_nodes` statuses, current `session_status`, and the latest `grader_reviews` entry for any failed node.

**Add `get_project_progress(project_id: str)` to `uplink_server.py`:**

```
Returns:
{
  "project": {id, name, goal, status},
  "nodes": [
    {id, name, type, status, dependencies,
     grader_verdict: str|null,   # latest verdict for this node if any
     grader_rationale: str|null} # latest rationale if verdict is fail/pause
  ],   # ordered by created_at
  "session": {phase, current_action, updated_at} | null,  # latest session_status row
  "auto_cycle_enabled": bool
}
```

Supabase queries:
- `aadp_projects?id=eq.{project_id}&select=id,name,goal,status`
- `aadp_project_nodes?project_id=eq.{project_id}&select=id,name,type,status,dependencies,created_at&order=created_at`
- `session_status?order=updated_at.desc&limit=1`
- `grader_reviews?card_id=in.({node_ids})&select=card_id,verdict,rationale&order=created_at.desc` — one per node, take the most recent
- `system_config?key=eq.auto_cycle_enabled&select=value`

Also add `get_active_project()` that queries `aadp_projects?status=eq.active&limit=1` and returns the first active project, or `null` if none. Used by the Projects tab on load to determine initial state.

**Done when:**
- `get_project_progress(project_id)` callable exists and returns the structure above
- `get_active_project()` callable exists and returns the active project or null
- Tested against the `Grader-Gated Node Completion Test` project (`cb457489-878f-4aad-a385-3b0dc44bc3bc`): response includes Node 1 (done), Node 2 (pending, grader_verdict=fail, grader_rationale present), Node 3 (pending, no grader entry)
- `auto_cycle_enabled` field reflects live Supabase value
- Print the full JSON response for the test project in your response so the grader can verify structure and correctness

---
