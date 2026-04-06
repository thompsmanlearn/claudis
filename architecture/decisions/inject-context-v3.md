# ADR: inject_context_v3 — Task-Type Routing + Retrieval-vs-Reasoning Signal

**Date:** 2026-04-06  
**Status:** Implemented  
**Source:** Architecture review action — "Memory in the Age of AI Agents" (arXiv 2512.13564v2)  
**Implemented by:** Claudis (Claude Sonnet 4.6), sentinel session

---

## Context

The arch_review agent queued a task to "redesign memory_architecture using the paper's taxonomy to implement tiered memory and add retrieval-vs-reasoning decision logic."

Assessment revealed:
- `inject_context_v2` (v2.1) **already** implements tiered retrieval: session_memory (episodic), lessons_learned + error_patterns + reference_material + research_findings (semantic), with housekeeping-skip routing and Haiku intent expansion.
- A prior lesson (`lesson_memory_tier_taxonomy_aadp_2026-04-06`) incorrectly claimed session_memory was missing — it was already present at line 1183.
- The genuine gap: all task types queried the same collections with the same thresholds. No per-task routing. No signal to the caller about retrieval confidence.

## Decision

Add `inject_context_v3` endpoint to `stats_server.py`. **Do not modify v2** — callers continue working unchanged. Update lesson_injector (MFmk28ijs1wMig7h) to call v3.

## What v3 Adds

### 1. Task-Type Routing Table

Different tasks need different memory: a `self_diagnostic` task needs the `self_diagnostics` ChromaDB collection, not `research_findings`. A `gh_weekly_search` only needs `research_findings`. All task types now query only their relevant collections.

```python
_V3_TASK_ROUTING = {
    "agent_build":      all 5 tiers (maximum context),
    "research_cycle":   research_findings + lessons + reference + session_memory,
    "explore":          lessons + session_memory + research_findings,
    "self_diagnostic":  self_diagnostics + error_patterns + lessons,
    "directive":        lessons + errors + reference + session_memory,
    "gh_weekly_search": research_findings only,
    "gh_report":        session_memory + lessons,
}
# Unknown task types → default (all 5 tiers)
```

### 2. Retrieval-vs-Reasoning Confidence Signal

New response fields:
- `confidence_tier`: `"high"` (min_dist < 0.8), `"medium"` (0.8–1.1), `"low"` (1.1+), `"none"` (no results)
- `min_distance`: smallest distance across all retrieved documents
- `retrieve_confidence`: float 0–1.0
- `retrieve_recommendation`: `"retrieve"` | `"reason_with_context"` | `"reason"`
- `routing_applied`: which routing rule was used
- `collections_queried`: list of collections actually queried

## Consequences

- Lesson injector v3.0 active as of 2026-04-06T09:36 UTC (execution 2081 confirmed success)
- `inject_context_v2` endpoint unchanged — backward compatible
- Stats server restarted successfully with new code
- Future sessions receive routing_applied and retrieve_recommendation in their context blocks
- `self_diagnostic` tasks now correctly pull from `self_diagnostics` ChromaDB collection

## What Was Not Changed

- Session_memory is already queried in v2.1 — v3 preserves this
- Haiku intent expansion preserved
- Staleness penalty on lessons preserved
- 2000-token cap preserved
- Deduplication preserved
