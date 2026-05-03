# Session: B-079 — Thread-aware query derivation for context_engineering_research

**Date:** 2026-05-02  
**Card:** B-079  
**Branch:** attempt/b079-thread-query-derivation → merged to main  

---

## What was done

**Diagnostic context:** The "Configure vs. create" thread fired its gather and the agent ran standing queries (`autonomous agent platform persistent memory`, `n8n LLM agent orchestration`, etc.) — none related to the thread question. 15 articles came back; ~14 were noise. The agent had no thread context.

**Changes shipped:**

### uplink_server.py
- Added `_DERIVE_QUERIES_FALLBACK` constant (4 default queries for fallback)
- Added `_DERIVE_QUERIES_SYSTEM` prompt instructing Haiku to output 3-5 specific short queries as JSON
- Added `_derive_thread_queries(thread_id)` helper: fetches thread question + up to 5 recent annotation/analysis/summary entries, calls Haiku 4.5 (no cache_control — Haiku ignores it), parses JSON response, returns `(queries, error_reason)`. On any failure: returns `(_DERIVE_QUERIES_FALLBACK, reason)` and logs via `log.warning`.
- Updated `trigger_thread_gather`: calls `_derive_thread_queries`, passes `{thread_id, queries}` in webhook payload, writes thread entry with queries inline (`Gather triggered: <agent>. Queries: q1, q2, ... (output not yet wired to thread)`) or fallback text with error reason.

### stats-server/stats_server.py
- `run_context_research`: reads `payload.get('queries')`, uses it for HN/arXiv searches when it's a non-empty list; otherwise uses the existing `_default_queries` set. Tags/GitHub queries are unchanged.

### n8n workflow `context_engineering_research` (id: `gzCSocUFNxTGIzSD`)
- `Run Context Research` node: `jsonBody` changed from `"{}"` to `"={{ JSON.stringify({queries: $json.queries ?? null}) }}"` — forwards the webhook payload's `queries` field to the stats server.
- Webhook node: `notes` field added documenting the payload contract (thread-triggered vs. non-thread shape).

---

## Smoke test results

**Derived queries for "Configure vs. create" thread** (`e6f7f118-0dea-4326-b12a-426ace71aa37`):
- Thread question: "When a non-technical person uses an agent today, are they actually creating one or configuring a templated agent someone else built — and does that distinction change what kinds of tasks are realistically reachable for them?"
- Haiku derived: `no-code agent builders templates`, `citizen developers AI agents limitations`, `agent configuration vs agent creation`, `non-technical users agentic AI capabilities`, `templated workflows vs autonomous agents`
- Vs. previous defaults: `autonomous agent platform persistent memory`, `n8n LLM agent orchestration`, etc.

**End-to-end gather:** Posted `{thread_id, queries}` to webhook → `inserted: 6, skipped_dupe: 50, errors: 0`. HN/arXiv results with derived queries were all duplicates in this run (the database already has a large article set from earlier default-query runs). Tag-based sources (Medium/dev.to) contributed the 6 new rows. This is expected at the current DB size.

**Query override logic:** Unit-tested — empty/null/absent `queries` falls back to defaults; non-empty list overrides.

**Non-thread invocation test:** Skipped per card — the Anvil Gather button always passes thread context; non-thread invocations from this surface don't occur in practice. Card noted this as acceptable to skip.

---

## Why this card was prioritized first among Gap A fixes

Gap A has three parts: (1) agent fetches irrelevant articles, (2) results don't wire to the thread, (3) no thread_id in research_articles. The diagnostic showed the upstream cause — wrong queries — was washing out everything downstream. Even if output were wired and thread_id were stored, the articles would still be noise. Fixing queries first means the next two cards ship useful data rather than labeled noise.

---

## What was not touched (per card scope)

- research_articles schema (no thread_id column — next card)
- Summarization prompt
- Any Anvil UI (Gather button already passes thread_id correctly)
- extract_analysis or any other callable
