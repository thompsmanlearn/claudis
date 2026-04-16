# Session: 2026-04-16 — capability-amplifier-seed

## Directive
B-017: Create GitHub file structure and seed first inquiry thread.

## What Changed

### GitHub (claudis repo)
- `INQUIRIES.md` — created at repo root. Sections: Active Threads, New Questions, Refinements, Paused. Seed thread documented with thread_id and all 4 refinements.
- `processed/.gitkeep` — created at repo root.

### Supabase
- `inquiry_threads` — 1 row inserted:
  - id: `c831712e-61e0-45e7-8f0e-4ccbc590e432`
  - domain_name: `game-development`
  - description: "Game development with Blender and UE5, using AI to skip traditional learning curves."
  - status: `active`, parent_id: null (trunk)

- `refinements` — 4 rows inserted, all linked to thread `c831712e`, source = `github`:
  - `a3d45ca3` — "Not tutorials — AI-assisted workflows and tools"
  - `362947b7` — "More like practical tools I can try today (e.g. Meshy AI) than theory"
  - `65a72f67` — "How people are using Claude and other AI for Blender Python scripting and UE5 Blueprints"
  - `c8bcb32d` — "Tool announcements and new releases over educational content"

### Verification
- B-016 dependency confirmed: all 5 Capability Amplifier tables exist in Supabase before proceeding.
- Short-pointer path used: DIRECTIVES.md contained `Run: B-017`; BACKLOG.md read; card executed.

## What Was Learned
- The `inquiry_threads` table has `domain_name` (NOT NULL) in addition to `description` — the architecture doc's schema differs slightly from what B-016 created. Used `game-development` as the domain_name slug.
- A single CTE (`WITH trunk AS (INSERT ... RETURNING id) INSERT INTO refinements ...`) handles the FK dependency cleanly without a second round-trip.

## Unfinished
- INQUIRIES.md New Questions and Refinements sections are stubs — the processing pipeline (the agent that reads these and creates rows) is not yet built. That's a future card.
- `processed/` directory exists but no processing logic yet routes files there.
