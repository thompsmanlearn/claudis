B-064: Audit lean-boot lesson retrieval against the binding problem

Status: ready
Depends on: none

Goal
Audit the current lean-boot lesson retrieval pipeline and produce a written proposal that addresses the binding problem: abstract lessons stored without their originating episode are likely being retrieved, evaluated as too abstract to act on, and silently discarded. This card produces a proposal Bill reviews before any code changes. No implementation.

Context
Research (Marco Somma, "I Ran 500 More Agent Memory Experiments") demonstrates that abstract skills stored without grounding episodes are ignored at retrieval time — recalled but not used because there is no evidence for the model to act on. AADP's current lessons_learned rows store lesson text + tags + times_applied, which is the impoverished-skill shape. The lean-boot inject_context_v3 call already pulls "Prior Session Context" (session-level grounding), so partial episode binding exists at the session level — but not at the lesson level. The audit should characterise what already works before proposing changes.

Done when

1. Schema and retrieval path documented: what gets stored when a lesson is written (ChromaDB fields + Supabase columns), what inject_context_v3 returns at boot, and what of that makes it into the active session context. Plain prose, concrete field names.

2. Last 10 lessons evaluated: for each, answer whether the lesson alone is enough for Claude Code to know when and how to apply it, or whether the originating episode (card, session log, failure) is needed to make sense of it. Each lesson marked "self-sufficient" or "needs episode" with one-line reasoning.

3. If most lessons are "needs episode," a binding scheme proposed: what additional fields the lesson row should carry (candidates: originating_card_id, originating_session_id, situation — concrete trigger, outcome — what happened, kind — typed category: mistake / convention / anti-pattern / successful-pattern); whether episode data lives inline or in a linked table; how retrieval changes so the boot context receives lesson + situation/outcome without meaningfully bloating context; what a kind field buys at retrieval time.

4. Write-side change proposed: what the close ritual should capture beyond current lesson text when a lesson is written, using the assumed pattern of Claude Code drafting and Bill confirming/editing.

5. Anything else the audit surfaces — including where the current pipeline is already doing something right.

Output
A markdown document with five sections matching the steps above. Concrete examples from actual lesson rows wherever possible. Ends with a "what I'd do first" recommendation: the single smallest change that would test whether richer lessons get used more often.

Out of scope:
- Implementing any changes
- Touching the write pipeline
- Changing retrieval k or distance thresholds
- Schema migrations
- Decay or pruning policy

Scope
Touch:
  Read: ~/aadp/claudis/anvil/uplink_server.py — inject_context_v3 path, lesson storage callables
  Read: Supabase lessons_learned table schema and recent rows
  Read: ChromaDB lessons_learned collection schema
  Read: close-session skill for current write-side lesson capture pattern
  Write: sessions/lean/YYYY-MM-DD-b064-lesson-binding-audit.md — the proposal document

Do not touch:
  Any lesson rows, ChromaDB documents, or uplink callables

Verification checklist
- Proposal document written and committed
- Five sections present, all with concrete examples from actual rows
- "What I'd do first" recommendation included
- Bill has read the document and either approved a follow-on card or rejected with reasons

Notes
- inject_context_v3 already returns "Prior Session Context" — this is session-level grounding that predates this card. Note it explicitly so the proposal doesn't re-propose what already exists.
- times_applied is server-incremented by inject_context_v3 — the audit should check whether high times_applied actually correlates with lessons that look self-sufficient vs. needs-episode.

---

B-065: Fix times_applied double-count in inject_context_v3

Status: ready
Depends on: none

Goal
inject_context_v3 fires two Supabase RPCs after every retrieval: `increment_lessons_applied_by_id` (by chromadb_id) and `increment_lessons_applied` (by content match). When both succeed on the same lesson, times_applied increments by 2 instead of 1. Zero-applied wildcards are also always incremented regardless of whether the model acted on them. This makes times_applied an unreliable metric: the top lessons (n8n gotchas) may have half their actual retrieval count; zero_applied is inflated by random wildcard exposure. Fix the double-count so the counter means what it says.

Context
From B-064 audit: top lesson `n8n sets finished:false` shows times_applied=34; with double-counting the real count may be ~17. The `increment_lessons_applied` (content-match) RPC was a safeguard for UUID-keyed entries that predate the slug convention. B-062 backfilled chromadb_ids, so the content-match path is now redundant for any lesson with a valid chromadb_id.

Done when

1. Root cause confirmed: read both RPC function bodies in Supabase to verify the double-increment.

2. Fix applied: remove `increment_lessons_applied` (content-match) call from inject_context_v3, OR add a guard so it only fires for lessons whose chromadb_id is a UUID (legacy entries). The `increment_lessons_applied_by_id` (slug-based) path is the canonical one.

3. Wildcard increment behaviour reviewed: decide whether zero_applied wildcards should increment on exposure or only on explicit apply. Document the decision in a code comment.

4. Stats server deployed (cp claudis/stats-server/ → ~/aadp/stats-server/ + systemctl restart).

5. Verification: retrieve a known lesson twice in one session (two inject_context_v3 calls), confirm times_applied increments by exactly 1 per call, not 2.

Scope
Touch:
  ~/aadp/stats-server/stats_server.py (and claudis copy) — inject_context_v3 increment block
  Supabase: read-only inspection of increment_lessons_applied and increment_lessons_applied_by_id RPCs

Do not touch: lesson rows, ChromaDB documents, schema

Verification checklist
- Root cause confirmed (double-RPC or single-RPC depending on findings)
- Fix applied and stats server restarted
- times_applied increments by 1 per retrieval event, verified empirically

---

B-066: Add situation field to lessons_learned + ChromaDB preamble

Status: ready
Depends on: B-065 (so times_applied is trustworthy before we test whether richer lessons get applied more)

Goal
Add a `situation` column (nullable text) to Supabase `lessons_learned`. When writing a lesson during close-session, prompt for 1–2 sentences describing the concrete trigger that caused the lesson to be written. Prepend `Situation: {situation}\n\n` to the ChromaDB document content so the embedding carries episode context. This is the "what I'd do first" recommendation from the B-064 audit.

Context
B-064 found that binding failures concentrate in older abstract/strategic lessons — ones that don't carry explicit trigger conditions. The `situation` field brings session-level episode grounding down to the individual lesson level. The ChromaDB prepend improves embedding specificity: when the same trigger situation recurs, the query naturally matches the situation sentence. Session-level grounding already exists (session_memory collection) but is orthogonal to individual lessons.

Done when

1. Schema change: `ALTER TABLE lessons_learned ADD COLUMN situation text;` executed.

2. Close-session step 7 updated: after drafting lesson body, prompt "In 1–2 sentences: what specific condition or observation triggered this lesson?" Bill confirms/edits. Situation written to Supabase `situation` column.

3. ChromaDB write change: when `situation` is present, prepend `Situation: {situation}\n\n` to the document content before calling `memory_add`. Supabase `content` column unchanged.

4. Test on 3 existing "needs episode" lessons: add situation text to Supabase, delete and re-embed ChromaDB entries with the preamble. Query with a prompt describing the triggering situation. Confirm distance improves by ≥0.05 vs the current embedding.

5. close-session.md skill file updated (in claudis/skills/, symlinked).

Scope
Touch:
  Supabase: ALTER TABLE lessons_learned ADD COLUMN situation text
  ~/aadp/mcp-server/.claude/skills/close-session.md (via claudis/skills/ symlink)
  3 existing ChromaDB lesson entries (re-embed only, no content change)

Do not touch: inject_context_v3 (situation arrives naturally via document content), other lesson rows

Verification checklist
- situation column exists in lessons_learned
- close-session step 7 prompts for situation and writes it
- ChromaDB documents for new lessons include Situation: preamble
- 3 test lessons show improved retrieval distance

---

B-067: Exempt session_memory from inject_context_v3 token-trim

Status: ready
Depends on: none

Goal
inject_context_v3 trims context blocks from the bottom when the 2000-token cap is exceeded. Session ordering is by routing list: lessons_learned → error_patterns → reference_material → session_memory → research_findings. Trimming pops from the end, so session_memory (episode grounding) is dropped before reference_material and error_patterns (generic patterns). This is backwards — session context is more valuable than generic architecture patterns when diagnosing a task. Fix the ordering so session_memory survives trimming.

Context
From B-064 audit: "The token budget currently optimises for lesson text over episode evidence." Session_memory results are 2 entries × 400-char truncation ≈ 200 tokens — small enough to always include. The fix is either to move session_memory earlier in the collections_to_query list (so it appears before reference_material in the output block and survives trimming) or to exempt it from trimming entirely.

Done when

1. Fix applied: in `_V3_DEFAULT_COLLECTIONS` and all per-task-type routing lists that include session_memory, move session_memory to position 2 (after lessons_learned, before error_patterns). This makes session context appear early in the block and survive bottom-up trimming.

   OR: Add a trim exemption: collect session_memory results separately, append them after trimming is complete. Either approach is acceptable — document which was chosen and why.

2. Stats server deployed.

3. Verification: construct a synthetic request that exceeds 2000 tokens. Confirm session_memory section appears in output and reference_material is the section that gets trimmed instead.

Scope
Touch:
  ~/aadp/stats-server/stats_server.py (and claudis copy) — _V3_DEFAULT_COLLECTIONS, per-task-type routing dicts, trim loop

Verification checklist
- session_memory section survives token-cap trimming in a test request
- Stats server restarted and responsive

---

B-068: Dedup duplicate lessons in lessons_learned

Status: ready
Depends on: B-065 (so times_applied counts are trustworthy before we decide which duplicate to keep)

Goal
At least 2 confirmed duplicate pairs exist in lessons_learned. Duplicates inflate retrieval scores (both entries surface for the same query, consuming 2 of the 5 lesson slots), inflate times_applied (both get incremented), and waste context budget. Identify all near-duplicates, merge or delete extras, and add a structural dedup check to close-session step 7 to prevent future duplicates.

Context
Confirmed pairs from B-064:
- `lesson_retrieval_reactive_not_proactive_2026-03-25` and `368244db-20aa-4b2c-bfe7-6d15a0c6ae4a` (same root cause, same day, both high times_applied)
- `lesson_n8n_merge_deadlock_2026-03-25` (times_applied=20) and `8eeaacd6` (times_applied=28) — both about n8n Merge node deadlock

Done when

1. Full duplicate scan: query Supabase for lessons with matching or highly similar titles (use ChromaDB search_lessons with each title as query, flag results with distance < 0.3 to a different lesson).

2. For each confirmed pair: keep the richer entry (more content, higher confidence, better title), sum times_applied from both, delete the weaker from both Supabase and ChromaDB.

3. Close-session step 7 dedup check strengthened: before writing any new lesson, the close ritual must run a ChromaDB search for the lesson title keywords and confirm no result returns distance < 0.4. If one does, update the existing lesson instead of creating a new one.

4. Step 7 skill file updated to make the dedup check mandatory (currently it says "Before writing, search lessons_learned" — upgrade to a hard gate with explicit distance threshold).

Scope
Touch:
  Supabase lessons_learned: DELETE duplicate rows (after Bill approves the specific deletion list)
  ChromaDB lessons_learned: DELETE duplicate entries
  ~/aadp/mcp-server/.claude/skills/close-session.md step 7 — dedup gate

Do not touch: canonical lesson rows (only the duplicates are deleted)

Verification checklist
- No two lessons_learned rows share a ChromaDB search result at distance < 0.3
- Duplicate rows deleted from Supabase and ChromaDB
- close-session step 7 has a hard dedup gate with distance threshold
- Bill has reviewed and approved the specific deletion list before any deletes run

---

