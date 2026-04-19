# Session: 2026-04-18 — B-037: Agent Input/Output Declarations

## Directive
Populate `input_types` and `output_types` fields in `agent_registry` for all active and paused agents, using actual workflow logic as source of truth.

## What Changed

Updated 9 agents where declarations were empty or materially wrong:

| Agent | input_types | output_types | Rationale |
|-------|-------------|--------------|-----------|
| `autonomous_growth_scheduler` | `["work_queue", "system_config"]` | `["work_queue"]` | Workflow reads work_queue to gate insertion, reads system_config for rotation counter, writes work_queue task |
| `processed_content_agent` | `["github_repo_processed"]` | `["supabase_resources", "telegram_message"]` | Delegates to stats_server /run_processed_content_agent; description confirms GitHub processed/ → resources table |
| `resource_scout_reddit` | `["reddit_api", "supabase_inquiry_threads", "supabase_refinements", "supabase_resources"]` | `["supabase_resources", "audit_log"]` | Workflow fetches 3 subreddits, reads inquiry_threads+refinements for scoring context, reads resources for dedup, writes qualified posts to resources |
| `morning_briefing` | `["work_queue", "agent_registry", "system_status", "experimental_outputs", "agent_feedback"]` | `["telegram_message", "experimental_outputs", "audit_log"]` | Workflow confirmed: 5 sequential fetches before building message; agent_feedback fetch added 2026-04-19 |
| `github_issue_tracker` | `["github_api", "supabase_experimental_outputs"]` | `["experimental_outputs", "telegram_message", "audit_log"]` | Workflow reads GitHub issues API + checks experimental_outputs for idempotency; previously only had "webhook_trigger" |
| `lesson_injector` | `["chromadb_lessons_learned", "chromadb_error_patterns", "chromadb_reference_material"]` | `["context_block"]` | Delegates to inject_context_v3 which queries 3 ChromaDB collections; trigger mechanism removed from input_types |
| `usage_stats` | `["system_config"]` | `["telegram_message"]` | Work queue node exists in workflow but is NOT connected — only system_config heartbeat keys are in the live execution path |
| `weather_agent` | `["open_meteo_api"]` | `["telegram_message"]` | Workflow fetches open-meteo.com/v1/forecast only; telegram_command is a trigger mechanism, not a data source |
| `heritage_watch` | `["web_scrape_heritage", "web_scrape_news_feeds", "federal_register_api"]` | `["telegram_message"]` | No workflow; inferred from description (Heritage, 19th News, NWLC, Ms. Magazine, Federal Register, Google News) |

Left unchanged (20 agents with accurate existing declarations):
`agent_evaluator_4pillars`, `agent_health_monitor`, `architecture_review`, `arxiv_aadp_pipeline`, `behavioral_health_check`, `claude_code_master`, `feedback_agent`, `research_synthesis_agent`, `session_health_reporter`, `telegram_command_agent`, `ai_frontier_scout`, `coast_intelligence`, `cosmos_report`, `daily_briefing_agent`, `daily_research_scout`, `greeter_bot`, `macro_pulse`, `research_agent`, `serendipity_engine_prod`, `session_report_agent`, `wiki_attention_monitor`

## What Was Learned

- `webhook_trigger` had leaked into `input_types` on several agents — triggers are execution mechanisms, not data sources. The dependency graph only makes sense with actual data sources.
- `usage_stats` workflow has a dead node: `Query Work Queue` is defined but not wired into the execution chain. Declarations must reflect what actually runs, not what's in the node list.
- `processed_content_agent` delegates entirely to stats_server — the n8n workflow is just a thin trigger wrapper. Declarations describe the logical data flow, not the n8n implementation layer.

## Unfinished

- `heritage_watch` has no workflow_id — declarations are inferred from description only. If the workflow is ever built, verify against actual implementation.
- Next step per ADR: create `agent_artifacts` table and update 2-3 agents to write artifacts using these output_types as the `artifact_type` values.
