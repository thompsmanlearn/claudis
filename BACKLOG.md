B-033: Lean session status indicator on Anvil dashboard
Status: ready
Goal
Add a visible status indicator next to the Trigger Lean Session button on the Anvil dashboard so Bill can see whether a lean session is currently running before triggering a new one. This prevents accidental concurrent sessions (no coordination layer exists) and closes the visibility gap on the primary control surface.
Context
The Trigger Lean Session button calls trigger_lean_session() which hits stats_server /trigger_lean. This spawns a claude -p process. There is currently no way to know from the dashboard whether a session is already running. Two concurrent sessions can silently conflict on git, Supabase, and file writes. The detection mechanism is a ps aux check for claude processes — crude but sufficient. The uplink_server.py registers callable functions that the dashboard invokes; a new callable get_lean_status() is needed. The dashboard UI is programmatic (add_component() in client_code/Form1/__init__.py). Anvil skill reference at skills/anvil/REFERENCE.md.
Done when

get_lean_status() callable registered in uplink_server.py, returns {"running": bool, "pid": int|null}
Dashboard shows status indicator next to Trigger button — idle vs running
Trigger button refreshes status after a short delay so Bill sees the state change
Trigger button disabled or shows warning when a session is already running
Both repos committed and pushed (claudis main, claude-dashboard master)

Scope
Touch: ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py
Do not touch: stats_server.py, agent fleet, n8n workflows

B-034: Commit curation surface ADR and update brief
Status: ready
Goal
Commit the Anvil curation surface ADR to the repo and update DEEP_DIVE_BRIEF.md Sections 4 and 10 to reference it. This establishes the design foundation that all subsequent dashboard and artifact convention cards depend on. Also update TRAJECTORY.md to drop the /oslean fix as next milestone and reflect the curation surface direction.
Context
The ADR was produced in a desktop session on 2026-04-18 and saved externally. It defines the tab structure for the evolving Anvil dashboard, the cross-agent artifact convention, agent input/output declarations, routing discipline, and sequencing. The file goes to ~/aadp/claudis/architecture/decisions/anvil-curation-surface.md. The brief's Section 4 (Current Project: Anvil Dashboard) should add a subsection pointing to the ADR as the next phase. Section 10 (Platform Roadmap) Anvil entry should reference it. TRAJECTORY.md next milestone should read: "B-033 — lean session status indicator on Anvil dashboard" and reference the curation surface ADR as the broader direction. Remove any /oslean references from next milestone.
Done when

ADR file committed at ~/aadp/claudis/architecture/decisions/anvil-curation-surface.md
DEEP_DIVE_BRIEF.md Sections 4 and 10 updated with references to the ADR
TRAJECTORY.md next milestone updated, /oslean removed
Committed and pushed to main

Scope
Touch: architecture/decisions/, DEEP_DIVE_BRIEF.md, TRAJECTORY.md
Do not touch: BACKLOG.md, uplink_server.py, dashboard code, stats_server.py, agent fleet

B-035: Add agent feedback summary to morning briefing
Status: ready
Depends on: B-034
Goal
Close the feedback loop gap. The agent_feedback table captures thumbs-up/thumbs-down ratings and comments from the Anvil dashboard but nothing reads them. Add a feedback summary section to the morning briefing so Bill sees agents with recent negative feedback alongside the existing health and error reporting. This is the minimum viable feedback consumer — no new agent or workflow, just extending what already works.
Context
The morning briefing workflow (xt8Prqvi7iJlhrVG) already aggregates system health, agent status, and error counts. It uses no LLM — it's a structured data pull. The agent_feedback table has fields: agent_name, rating (1 or -1), comment, created_at. The briefing should query for feedback received since the last briefing (roughly 24 hours) and include a section listing any agents with thumbs-down ratings and the associated comments. Thumbs-up can be summarized as a count. The briefing output goes to Telegram and/or the dashboard — match whatever the current delivery mechanism is. See ADR at architecture/decisions/anvil-curation-surface.md for broader context on why feedback consumption matters.
Done when

Morning briefing output includes a "Recent Feedback" section
Section lists agents with thumbs-down ratings from the last 24 hours, including comments
Section shows thumbs-up count if any exist
Section shows "No feedback" if the table has no recent entries (not an error, just quiet)
Briefing still works correctly when agent_feedback table is empty
Committed and pushed to main

Scope
Touch: Morning briefing workflow (xt8Prqvi7iJlhrVG) in n8n, any supporting stats_server endpoint if the briefing delegates there
Do not touch: agent_feedback table schema, Anvil dashboard code, other agent workflows
