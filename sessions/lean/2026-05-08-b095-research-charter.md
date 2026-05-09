# Session: 2026-05-08 — B-095: Research charter format and creation flow

## Directive
Establish the charter as a structured artifact within the thread system, with desktop session creation flow.

## What Changed
- **DDL on thread_entries**: Dropped and recreated CHECK constraint to add 'charter', 'cycle_metadata', 'memory_consultation' entry types alongside existing 9 types.
- **anvil/uplink_server.py**: Added `add_charter(thread_id, charter_content)` callable. Writes charter entry, triggers /consult_memory (B-099 will complete that path).
- **architecture/decisions/research-charter.md** (new): Charter template with 8 required sections. Parser contract (section headers = `## Section Name`). Storage model (most recent at top, older = superseded).
- **skills/research/charter-creation.md** (new): 9-step desktop session procedure. Quality checklist.
- **Form1/__init__.py**: Charter block at top of thread page (parsed section headers as bold labels). Superseded charter badge in chronological list. New entry type rendering: cycle_metadata (compact), memory_consultation ("What we already know" block). Icons added for all 3 new types.

## Smoke Test
- Created test thread 'TEST: Charter smoke test' (id: e0560a85)
- Inserted charter entry (id: 39b3f771) directly via Supabase
- Charter entry written with correct entry_type='charter' ✓

## What Was Learned
The existing thread_entries CHECK constraint was named `thread_entries_entry_type_check` (already existed). DROP and re-CREATE was needed. The old constraint name suggests this has been managed before — always check before trying to ADD CONSTRAINT.

## Unfinished
add_charter() calls /consult_memory but that endpoint doesn't exist yet (B-099). The call fails silently (non-fatal log warning). Full memory consultation wired after B-099 lands.
