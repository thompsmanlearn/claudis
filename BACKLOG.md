## B-044: Silent-failure diagnostic sweep
Status: ready
Depends on: none

### Goal
The system has several documented silent-failure modes (DEEP_DIVE_BRIEF §13). Current state of each is unknown. This card produces one diagnostic artifact reporting the status of each probe with evidence, so follow-up fix cards can be written against findings rather than assumptions. This card diagnoses only. It does not fix.

### Context
Read-only operation with one exception: the Telegram probe sends a real message to chat_id 8513796837. That side effect is intentional.

Run probes in this order:

1. **Anvil uplink health.** Capture `systemctl status aadp-anvil.service` output (active state, uptime, restart count). Separately, from an Anvil-side context, invoke `get_system_status()` with a 10-second timeout. A "systemd active + callable timed out" result is the silent-disconnect signature.

2. **Telegram webhook.** Via n8n MCP tool, `workflow_get kddIKvA37UDw4x6e` — confirm `telegram_command_agent` is active. Then POST to `/webhook/telegram-quick-send` with body text `[DIAG B-044] self-test, disregard`. Record HTTP response. Note that HTTP 200 does not prove delivery — only Bill's phone does. Record both.

3. **n8n API key validity.** Call `workflow_list`. Record response. 401/403 = expired key in `.env`.

4. **lean_runner.sh drift.** Run `diff ~/aadp/sentinel/lean_runner.sh ~/aadp/claudis/sentinel/lean_runner.sh`. Record identical or full diff.

5. **ChromaDB orphans.** `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` via Supabase. Record count.

6. **Supabase RPCs.** Query `pg_proc` via DDL endpoint for `increment_lessons_applied_by_id` and `increment_lessons_applied`. Record existence of each.

7. **Capabilities table.** `SELECT COUNT(*) FROM capabilities`. Record count. This is a state check, not pass/fail.

Do not call `/trigger_lean` — it launches real sessions (§13).

Do not restart services, rotate keys, copy files, or execute schema changes. All remediation is out of scope; write it up, move on.

### Done when
- Artifact exists at `~/aadp/claudis/sessions/lean/B-044-diagnostic-sweep.md`.
- Artifact contains seven probe sections in the order above.
- Each section contains three fields: `status` (one of `ok`, `broken`, `unknown`, `info`), `evidence` (raw command output, HTTP code and body, query result, or diff), `recommended_action` (one line: either `no action` or `fix card needed: <one-sentence description>`).
- Probe 2's `status` is `unknown` until Bill confirms Telegram delivery; artifact flags this explicitly.
- Artifact ends with a summary table: probe name, status, follow-up card needed (yes/no).
- No file outside the artifact was created or modified. No service was restarted. No key, workflow, or schema was altered.

### Scope
Touch: `~/aadp/claudis/sessions/lean/B-044-diagnostic-sweep.md` (new file only).
Do not touch: `.env`, any systemd unit, any `lean_runner.sh`, any Supabase row or schema, any n8n workflow state, any ChromaDB collection, DIRECTIVES.md, BACKLOG.md, agent configuration.
