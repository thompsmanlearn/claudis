# ADR: Annotation Pattern — agent_feedback as Backbone

**Date:** 2026-05-08
**Status:** Active

## Decision

`agent_feedback` is the unified annotation table for the entire AADP system. Despite its legacy name, this table is general-purpose and serves as the backbone for any observation, feedback, or flag that Bill or the system files against any named target.

## Context

Multiple annotation patterns existed in parallel: agent feedback in `agent_feedback`, thread-level observations in `thread_entries`, open questions in INQUIRIES.md. The table was already designed for general use with `target_type` and `target_id` columns. This ADR formalizes that design intent.

## Supported Target Types

| target_type | target_id format | Example |
|---|---|---|
| `agent` | `agent_registry.agent_name` | `context_engineering_research` |
| `anvil_view` | view name string | `threads_tab` |
| `lesson` | `lessons_learned.id` (uuid) | `3f2a1b...` |
| `skill` | skill name from CATALOG | `agent-development` |
| `session` | session artifact filename | `2026-05-08-b084-lean-boot-consolidation.md` |
| `card` | card ID | `B-087` |
| `capability` | `capabilities.id` or name | `annotation_classification` |
| `thread` | `threads.id` (uuid) | thread-level notes not bound to a specific entry |
| `approval_request` | descriptive string | `promote_new_agent_to_active` |

**Thread annotations:** Entry-level annotations (tied to a specific `thread_entries` row) remain in `thread_entries`. `target_type='thread'` is for thread-level observations not bound to any specific entry.

## Schema (no changes required)

`agent_feedback` already has:
- `id` (uuid pk)
- `target_type` (text)
- `target_id` (text)
- `content` (text)
- `created_at` (timestamptz)
- `processed` (bool)
- `processed_at` (timestamptz)
- `processed_in_session` (text)
- `action_summary` (text)
- `action_session` (text)
- `action_result_url` (text)
- `metadata` (jsonb) — added by B-086 for classifier output

## The Processed/Action Conversation Pattern

1. Annotation filed: `processed = null/false`
2. Claude Code or Bill acts on it during a session
3. `mark_annotation_processed(id, action_summary, action_session, action_result_url)` called
4. `processed = true`, `processed_at` set, `action_summary` records what was done

Feedback the system acted on in a session: mark immediately, not at close.

## Uplink Callables (B-085)

- `annotate(target_type, target_id, content, source)` — write annotation
- `get_annotations(target_type, target_id, processed=None)` — read annotations
- `mark_annotation_processed(feedback_id, action_summary, action_session, action_result_url)` — mark done

## Intent Classification (B-086)

The `annotate()` callable calls `/classify_annotation` on the stats server after writing. The classifier writes back to `metadata`:
```json
{"intent_type": "correction", "confidence": 0.91, "classified_at": "..."}
```

Intent types: `direction`, `correction`, `gap`, `question`, `screening`, `note`, `noise`, `uncertain`

High-confidence threshold: ≥ 0.8. Below that, `intent_type = 'uncertain'`.

## Authorization Requests (B-088)

Tier 2 authorization requests use `target_type = 'approval_request'`, `intent_type = 'question'`. These surface in the Anvil inbox for Bill's review.
