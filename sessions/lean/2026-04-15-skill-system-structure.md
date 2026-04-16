# Session: 2026-04-15 — Skill System Structure Update

## Directive
Update skill system structure based on design review answers from previous session
(2026-04-15-skill-design-questions.md). Four design decisions: merge agent-development +
api-integration, add "Also triggers when" column to CATALOG, create PROTECTED.md, add triage skill.

## What Changed

**skills/agent-development/SKILL.md** — Rewritten with two internal sections: "Building and Managing
Agents" and "API and Integration Patterns". Both remain stub sections pending content fill.

**skills/api-integration/** — Directory removed. Content was stub-only; structural intent merged
into agent-development Part 2. git rm tracked the deletion.

**skills/triage/SKILL.md** — New stub skill for cross-layer diagnostic reasoning. Created with
references/ directory. Distinct from system-ops: triage is for unknown-layer failures; system-ops
is for known-procedure execution.

**skills/PROTECTED.md** — New file. Single source for resources requiring explicit approval:
Telegram Command Agent workflow (`kddIKvA37UDw4x6e`), DIRECTIVES.md, .env, MCP server. Cross-referenced
from all skill files and LEAN_BOOT.md startup sequence.

**skills/CATALOG.md** — Three-column table (Applies when / Provides / Also triggers when).
Five skills: agent-development, research, system-ops, communication, triage. Communication
description narrowed from "any artifact Bill will read" to Telegram alerts and session artifacts.

**LEAN_BOOT.md** — Startup sequence updated: added step 3 (read PROTECTED.md) before existing
DIRECTIVES.md step. Steps 3–6 renumbered to 4–7.

**~/aadp/prompts/LEAN_BOOT_stable.md** — Stable backup updated to match.

## What Was Learned

All skill SKILL.md files were stubs — no content was lost in the api-integration merge. This means
the skill content-fill work is still fully ahead. The structure (which skills exist, how CATALOG
triggers them, what PROTECTED.md covers) is now stable enough to begin filling content.

The "Also triggers when" column surfaces problem-state entry points that weren't reachable from
task-name matching alone. This is most valuable for triage (unknown-layer failure) and agent-development
(silent API failures that don't raise exceptions).

## Unfinished

- All SKILL.md files remain stubs — content-fill is next phase
- LEAN_BOOT.md does not yet reference CATALOG.md or explain when to load skills — auto-loading
  mechanism is not yet designed
- triage references/ files are empty — cross-layer trace procedure not written
