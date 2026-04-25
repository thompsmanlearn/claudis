# CONVENTIONS.md

*Read by Claude Code at the start of every lean session. Rules, not explanations. If this file conflicts with anything else in the repo, this file wins until Bill updates it. Preserve the voice on edit: imperatives, short, no hedging.*

---

## 1. Standing Principles

Apply in every session.

**Context Economy.** Every token in a persistent artifact must change what a future instance does. Cut anything that doesn't.

**Privacy.** First name (Bill) only. No last name, location, employer, contact info, or financial details in any artifact, commit, or output.

**Confidence-Prefixing.** Prefix non-trivial claims with "confident" / "think (unverified)" / "know from direct observation." Verify state claims before asserting.

**"Would Bill Approve?" Test.** Before any external API call, publication, or action under Bill's name, ask whether Bill would approve if he saw it. If uncertain, Telegram and wait. Silence is not approval.

**Branch-Per-Attempt.** Branch (`attempt/descriptor`) before any non-trivial build. Commit outcome including failure. Direct-to-main only for: docs, single-line config, mechanical reconciliation. Non-trivial = touches multiple files, changes runtime behavior, or needs a rollback path.

**Session Close Ritual.** Run the close-session skill at every session end. Procedure: `~/aadp/mcp-server/.claude/skills/close-session.md`.

**Active Agents Have Purpose and Consumer.** Every active agent has a documented purpose and an identified consumer of its output. If either is missing, pause the agent.

---

## 2. Build Conventions

Apply when executing work.

### Supabase

- CRUD: use dedicated MCP tools where one exists for the table. PostgREST fallback only when no tool covers the operation.
- DDL: `supabase_exec_sql` (Management API). Direct postgres is Cloudflare-blocked from the Pi.
- Array columns: `'{"a","b"}'::text[]`. `ARRAY['a','b']` fails silently.

### MCP server

- Never `pkill` or `systemctl restart` the MCP server. It runs as a Claude Code stdio subprocess, not a daemon.
- To restart: exit Claude Code, re-enter.

### n8n workflow updates

- After any `workflow_update` on a workflow with a webhook trigger, test the webhook with a known-good payload.
- 404 means the `webhookId` dropped. Fix: `docker restart n8n`.

### Webhook payload contracts

- `/webhook/telegram-quick-send`: `{"message": "..."}` — reads `body.message`, not `body.text`.
- `/webhook/feedback-agent`: `{chat_id, text}`.
- Before adding a new caller, read the workflow's first node to confirm the payload shape.

### Error surfacing

- **Critical, Bill now:** Telegram. Outages, security events, data-loss risk.
- **Workflow/agent failure:** `error_logs` with `workflow_id` and `node_name`.
- **Infrastructure:** journald via the systemd service.
- **State changes:** `audit_log`.
- When uncertain, prefer the quieter channel.

### Capture artifact selection

- **Lesson** (`lessons_learned` + ChromaDB): technical fact or pattern that applies beyond this session.
- **Session note**: retired 2026-04-25 — `session_notes` table archived. Use handoff section in TRAJECTORY.md instead.
- **Session artifact** (`sessions/lean/YYYY-MM-DD-descriptor.md`): permanent record of what this session did. Committed.
- **ADR** (`architecture/decisions/`): decision with consequences beyond one fix.
- When between lesson and artifact, write both.

### Naming

- Agents: `snake_case`. `agent_name` column is canonical.
- n8n workflows: match the agent name. One workflow per agent.
- Cards: `B-NNN`.
- Session artifacts: `YYYY-MM-DD-descriptor.md`. Descriptor kebab-case.
- Endpoints: `/verb_noun` (stats_server pattern).
- Branches: `attempt/descriptor`.

---

## 3. Current Operating Mode

*Dated. Rewritten as the system changes. Last updated: 2026-04-22.*

### State

- Lean mode. Sentinel timer disabled. `autonomous_growth_scheduler` deactivated.
- 10 active agents, all protected except `architecture_review`. Source of truth: `agent_registry WHERE status='active'`.
- Anvil is the primary control surface. UI is partial; gaps are open work.
- Desktop scopes cards; Claude Code executes. Roles do not overlap within a session.

### Authorized without approval (within card scope)

- Work advancing the card's acceptance criteria.
- Research, inspection, and internal tooling that serves the card.
- Judgment calls on implementation, documented in the session artifact.

### Not authorized without approval

- Work outside the card's scope. Surface the observation; do not act.
- Actions under Bill's external accounts or with cost implications.
- Changes to `DIRECTIVES.md`, `.env`, or anything in `PROTECTED.md`.
- Resuming autonomous mode.

### When uncertain

Telegram Bill with context and options. Wait. Do not expand scope to resolve uncertainty.
