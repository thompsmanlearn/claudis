# Session: 2026-04-22 — B-044 Diagnostic Collaboration

## Directive
B-044: Open diagnostic collaboration session on silent-failure surface. Establish working
exchange between Pi (Claude Code, real system access) and desktop (Opus 4.7, design context).
Produce written response covering §12 reachability, side effects, known state, additions,
reframings, probe ordering, and open questions.

## What Changed
- `claudis/sessions/lean/B-044-diagnostic-collab.md` — initial 7-section diagnostic brief written
  and pushed (dec022d..d88317d).
- `~/aadp/mcp-server/.env` — SUPABASE_MGMT_PAT updated to new value (old PAT was expired,
  discovered live during session when supabase_exec_sql returned 401 on all calls).
- Two lessons written to both ChromaDB and Supabase:
  - `4ed63ccc`: "MCP server stdio transport: pkill-relaunch does not work" (system-ops, 0.98)
  - `c30287d5`: "Expiring credential TTL monitoring: silent failure pattern for MGMT_PAT and n8n
    API key" (system-ops, 0.95)

## What Was Learned
**MCP server stdio transport.** No systemd unit; lives as a child process of Claude Code via
stdin/stdout. pkill kills it unrecoverably for the session. The pkill permission in
settings.local.json is a historical artifact — treat it as dangerous. Restart = exit + re-enter.
Plan .env changes needing MCP restart at session boundaries.

**SUPABASE_MGMT_PAT was expired.** supabase_exec_sql 401'd on every call. PostgREST (service key)
still worked for all read/write operations. DDL operations would have silently failed any session
that needed them since the PAT expired. No alert fired.

**9101/ping does not verify the Anvil websocket.** It verifies process liveness and Supabase
reachability (keepalive within 20 min). A silently disconnected uplink returns 200 if the
process is alive and Supabase is reachable — false healthy. Open question: does anything external
poll 9101 and restart aadp-anvil.service on 503?

**Three §12 probes completed:**
- chromadb_id IS NULL: 4 (minor re-opened gap since April 13 repair)
- RPCs (increment_lessons_applied_by_id, increment_lessons_applied): both exist
- capabilities rows: 90 (not empty)

**lean_runner.sh drift: not a current problem.** Both copies byte-for-byte identical as of this
session.

## Unfinished
- Remaining §12 probes deferred to next session (needs full MCP tools):
  - Telegram Quick Send workflow state (n8n API, verify active)
  - n8n API key TTL / validity check
  - Anvil uplink websocket liveness (no clean probe exists from Pi)
- 4 lessons with chromadb_id IS NULL — minor gap, low urgency
- TTL monitoring build (lesson captured, card not yet written)
- Whether anything polls 9101/ping externally — open question for desktop/Bill

## Lessons Applied
- system-ops SKILL: PostgREST service key as fallback when Management API blocked/expired
- communication SKILL: tight bullet format throughout

## Collaboration Notes
This was a live relay session with desktop (Opus 4.7). Pi-side role: observe, probe, report.
Desktop-side role: design hypotheses, direct probe ordering. Bill relayed between sessions.
Format worked well — short probe/report cycles. Recommendation: continue same format for
remaining §12 sweep next session.
