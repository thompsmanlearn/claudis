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

**When Uncertain.** Telegram Bill with context and options. Wait. Do not expand scope to resolve uncertainty.

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

### Symlink pattern for dual-path files

When a file needs to live at a runtime path (hardcoded in a service) and a version-controlled path (in claudis), replace the runtime copy with a symlink: `ln -s ~/aadp/claudis/path/to/file ~/aadp/runtime/path/file`. Edit only the claudis canonical; the runtime path follows automatically. Examples: `~/aadp/sentinel/lean_runner.sh`, `~/aadp/mcp-server/.claude/skills/*.md`.

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

### Session artifacts must ride with the code they document

Commit session artifacts and code changes **together in the same commit** when possible. If code was committed earlier in the session, reference those commit SHAs explicitly in the artifact header (e.g. `Code commit: abc1234`). A reviewer (human or grader) should be able to find the code by reading the artifact. Artifact-only commits that don't reference code SHAs fail the grader. (B-111, 2026-05-08)

### Annotations

`agent_feedback` is the unified annotation table for the whole system — agents, lessons, skills, sessions, cards, capabilities, threads. File observations here; the classifier (B-086) determines intent. See `architecture/decisions/annotation-pattern.md` for target_type vocabulary and uplink callables.

### Authorization Tiers

Every agent and capability has a tier (1/2/3). Tier 1: act then notify. Tier 2: ask first, 24h/72h timeout escalation, Tier 2 requests use `agent_feedback` with `target_type='approval_request'`. Tier 3: no act without in-session confirmation. See `architecture/decisions/authorization-tiers.md`.

### Naming

- Agents: `snake_case`. `agent_name` column is canonical.
- n8n workflows: match the agent name. One workflow per agent.
- Cards: `B-NNN`.
- Session artifacts: `YYYY-MM-DD-descriptor.md`. Descriptor kebab-case.
- Endpoints: `/verb_noun` (stats_server pattern).
- Branches: `attempt/descriptor`.

