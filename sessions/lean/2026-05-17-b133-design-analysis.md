# Session Artifact — B-133 Pre-card Design Analysis: Boot Path Unification

**Date:** 2026-05-17
**Type:** Design collaboration (no code built)
**Output:** Factual analysis delivered to Desktop Claude for card writing

---

## Tasks completed

Answered five design questions for Desktop Claude before B-133 (boot path unification) is written:

1. **Specific overlaps and divergences** between LEAN_BOOT.md and bootstrap — step-by-step diff, not a summary.
2. **Is bootstrap still actively invoked?** Confirmed Sentinel-only, currently invoked by nothing active (Sentinel disabled).
3. **Right unification shape** — what the code says, not theory.
4. **Bootstrap steps missing from LEAN_BOOT.md that would matter** — only heartbeat update is functionally missing.
5. **Gotchas** — four concrete items Desktop Claude should know.

Follow-up question answered: whether lean_runner.sh lesson injection (n8n webhook, task_type: general) and LEAN_BOOT step 11 (inject_context_v3 direct, task_type: design_and_build) are genuinely different or redundant.

## Key findings

- **lean_runner.sh lesson injection is dead.** The `lesson_injector` n8n workflow was deleted in B-130 (2026-05-16). The webhook at `http://localhost:5678/webhook/inject-context` returns 404. lean_runner.sh gets an empty CONTEXT_BLOCK and logs "no context returned" on every lean session. No double injection is occurring. No double times_applied increment.
- **Only live lesson injection** is LEAN_BOOT.md step 11 → stats server direct, `task_type: design_and_build`, queries `lessons_learned` + `reference_material`.
- **Double git pull is the only real live redundancy.** lean_runner.sh pulls before spawning Claude; LEAN_BOOT step 1 pulls again inside Claude. Second pull is always a no-op. Harmless but dead weight.
- **bootstrap is Sentinel-only.** It's invoked via wake_prompt.md in Sentinel sessions. Sentinel is disabled. bootstrap is currently called by nothing.
- **One functional gap:** LEAN_BOOT.md has no boot heartbeat update. lean_runner.sh writes to `session_status` (a different table) but not to `system_config.claudis_current_task`. During a lean session, `system_config` shows 'idle'. bootstrap step 7 handles this for Sentinel sessions; lean sessions have no equivalent.

## Key decisions / what Desktop Claude should put in B-133

- Remove the dead lesson injection block from lean_runner.sh (~lines 90-114) and the stale comment on line 4.
- LEAN_BOOT step 1 (git pull) should stay — needed for interactive sessions where lean_runner.sh hasn't pre-run.
- session_notes_load call in bootstrap is deprecated (CONVENTIONS.md 2026-04-25) — remove it.
- Whether to add a boot heartbeat update to LEAN_BOOT.md is an open question for the card to resolve.
- "Unification" is not merging two files into one — it's cleaning up the lean path (dead code in lean_runner.sh) and clarifying bootstrap as Sentinel-only in its header.

## Capability delta

None — no code built this session. The output is design clarity that enables B-133 to be written correctly.

## Lessons written

1. lean_runner.sh lesson injection dead after B-130 (lesson_injector n8n workflow deleted)
