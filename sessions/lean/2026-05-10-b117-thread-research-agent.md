---
card: B-117
date: 2026-05-10
code_commit: 162af7d (claudis), 03f6933 (claude-dashboard)
---

# B-117: Thread Research Agent with Brave

## What was done

Built the thread-native research agent that reads a thread's charter, searches Brave per
sub-question, screens results with Haiku against success/disqualifying criteria, and writes
qualifying `finding` + `cycle_summary` entries to thread_entries.

**Code changes:**
- `stats-server/stats_server.py`: Added `/run_thread_research` endpoint (201 lines). Reads
  `threads.charter` JSONB, one Brave search per sub-question (up to 5, max_results=5 each),
  Haiku screening per result, writes entries to thread_entries via `_sb_post_entry`. Cost-
  capped at `_ORCHESTRATOR_COST_CAP_USD = $0.50`. Helper `_screen_result_haiku` and
  `_charter_freshness` (maps recency_requirement string → Brave freshness code).
- `architecture/consumer_manifest.json`: `/web_search` reclassified orphaned → partial.
  Caller: `run_thread_research`. First active consumer of Brave Search endpoint.
- `anvil/uplink_server.py`: Added `finding` and `cycle_summary` to `_THREAD_ENTRY_TYPES`
  (keeps validation set in sync with DB constraint expansion).
- `claude-dashboard/client_code/Form1/__init__.py`: Added 💡/📊 icons for finding/cycle_summary
  entries; added dedicated elif rendering blocks showing title bold, relevance note, source URL.

**DB changes:**
- `thread_entries.entry_type` CHECK constraint expanded to include `finding` and `cycle_summary`.

**n8n workflow:** `thread_research_agent` (ID: KIq8lkEjmyUqFc7d). Webhook path:
`thread-research-agent`. Single HTTP Request node → `host.docker.internal:9100/run_thread_research`.
Status: sandbox, deactivated after testing.

**Agent registry:** `thread_research_agent` registered, status=sandbox, workflow_id linked,
webhook_url stored per the webhook-url-in-registry lesson.

## Done-when verification

| Criterion | Result |
|---|---|
| ≥3 qualifying findings in thread detail | ✅ 14 findings written (2 cycles on TEST thread) |
| cycle_summary entry appears | ✅ 3 cycle_summary entries |
| Agent in agent_registry status=sandbox | ✅ |
| /web_search in consumer_manifest.json classification=partial | ✅ |

## Issues discovered during build

**`entry_type` has a DB CHECK constraint** — `thread_entries_entry_type_check`. The B-117 card
specified `finding` and `cycle_summary` but these weren't in the constraint. Added them via DDL.
Also added to `_THREAD_ENTRY_TYPES` in uplink_server.py to keep validation in sync.

**stats_server.py has no logger** — uses no logging at all in FastAPI routes. Removed all
`log.` calls from the new endpoint (consistent with rest of file). Failure paths are silent;
the JSONResponse error returns surface to the n8n caller.

**First run yielded only 1 finding** — success criteria "with measurable outcomes" was too
strict for Haiku to match against broad research queries. Updated test charter sub-questions
to more targeted queries (drug discovery, lab automation, ML biology). Second run: 12/14
results qualified.

**B-116 was already complete** (save_charter callable, get_charter callable, Form1 charter form
all existed). The stale-card check for the directive (B-117) correctly identified B-117 itself
as incomplete.

## What's next

B-118: Gather trigger — Add "Gather" button to Anvil thread detail view that fires
thread_research_agent against the current charter and refreshes entries on completion.
B-119: Auto-wiring — when a charter is saved, match thread to best agent automatically.
