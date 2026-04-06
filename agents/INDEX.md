# Agent Index

Read at session start. Lightweight manifest — check before building to avoid rebuilding what exists.

For full workflow JSON, fetch from the appropriate subdirectory. All workflow JSONs have credentials replaced with `{{CREDENTIAL_NAME}}` placeholders.

## Production

| agent_name | telegram_command | description |
|---|---|---|
| daily_briefing_agent | — | Daily 6AM Pacific digest: system health, agent status, errors, work queue |
| telegram_command_agent | — | Watches Telegram; parses commands; routes to work_queue or webhooks |
| weather_agent | /weather | Current weather + 3-day forecast, CA (Open-Meteo) |
| wiki_attention_monitor | /wiki | Wikipedia top page traffic velocity. Fetches Wikimedia pageviews (yesterday), filters spikes >50k views + focus topics, Haiku-clusters into thematic groups, Telegram digest. Writes to experimental_outputs + audit_log. Webhook: POST /webhook/wiki-run. Workflow: IYaj3zv9xj79h9jg. **Promoted 2026-04-01** (4/5 evaluator score, Bill approved). |
| github_weekly_search | — | Searches GitHub for MCP/agent repos weekly (Sunday 6AM UTC); queues findings as gh_weekly_search for Sentinel review |
| serendipity_engine_prod | — | Daily 8AM Pacific: Wikipedia On This Day → Haiku synthesis → surprising historical echo to 2026 → Telegram. Degrades gracefully when Haiku API unavailable. Workflow: ROhfvqO3yJW6j955. **Promoted 2026-03-25.** |
| github_issue_tracker | /gh_issues | Scans thompsmanlearn/claudis for open GitHub issues unactioned >3 days. Fetches via GitHub API (credential store), idempotency guard (skips if already ran today), sends Telegram alert, writes to experimental_outputs + audit_log. Webhook: POST /webhook/github-issue-tracker. Workflow: F2lRufWUOXAGv5GB. **Promoted 2026-04-04** (Bill approved; evaluator concerns verified-resolved: idempotency guard confirmed, empty-array N/A, config externalized). |
| morning_briefing | — | Daily Telegram briefing: work queue status, agent counts (active/sandbox/paused), system health (CPU/RAM/Disk/Temp), 24h output count. No LLM calls. Webhook: POST /webhook/morning-briefing. Workflow: xt8Prqvi7iJlhrVG. **Promoted 2026-04-04** (Bill approved). Note: monitor for overlap with daily_briefing_agent. |

## Platform Infrastructure

| agent_name | telegram_command | description |
|---|---|---|
| lesson_injector | — | Auto-RAG context enrichment. Called by scheduler.sh before every claude -p invocation. Runs 3 semantic searches (lessons_learned, error_patterns, reference_material) and prepends PRE-LOADED CONTEXT block to wake_prompt. Now increments times_applied in Supabase for each retrieved lesson via /lessons_applied stats_server endpoint + Supabase RPC. Webhook: `POST /webhook/inject-context`. Workflow: MFmk28ijs1wMig7h. **Promoted 2026-03-25. Enhanced 2026-03-31.** |
| session_health_reporter | — | Fires after every Sentinel session via scheduler.sh. Queries Supabase (tasks, lessons, exit code, session notes) and commits structured markdown to experiments/sessions/ in GitHub. No Anthropic API calls. Workflow: 5x6G8gFlCxX0YKdM. **Built 2026-03-29.** |
| daily_research_scout | — | Fetches arXiv + HN for 7 rotating AADP topics (3/day), Haiku-scores for relevance ≥7/10, writes experiments/research/YYYY-MM-DD.md + INDEX.md. Cron: 14:00 UTC daily. Webhook: POST /webhook/daily-research-scout. Orchestrated via stats server /run_daily_research. Workflow: xNbmcFrNvqbmhlJW. **Built 2026-03-29.** |
| autonomous_growth_scheduler | — | Fires every 6 hours. If work_queue is empty, inserts a free-mode task rotating: explore → agent_build → research_cycle. Keeps Sentinel working autonomously without waiting for Bill's queue. No usage cap — leans toward growth. Workflow: Lm68vpmIyLfeFawa. **Built 2026-03-29.** |
| usage_stats | /usage | On-demand Telegram report: Claudis state, heartbeat age, active agent count, weekly token reset reminder. Webhook: GET /webhook/usage-stats. Workflow: NeVI0bEB6WsJEf6I. **Built 2026-03-29.** |
| agent_evaluator_4pillars | /evaluate | Haiku-as-judge 4-pillar evaluation (behavior_consistency, output_quality, reliability, integration_fit). GET `?agent_name=xxx` → scores 1-5 → writes to experimental_outputs. Webhook: GET /webhook/evaluate-agent. Workflow: kQ5OALBwexLQS7in. **Promoted 2026-03-30. Fixed 2026-04-01** (flattenContent maxLen 400→1200 — health scan outputs were truncated in Haiku prompt causing false truncation findings). Evidence gaps: does not query audit_log; cannot verify audit convention compliance. |

## Sandbox

| agent_name | telegram_command | description |
|---|---|---|
| architecture_review | — | Biweekly research-to-architecture review. Queries high-scored arxiv_aadp_pipeline findings by component_tag, calls Sonnet to produce fixed decision schema (implement/defer/already_addressed/not_applicable/investigate_further). Queues work_queue items for implement decisions. Writes already_addressed_since back to research_papers to close backward loop. Webhook: POST /webhook/architecture-review. Workflow: 7mVc61pDCIObJFos. **Built 2026-04-05.** |
| arxiv_aadp_pipeline | — | Fetches arXiv preprints on agent evaluation, memory retrieval, tool use, multi-agent coordination. Haiku scores for design implications (what should AADP do differently?). Writes to research_findings (ChromaDB, source=arxiv_aadp_pipeline) + research_papers (Supabase). Telegram digest per run. Webhook: POST /webhook/arxiv-aadp. Workflow: bZ35VinkRjRT7gYi. **Built 2026-04-05.** |
| agent_health_monitor | — | Checks all active agents for consecutive n8n execution failures. Scans execution logs per agent, counts consecutive errors, flags agents needing retirement (≥3 errors). Writes scan + audit_log to experimental_outputs. Notifies via sandbox_notify if issues found. Retirement escalation path: Check Retiring → Retire Agent (PATCH registry) → Notify Retirement. Webhook: POST /webhook/agent-health-monitor. Workflow: w5vypq4vb2rSrwdl. **Built 2026-03-30. Fixed 2026-04-01** (truncation: removed all_reports from output body; audit_log now unconditional). Re-eval 3/5 keep_sandbox (output_quality 3→4). |
| wiki_attention_monitor | /wiki | **→ Promoted to Production 2026-04-01.** See production entry above. |

## Retired

| agent_name | description |
|---|---|
| haiku_self_critic | Two-pass Haiku self-reflection demo. Retired 2026-04-04 — 11 days in sandbox, never tested end-to-end. Mutual agreement: self-reflection belongs integrated into production pipeline, not as standalone demo. Workflow: 1v0JFPdtVte5MJrO (deactivated). |
| serendipity_engine | Sandbox version of Serendipity Engine. Superseded by serendipity_engine_prod (ROhfvqO3yJW6j955) promoted 2026-03-25. Mistakenly re-activated 2026-03-29, immediately deactivated. Retired 2026-04-05 — Bill confirmed not needed. Workflow: ToMG7Y5hkp9UlyJM (deactivated). |

---
*Last updated: 2026-04-05 (Bill session) — arxiv_aadp_pipeline + architecture_review added to sandbox; serendipity_engine retired; inject_context_v2 deployed (intent-expanded retrieval + session_memory); research_papers extended with component_tag, action_type, already_addressed_since.*
