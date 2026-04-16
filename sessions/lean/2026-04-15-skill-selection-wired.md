# Session: 2026-04-15 — skill-selection-wired

## Directive
B-015: Add a skill selection step to LEAN_BOOT.md so Claude Code matches each directive
against CATALOG.md and loads relevant skills before executing. Step goes between reading
the directive (step 4) and reading CONTEXT.md (step 5).

## What Changed

**LEAN_BOOT.md** (`~/aadp/claudis/LEAN_BOOT.md` and `~/aadp/prompts/LEAN_BOOT_stable.md`):
- Added step 5 (Skill selection) between old steps 4 and 5
- Renumbered: old steps 5, 6, 7 → new steps 6, 7, 8
- Step 5 logic:
  1. Read skills/CATALOG.md
  2. Match directive against "Applies when" and "Also triggers when" using judgment
  3. Read matching SKILL.md files into context
  4. If no match: proceed without
  5. Output: `Loading: [names]. Proceeding.` or `No skills matched. Proceeding.`
  6. Do NOT auto-load references/lessons.md or references/patterns.md — pull on demand

## Verification: Three Test Directives

**Directive 1:** "Diagnose why the research synthesis agent stopped producing output after yesterday's n8n update"
- triage — MATCH via "Applies when" (failure, unclear layer) AND "Also triggers when" (agent stopped after system change)
- system-ops — MATCH via "Applies when" (diagnosing Pi services, n8n)
- agent-development — NOT loaded; triage covers the workflow-output symptom more specifically
- **Result: Loading: triage, system-ops. Proceeding.**

**Directive 2:** "Write a new monitoring workflow for sandbox agent staleness"
- agent-development — MATCH via "Applies when" (designing agents, n8n endpoints)
- system-ops — NOT loaded; directive is build/design, not operate/diagnose
- **Result: Loading: agent-development. Proceeding.**

**Directive 3:** "Update TRAJECTORY.md with Q2 milestones"
- No skills matched — mechanical document edit, no diagnostic/build/research/comms challenge
- communication: TRAJECTORY.md is Bill-readable but the task has no tone/format difficulty
- **Result: No skills matched. Proceeding.**
- Negative case confirmed correct.

## What Was Learned

- The "Also triggers when" column catches symptom-driven matches that "Applies when" misses.
  A directive that mentions "stopped working after a system change" lands triage even if it
  doesn't say "unclear layer" — matching on the described symptom, not just the task type.
- The negative case (directive 3) is important: communication skill nearly matched because
  TRAJECTORY.md is Bill-readable, but the task has no communication challenge. The selection
  step should ask "does this directive have a problem this skill solves?" not just "does this
  directive involve something this skill relates to?"
- Skill selection confirmation line keeps boot output lean — one line, not a paragraph.

## Unfinished

Nothing. Both LEAN_BOOT.md and stable backup updated. Verification complete.
