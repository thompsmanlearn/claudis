## B-044: Open diagnostic collaboration session on silent-failure surface
Status: ready
Depends on: none

### Goal
Before any diagnostic or remediation work on the silent-failure items in DEEP_DIVE_BRIEF §13, establish a working exchange between Claude Code (on the Pi, with real system access) and the desktop session (with design context and Bill's direction). Desktop has hypotheses about what's broken and how to probe it; Claude Code knows what's actually reachable, what the current state of each service looks like, and which probes are safe to run without side effects. Neither side can design the sweep well alone. This card produces a written response from Claude Code that the desktop session can read and respond to in the next desktop turn.

### Context
The silent-failure items under discussion are from DEEP_DIVE_BRIEF §13: Anvil uplink silent disconnects, `/webhook/telegram-quick-send` as a single point of failure, n8n API key TTL, dual `lean_runner.sh` drift, `chromadb_id IS NULL` orphans, Supabase RPC existence (`increment_lessons_applied_by_id`, `increment_lessons_applied`), and capabilities table population.

This is not a diagnostic pass. Do not probe, test, fix, or modify. The only action is producing a written response.

Read §13 and any relevant service source (`aadp-anvil.service`, `stats_server.py`, `mcp-server/server.py`, both `lean_runner.sh` copies) only as needed to answer the questions below honestly. No external calls, no Supabase queries, no n8n API calls, no filesystem mutations.

Write the response to `~/aadp/claudis/sessions/lean/B-044-diagnostic-collab.md`. Address each of the following:

1. **Reachability.** For each §13 item, can Claude Code observe its state from the Pi without side effects? If not, what's the closest proxy? Specifically: can the Pi invoke Anvil uplink callables the way the browser client does, or only observe the uplink from the server side?

2. **Side-effect inventory.** For each item, what's the minimum-impact probe you'd actually use? Flag anything with a visible side effect (Telegram message, log entry, rate-limited API call, cache invalidation).

3. **Known-state shortcuts.** Anything in §13 you already know the state of from recent sessions, without needing to probe? If yes, say what and when you last observed it.

4. **Items you'd add.** Silent-failure modes you've encountered that aren't in §13. Brief — one line each, no investigation.

5. **Items you'd drop or reframe.** Anything in §13 that you believe is already resolved, not actually silent, or misframed. Say why.

6. **Ordering.** If this turns into a diagnostic sweep, what order would you run probes in, and why? (Dependencies between probes, blast radius, information value.)

7. **Open questions for Bill or desktop.** Anything you'd want answered before designing the sweep.

Keep responses tight. Bullet points or short paragraphs. This is an exchange, not a report.

### Done when
- Artifact exists at `~/aadp/claudis/sessions/lean/B-044-diagnostic-collab.md`.
- All seven sections above are present and non-empty. "Nothing to add" is a valid answer for 4 and 5 if honest; it still appears as a section.
- No probe was executed. No service touched. No Supabase row read or written (reading source code on the filesystem is fine; calling the API is not). No n8n API call made. No Telegram message sent. No file modified except the artifact.
- Session artifact closes normally; site regenerates per usual lean-session behavior.

### Scope
Touch: `~/aadp/claudis/sessions/lean/B-044-diagnostic-collab.md` (new file only).
Do not touch: anything else. In particular: `.env`, any systemd unit, any `lean_runner.sh`, any Supabase row or schema, any n8n workflow, any ChromaDB collection, DIRECTIVES.md, BACKLOG.md.

## B-045: Fix /ping to reflect websocket state; complete remaining §13 probes
Status: ready
Depends on: B-044 (diagnostic-collab session, complete)

### Goal
Two deliverables. First: make `localhost:9101/ping` an honest health signal by having it reflect Anvil websocket connection state, not just process liveness and Supabase reachability. Without this, any watchdog polling `/ping` is theatre — the §13 "Anvil uplink silent disconnects" item cannot be closed with the current endpoint. Second: complete the three remaining §13 probes that last session deferred or couldn't reach (Telegram webhook self-test, n8n API key validity, `lean_runner.sh` dual-copy diff). These are read-mostly checks that close open questions from B-044.

### Context
Prior session B-044 established:
- `/ping` in `uplink_server.py` returns 200 when `_last_keepalive` is under 1200s old. `_last_keepalive` is updated by a Supabase-probing background worker and by the Anvil `ping()` callable. The websocket state itself is never consulted. A dead websocket with a live process returns healthy.
- Four orphan lessons (`chromadb_id IS NULL`); both RPCs exist; `capabilities` has 90 rows; SUPABASE_MGMT_PAT has been rotated and `.env` updated.
- MCP server has no systemd unit and uses stdio transport — standard restart patterns don't apply. See lesson written 2026-04-22.

This session is a working session w
