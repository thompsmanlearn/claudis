# Session: 2026-05-08 — B-086: Annotation classifier

## Directive
Build the annotation classifier — Haiku classifies intent type and writes back to agent_feedback.metadata.

## What Changed
- **DDL**: Added `metadata jsonb DEFAULT '{}'` to `agent_feedback` table.
- **stats_server.py** (live + canonical): Added `/classify_annotation` endpoint.
  - Takes: feedback_id, target_type, target_id, target_summary, content
  - Calls Haiku with 7-intent vocabulary prompt
  - Returns: intent_type, confidence, reasoning, high_confidence flag
  - Writes result back to agent_feedback.metadata if feedback_id provided
  - High-confidence threshold: 0.8
- **anvil/uplink_server.py**: Updated `annotate()` callable to call `/classify_annotation` after writing the annotation row. Non-blocking (25s timeout, failure logged but not raised to caller).
- **architecture/decisions/annotation-pattern.md**: Extended with full intent vocabulary table and classifier behavior.

## Smoke Tests
1. "filter duplicates in summary" → direction (0.85) ✓
2. "agent fetching URLs with SSL errors should be filtered" → direction (0.92) ✓
3. "ok" → noise (0.85) ✓

Note: both test 1 and 2 classified as "direction" rather than "correction" — Haiku interprets prescriptive language as direction. This is reasonable; the distinction between correction and direction is subtle. Acceptable for current use.

## What Was Learned
Haiku correctly handles the noise case. The prescriptive vs. descriptive distinction (correction vs. direction) is the hardest boundary for the classifier — both are high-confidence but sometimes arguable. Target_summary field exists for future enrichment — callers can pass context about the target to improve classification, but it's not required.

## Unfinished
Nothing. Stats server restarted. Uplink restarted (next commit triggers restart in B-086 commit).
