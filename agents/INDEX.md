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
| behavioral_health_check | /health_check | SpecOps-inspired behavioral analysis. GET `?agent_name=xxx` → fetches last 10 n8n executions → computes success_rate/avg_duration/error_streak/consistency_score → Haiku 0-10 reliability score + promote/retire/investigate/monitor recommendation. Writes to experimental_outputs + sandbox_notify. Complements 4-Pillars Evaluator (static) with dynamic execution-log analysis. Webhook: GET /webhook/behavioral-health-check. Workflow: kdzJPyZtchNA3Seq. **Promoted 2026-04-08** (autonomous, 5-criteria passed: 3 verified success runs, sandbox_notify only, Haiku cost <$0.50/mo, no destructive SQL, Bill notified). First results: daily_research_scout 9/10 PROMOTE, serendipity_engine_prod 8/10 MONITOR, github_issue_tracker 7.5/10 MONITOR. |
| agent_health_monitor | — | Fleet-wide automated health monitoring. **Two parallel branches from webhook:** (1) Active agents: scans all active agents for consecutive n8n execution errors; flags ≥1, auto-pauses ≥3. (2) Building/sandbox agents: detects agents stuck in building/sandbox status >7 days, writes stale_build_scan to experimental_outputs, fires sandbox_notify. Guard Code node prevents empty-array chain-halt. Webhook: POST /webhook/agent-health-monitor. Workflow: w5vypq4vb2rSrwdl. **Promoted 2026-04-12. Extended 2026-04-13** (building/sandbox detection — exec 2277 confirmed both branches). |
| research_synthesis_agent | — | Weekly synthesis of research_findings corpus. Calls stats server /run_research_synthesis (delegates all logic — no hardcoded keys in n8n). Two modes: accumulation (runs 1-3, builds baseline) / synthesis (run 4+, temporal comparison vs prior). ChromaDB 21-day window → Sonnet topic trajectory analysis → experimental_outputs + Telegram digest. Idempotency guard (skips if ran < 5 days ago, override with force=true). Webhook: POST /webhook/research-synthesis. Workflow: JUBCbXJe3TwwpB2T. **Promoted 2026-04-14** (stats server endpoint added, workflow upgraded from 10-node to 4-node, exec 2300 success). |
| arxiv_aadp_pipeline | — | Fetches arXiv preprints Mon/Wed/Fri on agent evaluation, memory retrieval, tool use, multi-agent coordination. Haiku scores for AADP design implications. Writes to research_findings (ChromaDB, source=arxiv_aadp_pipeline) + research_papers (Supabase). Telegram digest per run. Dedup guard (no_candidates if already processed today). Webhook: POST /webhook/arxiv-aadp. Workflow: bZ35VinkRjRT7gYi. **Promoted 2026-04-14** (10 papers written April 5-7; live test 200 OK with dedup; Haiku cost ~$0.10/mo; no destructive SQL; Bill notified. Note: behavioral_health_check unavailable due to expired n8n API key — direct evidence assessment used). |
| context_engineering_research | — | On-demand research agent. 8 sources: HN, arXiv, dev.to, GitHub, lobste.rs, Medium, openai RSS, deepmind RSS. Fetches pages, summarizes with Haiku, writes to research_articles (dedup by URL). Company blogs freshness-driven (30-day window, 3/feed). Logic delegated to stats_server /run_context_research. Webhook: POST /webhook/context-engineering-research. Workflow: gzCSocUFNxTGIzSD. **Built 2026-04-26 (B-055). Updated B-082 2026-05-03 (company RSS feeds added).** |

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
| arxiv_aadp_pipeline | — | **→ Promoted to Production 2026-04-14.** See production entry above. |
| agent_health_monitor | — | **→ Promoted to Production 2026-04-12.** See production entry above. |
| wiki_attention_monitor | /wiki | **→ Promoted to Production 2026-04-01.** See production entry above. |

## Retired

| agent_name | description |
|---|---|
| haiku_self_critic | Two-pass Haiku self-reflection demo. Retired 2026-04-04 — 11 days in sandbox, never tested end-to-end. Mutual agreement: self-reflection belongs integrated into production pipeline, not as standalone demo. Workflow: 1v0JFPdtVte5MJrO (deactivated). |
| serendipity_engine | Sandbox version of Serendipity Engine. Superseded by serendipity_engine_prod (ROhfvqO3yJW6j955) promoted 2026-03-25. Mistakenly re-activated 2026-03-29, immediately deactivated. Retired 2026-04-05 — Bill confirmed not needed. Workflow: ToMG7Y5hkp9UlyJM (deactivated). |

---
*Last updated: 2026-04-26 (lean session B-055) — context_engineering_research added to production. On-demand research agent, HN+arXiv search via stats_server, Haiku summarization, dedup by URL. Webhook live, error logging verified.*

