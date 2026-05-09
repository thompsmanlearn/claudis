# Session: 2026-05-08 — B-097: Grader integration for research cycles

## Directive
Extend the grader to evaluate research cycles: did the cycle advance the charter?

## What Changed
- **DDL on grader_reviews**: Added review_type text default 'card', target_id text. Extended verdict CHECK constraint to include 'continue' and 'complete' (was only 'pass'/'pause'/'fail').
- **stats_server.py** (live + canonical): Added `/grade_research_cycle` endpoint:
  - Reads charter + most recent cycle entries from thread
  - Calls Sonnet with research-specific rubric (separate context from builder)
  - Verdicts: continue/complete/pause/fail
  - Persists to grader_reviews with review_type='research_cycle', target_id=thread_id
  - Handles verdicts: complete → thread state='closed'; pause/fail → annotation + agent_feedback entry
- **anvil/uplink_server.py**: Added get_grader_reviews_by_type(review_type, limit) and get_latest_cycle_verdict(thread_id).
- **Form1/__init__.py**: Cycle grader verdict badge in thread view (icon + verdict + timestamp + rationale). Grader tab: Cards/Research Cycles filter buttons.

## Smoke Test
Thread: e0560a85. Cycle 1 graded:
- verdict: continue ✓
- rationale: meaningful progress but success criteria only partially met ✓  
- 3 criteria each with specific evidence citations ✓
- review_id: 33bd6648 (persisted) ✓

Initial persist failed due to verdict CHECK constraint (`continue` not in pass/pause/fail). Fixed by extending constraint. Lesson: when adding new verdict vocabulary to an existing table, always check existing constraints.

## Unfinished
/run_research_cycle now calls /grade_research_cycle at step 8 — fully wired. Next cycle on this thread will get a live grader verdict in the response.
