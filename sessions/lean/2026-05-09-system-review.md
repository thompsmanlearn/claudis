# Session: System Review
**Date:** 2026-05-09
**Directive:** System review — examine, test, and revise before Chapter 4.

---

## What was done

### Task 1: B-115-cmt executed + B-114 pipeline verified

- Confirmed B-114 pipeline live: `/classify_annotation`, `/generate_card_from_comment`, `/export_comment_driven_results` in stats_server.py; `annotate()` and `export_comment_driven_results()` callables in uplink_server.py.
- Verified B-115-cmt provenance: `agent_feedback` bb49d2c9 has `intent_type=correction, confidence=0.95, generated_card_id=B-115-cmt`. Pipeline fired correctly.
- Executed B-115-cmt: updated `agent_registry` for `architecture_review`:
  - description: "Biweekly review…" → "Architecture review… Has run once (2026-04-05, initial setup); biweekly cadence is configured but recurrence is unconfirmed."
  - schedule: "Biweekly Sunday 16:00 UTC" → "Every other Sunday 16:00 UTC — configured, recurrence unconfirmed"
- Grader verdict: **fail** (see revision finding #1 — data-only card grader blind spot).
- Direct SELECT confirms all done-when criteria met.

### Task 2: Comment-driven export verified

`export_comment_driven_results` correctly bundles: original comment text, generated card text (truncated), grader verdict, count=1. Export endpoint is working as designed. Grader verdict shows "fail" in bundle due to blind spot — not an export defect.

### Task 3: Curation queue worked

**Agents retired (5):** ai_frontier_scout, coast_intelligence, heritage_watch, macro_pulse, research_agent — all paused with no workflow_id, no path to restore. Retirement annotations written to agent_feedback.

**Skills kept (4, monitor):** agent-development, research, system-ops, anvil — all times_used=0 at time of flag. After today's boot, agent-development=1, system-ops=1, triage=2. Skills are loading; curation flags were valid at generation time.

All 10 curation feedback items marked processed.

### Task 4: "Document AADP on the Site" project confirmed complete

All 8 nodes verified done. All 6 HTML pages present: index, fleet, capabilities, architecture, sessions, direction. `aadp_projects` status set to `complete`. project_completion feedback item (ac6a351a) marked processed.

### Task 5: Health check

| Metric | Value | Status |
|--------|-------|--------|
| Unresolved error_logs | 0 | ✓ |
| lessons_learned NULL chromadb_ids | 0 | ✓ |
| Lessons total / never-applied | 255 / 83 (32.5%) | Watch |
| session_memory (ChromaDB) | 100 entries | ✓ |
| Pending work_queue tasks | 1 (agent_build, 2026-05-03) | Needs decision |

---

## Revision findings (surface only — no builds)

**1. Grader blind spot for data-only cards**
Cards whose only output is a Supabase row update (no file changes) will always grade "fail" — grader reads git diff only. Export bundles show misleading "fail" for valid work. Options: add `verify_sql` to done-when schema; add a `data_only` card type that skips grader; or extend grader to run a verification query.
_Suggest: write a card to add `verify_sql` support to the grader._

**2. generate_card_from_comment uses wrong table name**
B-115-cmt specified `agents` table; actual table is `agent_registry`. Sonnet prompt for `/generate_card_from_comment` lacks DB schema context. Future correction/gap cards touching Supabase may reference wrong tables.
_Suggest: inject a schema summary (table names + key columns) into the Sonnet prompt at card generation time._

**3. Lesson never-applied rate at 32.5%**
83 of 255 lessons have never been injected. Could indicate obsolete lessons, poor categorization, or narrow query matching. A wisdom-review pass would identify which to retire.
_Suggest: schedule wisdom-review (monthly cadence check overdue)._

**4. Pending agent_build task — 6 days, no owner**
work_queue id 13c0ea43 (SpecOps GUI testing module, priority 2) created 2026-05-03, unassigned. Lean mode means no automatic pickup. Either needs a card to execute or an explicit discard.
_Suggest: Bill decides — build or discard._

**5. autonomous_growth_scheduler workflow_id NULL in DB**
Description references Lm68vpmIyLfeFawa but `workflow_id` column is NULL. Protected — no action. Minor data inconsistency for awareness.

---

## Left better

- B-115-cmt executed: architecture_review description and schedule are now accurate.
- Comment-driven pipeline confirmed end-to-end: annotate → classify → generate card → export.
- 5 zombie agents retired. Registry clean.
- "Document AADP on the Site" project closed.
- All pending feedback processed (11 items cleared).
