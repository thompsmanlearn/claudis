# Agent Index

Read at session start. Lightweight manifest — check before building to avoid rebuilding what exists.

For full workflow JSON, fetch from the appropriate subdirectory. All workflow JSONs have credentials replaced with `{{CREDENTIAL_NAME}}` placeholders.

## Production

| agent_name | telegram_command | description |
|---|---|---|
| daily_briefing_agent | — | Daily 6AM Pacific digest: system health, agent status, errors, work queue |
| telegram_command_agent | — | Watches Telegram; parses commands; routes to work_queue or webhooks |
| weather_agent | /weather | Current weather + 3-day forecast, CA (Open-Meteo) |
| wiki_attention_monitor | /wiki | Wikipedia page traffic velocity; detects emerging topics; daily 7AM Pacific |
| github_weekly_search | — | Searches GitHub for MCP/agent repos weekly (Sunday 6AM UTC); queues findings as gh_weekly_search for Sentinel review |
| serendipity_engine_prod | — | Daily 8AM Pacific: Wikipedia On This Day → Haiku synthesis → surprising historical echo to 2026 → Telegram. Degrades gracefully when Haiku API unavailable. Workflow: ROhfvqO3yJW6j955. **Promoted 2026-03-25.** |

## Platform Infrastructure

| agent_name | telegram_command | description |
|---|---|---|
| lesson_injector | — | Auto-RAG context enrichment. Called by scheduler.sh before every claude -p invocation. Runs 3 semantic searches (lessons_learned, error_patterns, reference_material) and prepends PRE-LOADED CONTEXT block to wake_prompt. Webhook: `POST /webhook/inject-context`. **Promoted 2026-03-25.** |
| session_health_reporter | — | Fires after every Sentinel session via scheduler.sh. Queries Supabase (tasks, lessons, exit code, session notes) and commits structured markdown to experiments/sessions/ in GitHub. No Anthropic API calls. Workflow: 5x6G8gFlCxX0YKdM. **Built 2026-03-29.** |
| daily_research_scout | — | Fetches arXiv + HN for 7 rotating AADP topics (3/day), Haiku-scores for relevance ≥7/10, writes experiments/research/YYYY-MM-DD.md + INDEX.md. Cron: 14:00 UTC daily. Webhook: POST /webhook/daily-research-scout. Orchestrated via stats server /run_daily_research. Workflow: xNbmcFrNvqbmhlJW. **Built 2026-03-29.** |
| autonomous_growth_scheduler | — | Fires every 6 hours. If work_queue is empty, inserts a free-mode task rotating: explore → agent_build → research_cycle. Keeps Sentinel working autonomously without waiting for Bill's queue. No usage cap — leans toward growth. Workflow: Lm68vpmIyLfeFawa. **Built 2026-03-29.** |
| usage_stats | /usage | On-demand Telegram report: Claudis state, heartbeat age, active agent count, weekly token reset reminder. Webhook: GET /webhook/usage-stats. Workflow: NeVI0bEB6WsJEf6I. **Built 2026-03-29.** |

## Sandbox

| agent_name | telegram_command | description |
|---|---|---|
| agent_evaluator_4pillars | — | Haiku-as-judge 4-pillar evaluation (behavior_consistency, output_quality, reliability, integration_fit). POST `{agent_name}` → scores 1-5 → writes to experimental_outputs. Workflow: kQ5OALBwexLQS7in. Built 2026-03-24. |

## Retired

*Empty — no retired agents.*

---
*Last updated: 2026-03-29 — usage_stats /usage command added to Platform Infrastructure*
