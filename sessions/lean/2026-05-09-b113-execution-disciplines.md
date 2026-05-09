# Session: 2026-05-09 — B-113: Karpathy execution disciplines

Documentation card. No code changes.

## What Changed

**CONVENTIONS.md** — Added "Execution discipline" block to Section 1 (Standing Principles), after "When Uncertain":
- Trace to the request: every changed line traces to the directive; remove anything that doesn't before committing
- Don't improve adjacent code: match existing style, don't refactor things that aren't broken, mention dead code in artifact rather than deleting it
- Simplicity over speculation: no unasked features, no single-use abstractions, rewrite 200-line solutions to 50 before committing

**skills/close-session.md** — Added Step 4a (Scope check) between Step 4 and Step 5 (artifact commit). One question: did this session change anything beyond the directive? If yes, note it in the artifact. Captures where the system tends to over-build without requiring a rewrite.

## Scope check (Step 4a)

No. Both edits are exactly what the directive asked for. CONVENTIONS got the three rules; close-session got the one-question check before the artifact step.

## Lessons Applied

None pre-loaded were directly triggered.
