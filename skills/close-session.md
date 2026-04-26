# Skill: close-session
# Invoked via: /close-session
# Purpose: Execute the 10-step AADP session close ritual.
# Load cost: zero until invoked. Replaces ~200 lines of prompt carried every session.
# Last updated: 2026-04-26 (v27 — feedback write-back: action_summary/action_session required on every processed=true)

Execute the following 10 steps in order. Do not skip steps. Do not mark the session complete until all 10 are done.

GitHub steps (1–5) happen BEFORE narrative entries (6–10) so narratives can reference actual commit hashes.

---

## Step 1 — Close open attempt branches

For any attempt branches opened this session:
- Write a close-note commit: what happened, failure type if failed, corrective direction
- Apply `signal:keep` tag if the failure revealed something structurally non-obvious
- Default: archive after 14 days

If no attempt branches were opened this session, skip to Step 2.

---

## Step 2 — Commit completed agents

Any agents completed this session go to `~/aadp/claudis/agents/{category}/{name}/`.
- Strip all credentials (replace with `{{CREDENTIAL_NAME}}` placeholders)
- Update `~/aadp/claudis/agents/INDEX.md`
- Commit and push

If no new agents were built this session, skip to Step 3.

---

## Step 3 — Update TRAJECTORY.md

Do this early, before context pressure builds.

Open `~/aadp/claudis/TRAJECTORY.md`:

- **Where we are:** Rewrite the bullets to reflect current state. Do not append — replace.
- **Project arc next:** Update if the next step shifted this session.
- **Handoff:** Add a new entry at the top with today's date. Include: what was done, what is still open, and the one specific next action the next session should start with. Add a usage note (session % and weekly % if known). Drop the oldest entry if the list exceeds 3. Be specific — "check work queue" is not a handoff.

Do not edit Current project, Destinations, or Back burner — those are Bill's, edited from Anvil. If Bill's direction implied a change, propose it in the handoff note (Step 10) rather than editing autonomously.

Commit and push.

---

## Step 4 — Commit prompt version if changed

If the master prompt (disk_prompt.md) changed this session:
- Write current text to `~/aadp/claudis/architecture/prompts/v{N}.md`
- Commit message = the Supabase change_notes for that version
- Update `~/aadp/prompts/master_prompt_backup.txt`

If prompt did not change this session, skip to Step 5.

---

## Step 5 — Commit session artifact

Write `~/aadp/claudis/sessions/YYYY-MM-DD-HHMM.md` with:
- Date and session type (bill-initiated / sentinel / etc.)
- Tasks completed (one line each)
- Key decisions made
- Capability delta: what can the system do now that it couldn't at session start?
- Lessons written (count + titles)
- Branches opened/closed
- Commit hashes for artifacts produced
- Usage % at close if known

Commit and push this file to GitHub.

---

## Step 6 — Check wisdom-review cadence

Query system_config for `last_wisdom_review`.

```sql
SELECT value FROM system_config WHERE key = 'last_wisdom_review';
```

**Wisdom review cadence:**
- Until 2026-05-04: due if NULL or > 30 days ago
- After 2026-05-04: due if > 42 days ago

If due: add a note to the handoff (Step 10) — "Review due: /wisdom-review" — and queue a work_queue item if one doesn't already exist. Do not invoke the skill now; queue it for next session.

If not due: skip to Step 7.

---

## Step 7 — Write lessons to BOTH stores

Every lesson learned this session must go to BOTH Supabase AND ChromaDB.
Writing to only one store is a failure — the lesson becomes invisible to either SQL queries or semantic search.

**Lesson quality checklist — apply before writing:**

- **Title states the pattern, not the instance.** "PostgREST column names must match Supabase schema exactly" not "Fixed error_logs column name." The title is the primary retrieval signal — make it the rule a future instance would search for.
- **Content includes the trigger condition.** Structure: rule (1–2 sentences) → when it applies → what breaks if ignored. Example: "Anvil callables must return portable types only (str, int, float, bool, None, list, dict, datetime). Returning a custom object or set raises a SerializationError that surfaces as a cryptic client-side exception."
- **No session-specific references.** No card numbers, no file line numbers, no "this session." Lessons must survive codebase churn.
- **No duplicates.** Before writing, search `lessons_learned` for the topic. Update an existing lesson rather than writing a near-duplicate.
- **Content is written for semantic retrieval.** Include the keywords a future instance would naturally use when querying. If the lesson is about Anvil, say "Anvil" in the body, not just the title.

**Supabase first:**
```sql
INSERT INTO lessons_learned (title, content, category, confidence, source)
VALUES ('...', '...', '...', 0.X, 'session_YYYY-MM-DD');
```
Capture the returned `id` — you need it to link the ChromaDB entry.

**ChromaDB second** (use `mcp__aadp__memory_add`):
- collection: `lessons_learned`
- doc_id format: `lesson_{topic}_{YYYY-MM-DD}`
- content: same as Supabase `content`
- metadata: `{"title": "...", "category": "...", "supabase_id": "<id from above>"}`

**Link back** — update the Supabase row with the ChromaDB doc_id:
```sql
UPDATE lessons_learned SET chromadb_id = '<doc_id>' WHERE id = '<supabase_id>';
```

If no new lessons were learned this session, note this explicitly and continue to Step 8.

---

## Step 8 — Update capabilities and increment counters

For anything new you did this session:
```sql
INSERT INTO capabilities (name, description, category) VALUES ('...', '...', '...');
```

For every lesson applied this session — including any flagged "Applying lesson [id]: ..." during boot step 10 — increment the counter using the Supabase ID:
```sql
UPDATE lessons_learned SET times_applied = times_applied + 1 WHERE id = '<supabase_id>';
```
If you only have a ChromaDB ID, resolve it first: `SELECT id FROM lessons_learned WHERE chromadb_id = '<id>' OR id::text = '<id>' LIMIT 1`. The `OR id::text` branch handles lessons whose ChromaDB doc_id is their Supabase UUID (written before slug convention).

**Skip lessons retrieved via inject_context_v3** (bootstrap step 3 or LEAN_BOOT step 10 when using the inject_context_v3 path) — those are already incremented server-side by the stats server. Only run the UPDATE above for lessons retrieved via raw `memory_search` fallback.

For every capability exercised:
```sql
UPDATE capabilities SET times_used = times_used + 1 WHERE name = '...';
```

---

## Step 9 — Write session narrative to ChromaDB session_memory

Written LAST among the memory steps, after all artifacts exist so it can reference them.

Use memory_add:
- collection: `session_memory`
- doc_id: `session_{YYYY-MM-DD}_{HHMM}`
- content: What was attempted, what worked, what failed, what was learned, what comes next
- metadata: `{date, sentinel_version, tasks_completed, lessons_written}`

---

## Step 10 — Feedback write-back + Intent queue check

**Feedback write-back (do this first):**

For any `agent_feedback` items surfaced at session start that were not acted on during this session, mark them now:

```sql
UPDATE agent_feedback
SET processed = true,
    processed_at = now(),
    processed_in_session = '<artifact filename>',
    action_summary = 'Deferred: <reason — e.g. outside scope of B-NNN; suggest B-curate-agents>',
    action_session  = '<artifact filename>'
WHERE id = '<id>';
```

**Standing rule — applies any time processed=true is written, mid-session or at close:**
Every UPDATE that sets `processed = true` must include `action_summary` (required) and `action_session` (required). No exceptions. `action_result_url` is optional — populate only when a specific URL exists (e.g. a bundle URL, a commit link).

Use the prefix `"Deferred: "` exactly when the item was surfaced but not acted on. Use a plain statement ("Expanded sources to dev.to, GitHub, lobste.rs — see session artifact") when the item was acted on.

If no feedback items were surfaced at session start, skip this sub-step.

---

**Intent queue check:**

Scan this session's conversation for any stated intention from Bill (a direction, goal, or concern) that has no corresponding work_queue entry or active vector in TRAJECTORY.md.

If found: create the work_queue entry now, or add a destination change proposal to the Step 3 handoff entry.

If nothing is missing: note "intent queue clear" and proceed.

---

## After all 10 steps are complete

Update the heartbeat:
```
config_set: claudis_current_task = 'idle', claudis_heartbeat_at = now
```

Then confirm to the user (or log, in headless mode): "Session close ritual complete. [N] lessons written, session artifact committed."
