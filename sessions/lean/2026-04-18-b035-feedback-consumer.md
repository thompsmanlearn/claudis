# Session: 2026-04-18 — B-035: Add agent feedback summary to morning briefing

## Directive
Add a "Recent Feedback" section to the morning briefing (workflow xt8Prqvi7iJlhrVG) that reads from the agent_feedback table and surfaces thumbs-down ratings and comments from the last 24 hours.

## What Changed
- **n8n workflow xt8Prqvi7iJlhrVG (Morning Briefing)** updated:
  - Added `Fetch Agent Feedback` node (HTTP GET, continueOnFail: true) querying `agent_feedback` for last 24h, ordered by created_at desc
  - Inserted into chain between `Fetch 24h Outputs` and `Build Message`
  - Updated `Build Message` jsCode to parse feedback, group by rating (-1 = 👎, 1 = 👍), and append a "Recent Feedback:" section to the Telegram message
  - Added Telegram 4000-char safety truncation to Build Message
- Live test: execution 2437 succeeded. Message included "Recent Feedback: none" (table is empty — empty path confirmed working).

## What Was Learned
- The agent_feedback table schema: id (uuid), agent_name (text), rating (int), comment (text), created_at (timestamptz). Empty on 2026-04-18.
- The n8n HTTP Request node with continueOnFail wraps errors gracefully — the try/catch in Build Message handles both null response and parse failure without breaking the briefing.
- Telegram truncation at 4000 chars (not 4096) added as a safety measure per communication skill guidance. This was missing from the original Build Message.

## Unfinished
- agent_feedback table has no data yet — the 👎/👍 rendering paths are code-verified but not live-verified. Will self-validate once Bill submits feedback via the Anvil dashboard.
- Feedback consumer is minimum viable. Future: if thumbs-down count exceeds a threshold, add a work_queue item automatically. That's a future card.
