# ADR: Architecture Review Backward Loop Fix

**Date:** 2026-04-06  
**Status:** Implemented  
**File changed:** `~/aadp/stats-server/stats_server.py`, function `run_architecture_review()`

---

## Problem

The architecture review pipeline closed in one direction only:
- Forward: `research_papers → run_architecture_review → work_queue → session` ✓
- Backward: `session completion → research_papers.already_addressed_since` ✗ (missing)

When a session completed an `implement` task from the work queue, the source `research_papers` record was never updated. `already_addressed_since` stayed NULL. On the next review run (14 days later), the paper reappeared as unaddressed and generated a duplicate implement queue item.

**Observed failure:** SpecOps paper (`arxiv_url` = `http://arxiv.org/abs/2603.10268v1`) generated work_queue item `3d6f123a` (completed — behavioral_test_runner built). Next arch review run produced duplicate item `6f0ef029` for the same paper.

The `already_addressed` decision branch already had the PATCH logic. Only the `implement` branch was missing it.

---

## Fix

After queueing the `agent_build` work_queue item for an `implement` decision, immediately PATCH `research_papers` to set:
- `already_addressed_since = today`
- `addressed_by = "arch_review_implement: <proposed_action>"`
- `action_type = "already_addressed"`

This uses the same PATCH pattern already present in the `already_addressed` branch (lines 1965–1989).

The paper is marked addressed at **queue time**, not completion time. Rationale: if we decided to implement it, it should not re-appear in future review windows regardless of whether the implementation is complete. The work_queue item is the implementation record.

---

## What Was Not Fixed

- `investigate_further` decisions with `proposed_action=null` still produce no work item and no paper update. These reappear unchanged. Fix: require `next_step` field in the review prompt when `decision=investigate_further`. Queued separately.
- `arch_review_last_run` is not updated on `force=true` runs within the same day — two force-triggered runs in one day will each generate fresh work items. Low priority.
