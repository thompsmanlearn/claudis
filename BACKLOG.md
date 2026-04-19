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



B-039: Sessions tab on Anvil dashboard

Status: ready Depends on: B-033
Goal

Add a Sessions tab to the Anvil dashboard so Bill can see what Claude Code is doing right now and review completed session artifacts from a browser or phone. This closes the visibility gap — currently Bill has no way to know what a session accomplished unless he opens the repo or asks in a desktop session.
Context

There are two parts to this: live status and history. Live status depends on B-033's get_lean_status() callable which returns whether a session is running. This card extends that with richer state. Create a session_status Supabase table that lean sessions write to as they progress. The lean boot chain (LEAN_BOOT.md → PROTECTED.md → DIRECTIVES.md → etc.) has natural phase boundaries. Adding a Supabase write at each phase transition gives Bill a live view of where the session is: booting, reading context, executing, committing, writing artifact. The current card ID and a short current_action text field give additional context. Schema: CREATE TABLE session_status (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, session_id text, card_id text, phase text, current_action text, started_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now()); History is simpler. Session artifacts already land in ~/aadp/claudis/sessions/lean/ as markdown files. A callable that reads the directory listing and returns file contents gives the tab a chronological session history with drill-down. The tab navigation pattern already exists from B-036 (Lessons tab). This card adds a third tab. See ADR at architecture/decisions/anvil-curation-surface.md, Sessions section. Anvil skill reference at skills/anvil/REFERENCE.md.
Done when

    session_status table exists in Supabase with the schema above
    lean_runner.sh (or boot chain scripts) writes phase transitions to session_status — at minimum: started, executing, complete
    Sessions tab on dashboard shows current session state (idle, or running with phase and card ID)
    Sessions tab shows a list of recent session artifacts with titles and dates
    Tapping a session artifact shows its full content
    Uplink callables registered: get_session_status(), get_session_artifacts(limit)
    Usable at phone width
    Both repos committed and pushed (claudis main, claude-dashboard master)

Scope

Touch: ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py, Supabase schema (new table), lean_runner.sh or boot chain scripts (phase writes only) Do not touch: stats_server.py core logic, agent workflows, lesson system, LEAN_BOOT.md content (only add writes, don't change boot sequence)

B-040: Memory tab on Anvil dashboard

Status: ready Depends on: B-036
Goal

Add a Memory tab to the Anvil dashboard so Bill can browse, search, and clean up ChromaDB collections and key Supabase tables directly from a browser or phone. Right now the only way to see what's in the system's memory is through Claude Code terminal queries. This gives Bill direct visibility into the knowledge the system is operating on, and the ability to remove stale or bad entries without needing a session.
Context

ChromaDB has seven collections: lessons_learned (224+), reference_material (173), research_findings (141), session_memory (71+), error_patterns (15), self_diagnostics (11), agent_templates (4). All use all-MiniLM-L6-v2 embeddings at localhost:8000. Critical gotcha: never include "embeddings" in the include list for bulk-get operations — causes IndexError at scale. Use ["documents", "metadatas"] only. The tab has two sections. ChromaDB browser: collection picker showing name and document count. Selecting a collection shows a paginated list of documents with metadata. Semantic search input queries the selected collection and returns ranked results with distances. Delete button per document removes from ChromaDB (and from Supabase lessons_learned if the collection is lessons_learned — use the chromadb_id link). Supabase browser: not a generic SQL console. Curated views for key tables — research_papers (title, relevance_score, status, discovered_at), error_logs (unresolved errors, workflow_name, timestamp), agent_artifacts (recent artifacts by type). Each view has sensible default filters and sort order. The tab navigation pattern exists from B-036 and B-039. Anvil skill reference at skills/anvil/REFERENCE.md. See ADR at architecture/decisions/anvil-curation-surface.md, Memory section.
Done when

    Memory tab exists on the dashboard with ChromaDB and Supabase sections
    ChromaDB section shows collection list with document counts
    Selecting a collection displays paginated documents with metadata
    Semantic search works against the selected collection
    Delete removes a document from ChromaDB (and Supabase lessons_learned if applicable)
    Supabase section shows curated views for at least research_papers and error_logs
    Usable at phone width
    Uplink callables registered: get_collection_stats(), browse_collection(name, limit, offset), search_collection(name, query), delete_document(collection, doc_id), get_table_rows(table, filters, limit)
    Both repos committed and pushed (claudis main, claude-dashboard master)

Scope

Touch: ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py Do not touch: ChromaDB collection structure or embeddings model, stats_server.py, agent workflows, lesson injection logic
