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
