# LEAN_BOOT.md

*Reading this file is the trigger. Execute the startup sequence immediately. Do not wait for a directive or user prompt.*

You are Claude Code operating the AADP on a Raspberry Pi 5. Bill directs; you execute. Lean Mode: autonomous loop suspended. Bill states the session goal in his first prompt.

*System facts: CONTEXT.md. Rules: CONVENTIONS.md. State: TRAJECTORY.md. Constraints: skills/PROTECTED.md.*

---

## Startup Sequence

1. `git pull` on `~/aadp/claudis/`. If pull fails, Telegram Bill that directives may be stale and STOP.

1.5. **Boot heartbeat** — Peek at `~/aadp/claudis/DIRECTIVES.md` (first line, truncated to 80 chars) and write active status to system_config. Use `mcp__aadp__supabase_exec_sql` — do not use `config_set`, which targets agent_config, not system_config:
   ```sql
   INSERT INTO system_config (key, value) VALUES
     ('claudis_current_task', to_jsonb('<first 80 chars of first line of DIRECTIVES.md>'::text)),
     ('claudis_heartbeat_at', to_jsonb(NOW()::text))
   ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
   ```
   close-session resets `claudis_current_task` to `idle`.

2. `cp ~/aadp/claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md`.
3. Read `~/aadp/claudis/skills/PROTECTED.md`.
4. Read `~/aadp/claudis/CONVENTIONS.md`.

4.5. **Check for pending Bill input** (`mcp__aadp__supabase_exec_sql`, read-only):
   ```sql
   SELECT id, mode, text FROM bill_input WHERE status = 'pending' LIMIT 1;
   ```
   **If a row is found**, process it by mode before reading DIRECTIVES.md:

   - **Command** — write the text to `~/aadp/claudis/DIRECTIVES.md`, commit and push (`cd ~/aadp/claudis && git add DIRECTIVES.md && git commit -m "bill_input: command from Bill" && git push`). Write response: `"Command written to DIRECTIVES.md — executing as directive this session"`. The command replaces DIRECTIVES.md for this session; continue to step 5 which will now read the new directive.
   - **Question** — answer the question using current system knowledge (read CONTEXT.md, TRAJECTORY.md, query Supabase as needed). Write the answer to the response field.
   - **Comment** — save the text as a lesson in `lessons_learned` + ChromaDB using `mcp__aadp__memory_add`. Write response: `"Saved as lesson: [title]"`. DIRECTIVES.md is unchanged.

   Mark the row processed regardless of mode:
   ```sql
   UPDATE bill_input SET status = 'processed', processed_at = now(), response = '<response text>' WHERE id = '<id>';
   ```
   **If no row is found**, skip silently.

5. Read `~/aadp/claudis/DIRECTIVES.md`. If it contains `Run: B-NNN`, read that card from `~/aadp/claudis/BACKLOG.md` — the card is the directive.

   **Stale-card check:** Before continuing, verify the card is not already complete. Check the card's verification checklist against actual state (read key artifacts, one fast Supabase query if needed). If all criteria are already met:
   - Compose a structured briefing (≤600 chars): directive seen, TRAJECTORY.md project arc next, pending `work_queue` count + task types, unresolved `error_logs` count, active agent count.
   - If a `bill_input` row was processed in step 4.5 (Question or Comment mode), append it to the briefing: `"## Bill input\nQ: <question text>\nA: <response text>"`.
   - Call `post_boot_briefing(content, directive_seen)` via the Anvil uplink callable.
   - Telegram Bill: "🔔 Stale directive (Run: B-NNN already complete). Boot briefing posted to Anvil Sessions tab."
   - **STOP. Do not proceed to step 6.**

   If the card is not complete (or completion cannot be determined quickly), continue normally.

   **Design-review check:** Cards that create a new agent, table, UI surface, or pattern (new convention, file type, or workflow shape) require two-pass review before execution — see CONVENTIONS.md § "Two-pass review for architecture cards". Reviewed cards carry a `Design reviewed by Claude Code` marker. If the card matches the heuristic and the marker is absent: stop. Telegram Bill: "Design review needed for [card ID]. This card creates [new X] — it should go through two-pass review before I build. Reply to proceed or route it through Opus first." Do not execute until Bill responds.

6. Resolve skills via stats server:
   ```
   POST http://localhost:9100/resolve_skills
   Body: {"directive_text": "<directive text>", "increment_on_load": true}
   ```
   For each returned skill with confidence ≥ 0.6: read its `SKILL.md` (path from `file_path` field). Do not auto-load `references/*.md` — pull those on demand. Confirm: `Loading: [skills]. Proceeding.` or `No skills matched. Proceeding.`
   **Fallback** if stats server unreachable: read `~/aadp/claudis/skills/CATALOG.md` and match the directive against the "Applies when" columns using judgment.
7. Read `~/aadp/claudis/CONTEXT.md`.
8. Read `~/aadp/claudis/TRAJECTORY.md`.
9. **Live-state ping** — Run both checks and include results in the boot summary:

   **Hardware** (`mcp__aadp__system_status`): report CPU%, memory%, disk%, temp, uptime.

   **System state** (`mcp__aadp__supabase_exec_sql`, read-only):
   ```sql
   WITH
     agents AS (
       SELECT COUNT(*) AS count,
              json_agg(json_build_object(
                'name', agent_name,
                'flag', CASE WHEN workflow_id IS NULL AND agent_name != 'claude_code_master'
                          THEN 'no_workflow_id' ELSE '' END
              ) ORDER BY agent_name) AS list
       FROM agent_registry WHERE status = 'active'
     ),
     errs  AS (SELECT COUNT(*) AS unresolved FROM error_logs WHERE resolved = false),
     queue AS (
       SELECT COUNT(*) AS pending,
              string_agg(task_type, ', ' ORDER BY priority) AS types
       FROM work_queue WHERE status = 'pending'
     )
   SELECT a.count AS active_agents, a.list AS agents,
          e.unresolved AS unresolved_errors,
          q.pending AS pending_tasks, q.types AS pending_task_types
   FROM agents a, errs e, queue q;
   ```
   Flag any agent where `flag = 'no_workflow_id'`. No writes.

10. **Pending feedback** (`mcp__aadp__supabase_exec_sql`, read-only):

    ```sql
    SELECT id, target_type, target_id, content, created_at
    FROM agent_feedback
    WHERE processed = false OR processed IS NULL
    ORDER BY created_at ASC;
    ```

    If rows exist: include in boot summary as `## Pending Feedback`. Surface `target_type = 'agent'` or `'anvil_view'` rows again after step 5 as "Feedback to consider during execution:" — do not auto-act. When feedback is acted on, mark immediately:
    ```sql
    UPDATE agent_feedback SET processed = true, processed_at = now(), processed_in_session = '<artifact or card ID>' WHERE id = '<id>';
    ```
    If no pending feedback, skip silently.

11. **Lesson retrieval** — POST to the stats server:
    ```
    POST http://localhost:9100/inject_context_v3
    Body: {"task_type": "design_and_build", "description": "<directive text + card goal summary>"}
    ```
    For each ID in `lesson_ids`: state "Applying lesson [id]:" and honour it. Keep a running list — close-session step 8 references it. inject_context_v3 increments `times_applied` server-side; close-session step 8 should skip these IDs.

    **Fallback** if stats server unreachable: three `mcp__aadp__memory_search` calls (`collection=lessons_learned, n_results=5`): (1) directive keywords, (2) `"how to improve [domain]"`, (3) `"common failures in [domain]"`. Apply results with distance < 1.4. Close-session step 8 must increment these.

12. Execute the directive. Do not pause for confirmation.

If LEAN_BOOT.md is corrupted, restore from `~/aadp/prompts/LEAN_BOOT_stable.md`.

---

## Session Close

**When triggered via lean_runner (dashboard "Trigger Lean Session"):** close-session runs automatically as a second invocation after the directive completes. No manual action needed.

**When running interactively (Bill opens a session manually):** run the close-session skill: `~/aadp/mcp-server/.claude/skills/close-session.md`.

Regenerate the site before ending:
```
cd ~/aadp/mcp-server && source venv/bin/activate && python3 ~/aadp/thompsmanlearn.github.io/generate_site.py
```
