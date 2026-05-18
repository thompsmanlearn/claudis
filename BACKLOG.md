B-133: Boot Cleanup — Dead Code and Missing Heartbeat
Status: ready
Depends on: none
Goal
Remove dead code from lean_runner.sh, remove a deprecated call from bootstrap, and add a session heartbeat to lean sessions so system_config reflects active state during execution.
Context
Three specific problems found during boot path investigation (2026-05-17):

lean_runner.sh contains a lesson injection block (~lines 90-114) that calls http://localhost:5678/webhook/inject-context. The lesson_injector n8n workflow was deleted in B-130. The call returns 404 on every lean session. The block is dead and should be removed along with the stale comment on line 4 referencing it.
skills/bootstrap.md contains a session_notes_load(consume=true) call. session_notes table was archived 2026-04-25 per CONVENTIONS.md. Dead call, remove it.
Lean sessions show system_config.claudis_current_task = 'idle' for their entire duration. lean_runner.sh writes to session_status (different table) but doesn't update system_config. LEAN_BOOT.md has no heartbeat step either. agent_health_monitor sees 'idle' during active lean sessions. Add a heartbeat update to LEAN_BOOT.md at boot start — sets claudis_current_task to the current directive text (truncated to 80 chars) and claudis_heartbeat_at to now. Use config_set MCP tool. Close-session already resets it to idle.

lean_runner.sh lives at ~/aadp/sentinel/lean_runner.sh — confirm this path before editing. It is a symlink to ~/aadp/claudis/sentinel/lean_runner.sh per CONVENTIONS.md — edit the claudis canonical, the symlink handles the rest.
LEAN_BOOT.md interactive path (Bill types path manually without lean_runner) must keep working after changes. Don't remove anything from LEAN_BOOT.md that only lean_runner duplicates — the interactive path has no pre-enrichment.
Done when

Dead injection block removed from ~/aadp/claudis/sentinel/lean_runner.sh (lines ~90-114 and stale comment on line 4)
session_notes_load(consume=true) removed from skills/bootstrap.md
LEAN_BOOT.md has a new step early in the sequence (after step 1 git pull, before step 4.5 bill_input check): calls config_set to write claudis_current_task = first 80 chars of current directive + claudis_heartbeat_at = now
curl localhost:9100/system_status shows non-idle claudis_current_task during a test lean session
Commit pushed to main

Scope
Touch: ~/aadp/claudis/sentinel/lean_runner.sh, skills/bootstrap.md, LEAN_BOOT.md

B-136: Enforce Capability Delta in session artifacts
Status: ready
Depends on: none
Goal
Make Capability Delta a required section in every session artifact with three mandatory fields. Currently the section exists but is routinely left empty. An artifact without a completed delta cannot be used to verify whether a session produced real value.
Context
Session export from 2026-05-17 shows B-135 with empty Before/After fields. B-130 is the only recent artifact with a complete delta including a named reader. The close-session skill needs to enforce this, not suggest it. Read skills/close-session.md before editing to find the exact location of the artifact template.
Required format for every artifact — all three fields mandatory:
Capability delta
Before: one concrete sentence. "Works correctly" is not acceptable. "Bill can now trigger synthesis without running a lean session" is acceptable.
After: one concrete sentence matching the same standard.
Reader of this change: name a specific person or process and how they encounter the change. "Future sessions" is not acceptable. "Bill — via dashboard Home tab" is acceptable.
If a session made no capability change: write "No capability change this session — investigation only" in the delta section. Empty is not acceptable.
Done when
skills/close-session.md artifact template updated with the three-field Capability Delta format above, marked required, with the acceptability rules stated explicitly. The enforcement language reads: "Do not mark artifact complete until all three fields are filled or the investigation-only exception is stated." One concrete example of a correctly filled delta is included in the template. Commit pushed to main.
Scope
Touch: ~/aadp/claudis/skills/close-session.md
Do not touch: existing session artifacts, LEAN_BOOT.md, any other skill file, any Supabase table
Do not touch: uplink_server.py, any n8n workflows, session_status table writes in lean_runner.sh, close-session heartbeat reset, LEAN_BOOT.md step 11 (live lesson injection)
