# Session: 2026-04-18 — B-038: agent_artifacts table and initial artifact writers

## Directive
B-038: Create the `agent_artifacts` table in Supabase and update 2-3 agents to write artifacts as the final step of their workflow. Prove the cross-agent artifact convention with real data flowing.

## What Changed

### Supabase
- Created `agent_artifacts` table with full ADR schema: `id`, `agent_name`, `artifact_type`, `content` (jsonb), `summary`, `confidence`, `consumed_by`, `reviewed_by_bill`, `bill_rating`, `bill_comment`, `created_at`

### morning_briefing (n8n workflow xt8Prqvi7iJlhrVG)
- Added "Write Artifact" node (HTTP POST → agent_artifacts) as third parallel branch from "Build Message"
- artifact_type: `experimental_outputs` (matches declared output_types)
- content: `{today, wq_count, agent_counts, output_count}`
- summary: human-readable one-liner, e.g. "Daily briefing Sat, Apr 18: 0 queue items, 18 active agents"

### weather_agent (n8n workflow F3khynqQBUXSnadu)
- Added "Write Artifact" node as parallel branch from "Format Weather"
- Added `webhookId: "weather"` to webhook node (was missing — required for n8n 2.6.4 route registration)
- artifact_type: `telegram_message` (matches declared output_types)
- content: `{current, daily, retrieved_at}` (raw API data from open-meteo)
- summary: e.g. "Weather Apr 18: 72°F, code 3"

### arxiv_aadp_pipeline (stats_server.py `/run_arxiv_aadp`)
- Added artifact write block before the return statement
- artifact_type: `research_papers_supabase` (matches declared output_types)
- content: `{date, candidates_fetched, papers_written, papers: [{title, score, url, implication}]}`
- summary: "{N} papers ingested on {date} (top: {title})" or "No papers met threshold on {date}"
- confidence: 0.9

## Verified
- morning_briefing: artifact row confirmed in table (summary: "Daily briefing Sat, Apr 18: 0 queue items, 18 active agents")
- weather_agent: artifact row confirmed in table (summary: "Weather Apr 18: 72°F, code 3")
- arxiv_aadp_pipeline: artifact row confirmed in table (summary: "No papers met threshold on 2026-04-19" — ran force=true, no papers scored ≥7 today)

## What Was Learned
- n8n weather workflow had no `webhookId` on the Webhook node and was still working — unclear why. After workflow update via API, the webhook path lost registration. Adding explicit `webhookId: "weather"` matching the path fixed it. Always include `webhookId` when updating webhook-triggered workflows via API.
- The `_sb_upsert` helper in stats_server.py works fine for plain inserts to tables with uuid PKs — the `Prefer: resolution=merge-duplicates` header is harmless when there's no conflict.

## Unfinished
- B-038 is complete. Next: Anvil Artifacts tab (depends on this convention being live — it now is).
- The morning_briefing also still needs the feedback consumer card (agent_feedback → Telegram alert pattern).

## Lessons Applied
- Skill agent-development: webhookId pattern, workflow creation/update rules
