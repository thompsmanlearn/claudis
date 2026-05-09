# Session: 2026-05-08 — B-110/B-111: Boot episodic memory + Lesson utilization visibility

## B-110: Boot episodic memory

### Discovery
inject_context_v3 already queries session_memory in all routing paths — the B-110
scope as originally framed ("add session_memory to inject_context_v3") was already done.

The real gap: session_memory only had March 2026 entries (96 total). April/May lean
sessions skipped close-session step 9. inject_context_v3 was querying the right
collection but finding stale data.

### What Changed
- Backfilled two Chapter session narratives to session_memory via memory_add:
  - session_2026-05-08_chapter1: Chapter 1 (B-084–B-093) narrative
  - session_2026-05-08_chapter2: Chapter 2 (B-094–B-101) narrative
  (session_2026-05-08_2300 already existed, covering Chapters 1+2 combined)
- Updated close-session step 9 with "Do not skip" warning and verification step,
  explaining why the April/May gap exists.

### Verification
Semantic query "grader annotation backbone foundation cards B-084 B-087" returned
session_2026-05-08_chapter1 at dist=0.978 (top result) — embeddings working.

## B-111: Lesson utilization visibility

### What Changed
- **stats-server/stats_server.py** (canonical + live): Added `GET /lesson_stats` endpoint.
  Returns: total, never_applied count + %, mean_times_applied, max, top 5 categories by
  count, top 5 most-applied lessons.
- **anvil/uplink_server.py**: Added `get_lesson_stats()` callable (calls /lesson_stats).
- Both services restarted.

### Smoke test results
total=255, never_applied=83 (32.5%), mean=2.45, max=51
Top categories: n8n (40), architecture (33), infrastructure (20), operations (17), knowledge_management (13)
Top applied: "n8n Merge node chooseBranch" (51), "n8n HTTP Request error handling" (47)

### Work queue item closed
context_engineering_research lesson_injector compression task (3e09d9ff) closed with reasoning:
utilization data now shows 32.5% of lessons never applied — compression addresses
token size, not utilization rate. Re-evaluate compression if high-value lessons
remain at times_applied=0 after 2-3 months.

## Lessons Applied
- lesson_memory_tier_taxonomy_aadp_2026-04-06: Applied — confirmed session_memory tier
  is queried at boot; discovered the real gap was missing writes, not missing queries.
