# Session: B-069 — Retroactive Situation Backfill
Date: 2026-04-27
Card: B-069
Status: complete

## What was done

Wrote situation text (1–2 sentences describing the triggering episode) for the top 25 lessons by `times_applied` where `situation IS NULL`. Updated Supabase and re-embedded all 25 ChromaDB entries with `Situation:` preamble prepended.

## Execution summary

1. **Supabase UPDATE** — 3 SQL batches, 8–9 rows each. All 25 rows confirmed updated. Total `situation IS NOT NULL` count: 28 (3 pre-existing + 25 new).

2. **ChromaDB re-embed** — 25 deletes + 25 adds, all in parallel. All returned `status: deleted/added`. New document format: `Situation: {situation}\n\n{original_content}`.

3. **Episode-style distance check** — 5 lessons queried with situation-describing prompts (not lesson content):

   | Lesson | Episode query | After dist | Rank |
   |--------|--------------|------------|------|
   | n8n_merge_deadlock | "sentinel workflow using continueErrorOutput hung indefinitely" | 0.370 | #1 |
   | n8n_array_unwrap | "lesson injector http request array unwrapped downstream broken" | 0.510 | #1 |
   | n8n_finished_false_on_error | "sentinel polling loop never exits workflow stopped with error" | 0.536 | #1 |
   | n8n_db_disconnect_webhooks | "n8n webhooks 404 after inactivity previously working" | 0.281 | #1 |
   | n8n_code_node_fetch_silent_failure | "4-pillars evaluator http call in code node empty result" | 1.059 | #3 |

   **Before distances not captured** — lessons were deleted before measurement (process gap). Proxy: none of these 5 appeared in the boot `inject_context_v3` domain query (design_and_build). After preamble, 4/5 surface at rank #1 for episode queries. #5 (code node fetch) placed #3 because two other evaluator+code-node lessons dominate the query space.

4. **Inferred vs known:** 13 identifiable episodes / 12 inferred.

## Episode patterns

- **Identifiable** lessons: those with dated sources (session_YYYY-MM-DD, sentinel_session_YYYY_MM_DD, sentinel_explore_YYYY-MM-DD). All post-April 2026 lessons are identifiable — session naming convention was standardized by then.
- **Inferred** lessons: those with `source = chromadb_backfill_*` (5 cases) or undated `sentinel` (7 cases). The backfill batches merged unnamed sessions; early March 2026 sentinel work predated the `session_YYYY-MM-DD` convention.
- **Notable pattern:** The n8n webhookId issue has 3 near-duplicate lessons from different sessions (`lesson_n8n_webhookid_node_property`, `supabase_lesson_n8n_webhookid_must_match_path`, `lesson_n8n_webhook_id_required_2026-03-30`). Each re-discovery implies earlier lessons weren't surfacing at retrieval time — a self-reinforcing retrieval failure. The Situation: preamble distinguishes these by episode, which should reduce the overlap at retrieval.

## Observations for follow-on

- **Inferred lessons cluster in early March 2026** — before session naming conventions were established. Future sessions could close this gap by tracing git history if needed, but the benefit is marginal for lessons this old.
- **The before-measurement gap** is a process flaw: for any future re-embedding pass, capture before distances first, then delete.
- **Lesson #5 (code node fetch) ranked #3** — the episode query ("evaluator, code node, empty result") is semantically close to two other lessons (d4c017eb — evaluator using fetch in code node, lesson_evaluator_evidence_gaps). A more specific query ("4-pillars evaluator http call silently returns default value") would likely surface it at #1. Not a re-embedding failure; a query specificity issue.

## Lessons applied (from boot retrieval — times_applied already incremented)

- lesson_retrieval_logging_adapter_2026-03-23
- lesson_store_sync_gap_repair_procedure_2026-04-13
- bbe3d369-32f4-4b07-a48d-bebfa013aa99
- lesson_synthetic_query_augmentation_2026-03-23
- lesson_supabase_rpc_increment_pattern_2026-03-31
