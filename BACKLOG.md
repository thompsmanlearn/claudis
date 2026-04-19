B-037: Populate agent input/output declarations in registry
Status: ready
Depends on: B-034
Goal
Populate the input_types and output_types fields in the agent_registry table for all active and protected agents. These declarations create the dependency graph that the cross-agent artifact convention relies on — each agent explicitly states what data sources it reads and what it produces. Without this, the artifact routing has nothing to route on.
Context
The agent_registry table already has input_types and output_types columns (text arrays). They are probably empty or meaningless for most agents. This card is a data population task, not a schema change. The declarations should reflect what each agent actually does today — what tables or data sources it reads, what it writes or produces. Use the agent workflow logic and stats_server endpoints as the source of truth, not aspirational descriptions. See ADR at architecture/decisions/anvil-curation-surface.md, "Agent input/output declarations" section, for example declarations. The full agent list with workflow IDs is in DEEP_DIVE_BRIEF.md Section 8. Only populate for agents with status active or paused — skip retired or broken.
Example declarations for reference (verify against actual workflow logic before writing):

arxiv_aadp_pipeline: input_types [], output_types ["research_papers"]
morning_briefing: input_types ["system_status", "error_logs", "agent_feedback"], output_types ["daily_briefing"]
weather_agent: input_types [], output_types ["weather_forecast"]
agent_health_monitor: input_types ["error_logs", "agent_registry"], output_types ["health_scan"]

Done when

Every active and paused agent in agent_registry has input_types and output_types populated with accurate arrays
Declarations reflect what the agent actually reads and writes today, verified against workflow logic or stats_server code
A session artifact documents the final declarations for each agent with a one-line rationale
Committed and pushed to main

Scope
Touch: Supabase agent_registry table (UPDATE input_types and output_types only)
Do not touch: agent workflows, uplink_server.py, dashboard code, stats_server.py, agent status fields
