# B-061: Generalize Export Across All Dashboard Tabs

**Date:** 2026-04-26
**Session type:** Lean — single card
**Card:** B-061

## Tasks Completed

- Added 7 uplink callables to `anvil/uplink_server.py`: `get_lessons_bundle`, `get_memory_bundle`, `get_sessions_bundle`, `get_fleet_bundle`, `get_errors_bundle`, `get_skills_bundle`, `get_artifacts_bundle`. Each returns structured markdown with YAML frontmatter (bundle_type, generated_at, view_filter, row_count), a Summary section, domain-specific content, and optional Recently Resolved Feedback section.
- Added shared helpers `_bundle_header()` and `_bundle_resolved_feedback()` to avoid repetition across callables.
- Added ⬇ Export buttons to all 7 tabs in `client_code/Form1/__init__.py` (Fleet, Sessions, Lessons, Memory, Errors, Skills, Artifacts). Shared `_run_export()` helper implements clipboard-then-fallback TextArea pattern for all 7.
- Lessons export honors current filter (recent/most_applied/never_applied/broken). Memory export honors selected collection (None = collection stats, collection = up to 30 docs). Artifacts export honors agent/type filters.
- Errors export button placed in Memory tab Supabase row (Research Papers | Error Log | ⬇ Export Errors).
- Fleet tab received a new header FlowPanel (it had no `_build_fleet_layout` — was built inline in `_build_layout`).
- Anvil service restarted; all callables verified via direct function test (correct frontmatter, Summary heading present for all 7).
- Both `attempt/b061-export-generalize` branches merged to main/master and pushed.

## Key Decisions

- `_run_export()` helper extracts the clipboard-then-fallback pattern from the Research tab handler — reduces 7×20 lines to 7×2 lines in handlers.
- Errors export placed in Memory tab sb_row rather than as a standalone tab (consistent with card spec: "Memory tab → Error Log").
- Sessions bundle skips files starting with `B-` (old naming convention) to avoid parsing non-date-prefixed legacy files.
- No new lessons written: session was clean execution of a well-understood pattern; no novel system behaviors encountered.

## Capability Delta

**New:** All 7 Anvil dashboard tabs export paste-ready markdown bundles for desktop Claude analysis. The pattern proven by B-057 (Research export) is now system-wide. Bill can export any domain view — lessons, memory, sessions, fleet, errors, skills, artifacts — and paste directly into a desktop Claude session for analysis.

**New callables (7):** `get_lessons_bundle`, `get_memory_bundle`, `get_sessions_bundle`, `get_fleet_bundle`, `get_errors_bundle`, `get_skills_bundle`, `get_artifacts_bundle`.

## Lessons Written

0 new lessons (pattern was established in B-057; `_run_export` helper is standard Python refactoring, not a novel system pattern).

## Branches / Commits

- claudis: `attempt/b061-export-generalize` → merged `c3078e1`, deleted
- claude-dashboard: `attempt/b061-export-generalize` → merged `2a72dc4`, deleted
- claudis main: `642f4f6` (merge) → `35f1651` (trajectory)
- claude-dashboard master: `a9ec416` (merge)

## Usage

Session ~25%, weekly ~100%
