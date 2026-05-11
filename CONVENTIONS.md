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

**Comment-driven cards.** Comments classified as `correction` or `gap` against agents, skills, or capabilities (confidence ≥ 0.8) automatically generate a backlog card and queue it for execution. The grader is the safety mechanism; no approval gate. To leave an observational note that doesn't produce a card, use framing like "noticed that..." or "worth watching..." — this routes to `note` intent. See `architecture/decisions/comment-driven-cards.md`.

**Execution discipline.** Apply at the line level, not just the file level:

- **Trace to the request.** Every changed line should trace directly to the directive. If a line doesn't, remove it before committing.
- **Don't improve adjacent code.** Match existing style even if you'd do it differently. Don't refactor things that aren't broken. Don't reformat code outside the scope of the change. If you notice unrelated dead code, mention it in the artifact — don't delete it.
- **Simplicity over speculation.** No features beyond what was asked. No abstractions for single-use code. No flexibility that wasn't requested. If you wrote 200 lines and it could be 50, rewrite it before committing.

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

---

## 3. Two-pass review for architecture cards

### Which cards need review

**Goes through review:** any card that creates a new agent, a new table, a new UI surface, or a new pattern (new convention, new file type, new workflow shape).

**Straight execution:** bounded fixes — bug fixes, updates to existing lessons, adding a field to an existing table, polish, retries, restoration jobs.

Any of the three actors (Opus, Claude Code, Bill) can request review on a card that wouldn't normally require it.

### Flow

1. Opus produces a design sketch — not a full card. Problem, proposed shape, open questions. ~200 words.
2. Bill pastes the sketch to Claude Code as a "design review" prompt (not an executable card).
3. Claude Code reviews against current system state. Responds in roughly the same length: what's right, what's off, what changes the proposal needs. May propose a different shape entirely.
4. Bill pastes Claude Code's response back to Opus.
5. Opus revises the design and produces the final card with review-shaped changes baked in. Card includes a `Design reviewed by Claude Code` marker.
6. Bill decides whether to send the card. If yes, paste to Claude Code as a normal directive.

Bill sees the design sketch and the resolved card. He does not need to read the review exchange unless he wants to.

### Resolved standard

A card is resolved when either:
- Opus and Claude Code agree the design is buildable as written, OR
- The disagreement is named explicitly in the card under `## Resolved with disagreement` so Bill can decide.

A sketch without a concrete proposed shape is not resolved. Agreement on the problem without agreement on the solution is not resolved.

### Reader-writer check

For any card that creates a writer — a new table, a button that logs a row, a hook that generates output, a new artifact format — ask during design review: **"Where's the reader? What consumes this output and acts on it?"**

Acceptable answers:
- A named reader that already exists
- A named follow-on card that will build the reader
- An explicit deferral with reasoning

"We'll figure it out later" is not acceptable. If the reader can't be named, the card needs a follow-on card or should be reconsidered before it ships. This is a question, not a hard rule — sometimes building the writer first is deliberate — but the decision to defer the reader must be explicit.

### Design sketch format

~200 words. Five fields. Name the writer and reader together when possible.

**Problem:** What gap or failure is this fixing? One sentence.
**Proposed shape:** What the solution looks like — components, flow, data. Enough for Claude Code to review against actual system state.
**Writer:** What this card produces — table row, artifact, output, UI element.
**Reader:** What consumes it — an existing system component, a named follow-on card, or an explicit deferral with reasoning.
**Open questions:** What's unresolved. What the reviewer should push on.

**Worked example:**

> **Problem:** The comment-classifier sometimes routes correction-intent comments to `note` — observed twice on 2026-05-08, both borderline confidence cases.
>
> **Proposed shape:** Add a confidence floor (0.7) in `classify_comment_intent()`. Below floor, route to a new `ambiguous` bucket. Write `ambiguous` rows to `agent_feedback` with `target_type='review_request'` for Bill to classify. No new table.
>
> **Writer:** `classify_comment_intent()` — writes `ambiguous` rows to `agent_feedback`.
>
> **Reader:** Bill via Anvil annotation view (existing). `agent_feedback` rows already surface in Anvil; no new consumer needed.
>
> **Open questions:** Is 0.7 the right floor, or should it be tunable per target_type? Does `review_request` exist in the annotation vocabulary (annotation-pattern.md) or does it need to be added?

Claude Code reviewing this sketch would note: `review_request` is not in annotation-pattern.md — adding it is a new pattern, which makes this card architecture-adjacent and warrants review before execution.

