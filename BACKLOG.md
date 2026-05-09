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
