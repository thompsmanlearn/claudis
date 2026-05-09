# Session: 2026-05-08 — B-091: Carry-document pattern

## Directive
Re-establish the carry-document pattern for desktop session handoff with three auto-generated files.

## What Changed
- **CARRY_QUESTIONS.md, CARRY_PROPOSALS.md, CARRY_HEALTH.md** (new): Template files at claudis repo root. Auto-generated on every session close.
- **stats_server.py** (live + canonical): Added `/generate_carry_documents` endpoint:
  - CARRY_QUESTIONS: thread sub_question_candidates + grader pause/fail verdicts + question-intent annotations
  - CARRY_PROPOSALS: targets with 2+ annotations (may warrant a card)
  - CARRY_HEALTH: lesson store integrity, agent fleet, unresolved errors, recent grader verdicts
- **close-session.md** (both copies): Added generate_carry_documents call and git commit step at close
- **DEEP_DIVE_BRIEF.md Section 11**: Added Carry Documents subsection explaining the three files and their role at desktop session start. Updated Starting a Desktop Session to read carry docs first.

## Smoke Test
`POST /generate_carry_documents` returned ok for all three files.
CARRY_HEALTH.md content: 250 lessons (0 broken), 10 active agents (claude_code_master flagged correctly — no workflow by design), 0 unresolved errors, 1 grader verdict (pause). ✓

## What Was Learned
CARRY_PROPOSALS.md pattern (3+ similar annotations) was simplified to 2+ because there may not be enough annotation volume yet to hit 3. Threshold can be raised in a follow-up card if noise becomes an issue.

## Unfinished
Nothing. Three files generated, close-session updated, DEEP_DIVE_BRIEF updated.
