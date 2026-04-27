# B-064: Lesson Binding Audit

*Date: 2026-04-26 | Card: B-064 | Type: Proposal (no implementation)*

---

## Section 1: Schema and Retrieval Path

### What gets stored when a lesson is written

**Supabase `lessons_learned` — columns:**

| Column | Type | Notes |
|--------|------|-------|
| `id` | uuid NOT NULL | primary key |
| `title` | text NOT NULL | human-readable summary; primary retrieval signal |
| `category` | text | e.g. "lessons_management", "system-ops", "n8n", "anvil" |
| `content` | text | full lesson body |
| `confidence` | float | 0.0–1.0 |
| `times_applied` | integer | incremented by inject_context_v3 server-side |
| `source` | text | e.g. "session_2026-04-26", "B-061a" — session of origin, not a structured reference |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |
| `chromadb_id` | text | link to ChromaDB doc_id; NULL for older or not-yet-linked lessons |

No columns for: `situation`, `outcome`, `kind`, `originating_card_id`, `originating_session_id`.

**ChromaDB `lessons_learned` collection (collection id `30d40b91`):**

- Embedding model: all-MiniLM-L6-v2, dimension 384, L2 distance
- `doc_id`: `lesson_{topic}_{YYYY-MM-DD}` (slug format, introduced mid-session history). Older lessons used the Supabase UUID as doc_id, which causes `chromadb_id IS NULL` in Supabase until backfilled.
- `document`: identical to Supabase `content`
- `metadata`: `{"title": "...", "category": "...", "supabase_id": "<uuid>"}`. Some entries also carry `date` and `permanent` flags (used by inject_context_v3 staleness penalty and permanent exemption).

**Write flow (close-session step 7):** INSERT to Supabase → capture `id` → `memory_add` to ChromaDB with `supabase_id` in metadata → UPDATE Supabase `chromadb_id` with the slug. The model drafts, Bill confirms or edits.

### What inject_context_v3 returns at boot

1. **Haiku intent expansion**: task description → 3–4 specific technical phrases (expands search surface beyond a single query)
2. **Multi-phrase lessons query**: each phrase → ChromaDB `lessons_learned` (n_results=8, threshold=1.4). Per phrase: dedup by doc_id keeping best distance. Top 5 by distance after staleness penalty (age > 4 weeks: +0.05 per week added to distance).
3. **Other collections**: error_patterns (2, 1.2), reference_material (2, 1.2), session_memory (2, 1.3, 400-char truncated), research_findings (2, 1.1). Collection routing varies by task_type; "design_and_build" routes to default (all five).
4. **Zero-applied wildcards**: 2 random Supabase lessons with `times_applied=0` and `chromadb_id NOT NULL`, older than 3 days. Added to output as "Uncirculated Lessons" section and included in the increment call — so they always gain times_applied even if not acted on.
5. **times_applied increment**: two RPC calls per retrieval — `increment_lessons_applied_by_id` (by chromadb_id, covers semantic + wildcard results) AND `increment_lessons_applied` (by content match, a safeguard for old UUID-keyed entries). A lesson retrieved by both paths gets +2 per boot, not +1.
6. **Token cap**: 2000 tokens. Trimmed from bottom — session_memory (episode context) is pruned before lesson content when context is tight. Lesson content survives trimming; episode grounding does not.

### What makes it into active session context

For each lesson: `content` text and `distance` score. No source, no category, no episode data at the lesson level.

Session-level grounding arrives separately via `session_memory` results — truncated to 400 characters each, 2 results. This provides a rough "what was happening recently" signal but is orthogonal to individual lessons (session narratives are not linked to the lessons written in those sessions).

**The gap at the lesson level**: the model sees *what* the lesson says but not *when* it arose, *what symptom triggered it*, or *whether the situation still applies*. If a lesson references a past observation ("query returned distance 1.027 for 'session_start_checklist'"), there is no way to check whether that document still exists or whether that distance still holds.

---

## Section 2: Last 10 Lessons Evaluated

Evaluated by: does the lesson alone give Claude Code enough context to know when to apply it, or is the originating episode (card, session log, failure) needed?

| # | Title | Self-sufficient / Needs episode | Reasoning |
|---|-------|--------------------------------|-----------|
| 1 | Check for existing ChromaDB entry before backfilling a null chromadb_id lesson | **Self-sufficient** | Trigger is concrete (chromadb_id IS NULL), action sequence is explicit, failure mode (duplicates) is described. Episode adds color but the rule stands alone. |
| 2 | Symlink pattern for versioning files in non-git directories | **Self-sufficient** | Trigger (non-git file needs versioning), action (copy + symlink), comparison to dual-copy pattern. "Applied for B-061a" is a session ref that adds nothing to applicability. |
| 3 | Multi-source fetch pipelines need a per-source cap | **Self-sufficient** | Failure mode ("first source fills the global cap") is the trigger condition, stated explicitly. Fix is concrete. |
| 4 | dev.to API: use domain-specific tags, not broad ones | **Self-sufficient** | Trigger (dev.to API for research pipeline), failure (off-topic listicles), specific tag list provided. |
| 5 | stats-server deploy path: claudis/ is source, ~/aadp/stats-server/ is running | **Self-sufficient** | Exact paths, exact action (`cp` + `systemctl restart`), confirmed with date. |
| 6 | arXiv exact-phrase match fails for HN-style colloquial queries | **Self-sufficient** | Trigger (arXiv quoted query), failure (0 results), example phrase, redirect to HN Algolia. |
| 7 | PostgREST OR + AND filter combination pattern | **Self-sufficient** | Pattern, example, and verification context present. |
| 8 | Anvil Link component does not accept target kwarg | **Self-sufficient** | Exact error message is the trigger. Fix + alternative provided. `times_applied=2` — only lesson in top-10 with applied > 0. |
| 9 | n8n long-running webhooks need fire-and-forget in uplink callables | **Self-sufficient** | Trigger condition (responseMode='responseNode' + substantial work), failure (read timeout), fix (daemon thread + immediate return). |
| 10 | HN Algolia + arXiv via stats_server viable when no external search API | **Self-sufficient** | Trigger (no Brave/Serper/SerpAPI key), action, constraints documented. |

**Result: 10/10 self-sufficient.**

This is a selection artifact. The 10 most recent lessons are all concrete operational/debugging facts — the kind that naturally carry their own trigger conditions. The abstract and strategic lessons (which are the ones failing to get applied) don't appear in the most recent 10.

**Counterevidence from retrieved-at-boot lessons (older, higher times_applied):**

Two of the five lessons retrieved this boot session are weaker:

- `memory_system_distance_baseline_2026_03_23` (dist:1.13): References "session 2026-03-23, query 'session_start_checklist' returned distance 1.027" and ends with a CORRECTION that reverses the initial finding. Without the originating session, it's unclear whether `session_start_checklist` still exists in ChromaDB, and which rule to follow given the reversal. **Needs episode.**

- `368244db-20aa-4b2c-bfe7-6d15a0c6ae4a`: Near-duplicate of `lesson_retrieval_reactive_not_proactive_2026-03-25`, written same day, same root cause. Two identical lessons both get incremented on every retrieval, inflating times_applied for both. **Needs episode** — not because the lesson is abstract, but because the duplicate arose from a missing dedup check at write time and can only be resolved with the originating session context.

**times_applied correlation — does it predict self-sufficiency?**

Top 15 by times_applied examined: the highest-applied lessons (n8n: `finished:false`, array unwrap, Merge deadlock, activate endpoint) are all concrete error-message-triggered patterns. They ARE self-sufficient. They surface frequently because concrete error queries naturally match concrete lesson content.

But the correlation is circular: self-sufficient lessons get applied, which increases times_applied, which increases retrieval weight. Abstract lessons never match concrete queries, so they stay at zero. `times_applied` is not a measure of quality — it is a measure of how often a lesson happens to match the query pattern. It also double-counts (two increment RPCs per retrieval, wildcards always incremented regardless of relevance).

**Where the binding problem actually lives:** Not in the 10 most recent lessons. It lives in the abstract/strategic lessons that have never been applied — lessons about memory system health, ChromaDB quality signals, architectural patterns. These lack concrete trigger conditions, which means Haiku's expanded query phrases don't find them, and when they do surface (low distances possible on broader queries) there is no episode evidence to confirm the lesson still applies.

---

## Section 3: Binding Scheme Proposal

This section applies because the older, non-surfacing lessons are the binding problem cases even though the recent 10 are self-sufficient.

### Additional fields the lesson row should carry

| Field | Type | Purpose |
|-------|------|---------|
| `situation` | text | 1–2 sentences: concrete trigger that caused this lesson to be written. "When running the sync check in B-062, found 4 lessons with chromadb_id IS NULL." This is the key binding field. |
| `outcome` | text | 1–2 sentences: what happened. "Creating new ChromaDB entries caused duplicates — old entries used UUID as doc_id." |
| `kind` | text (enum) | `mistake` / `convention` / `anti-pattern` / `successful-pattern`. Routes retrieval weighting by task type. |
| `originating_card_id` | text | e.g. "B-062". A pointer to the authoritative context source. Read-only during retrieval; used for lookup if full context needed. |
| `originating_session_id` | text | Session artifact filename e.g. "2026-04-26-b062-lesson-curation". Same — pointer, not duplicated content. |

### Inline vs linked

- `situation` and `outcome`: **inline**. They are short (1–3 sentences) and should travel with the lesson during retrieval — they become part of the ChromaDB document, improving both embedding quality and in-context applicability.
- `originating_card_id` and `originating_session_id`: **linked** (Supabase column only, not embedded into ChromaDB). They are references for lookup, not retrieval signals. Including them in the document would waste embedding capacity on non-semantic content.
- `kind`: **inline** as a ChromaDB metadata field (not document text). Used for pre-filtering.

### How retrieval changes

**ChromaDB document content** gains a `Situation:` preamble:

```
Situation: {situation}

{content}
```

The situation text gives the embedding a concrete episode anchor. When the same situation recurs (or a similar one), the query naturally matches the situation sentence, not just abstract lesson keywords.

**kind-based pre-filtering** (optional, can be added without schema changes):
- Building/design tasks: add `where_document = {"kind": {"$in": ["successful-pattern", "convention"]}}` filter — surface what worked, not mistakes
- Debugging/triage tasks: bias toward `mistake` and `anti-pattern`
- inject_context_v3 already has per-task-type routing; kind filter would slot in alongside it

**inject_context_v3 change required:** None for the situation preamble — it's in the document content already. The `kind` metadata filter would require a small change to `_multi_phrase_query`.

### What a kind field buys at retrieval time

Currently, lessons are undifferentiated — "do this" and "don't do this" both come back in the same result set. `kind` lets inject_context_v3 weight results differently by task: avoid surfacing anti-patterns when building (can cause false negatives), avoid surfacing conventions when debugging (irrelevant). It also clarifies intent for the model reading the lesson: a `mistake` is prescriptive ("don't"), a `successful-pattern` is descriptive ("this worked").

---

## Section 4: Write-Side Change Proposal

**Current close-session step 7 captures:** title, content, category, confidence, source (session artifact name).

**Missing for binding:** situation, outcome, kind, originating_card_id.

**Proposed change to close-session step 7:**

After drafting the lesson body (as now), add four prompts before the Supabase INSERT:

1. **Situation** (required): "In one or two sentences: what specific condition or observation triggered this lesson?" Forces concreteness. Example: "While running B-064 sync check, found memory_system_distance_baseline referenced a document that no longer exists."

2. **Kind** (required, select one): mistake / convention / anti-pattern / successful-pattern. Forces categorization at write time when the episode is fresh.

3. **Originating card** (auto-populated): current session's directive card (B-NNN from DIRECTIVES.md). Claude Code fills this automatically — no prompt needed.

4. **Outcome** (optional): "What happened as a result of the mistake or the pattern?" Short, factual. Can often be derived from the lesson content itself and Bill can skip if it adds nothing.

**ChromaDB write change:** Prepend `Situation: {situation}\n\n` to the document content before embedding. The Supabase `content` column stores the lesson body unchanged (situation goes in its own column). The ChromaDB document gets the richer version.

**The assumed write pattern** (Claude Code drafts, Bill confirms/edits) means Bill reviews the situation and kind before they are written. Bill's edit of the situation field is where the episode binding becomes reliable — Bill was there, the model wasn't.

---

## Section 5: Other Observations

**1. times_applied is unreliable as a health metric.**
Two RPCs fire on each retrieval (`increment_lessons_applied_by_id` + `increment_lessons_applied`). If both succeed on the same lesson, it gets +2 per retrieval, not +1. The top-applied lessons (n8n finished:false at 34, HTTP array unwrap at 28) may actually have half those retrieval events. Additionally, zero_applied wildcards are always incremented regardless of whether the model acts on them — the counter conflates "surfaced" with "used."

**2. Duplicate lessons inflate signal.**
At least two duplicates confirmed: `lesson_retrieval_reactive_not_proactive_2026-03-25` and `368244db-20aa-4b2c-bfe7-6d15a0c6ae4a` (same root cause, same day); `lesson_n8n_merge_deadlock_2026-03-25` and `8eeaacd6` (both about n8n Merge deadlock, both with high times_applied). Close-session step 7 has a dedup check ("Before writing, search lessons_learned for the topic") but it relies on Claude Code running the search — no enforcement mechanism. Both duplicates were written on days when the close ritual was under time or context pressure.

**3. Session-level grounding already works — and is the right model, wrong granularity.**
inject_context_v3 includes session_memory results (2 sessions, 400-char truncated). This provides "what was the system doing recently" context. The binding proposal is essentially: bring this same episode structure down to the individual lesson level. The `situation` field is a micro-session-narrative for the specific lesson.

**4. The 2000-token cap trims episode context first.**
When the context block is trimmed, it drops from the bottom — session_memory (episode context) is trimmed before lesson content. The token budget currently optimizes for lesson text over episode evidence. If `situation` preambles add ~30 chars per lesson, the total lessons block grows by ~150 chars — well within the 2000-token cap — so this change does not worsen the trim problem.

**5. The zero_applied wildcard mechanism is a partial substitute for binding.**
Surfacing 2 random uncirculated lessons per session compensates for lessons that never match semantic queries. But it's random exposure rather than triggered exposure — the model can't act on a wildcard lesson unless the situation it describes happens to be relevant to the current session. With situation fields, the wildcard mechanism could be upgraded: instead of random selection, pick uncirculated lessons whose situation text is most similar to the current task description (one ChromaDB query against situation text only).

---

## What I'd Do First

**Add a `situation` column to `lessons_learned` (nullable text) and prepend it to the ChromaDB document content at write time.**

This is the smallest change that directly tests whether richer lessons get used more often. It requires:
- One `ALTER TABLE` (nullable, no migration)
- One close-session step 7 addition: a single "what triggered this?" prompt before each lesson write
- One ChromaDB write change: `f"Situation: {situation}\n\n{content}"` as the document

**Test:** Pick 3 older lessons currently rated "needs episode" (candidates: `memory_system_distance_baseline`, the strategic architecture lessons with zero_applied). Add situation text, delete and re-embed those ChromaDB entries. Query with prompts that describe the triggering situation (e.g. "retrieval distance changed after rewriting a lesson"). If retrieval distance drops by 0.1+ for those queries, the change is working.

The test is cheap (3 lessons, no schema risk, ChromaDB entries are editable) and directly falsifiable. A negative result (no distance improvement) would mean the problem is elsewhere — likely in the abstractness of the lessons themselves rather than missing episode anchors.

---

*Five sections complete. No code changes, no lesson rows modified, no ChromaDB entries touched.*
