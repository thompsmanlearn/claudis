# Session: 2026-05-08 — B-105: Fix Done when extraction + empty-rubric guard

## Directive
Fix BACKLOG.md done_when parser for format variants, add guard against grading with empty rubric.

## What Changed
- **stats_server.py** (live + canonical):
  - `_parse_card_from_backlog()`: done_when regex changed from `##\s+Done when` to `#{0,4}\s*Done when` — now matches `## Done when`, `### Done when`, and `Done when` (no hash). Fixes B-073, B-071.
  - `/grade_card`: added empty-rubric guard. If done_when is empty after parsing, returns HTTP 400 with `verdict='cannot_grade'` and a clear message naming what was missing. No Sonnet call when rubric is absent.

## Calibration Results (10 cards re-graded with commit SHAs)

| Card | Category | Verdict | Reason |
|---|---|---|---|
| B-084 | Should grade well | PAUSE | 60-line target not met (96 lines) — substantive |
| B-083 | Should grade well | FAIL | Artifact commit contains only session artifact .md, not code changes |
| B-082 | Should grade well | PAUSE | Anthropic RSS deferred + smoke test gap |
| B-078 | Should grade well | FAIL | Artifact commit contains only session artifact .md |
| B-079 | Partial/deferred | PAUSE | Commit contains only artifact, not code |
| B-073 | Partial/deferred | PAUSE | Parser now works; substantive concerns remain |
| B-057 | Partial/deferred | CANNOT_GRADE | No Done when section (pre-standardization card format) |
| B-080 | Known regression | PAUSE | Smoke test gap + code not in artifact commit — correct |
| B-071 | No strong memory | PAUSE | Parser now works; mostly passed but commit gap noted |
| B-058 | No strong memory | CANNOT_GRADE | No Done when (uses Verification checklist format instead) |

## Key Finding: New Systematic Issue Identified
The fix resolved the HEAD~3 window problem, but revealed a new pattern: several session artifacts were committed as standalone commits (just the .md file), separate from the code commits. The grader correctly notes "git log shows this commit changed only the artifact .md." This is accurate — but for retrospective calibration, it means we need the *code* commit SHA, not the *artifact* commit SHA.

## What Was Learned
- B-057, B-058: pre-standardization cards without "Done when" → correctly return cannot_grade
- B-083, B-078: FAIL verdicts because artifact was committed alone — not false positives, but also not evidence of broken implementation
- For future calibration: pass the code commit SHA (the one containing actual file changes), not the artifact commit SHA

## Unfinished
Nothing. Parser fixed, guard added, calibration results documented.
