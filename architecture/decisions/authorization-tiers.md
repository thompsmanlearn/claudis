# ADR: Authorization Tiers

**Date:** 2026-05-08
**Status:** Active

## Decision

Replace the binary autonomous/needs-approval distinction with three explicit authorization tiers. Each tier has a defined default behavior and escalation path.

## Tiers

### Tier 1 — Act, then notify
**Actions:** Reversible, internal state changes, default scope. Reading from any table, writing to operational tables (lessons_learned, audit_log, agent_feedback, work_queue, experimental_outputs), sending Telegram notifications (notify-only, not acting under Bill's accounts), committing to the claudis repo.

**Default behavior:** Execute. Write to audit_log. Include in daily briefing or session artifact. No pre-approval required.

### Tier 2 — Ask first, with timeout
**Actions:** External-facing actions, anything with a cost implication beyond the standing monthly budget, anything sensitive. Examples: promoting a new production agent that writes to external services, spending above monthly API cap, posting content under Bill's accounts, any irreversible change to shared infrastructure.

**Default behavior:**
1. Write annotation to agent_feedback with `target_type='approval_request'`, `intent_type='question'`
2. Telegram Bill with context and options
3. Wait. If unanswered after **24 hours**, send a second Telegram escalation
4. If still unanswered after **72 hours from first notification**: document a default action in agent_feedback and either proceed (if reversible) or stop (if irreversible). Default action must be stated in the original notification.

### Tier 3 — No act without explicit instruction
**Actions:** Irreversible actions, anything touching Bill's external accounts or personal data, anything Bill has explicitly flagged as requiring in-session confirmation. Examples: deleting production data, sending email under Bill's name, making financial commitments, modifying .env credentials.

**Default behavior:** Do not execute, even with a queued work_queue instruction. Require active confirmation from Bill in the current session. A prior session's approval does not carry forward.

## Agent Tier Assignment

Each agent in `agent_registry` carries an `authorization_tier` (smallint, default 1) column. The tier reflects the agent's most sensitive action class.

**Current fleet (all Tier 1):**
All 10 active agents perform internal reads/writes and Telegram notifications. No agent currently makes external account writes or irreversible external actions.

**Future agent builds:** The agent builder must assign a tier before promotion. A Tier 2 agent requires Bill's review before the first production run. A Tier 3 agent requires Bill's in-session confirmation for every action.

## Enforcement

This ADR establishes the convention. Enforcement is implemented in:
- **B-087 (grader):** Grader checks tier before passing autonomous chain execution
- **Chapter 2 (orchestrator):** Orchestrator checks tier before firing any action in an autonomous chain

## Approval Request Pattern

Tier 2 escalations use the annotation backbone (see annotation-pattern.md):
- `target_type = 'approval_request'`
- `target_id` = descriptive string (e.g. `promote_new_agent_to_active`)
- `intent_type = 'question'` (set by classifier or manually)
- Content: what is being requested, why, what the default action will be if unanswered

## Not Covered Here

- Session-level scope restrictions (within-card vs. outside-card) are handled by CONVENTIONS.md
- Capability-level authorization (what a specific capability can do) is tracked in the capabilities registry (B-089)
