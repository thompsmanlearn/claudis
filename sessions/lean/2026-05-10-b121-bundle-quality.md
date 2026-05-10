# Session: B-121 — Fix Working Bundle Output Quality
Date: 2026-05-10
Type: lean
Card: B-121
Code commit: 73b007f (attempt/b121-bundle-quality), merged dc56b35

## Tasks Completed
- Fixed `get_working_bundle()` in `anvil/uplink_server.py` — three issues resolved in one changeset

## Key Decisions
- **(no delta) handling**: exclude artifacts with no `**After:**` line entirely rather than labeling them. Labeled "(no delta)" entries have no signal value in the bundle; dropping them keeps the output clean.
- **Flagged filter scope**: narrowed from full artifact text to `after_line` only. Full-text search flagged sessions where historical references contained "failed", "stuck", etc. in non-outcome sections (e.g., "previously blocked by..."). After-line-only search matches intent: flag sessions whose *outcome* was problematic.
- **Truncation**: added `_clean_summary()` helper with word-boundary cut at ~120 chars + `…` suffix. The raw slice at 100/80 chars was cutting mid-word mid-backtick-span.

## Capability Delta
**Before:** Working bundle output was unusable — summaries truncated mid-word, flagged section surfaced most recent sessions regardless of outcome keywords, and "(no delta)" lines appeared without context.
**After:** Bundle summaries are clean one-liners capped at word boundaries. Flagged section contains only sessions where the recorded outcome mentions a failure keyword. Sessions with no After line are excluded. Output is readable and actionable at session start.

## Verified Output
```
## What's on Bill's mind

_Nothing pending._

## What Claude Code flagged

_Nothing flagged in the last 14 days._

## Recent activity

- [2026-05-10] Session: Thread Research Pipeline Bug Fixes: Dedup enforced at write time; consultation always uses correct charter question; non-200 webhook responses surfaced in…
- [2026-05-10] Session: B-120 — Bill's Mind Capture and Working Bundle: Bill can write free-text notes via the Workspace tab. Notes persist in `bill_notes`, surface in the working bundle at…
- [2026-05-09] Session: B-119 Auto-wiring: Charter save auto-wires the best-matched agent (≥0.7 confidence) or queues a build request. No manual step for…
- [2026-04-29] Session: B-073 — Anvil Threads Tab Actions: Thread architecture v0.1 is functionally complete. Bill can create threads, annotate them inline, change state (with…
- [2026-04-26] Bundle Review Follow-Up: Agent searches 5 broader platform/architecture topics yielding fresh articles each run. Research tab status line shows…
```

## Verification Checklist
- [x] Word-boundary truncation verified (no mid-word cuts in any entry)
- [x] Flagged section returns only After-line keyword matches (currently empty — correct, no recent sessions have failure outcomes)
- [x] No (no delta) entries appear in either section
- [x] `get_working_bundle()` output pasted above for Bill review
- [x] Uplink restarted (new PID 7347) — fix is live
