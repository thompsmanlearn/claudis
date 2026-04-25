# LEAN_BOOT.md

*Reading this file is the trigger. Execute the startup sequence immediately. Do not wait for a directive or user prompt.*

You are Claude Code operating the AADP on a Raspberry Pi 5. Bill directs; you execute. Lean Mode: autonomous loop suspended. Bill states the session goal in his first prompt.

---

## Startup Sequence

1. `git pull` on `~/aadp/claudis/`. If pull fails, Telegram Bill that directives may be stale and STOP.
2. `cp ~/aadp/claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md`.
3. Read `~/aadp/claudis/skills/PROTECTED.md`.
4. Read `~/aadp/claudis/CONVENTIONS.md`.
5. Read `~/aadp/claudis/DIRECTIVES.md`. If it contains `Run: B-NNN`, read that card from `~/aadp/claudis/BACKLOG.md` — the card is the directive.
6. Read `~/aadp/claudis/skills/CATALOG.md`. Match the directive against the "Applies when" columns. Read matching `SKILL.md` files. Do not auto-load `references/*.md` — pull those on demand. Confirm: `Loading: [skills]. Proceeding.` or `No skills matched. Proceeding.`
7. Read `~/aadp/claudis/CONTEXT.md`.
8. Read `~/aadp/claudis/TRAJECTORY.md`.
9. **Live-state ping** — Run both checks and include the results in the boot summary before proceeding:

   **Hardware** (`mcp__aadp__system_status`): report CPU%, memory%, disk%, temp, uptime.

   **System state** — one read-only `mcp__aadp__supabase_exec_sql` query:
   ```sql
   WITH
     agents AS (
       SELECT COUNT(*) AS count,
              json_agg(json_build_object(
                'name', agent_name,
                'flag', CASE WHEN workflow_id IS NULL THEN 'no_workflow_id' ELSE '' END
              ) ORDER BY agent_name) AS list
       FROM agent_registry WHERE status = 'active'
     ),
     errs  AS (SELECT COUNT(*) AS unresolved FROM error_logs WHERE resolved = false),
     queue AS (
       SELECT COUNT(*) AS pending,
              string_agg(task_type, ', ' ORDER BY priority) AS types
       FROM work_queue WHERE status = 'pending'
     )
   SELECT a.count  AS active_agents,  a.list AS agents,
          e.unresolved AS unresolved_errors,
          q.pending    AS pending_tasks, q.types AS pending_task_types
   FROM agents a, errs e, queue q;
   ```
   Flag any agent where `flag = 'no_workflow_id'`. No writes.

10. Execute the directive. Do not pause for confirmation.

If LEAN_BOOT.md is corrupted, restore from `~/aadp/prompts/LEAN_BOOT_stable.md`.

---

## Session Close

Run the close-session skill at session end. Procedure: `~/aadp/mcp-server/.claude/skills/close-session.md`.

Regenerate the site before ending:

```
cd ~/aadp/mcp-server && source venv/bin/activate && python3 ~/aadp/thompsmanlearn.github.io/generate_site.py
```
