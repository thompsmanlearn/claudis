# Session: 2026-05-08 — B-088: Authorization tiers

## Directive
Formalize authorization tiers replacing the binary autonomous/needs-approval model.

## What Changed
- **architecture/decisions/authorization-tiers.md** (new): Three-tier system defined:
  - Tier 1: Act + notify (all current agents)
  - Tier 2: Ask first, 24h/72h timeout escalation via agent_feedback + Telegram
  - Tier 3: No act without in-session confirmation
- **DDL**: `authorization_tier smallint DEFAULT 1` added to `agent_registry`
- **Migration**: All 10 active agents confirmed Tier 1 (UPDATE applied; all already defaulted to 1)
- **CONVENTIONS.md**: Authorization Tiers subsection added to Section 2
- **architecture/decisions/annotation-pattern.md**: Already contained the approval_request target_type; ADR cross-references authorization-tiers.md

## What Was Learned
All current agents are correctly Tier 1 — they do internal reads/writes and Telegram notifications only. No agent currently makes external account writes. The binary list in CONVENTIONS Section 3 (removed in B-084) was accurate but not actionable — the tier system makes it enforceable.

## Unfinished
Enforcement: grader (B-087) and orchestrator (Chapter 2). The tier column exists; the check logic comes later.
