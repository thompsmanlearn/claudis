# ADR: Comment-Driven Card Generation

**Date:** 2026-05-09
**Status:** Active (B-114)

## Context

Annotations filed via the Comment button (Fleet tab) route through the classifier (B-086) and produce a typed intent. Before this card, high-confidence corrections and gaps surfaced in the attention queue but required manual action — Bill had to read the queue, write a card, and trigger execution. Comments accumulated.

## Decision

When the classifier marks an annotation as `correction` or `gap` with confidence ≥ 0.8 against a scoped target type (`agent`, `skill`, `capability`), the system automatically generates a backlog card and queues it for execution. Human approval is deliberately omitted. The grader is the safety mechanism.

## Architecture

```
annotate() callable
  → classify_annotation (Haiku)
  → if intent in {correction, gap} AND confidence ≥ 0.8 AND target_type in {agent, skill, capability}:
      → /generate_card_from_comment (Sonnet) — background thread
          → appends B-NNN-cmt to BACKLOG.md
          → updates agent_feedback.metadata with generated_card_id
  → return to caller (card gen is non-blocking)
```

Generated cards enter the existing execution pipeline unchanged:
- `auto_cycle_enabled=true`: chains through auto_cycle, grader gates each
- `auto_cycle_enabled=false`: queues for next manually-triggered session

## Why no approval gate

The grader (B-087) is already the safety mechanism for card execution. Adding an approval gate before execution would duplicate review. The export pattern (Bill reviews at his cadence, not before execution) is the correct model for autonomous work with oversight.

## Export review

`export_comment_driven_results(since_date, agent_name)` bundles: original comment, generated card text, session artifact path, grader verdict, commit SHA. Bill pastes the bundle into a desktop session for review. Fleet tab "✏️ Comment work" button produces the export.

## Known risks and mitigations

| Risk | Mitigation |
|------|-----------|
| Classifier misclassifies 'note' as 'correction' | Confidence threshold ≥ 0.8; low-confidence routes to queue only |
| Generated card quality is poor | Grader will pause/fail it; no harm done; card stays in BACKLOG |
| Grader misses a bad card | Same risk exists for desktop-written cards; existing risk tolerance |
| Card number collisions | _next_card_number() scans sessions/ and BACKLOG.md; deterministic |

## Trigger conditions

- `intent_type` in `{'correction', 'gap'}`
- `confidence` ≥ 0.8
- `target_type` in `{'agent', 'skill', 'capability'}`

Not triggered for: threads, lessons, sessions (deferred), lower-confidence results, 'note'/'direction'/'question' intents.

## Framing comments to control routing

- **Generates a card:** "The description is wrong — it says X but it actually does Y" → correction
- **Generates a card:** "This agent is missing the ability to do X" → gap
- **Queue only:** "Noticed that this agent ran slowly today" → observation/note
- **Queue only:** "Worth watching whether X improves" → question

Bill can deliberately choose observational framing to keep a comment as a note.
