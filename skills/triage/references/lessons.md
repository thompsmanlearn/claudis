# Lessons — Triage

Curated from ChromaDB lessons_learned 2026-04-15. Actionable only — cross-layer diagnosis for unknown-layer failures.

---

## Diagnostic Discipline

**Self-diagnostic probes require 3 parts to be actionable.**
A probe that only detects a problem without specifying what to do causes decision paralysis. Every diagnostic entry must include: (1) exact query or search to run to detect the condition, (2) how to interpret the result — what counts as healthy vs unhealthy with specific thresholds, (3) concrete recommended action — if "alert Bill", specify the Telegram message format; if "fix automatically", specify the exact SQL or tool call.
*(2026-03-23)*

**At every session start, run these two probes before beginning work:**
- `diag_agent_stuck_tasks` — work_queue items claimed more than 2 hours
- `diag_memory_store_sync` — `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` (the real gap metric, not COUNT comparison)

Problems surface before new work begins rather than being discovered mid-session.
*(2026-03-23)*

---

## Known Failure Patterns

**Metacognitive failure thresholds — when to alert Bill and stop.**
Same error appearing 3+ times in error_log, a work_queue item claimed more than 2 hours without completing, or API budget approaching limit. These three signals indicate the system is stuck in a loop it cannot self-resolve. Alert Bill via Telegram rather than continuing to retry.
*(2026-03-23)*

**`work_queue_update` silent 400 failures — two known bugs.**
(1) The tool previously injected `updated_at` into the PATCH body, but `work_queue` has no `updated_at` column — Supabase PostgREST rejects unknown columns with 400. (2) Status completion check used `"completed"` but the DB constraint only allows `"complete"` (no trailing 'd'). If `work_queue_update` fails silently, use `supabase_exec_sql` as fallback. Verify actual status enum values before using work_queue_update.
*(2026-04-06)*

**`execution_get` returns metadata only — no node-level input/output data.**
Fields like token usage, cache stats, or intermediate node outputs are not inspectable after the fact via the MCP tool. To verify prompt caching is active or debug agent internals, the workflow itself must log relevant fields to `experimental_outputs` or `audit_log` at run time. Post-hoc execution inspection only tells you pass/fail and timing.
*(2026-04-06)*

---

## Evaluator Interpretation

**4-Pillars Evaluator has two systematic blind spots that cause false-low scores.**
(1) Production Telegram agents write output to Telegram, not `experimental_outputs` — evaluator finds no evidence and scores them 3/5 despite correct operation. Workaround: when `outputs=0` and `status=active`, fetch `audit_log` and n8n execution history as evidence. (2) Agents with nested JSONB synthesis fields — Haiku misses nested content and concludes no synthesis happened. Workaround: pre-flatten key fields before building the Haiku prompt.
*(2026-03-24/25)*

**When the evaluator flags a historical audit ratio as a concern, check when the audit node was added.**
If audit logging was just added this session, the historical ratio reflects pre-monitoring runs — not actual failures. The ratio self-corrects over 3+ runs. Do not restart workflows or manufacture fake audit entries. Document the artifact and re-evaluate.
*(2026-04-02)*

---

## Store Sync Diagnosis

**The real store sync gap is `chromadb_id IS NULL` in Supabase, not COUNT comparison.**
`COUNT(ChromaDB) ≈ COUNT(Supabase)` can show gap=4 while 43 lessons (29%) have `chromadb_id=NULL` — these lessons exist in Supabase but are completely invisible to `memory_search`. The diagnose probe measures the wrong thing. Real check: `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL`. Fix: run `memory_add` with UUID as doc_id, then `UPDATE lessons_learned SET chromadb_id = id::text WHERE chromadb_id IS NULL`.
*(2026-04-09)*
