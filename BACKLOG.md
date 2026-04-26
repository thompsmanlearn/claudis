B-062: Lesson curation — Never Applied filter, broken-lesson backfill, recurring sync check

Status: ready
Depends on: B-061 (Export pattern), prior wisdom-review work

Goal
Three small, high-leverage improvements to the lesson curation infrastructure surfaced by Bill's first real Lessons-tab Export → desktop Claude analysis round-trip. Together they make the Never Applied view trustworthy, repair lessons currently invisible to semantic search, and prevent the dual-store sync gap from silently recurring.

Context
Bill exported the Lessons tab "recent" view (50 rows) and analyzed with desktop Claude on 2026-04-26. Three concrete findings emerged:

1. The Never Applied view mixes two different things: genuinely stale lessons (real signal) and brand-new lessons that simply haven't had time to be applied yet (noise). Of the recent lessons exported, several from today and yesterday show times_applied=0 — not because they're failing to retrieve, but because they didn't exist long enough to be retrieved against. The view is currently misleading and erodes trust in the curation surface.

2. Two lessons in the recent corpus show chromadb_id=null but were written to Supabase ("n8n PUT body must contain exactly..." and "n8n API key expiry silently breaks workflows..."). Both are 8 days old, high-confidence, and invisible to semantic search. The "Store sync gap repair" lesson (13 days old, in this bundle) was written to address exactly this class of failure — but the bug has recurred since.

3. The dual-store sync gap (lessons in Supabase without chromadb_id) has no recurring check. Detection is reactive, only when a lesson should have surfaced and didn't.

Done when

1. Never Applied view filter:
   - get_lessons() callable accepts an optional age_threshold_days parameter (default 7) when filter='never_applied'
   - The "Never Applied" view in the Lessons tab uses this threshold — only lessons created at least 7 days ago and with times_applied=0 surface
   - Tab UI shows the threshold inline ("Lessons created 7+ days ago that have never been applied")
   - The threshold is configurable in the callable in case Bill wants to tune it later

2. Broken-lesson backfill:
   - SQL audit run: SELECT id, title, content, category FROM lessons_learned WHERE chromadb_id IS NULL — report count and titles
   - For each broken lesson: write to ChromaDB via memory_add with the existing supabase id as metadata, capture returned chromadb_id, UPDATE lessons_learned SET chromadb_id=<id> WHERE id=<supabase_id>
   - Verify: re-run the audit query and confirm zero rows
   - Report each backfilled lesson by title in the session artifact

3. Recurring sync check:
   - Add a step to close-session.md immediately after the existing lesson write step: SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL — if non-zero, flag in the session summary so Bill notices
   - Do not auto-fix in close-session — the manual repair is rare enough that surfacing the issue is the right behavior. Backfill happens deliberately as in step 2 above.
   - Document this check in DEEP_DIVE_BRIEF Section 7 (Database Schema → lessons_learned section): mention the integrity invariant chromadb_id IS NOT NULL for all live lessons

Out of scope (separate future cards):
- Wisdom-review merge operations (combining duplicate lesson clusters like the four n8n API key lessons) — that's a meaningful design question, not a quick fix
- Confidence field semantics — also a design question
- Backfilling Q-anchor titles on pre-March-25 lessons — large effort, separate decision
- Generalizing this curation pattern beyond Lessons (the broader "OS for the lesson corpus" thread)

Scope
Touch:
  ~/aadp/claudis/anvil/uplink_server.py — get_lessons() callable parameter
  ~/aadp/claude-dashboard/client_code/Form1/__init__.py — Never Applied view threshold display
  Supabase lessons_learned table — backfill rows where chromadb_id IS NULL
  ChromaDB lessons_learned collection — add documents for backfilled rows
  ~/aadp/claudis/skills/close-session.md — add sync check step
  ~/aadp/claudis/DEEP_DIVE_BRIEF.md — document the invariant

Do not touch:
  Existing lessons content or metadata beyond chromadb_id
  Confidence field on any lesson
  Any other tables
  LEAN_BOOT.md (no changes needed at boot — close-session check is sufficient)

Verification checklist
- get_lessons('never_applied') returns only lessons ≥ 7 days old with times_applied=0
- The Never Applied view in Anvil shows the age filter inline
- audit query returns zero rows after backfill
- Each backfilled lesson now retrievable via memory_search on a relevant query
- close-session.md updated with sync check step
- DEEP_DIVE_BRIEF Section 7 updated with the invariant
- Branch attempt/b062-lesson-curation on both repos, merged to main/master, pushed

Notes
- The age threshold of 7 days is a starting point. If Bill finds it too aggressive (legitimate stale lessons hiding) or too lax (still showing noise), tune it. Don't over-engineer the configurability.
- The backfill step matters more than it looks. Two invisible high-confidence lessons mean two real failure modes that future sessions can't learn from. Worth doing right.
- The recurring check is intentionally surface-only (not auto-fix). Auto-fixing would hide the underlying cause; surfacing forces Bill (or a future card) to notice when sessions are writing only to one store.
