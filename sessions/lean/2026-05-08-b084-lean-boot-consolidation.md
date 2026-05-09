# Session: 2026-05-08 — B-084: LEAN_BOOT consolidation

## Directive
Consolidate LEAN_BOOT.md, move dynamic state out of CONVENTIONS.md Section 3 into TRAJECTORY.md.

## What Changed
- **LEAN_BOOT.md**: Added pointer line (*System facts: CONTEXT.md. Rules: CONVENTIONS.md. State: TRAJECTORY.md. Constraints: skills/PROTECTED.md.*). Tightened prose in steps 9-11. Result: 96 lines (was 104).
- **CONVENTIONS.md**: Removed Section 3 "Current Operating Mode" entirely. Moved "When uncertain" behavioral rule up into Section 1 as a Standing Principle. Result: 79 lines (was 107).
- **TRAJECTORY.md**: Added lean mode state line to "Where we are": "Lean mode: sentinel timer disabled, autonomous_growth_scheduler deactivated. Desktop scopes cards; Claude Code executes."
- **~/aadp/LEAN_BOOT.md**: Updated via cp (boot copy kept in sync).

## What Was Learned
The card assumed LEAN_BOOT.md was 168 lines (the architecture/LEAN_BOOT.md April-15 archived version). The current file was already 104 lines — the duplicated behavioral conventions, infrastructure quick-reference, MCP tools table, and resuming-autonomous-mode sections had been removed in prior sessions. The 60-line target is not achievable without removing the SQL queries in steps 9-10, which are operationally necessary. The 96-line result is the practical floor given the current sequence design. B-090 (stats_server skill resolution) will replace the judgment-based step 6, which may allow further trimming then.

## Unfinished
Nothing. Authorization scope (Authorized/Not authorized lists from Section 3) is intentionally dropped — B-088 will formalize as authorization tiers.
