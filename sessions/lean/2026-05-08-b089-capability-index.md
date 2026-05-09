# Session: 2026-05-08 — B-089: Capability index

## Directive
Unify CATALOG.md, agent_registry, and capabilities table into a coherent three-registry model.

## What Changed
- **DDL on skills_registry**: Table pre-existed with schema (id, name, description, trigger_keywords, file_path, times_loaded, last_loaded). Added: applies_when, also_triggers_when, provides, status, times_used, last_used columns.
- **skills_registry population**: All 6 skills updated with applies_when, also_triggers_when, provides, file_path from CATALOG.md.
- **DDL on capabilities**: Added status, last_used, times_used, authorization_tier, dependencies columns (via B-088 + this card). All 114 existing rows have status='active'.
- **DDL on agent_registry**: Added skills_used text[], capabilities_provided text[] columns.
- **architecture/decisions/capability-index.md** (new): Three-registry ADR defining what each holds, status lifecycle, and build discipline.
- **skills/CATALOG.md**: Added three-line header noting skills_registry as authoritative source.
- **close-session.md** (both copies): Step 8 updated to include registry check discipline.
- **anvil/uplink_server.py**: Added get_capabilities() and get_skills_registry() callables.

## What Was Learned
skills_registry pre-existed with a partial schema. The CREATE TABLE IF NOT EXISTS silently did nothing. Always check column list before assuming a new table was created. The existing schema used `times_loaded`/`last_loaded` rather than `times_used`/`last_used` — both sets of columns now exist; times_used/last_used are the canonical names going forward (B-090 will increment these).

capabilities table: 114 rows, all active, populated in prior sessions. Content not audited — too large for this session's scope. Any drift should surface via the close-session registry check over subsequent sessions.

## Smoke Test
queries against skills_registry and capabilities confirmed via supabase_exec_sql: 6 skills with applies_when populated, 114 capabilities all active.

## Unfinished
agent_registry.skills_used[] and capabilities_provided[] are empty for all agents — linking is future work as agents are next touched. B-090 will use skills_registry.applies_when for /resolve_skills matching.
