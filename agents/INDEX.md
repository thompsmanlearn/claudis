# Agent Index

Read at session start. Lightweight manifest — check before building to avoid rebuilding what exists.

For full workflow JSON, fetch from the appropriate subdirectory. All workflow JSONs have credentials replaced with `{{CREDENTIAL_NAME}}` placeholders.

## Production

| agent_name | telegram_command | description |
|---|---|---|
| daily_briefing_agent | — | Daily 6AM Pacific digest: system health, agent status, errors, work queue |
| telegram_command_agent | — | Watches Telegram; parses commands; routes to work_queue or webhooks |
| weather_agent | /weather | Current weather + 3-day forecast, Watsonville CA (Open-Meteo) |
| wiki_attention_monitor | /wiki | Wikipedia page traffic velocity; detects emerging topics; daily 7AM Pacific |

## Sandbox

*Empty — no sandbox agents currently registered.*

## Retired

*Empty — no retired agents.*

---
*Last updated: 2026-03-24*
