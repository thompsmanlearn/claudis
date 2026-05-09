# Chapter 2 Cards — B-094 through B-101
# Reference copy for session continuity. Not a session artifact.
# Generated: 2026-05-08

## B-094: Web search integration
Depends on: Chapter 1 complete. BRAVE_API_KEY now in .env.
- POST /web_search: {query, max_results=10, freshness_window=null} → {results: [{url, title, snippet, source_domain, published_date}]}
- POST /web_fetch: {url} → page content as markdown text. Respects robots.txt.
- DDL: external_api_usage table (provider, endpoint, query, result_count, timestamp)
- ADR: architecture/decisions/web-search-integration.md
- Smoke test: 3 queries (general, technical, current-events). Fetch one URL.
- Touch: .env (done), stats_server.py (live+canonical), DDL, ADR

## B-095: Research charter format and creation flow
Depends on: B-094 (technically independent, depends on B-096 via orchestrator)
- entry_type='charter' allowed in thread_entries CHECK constraint
- Charter sections: Question, Scope, Success criteria, Disqualifying criteria, Initial sub-questions, Source preferences, Time bounds, Memory check
- New uplink callable add_charter(thread_id, charter_content): writes charter entry, supersedes old if exists
- ADR: architecture/decisions/research-charter.md with template
- Skill: skills/research/charter-creation.md (desktop session guidance)
- Anvil: charter entries render at top of thread, section headers visible, "superseded" badge on old ones
- Smoke test: create test thread, add sample charter, verify rendering
- Touch: DDL thread_entries, uplink_server.py, Form1/__init__.py, ADR, skills/research/

## B-096: Research orchestrator — core loop
Depends on: B-094, B-095, B-087
- POST /run_research_cycle: {thread_id} → runs one full cycle, returns cycle summary
- New entry_type='cycle_metadata' in thread_entries
- Cycle steps:
  1. Read charter from thread
  2. Memory pass: query research_findings, lessons_learned, reference_material (ChromaDB) + research_articles (Supabase)
  3. Plan: 3-7 specific searches with query, rationale, expected source type
  4. Execute searches via /web_search. Filter by charter source preferences.
  5. Fetch promising URLs via /web_fetch (cap 8 per cycle)
  6. Synthesize: extract relevant content, note authority/date, aggregate, identify agreement/disagreement/gaps
  7. Write entries: gather, analysis, summary (if applicable), sub_question_candidate(s), cycle_metadata
  8. Self-assess vs charter criteria
- Cost cap: $0.50 per cycle, stop with partial output if hit
- Authorization: Tier 1 for read-only fetches; Tier 2 for anything beyond read-only
- ADR: architecture/decisions/research-orchestrator.md
- Sonnet-class invocation
- Touch: stats_server.py (live+canonical), DDL thread_entries, ADR, Form1 (cycle_metadata rendering)

## B-097: Grader integration for research cycles
Depends on: B-096, B-087
- DDL: add review_type text default 'card' and target_id text to grader_reviews
- POST /grade_research_cycle: {thread_id, cycle_number} → reads cycle entries + charter → Sonnet verdict
- Research verdicts: continue/complete/pause/fail (different from card pass/pause/fail)
- /run_research_cycle calls /grade_research_cycle after writing entries
  - complete → thread state='closed' with close_reason
  - pause/fail → annotation to agent_feedback (target_type='thread')
  - continue → no immediate action (watch state handles next cycle)
- Anvil thread view: cycle grader verdict displayed prominently
- Grader tab: filter by review_type to avoid mixing card and cycle verdicts
- Touch: DDL grader_reviews, stats_server.py, uplink_server.py, Form1/__init__.py

## B-098: Watch state — scheduled re-cycles
Depends on: B-097
- DDL: threads gets watch_enabled bool, watch_interval text, last_watch_cycle_at, next_watch_due_at
- POST /run_watch_cycle: {thread_id} — lighter cycle, recency-focused, fewer queries, no fetch unless clearly novel
- Novelty detection: compare fetched URLs against existing thread_entry URLs for this thread; >80% overlap = no_change
- No-change: write only cycle_metadata with outcome='no_change', update last_watch_cycle_at
- New finding: write normal entries, grade, if significant → thread state='active', Telegram Bill
- Scheduled mechanism: n8n workflow or systemd timer, hourly check for due watch threads
- New uplink callable set_watch_state(thread_id, enabled, interval)
- Anvil thread: watch badge, last cycle time, next due time
- Touch: DDL threads, stats_server.py, uplink_server.py, Form1/__init__.py, n8n workflow or timer

## B-099: Memory consultation discipline
Depends on: B-096
- entry_type='memory_consultation' in thread_entries CHECK constraint
- POST /consult_memory: {question, charter_summary} → queries 4 sources, returns structured results
- add_charter() updated to call /consult_memory after writing charter, writes memory_consultation entry
- Anvil: memory_consultation entries render as "What we already know" block with top results + confidence
- Orchestrator analysis entries include "Memory contribution" section
- Smoke test: add charter on topic with prior coverage, verify memory_consultation entry
- Touch: DDL thread_entries, stats_server.py, uplink_server.py, Form1/__init__.py

## B-100: Sub-question spawning — recursive research
Depends on: B-097
- DDL: threads gets parent_thread_id uuid nullable FK to threads.id
- New uplink callable spawn_thread_from_sub_question(parent_thread_id, sub_question_entry_id, inherit_charter_sections)
  - Creates new thread with parent linkage
  - Copies relevant charter sections if requested
  - Marks sub_question entry as 'spawned' in metadata
- Anvil thread: spawn button on sub_question_candidate entries; "Spawned threads" section; "Parent thread" link
- Child completion writeback: when child grader verdict='complete', write analysis entry to parent with child's summary + link
- Auto-spawn: system_config flag auto_spawn_sub_questions (default false). Tier 2 authorization.
- Smoke test: create thread → run cycle → get sub_question_candidates → spawn child → run child cycle → mark complete → verify parent gets writeback analysis entry
- Touch: DDL threads, uplink_server.py, stats_server.py, Form1/__init__.py

## B-101: Chapter 2 wrap
Depends on: B-094–B-100 all complete
- Deprecate context_engineering_research: status='deprecated', deactivate n8n workflow, update registry entry
- DEEP_DIVE_BRIEF sections 4, 5, 7, 8, 12 updated
- TRAJECTORY: Chapter 2 complete, handoff, next up = Chapter 3
- Run /generate_carry_documents
- Touch: agent_registry, n8n, DEEP_DIVE_BRIEF.md, TRAJECTORY.md
