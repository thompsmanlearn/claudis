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

B-038: Create agent_artifacts table and update initial agents to write artifacts
Status: ready
Depends on: B-037
Goal
Create the shared agent_artifacts table in Supabase and update two or three agents to write a row as the final step of their workflow. This proves the cross-agent artifact convention with real data flowing before building the full monitoring surface. Pick agents that already produce meaningful output — the arxiv pipeline, morning briefing, and weather agent are good candidates because they run frequently and produce distinct artifact types.
Context
The table design is specified in the ADR at architecture/decisions/anvil-curation-surface.md, "Shared artifact table" section. Schema: CREATE TABLE agent_artifacts (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, agent_name text NOT NULL, artifact_type text NOT NULL, content jsonb NOT NULL, summary text, confidence float DEFAULT 0.5, consumed_by text[] DEFAULT '{}', reviewed_by_bill bool DEFAULT false, bill_rating int CHECK (bill_rating IN (1, -1)), bill_comment text, created_at timestamptz DEFAULT now()); Each agent's artifact_type value should match what was declared in its output_types in B-037. The artifact row is the agent's handoff — a structured summary of what it produced, not a dump of raw data. Domain-specific tables (like research_papers) coexist for detailed data. The artifact is the cross-cutting summary layer. The agents selected for this card should be ones whose workflows Claude Code can modify confidently. If an agent delegates to a stats_server endpoint, the artifact write may need to happen in the stats_server code rather than the n8n workflow — use whatever approach is cleanest for each agent.
Done when

agent_artifacts table exists in Supabase with the schema above
At least two agents write an artifact row as the final step of their execution
Each artifact has a meaningful summary (human-readable, one or two sentences) and structured content (jsonb with the key output data)
artifact_type values match the agent's declared output_types from B-037
Verify by triggering the agents and confirming rows appear in the table
Session artifact documents which agents were updated and the artifact format each produces
Committed and pushed to main

Scope
Touch: Supabase schema (new table), workflows or stats_server endpoints for the 2-3 selected agents
Do not touch: Anvil dashboard, uplink_server.py, lesson system, ChromaDB, agents not selected for this card
