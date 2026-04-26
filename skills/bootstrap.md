# Skill: bootstrap
# Invoked via: /bootstrap
# Purpose: Session start orientation — read foundation documents, write orientation
#   statement, signal Bill, update heartbeat.
# Load cost: zero until invoked.
# Last updated: 2026-04-26 (v28 — add step 3: agent_feedback pending feedback pickup)
#
# When to invoke:
#   - At every session start, after developer_context_load
#   - In Sentinel sessions: wake_prompt.md calls /bootstrap automatically
#   - In Bill-initiated sessions: invoke manually after greeting

---

## Step 1 — Pull latest from GitHub

```
cd ~/aadp/claudis && git pull
```

Bill edits foundation documents between sessions. Pull before reading.

---

## Step 2 — Read foundation documents

Read each file in order. These are load-bearing, not decorative:

1. `~/aadp/claudis/CONTEXT.md` — system facts: hardware, services, databases, working with Bill
2. `~/aadp/claudis/CONVENTIONS.md` — operational procedures
3. `~/aadp/claudis/TRAJECTORY.md` — long-term destinations and active vectors

Then load session context:

4. Call `session_notes_load` with `consume=true` — this reads unconsumed handoff notes AND marks them consumed so they don't accumulate across sessions. These contain: what was in progress at last close, the highest-priority next action, what was left better.

   **IMPORTANT: pass `consume=true` explicitly.** The default is `consume=false` (safe peek). Without `consume=true`, notes are never cleared and will pile up across sessions, growing DCL by ~1,700 tokens per session.

Approximate context consumed by this step: ~3,500 tokens for the three documents, plus variable for session notes (0–2 notes when working correctly).

---

## Step 3 — Pending feedback

Query `agent_feedback` for unprocessed rows (read-only):

```sql
SELECT id, target_type, target_id, content, created_at
FROM agent_feedback
WHERE processed = false OR processed IS NULL
ORDER BY created_at ASC;
```

- If rows exist: include them in the orientation statement as a `## Pending Feedback` section. List each as `- [target_type: target_id, created_at] content`.
- If any row has `target_type = 'agent'` or `target_type = 'anvil_view'`, surface it again before claiming work as "Feedback to consider during execution:" — do not auto-act, present as input.
- When a piece of feedback is acted on during the session, mark it immediately (not at close):
  ```sql
  UPDATE agent_feedback SET processed = true, processed_at = now(), processed_in_session = '<session artifact filename or card ID>' WHERE id = '<id>';
  ```
- If no pending feedback, skip silently — no placeholder.

---

## Step 4 — Lesson retrieval

Surface relevant lessons before writing the orientation statement.

Read `~/aadp/claudis/DIRECTIVES.md` for the current directive. If it says `Run: B-NNN`, also read that card from `~/aadp/claudis/BACKLOG.md` for the full goal. POST to the stats server:

```
POST http://localhost:9100/inject_context_v3
Body: {"task_type": "design_and_build", "description": "<directive text + card goal summary>"}
```

For each ID in the returned `lesson_ids`: state "Applying lesson [id]:" and note how it bears on the current task. Keep a running list of all applied IDs — close-session step 8 references this list. Note: inject_context_v3 already increments `times_applied` server-side; close-session step 8 should skip the UPDATE for these IDs (see step 8 note).

**Fallback** if stats server unreachable (connection refused / timeout): run three `mcp__aadp__memory_search` calls with `collection=lessons_learned, n_results=5`:
1. The raw directive keywords
2. `"how to improve [domain]"`
3. `"common failures in [domain]"`

For each result with distance < 1.4 that touches the task domain, apply and list. Close-session step 8 must increment these (server-side increment did not run).

If no results apply, continue without comment.

---

## Step 5 — Write orientation statement

Write three sentences before doing anything else:

1. **State:** Current understanding of where the system is right now
2. **Pickup:** The specific work or situation you're inheriting from the last session
3. **Trajectory:** Which destination and vector today's work serves

Then add one line: *"Bootstrap consumed approximately X tokens. Remaining budget: approximately Y."*

If you cannot write these sentences cleanly, re-read the documents. Unclear orientation now costs more than the re-read.

---

## Step 6 — Send orientation to Bill via Telegram

Send the three sentences plus the context note immediately. This is Bill's signal that a session is active and oriented.

```
POST http://localhost:5678/webhook/telegram-quick-send
Body: {"chat_id": 8513796837, "message": "<your 3 sentences + context note>"}
```

750 characters max. Lead with sentence 1. No preamble.

---

## Step 7 — Update heartbeat

```sql
INSERT INTO system_config (key, value) VALUES
  ('claudis_current_task', '"bill_session"'),
  ('claudis_heartbeat_at', to_jsonb(NOW()::text)),
  ('claudis_session_start', to_jsonb(NOW()::text))
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
```

Use `'sentinel_session'` instead of `'bill_session'` for automated Sentinel invocations.

---

## After /bootstrap completes

Run `/diagnose` next. Then claim work from the queue.

The bootstrap → diagnose → work sequence is the correct session opening order.
