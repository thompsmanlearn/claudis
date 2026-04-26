# Session Artifact — B-052: Boot Retrieval Quality Audit
**Date:** 2026-04-25  
**Entry path:** developer_context_load + bootstrap (not LEAN_BOOT)

---

## What This Session Did

Executed B-052: scored LEAN_BOOT step 10 (`memory_search`) and `lesson_injector` (inject_context_v3) against a manually-constructed ground truth for the B-052 directive domain (ChromaDB retrieval quality, lesson feedback loop validation).

---

## Findings

### Primary: Coverage gap (high severity)

Boot step 10 does not fire in Bill-initiated sessions. This session is a live example — no `memory_search` ran at boot; close-session step 8 will have no IDs to increment. The boot→close feedback loop is structurally absent for every session that enters via `developer_context_load + bootstrap` rather than LEAN_BOOT.

**Fix options:**
- (a) Add a step 10 call into the bootstrap skill
- (b) Factor step 10 into a shared callable both LEAN_BOOT and bootstrap invoke

Option (b) is cleaner: one implementation, two callers.

### Secondary: Boot query too narrow (medium severity)

Boot step 10 used raw directive text as the query. Injector uses Haiku expansion (4 orthogonal phrases). That single structural difference caused the 1-lesson gap.

**Scores against 5-lesson ground truth:**
- Boot step 10: **2/5** — hit GT-1 (structural enforcement), GT-2 (reactive not proactive); missed GT-3, GT-4, GT-5
- lesson_injector: **3/5** — hit GT-1, GT-2, GT-3 (retrieval_log/adapter); missed GT-4, GT-5

Boot query `"ChromaDB lesson retrieval times_applied feedback loop close-session increment"` retrieved the *why* lessons but not the *how-to-improve* lessons. Injector's expansion phrase `"ChromaDB query distance threshold and relevance scoring"` caught GT-3 that boot missed.

**Fix:** Boot step 10 should call `POST /inject_context_v3` (or replicate `_expand_intent_with_haiku`) rather than querying with raw directive text.

### Tertiary: GT-4 and GT-5 missed by both paths — lesson write quality

- **GT-4** (`48ba1edb` — "How do I improve ChromaDB retrieval when distance > 1.0?"): diagnostic framing doesn't embed near retrieval-quality queries
- **GT-5** (`d252f138` — "ChromaDB lesson titles must state the reusable pattern"): embeds under lesson-writing domain, not retrieval-quality domain

**Fix:** Rewrite both with synthetic Q&A prefix anchored in retrieval-quality language:
- GT-4: lead with "Q: My ChromaDB memory_search is returning off-topic lessons — how do I diagnose poor retrieval quality?"
- GT-5: lead with "Q: Why do well-written lessons fail to surface during retrieval? Q: What makes a lesson semantically findable?"

---

## B-051 Status Note

B-051 fixes landed (threshold fix commit `9440cde`). Close-session step 8 never ran for B-051 — session ended after the pre-close check at 23:49 UTC. The 3 flagged lessons were identified but not incremented. Lesson_injector (separate path, `lesson_injector` n8n workflow) accounts for all existing `times_applied` counts (8–30); those are valid, from Sentinel sessions.

---

## Judgment Calls

- Used B-051 session's `memory_search` (23:42 UTC audit_log) as leg 2 data — same query, same ChromaDB state, deterministic result
- Ground truth limited to 5 lessons; additional candidates (`lesson_chromadb_supabase_content_divergence`, `lesson_chromadb_atomic_chunks`) were close but not in the core domain for this directive

---

## Open Work Generated

| Priority | Item |
|---|---|
| 1 | Add boot step 10 to bootstrap skill (coverage fix) |
| 2 | Boot step 10: use Haiku expansion instead of raw directive text |
| 3 | Rewrite GT-4 and GT-5 with retrieval-quality Q&A prefix |

---

## Artifacts

- `experimental_outputs`: retrieval_audit, confidence=0.92
- This file
