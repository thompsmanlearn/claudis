B-084: Consolidate LEAN_BOOT, move dynamic state out of CONVENTIONS
Status: ready Depends on: none
Goal
LEAN_BOOT.md and CONVENTIONS.md have duplicated content (Behavioral Conventions exists in both) and CONVENTIONS Section 3 ("Current Operating Mode") contains dynamic state that drifts. Consolidate so each file has a single role: LEAN_BOOT triggers the session, CONVENTIONS holds rules, TRAJECTORY holds current state. This reduces boot context bloat and eliminates a known drift surface.
Context
LEAN_BOOT.md currently carries: trigger sequence, behavioral conventions (duplicated), infrastructure quick-reference (duplicated from CONTEXT.md), MCP tools table (duplicated from CONTEXT.md), and resuming-autonomous-mode instructions. Of these, only the trigger sequence and a brief "what this is" header earn their place in LEAN_BOOT.
CONVENTIONS.md Section 3 ("Current Operating Mode," dated 2026-04-22) lists active agent count and lean mode state. This is dynamic and belongs in TRAJECTORY.md.
The early Lean version (architecture/LEAN_BOOT.md, April 15) was 98 lines. Current is 168. Target after this card: ~50 lines for LEAN_BOOT, with everything moved to its proper home.
Done when
LEAN_BOOT.md contains only: a brief "what this is" header, the startup sequence steps, and a session close pointer. Total under 60 lines.
The duplicated Behavioral Conventions section is removed from LEAN_BOOT (CONVENTIONS.md is the source of truth).
The Infrastructure Quick-Reference, MCP Tools table, and Resuming Autonomous Mode sections are removed from LEAN_BOOT.
CONVENTIONS.md Section 3 (Current Operating Mode) is removed; the relevant content is moved into TRAJECTORY.md's existing "Where we are" section if not already there.
A single line at the top of LEAN_BOOT points to where each kind of information now lives ("System facts: CONTEXT.md. Rules: CONVENTIONS.md. State: TRAJECTORY.md. Constraints: skills/PROTECTED.md.")
The startup sequence still functions: wc -l shows the new LEAN_BOOT, and a manual walkthrough confirms each step still has its target file.
One commit on claudis main with the changes. Pushed.
Session artifact written.
Scope
Touch:
~/aadp/claudis/LEAN_BOOT.md
~/aadp/claudis/CONVENTIONS.md
~/aadp/claudis/TRAJECTORY.md (only to absorb the dynamic state if not already captured)
~/aadp/claudis/architecture/LEAN_BOOT.md (the April 15 archived version — leave alone, it's history)
Do not touch:
Any skill files
CONTEXT.md (already correct as the facts file)
DIRECTIVES.md, BACKLOG.md
inject_context_v3 or lean_runner.sh
The cp step that copies LEAN_BOOT.md to ~/aadp/
If you find yourself wanting to:
Rewrite the startup sequence — stop. This is consolidation, not redesign of the sequence itself.
Move skills routing out of LEAN_BOOT — stop. That's a different concern.
Two-hour ceiling.

## B-115-cmt: Correct architecture_review description and schedule fields to reflect actual run history

Status: ready Depends on: none

Goal
Update the `architecture_review` agent record so its description and schedule fields accurately reflect that the workflow has executed only once (at initial setup on 2026-04-05) rather than implying a consistent biweekly cadence. The original comment correctly identifies that the description's use of "Biweekly" is misleading given no subsequent executions have occurred since setup. The correction ensures the agent record is an accurate source of truth and does not misrepresent operational history to downstream consumers of AADP metadata.

Context
The agent `architecture_review` currently carries "Biweekly review" in its description and "Biweekly Sunday 16:00 UTC" in its schedule field. The n8n workflow `7mVc61pDCIObJFos` has not fired since the initial setup run on 2026-04-05, meaning the biweekly cadence has never been observed in practice. The description should be amended to note that the schedule is configured but unconfirmed in execution, and the schedule field should be qualified similarly — without removing the intended schedule, which remains the target configuration. Do not alter the webhook path, workflow ID, status, component logic description, or any output/queue behavior.

Done when
- The `description` field for `architecture_review` no longer opens with "Biweekly review" and instead includes a note that the workflow has run once (2026-04-05) and the biweekly cadence is configured but not yet confirmed by recurring execution.
- The `schedule` field value no longer reads "Biweekly Sunday 16:00 UTC" without qualification; it reflects the intended schedule alongside an indication that recurrence is unverified (e.g., "Every other Sunday 16:00 UTC — configured, recurrence unconfirmed").
- A `SELECT description, schedule FROM agents WHERE name = 'architecture_review'` query returns values matching the corrected text above with no mention of confirmed biweekly execution.
- All other fields (`status`, `webhook`, `workflow`, `built`, `component_tag` grouping logic, output targets) return unchanged values compared to pre-edit state.
- No migration or schema change is introduced; only row-level data is updated.

Scope
Touch: `agents` table row where `name = 'architecture_review'` (description and schedule columns only)
Do not touch: n8n workflow `7mVc61pDCIObJFos`, webhook route `/webhook/architecture-review`, any `experimental_outputs` records, `work_queue` table, Telegram integration config, any other agent rows

> Generated from agent_feedback bb49d2c9-58e2-4621-8013-a394c1a87882 on 2026-05-09 (intent=correction, confidence=0.95)

## B-116: Charter authoring UI

Status: ready Depends on: none

Goal
Add a charter form to the Threads tab so Bill can author and save a full research charter entirely from the Anvil UI without any direct API calls. The charter appears either at thread creation or as an "Add charter" step on an existing thread without a charter. Saved charters display as a readable block in the thread detail view.

Context
The charter schema (Question, Scope, Success Criteria, Disqualifying Criteria, Sub-Questions, Source Preferences, Recency) exists in the backend and is used by the research orchestrator. The threads table has a charter column (JSONB). There is currently no UI to author or view a charter — it can only be written via direct API call. This makes threads feel inert: Bill can state a research question but cannot define the criteria that govern how it gets answered. B-117 (thread research agent) depends on a charter being present; this card unblocks it.

Done when
- A charter form is reachable from the Threads tab — either inline at thread creation or via an "Add charter" button on an existing thread that has no charter.
- The form contains: Question (pre-filled from thread title), Scope, Success Criteria, Disqualifying Criteria, Sub-Questions (multi-line, one per line), Source Preferences, Recency Requirement (optional).
- Submitting the form writes the charter as JSONB to the `charter` column of the `threads` table for that thread_id.
- The thread detail view displays the saved charter as a readable block (field labels + values, not raw JSON).
- UI follows existing dashboard conventions: larger font sizes, minimal padding, dense layout — no large empty regions between fields.
- No direct API calls required from Bill to complete the authoring flow.

Scope
Touch: Anvil dashboard client code (Form1/__init__.py), threads table (charter column — no schema change needed if column exists; add if not), uplink_server.py (save_charter and get_charter callables if not present).
Do not touch: thread_entries table, research orchestrator logic, agent_registry, n8n workflows.


## B-117: Thread research agent with Brave

Status: ready Depends on: B-116

Goal
Build a thread-native research agent that reads a thread's charter, generates search queries from its sub-questions, fetches results via /web_search (Brave), screens results against the charter's criteria, and writes qualifying findings back to thread_entries. This wires Brave Search into the research pipeline for the first time.

Context
/web_search exists on the stats server with a working Brave API key but has zero callers (classified orphaned in the consumer audit). The thread infrastructure (thread_entries, charter, screening logic in the orchestrator) is in place but only the arxiv pipeline feeds it — and only for fixed topics on a fixed schedule. A thread research agent responds to a specific question rather than a preset topic list. It does not auto-run; B-118 adds the gather trigger.

Behavior
- Reads charter JSONB from the threads table for the given thread_id.
- Generates one search query per sub-question (up to 5 queries per cycle).
- Calls POST /web_search for each query (max_results=5 per call).
- Screens each result against success criteria and disqualifying criteria via a Haiku call.
- Writes qualifying results to thread_entries: entry_type="finding", content includes source URL, summary, and a brief relevance note.
- Writes a cycle summary entry (entry_type="cycle_summary") when complete: queries run, results screened, entries written, cost estimate.
- Respects the existing cost cap (_ORCHESTRATOR_COST_CAP_USD = 0.50).
- Triggered via webhook POST /webhook/thread-research-agent {thread_id}.

Done when
- Running the agent against a thread that has a real charter (authored via B-116) produces at least 3 qualifying thread_entries visible in the thread detail view in Anvil.
- A cycle summary entry appears after the run.
- The agent is registered in agent_registry with status=sandbox.
- /web_search appears in consumer_manifest.json with classification=partial (wired to this agent's workflow).

Scope
Touch: n8n workflow (new), stats_server.py (if agent logic delegated there), agent_registry (new row), consumer_manifest.json (/web_search entry).
Do not touch: existing thread_entries rows, arxiv_aadp_pipeline, research_synthesis_agent.


## B-118: Gather trigger

Status: ready Depends on: B-116, B-117

Goal
Add a "Gather" button to the thread detail view in Anvil. Clicking it fires the wired research agent against the current charter and refreshes the entry list when complete.

Context
Even with a charter (B-116) and a research agent (B-117), there is no UI trigger. Bill would need to call the webhook manually. The gather button closes this loop: chartered thread + wired agent + one click = research run.

Behavior
- Button only appears when: a charter exists on the thread AND an agent is wired.
- Clicking Gather calls the wired agent's webhook with {thread_id}.
- Shows a running indicator ("Gathering…") while the cycle executes.
- On completion (poll or callback), refreshes the thread entry list so new findings appear without a manual page reload.
- If the agent call fails, surfaces the error inline (no silent failures).

Done when
- Clicking Gather on a chartered, wired thread fires the research agent and new entries appear in the thread detail view without a manual refresh.
- The Gather button is absent on threads with no charter or no wired agent.
- A failed gather surfaces an error message in the UI.

Scope
Touch: Anvil dashboard client code (Form1/__init__.py), uplink_server.py (trigger_thread_gather already exists — verify it calls the wired agent's webhook with thread_id).
Do not touch: agent logic, thread_entries schema, n8n workflow internals.


## B-119: Auto-wiring

Status: ready Depends on: B-117

Goal
When a thread is created or a charter is saved, automatically match the charter to the best available agent and wire it — or queue a build request if no adequate agent exists.

Context
Currently Bill must manually wire an agent to each thread. The matching logic is implicit knowledge: "web search" in source preferences → thread research agent; arxiv topics → arxiv_aadp_pipeline. Auto-wiring makes this explicit and automated, removing a manual step and ensuring new threads don't sit unwired.

Behavior
- Triggers on: thread creation (if charter provided at creation) or charter save (B-116).
- Scores available agents against charter's source_preferences and question text. Scoring considers: agent capability tags (add a capability_tags column to agent_registry if not present), keyword overlap with source preferences, agent status (active or sandbox only).
- If best match score exceeds threshold (≥ 0.7): wire automatically, write an audit entry, notify Bill via Telegram ("🔗 Auto-wired [agent] to thread '[title]' — confidence [score].").
- If no match meets threshold: write an agent_feedback row (target_type='thread', intent='build_request') describing the gap, leave thread unwired, show "No matching agent found — build request queued" in the thread detail view.
- Wiring is always overridable from the thread detail view.

Done when
- Creating a chartered thread with "web search" in source preferences automatically wires the thread research agent (B-117) without manual intervention.
- A Telegram notification confirms the auto-wiring with agent name and confidence score.
- A thread whose source preferences match no available agent shows "build request queued" in the UI and a corresponding agent_feedback row exists in Supabase.

Scope
Touch: uplink_server.py (auto-wire logic on charter save), agent_registry (capability_tags column if absent), agent_feedback table (build_request rows), Anvil dashboard (thread detail view — show auto-wire status).
Do not touch: existing wired threads, n8n workflow internals, work_queue.

