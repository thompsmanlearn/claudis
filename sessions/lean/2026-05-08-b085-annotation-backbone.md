# Session: 2026-05-08 — B-085: Unified annotation pattern

## Directive
Establish agent_feedback as the unified annotation backbone for the whole system.

## What Changed
- **architecture/decisions/annotation-pattern.md** (new): ADR defining supported target_types (agent, anvil_view, lesson, skill, session, card, capability, thread, approval_request), target_id formats, the processed/action conversation pattern, and intent classification schema (placeholder for B-086).
- **anvil/uplink_server.py**: Added three new callables at end of file:
  - `annotate(target_type, target_id, content, source)` — write annotation with target_type validation
  - `get_annotations(target_type, target_id, processed=None)` — read with optional processed filter
  - `mark_annotation_processed(feedback_id, action_summary, action_session, action_result_url)` — mark done
- **CONVENTIONS.md**: Added "Annotations" subsection to Section 2 naming agent_feedback as backbone and pointing to ADR.
- No schema changes — the table already supported this.

## What Was Learned
agent_feedback already had all the columns needed (target_type, target_id, action_summary, action_session, action_result_url, processed, processed_at). The submit_agent_feedback_v2 callable (line 1022) already existed with partial generalization. The new annotate() callable adds target_type validation and returns the created row id — more useful than the existing callable which returns only {submitted: True}.

## Smoke Test
- Wrote test annotation: target_type='lesson', target_id='48e6f4f8-8a24-4001-a447-798fbd2894bd'
- Annotation landed in agent_feedback with id '8a7714ad-c5bc-489d-b593-df6a24ffe21d'
- Marked processed with action_summary — confirmed processed=true in returned row

## Unfinished
Uplink needs restart to pick up new callables (aadp-anvil.service). Done after this commit. B-086 will add classifier call to annotate() and metadata column to agent_feedback.
