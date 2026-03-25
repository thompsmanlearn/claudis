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

## Platform Infrastructure

| agent_name | telegram_command | description |
|---|---|---|
| lesson_injector | — | Auto-RAG context enrichment. Called by scheduler.sh before every claude -p invocation. Runs 3 semantic searches (lessons_learned, error_patterns, reference_material) and prepends PRE-LOADED CONTEXT block to wake_prompt. Webhook: `POST /webhook/inject-context`. **Promoted 2026-03-25.** |

## Sandbox

| agent_name | telegram_command | description |
|---|---|---|
| agent_evaluator_4pillars | — | Haiku-as-judge 4-pillar evaluation (behavior_consistency, output_quality, reliability, integration_fit). POST `{agent_name}` → scores 1-5 → writes to experimental_outputs. Workflow: kQ5OALBwexLQS7in. Built 2026-03-24. |

## Retired

*Empty — no retired agents.*

---
*Last updated: 2026-03-25 — lesson_injector promoted to Platform Infrastructure*
