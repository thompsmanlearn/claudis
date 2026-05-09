# Session: 2026-05-08 — B-090: Boot-time skill resolution

## Directive
Replace judgment-based skill matching in LEAN_BOOT step 6 with deterministic /resolve_skills endpoint.

## What Changed
- **stats_server.py** (live + canonical): Added `/resolve_skills` endpoint:
  - Fetches active skills from skills_registry
  - Calls Haiku with directive text and skill applies_when/also_triggers_when fields
  - Returns matches above confidence threshold (0.6)
  - Increments skills_registry.times_used + last_used when increment_on_load=true
  - Fallback: if Haiku fails, returns empty list (LEAN_BOOT falls back to CATALOG.md)
- **LEAN_BOOT.md step 6**: Updated to call /resolve_skills. Fallback to CATALOG.md judgment if stats server unreachable.
- **~/aadp/LEAN_BOOT.md**: Updated via cp.

## Smoke Tests
1. Anvil directive → anvil (1.0) ✓
2. Agent-build directive → agent-development (1.0), system-ops (0.7), communication (0.7) ✓
3. Ambiguous directive → 2 skills above threshold (wide net, acceptable) ✓

## What Was Learned
Haiku confidently returns 1.0 for clear directive-skill matches and 0.7 for secondary matches. The wide-net behavior on ambiguous directives (2 skills) is acceptable — loading extra context is cheaper than missing a relevant skill. If over-loading becomes an issue, raise threshold from 0.6 to 0.7.

## Unfinished
lean_runner.sh pre-resolution (resolving skills before the session starts, per the card's optional improvement) — deferred. In-session resolution via LEAN_BOOT step 6 is sufficient for now.
