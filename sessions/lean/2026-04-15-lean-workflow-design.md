# Session: 2026-04-15 — lean workflow design

## Directive
Back up LEAN_BOOT.md to the repo. Provide direct input on the lean session workflow design: startup sequence adequacy, session card format, artifact format, LEAN_BOOT.md ordering, and other risks.

## What Changed
- `~/aadp/claudis/LEAN_BOOT.md` — created (copy of ~/aadp/LEAN_BOOT.md). Now under version control. Commit 4d3a2d0.

## Decisions
**LEAN_BOOT.md sync direction:** Repo copy should be authoritative, but no sync step exists yet. The startup sequence currently reads the local Pi copy before git pull runs, so repo edits don't propagate until the local file is manually updated. Recommended fix: add `cp ~/aadp/claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md` as step 1b in the startup sequence (after git pull succeeds). Not implemented this session — waiting for Bill's direction.

**Git pull failure handling:** Current instruction (proceed on local state, notify Telegram) is underspecified. Recommended tightening: on pull failure, send Telegram and stop rather than proceeding — stale directives are worse than a delayed session. Not implemented this session.

## What Was Learned
Session card format: scope boundaries ("do not touch") are load-bearing and should be a first-class field, not optional. Without the explicit exclusion list in today's directive, CONVENTIONS.md was a plausible write target for the new behavioral conventions.

Session artifact format: the four sections don't capture decisions considered and rejected. A future instance may re-examine the same tradeoff and re-derive the same conclusion or go the other way. Recommend optional fifth section: "## Decisions — key choices and why alternatives were rejected."

Startup sequence: right-sized as-is. The four reads (DIRECTIVES → CONTEXT → TRAJECTORY, with LEAN_BOOT already loaded) provide genuine orientation in ~6-8 tool calls. Nothing to cut; the mandatory framing matters.

Skill catalog design (flagged for next session): catalog must be an index of names/descriptions only — load-on-demand. Inline skill content in boot context will re-bloat what was just cut.

## Unfinished
- Startup sequence sync step for LEAN_BOOT.md (cp from repo after pull) — not added, pending Bill's direction
- Git pull failure handling — not tightened, pending Bill's direction
- Skill catalog design — deferred to next session by design
