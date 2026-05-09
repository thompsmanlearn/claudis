# ADR: Capability Index — Three-Registry Model

**Date:** 2026-05-08
**Status:** Active

## Decision

Three registries track capabilities at different levels of abstraction. Each has a distinct scope and must not duplicate the other two.

## What Each Registry Holds

### `agent_registry` (Supabase)
**Holds:** Individual agents — named, deployable n8n workflows with a defined lifecycle.
**Does NOT hold:** Skills, abstract capabilities, tools that aren't agents.
**Key columns:** agent_name, status, workflow_id, authorization_tier, skills_used[], capabilities_provided[], protected.

### `skills_registry` (Supabase) — primary; `skills/CATALOG.md` — human-readable generated view
**Holds:** Claude Code skills — loadable instruction sets that augment session behavior.
**Does NOT hold:** Agents, abstract outcomes, production workflows.
**Key columns:** name (PK), description, applies_when, also_triggers_when, provides, file_path, status, times_used, last_used.
**Source of truth:** `skills_registry` table. `CATALOG.md` is a human-readable view; it does not need to be kept in sync programmatically, but should be updated when skills change.

### `capabilities` (Supabase)
**Holds:** End-to-end outcomes the system can produce — what the system *can do*, not how it does it.
**Does NOT hold:** Individual agents, individual skills (unless the skill is itself the capability).
**Key columns:** id, name, category, description, confidence, status, times_used, last_used, authorization_tier, dependencies.

## Status Lifecycle

All three registries use the same status enum: `active` / `deprecated` / `retired`.

| Transition | Meaning |
|---|---|
| → `deprecated` | Still works but being phased out; prefer alternatives |
| → `retired` | No longer functional or intentionally removed |
| `deprecated` → `active` | Rehabilitated |
| Any → `retired` | Terminal; requires explicit session decision |

## Build Discipline

**When adding a new agent:** Add an `agent_registry` row before the first production run. Link `skills_used[]` and `capabilities_provided[]` after the agent is working.

**When adding a new skill:** Add a `skills_registry` row at skill creation. Update `CATALOG.md` to match.

**When shipping a card that adds a new end-to-end capability:** Add a `capabilities` row naming the outcome. This is checked by the close-session ritual.

## Close-Session Check

At every session close, the close-session skill asks: "Did this session add or modify any capability? If yes, is the corresponding registry entry current?" This is a discipline check, not an automated sync.

## Pre-existing State (2026-05-08)

- `agent_registry`: 10 active agents, all Tier 1, all with `skills_registry` links to be populated over time
- `skills_registry`: 6 skills, all `active`, fully populated from CATALOG.md
- `capabilities`: 114 rows, all `active` — populated in prior sessions; content not audited in B-089 (if drift found, write a cleanup card rather than fixing in session)
