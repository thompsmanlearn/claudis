# Session: 2026-05-08 — B-109: First capability curation pass

Code commit: (this session)

## What Changed

- **stats-server/stats_server.py** (canonical + live): Added `POST /run_capability_curation_scan`.
  Signals: (1) agent paused + no workflow_id → retire recommendation, (2) skill times_used=0
  → monitor recommendation. Skips autonomous_growth_scheduler (intentionally paused per memory).
  Writes each candidate as agent_feedback annotation (action_session=capability_curator,
  intent_type=question in metadata).
- **anvil/uplink_server.py**: Added `retire_agent(agent_name, reason)` and
  `retire_skill(skill_name, reason)` callables. Both update status=retired, write
  state_change annotation.
- **architecture/decisions/capability-curation.md**: New ADR documenting signals,
  callables, cadence, and how to extend.

## Scan Results

6 agent retire candidates (all paused + no workflow_id):
  research_agent, greeter_bot, macro_pulse, ai_frontier_scout, coast_intelligence, heritage_watch

4 skill monitor candidates (times_used=0):
  agent-development, anvil, research, system-ops

All 10 written as agent_feedback annotations (processed=false) — visible in Anvil attention queue.

## Smoke Test

- 10 annotations confirmed in agent_feedback (query verified).
- Retired greeter_bot (54 days paused, no workflow, no purpose): annotation marked processed,
  agent_registry status=retired confirmed.
- retire_agent callable deployed, services restarted clean.

## Notes

- No `last_used` column in agent_registry — paused+no_workflow is the primary signal.
- Scanning capabilities table for deprecated-agent references deferred (capabilities table
  sparsely populated — not enough signal yet).
- 9 remaining candidates in queue for Bill's Anvil review.

## Lessons Applied
None pre-loaded were directly triggered.
