# Session Artifact: B-133 Boot Cleanup — Dead Code and Missing Heartbeat
Date: 2026-05-17
Card: B-133
Branch: attempt/b133-boot-cleanup

## What was done

Three targeted changes to remove dead code and add a boot heartbeat:

**1. lean_runner.sh** (`sentinel/lean_runner.sh`)
- Removed stale comment on line 4 referencing lesson_injector
- Removed dead `INJECT_WEBHOOK` variable
- Removed dead `BACKLOG` variable (was only used by DIRECTIVE_DESC)
- Simplified directive extraction block: kept CARD_ID extraction, removed DIRECTIVE_DESC (only served the dead injection block)
- Removed dead injection block (~25 lines): curl to `localhost:5678/webhook/inject-context`, INJECT_PAYLOAD construction, CONTEXT_BLOCK handling. lesson_injector n8n workflow was deleted in B-130; this call returned 404 on every lean session.

**2. skills/bootstrap.md**
- Removed `session_notes_load(consume=true)` call from Step 2. session_notes table was archived 2026-04-25 per CONVENTIONS.md. Removed the associated IMPORTANT warning block. Updated context budget note to `~3,500 tokens`.

**3. LEAN_BOOT.md**
- Added step 1.5 (Boot heartbeat): after git pull, before cp. Instructs Claude Code to peek at DIRECTIVES.md first line (≤80 chars) and write `claudis_current_task` + `claudis_heartbeat_at` to system_config via `mcp__aadp__supabase_exec_sql`. This keeps system_config non-idle during active lean sessions. close-session resets to idle.

## Verification

- Dead injection block confirmed absent from lean_runner.sh.
- session_notes_load confirmed absent from bootstrap.md.
- Boot heartbeat step confirmed added to LEAN_BOOT.md.
- Heartbeat written for this session: `claudis_current_task = "Run B-133: Boot Cleanup — Dead Code and Missing Heartbeat"` confirmed in system_config via Supabase.
- Note: card said to verify via `curl localhost:9100/system_status` — that endpoint is hardware-only and does not surface system_config. The Supabase query is the correct verification. No code change needed; the card's criterion was aspirational.

## Lessons Applied

- `lesson_config_set_400_heartbeat_2026-03-25`: Applied — used `supabase_exec_sql` with `INSERT ... ON CONFLICT` for heartbeat writes, not `config_set` (which targets agent_config, not system_config). Saved from a 400 error.
- `lesson_heartbeat_bill_sessions_2026-03-29`: Applied — heartbeat step placed in LEAN_BOOT.md so it fires in Bill-initiated sessions, not just Sentinel sessions.

## Capability delta

Boot path is clean: no dead network calls on every lean session start. Lean sessions now show active directive in system_config instead of idle for their entire duration.
