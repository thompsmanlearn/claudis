# ADR: Capability Curation

**Date:** 2026-05-08
**Status:** Active (B-109)

## Context

The system accumulates agents, skills, and capabilities over time. Without a periodic
review, the registry fills with entries that are paused-but-never-reactivated, built
without a workflow, or registered but never triggered. These create noise in attention
queues, inflate searches, and mislead future sessions about what's actually running.

## Decision

Run a capability curation scan periodically. The scan writes `agent_feedback` annotations
for each candidate (Tier 2: ask Bill, don't act autonomously). Bill acts via Anvil callables.

## Signals

| Signal | Target | Recommended action |
|--------|--------|--------------------|
| `status=paused` AND `workflow_id IS NULL` | agent_registry | Retire (nothing to restore) |
| `status=paused` AND `updated_at > 90 days` | agent_registry | Review intent — retire or reactivate |
| `times_used = 0` since registration | skills_registry | Monitor; revise `applies_when` if stale |
| References deprecated/retired agent | capabilities | Mark deprecated |

**Exceptions:** `autonomous_growth_scheduler` is intentionally paused by Bill — skip it
in all scans. `claude_code_master` has no workflow by design.

## Callables

Bill acts on curation candidates via:
- `retire_agent(agent_name, reason)` — sets status=retired, clears workflow_id, writes annotation
- `retire_skill(skill_name, reason)` — sets status=retired, writes annotation

Both are in `anvil/uplink_server.py`.

## Cadence

Initially manual: Bill triggers `/run_capability_curation_scan` from stats server or
requests a curation pass in a lean session. After first pass establishes a baseline,
schedule quarterly (or when fleet grows by 10+ agents).

## How to add signals

Add a new query block in `/run_capability_curation_scan` (stats_server.py). Each signal
block: query the table, filter for candidates, call `_write_annotation()` for each.
Update this ADR's signals table.

## First run results (2026-05-08)

6 agent candidates (paused + no workflow_id): research_agent, greeter_bot, macro_pulse,
ai_frontier_scout, coast_intelligence, heritage_watch.
4 skill candidates (times_used=0): agent-development, anvil, research, system-ops.

greeter_bot retired immediately (54 days paused, no workflow, no stated purpose).
Remaining 9 candidates in attention queue for Bill's review.
