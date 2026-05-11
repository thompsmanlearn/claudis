# B-126: Reader-writer discipline in two-pass review
Date: 2026-05-10
Code commit: f6cdcd7

## What was done

Added reader-writer discipline to CONVENTIONS.md §3 (two-pass review convention).

Changes:
1. New `### Reader-writer check` subsection between "Resolved standard" and "Design sketch format" — standard question to ask during design review when a card creates a writer: "Where's the reader? What consumes this output and acts on it?" Acceptable answers defined. "We'll figure it out later" explicitly not acceptable.
2. Design sketch format updated from three fields to five — added Writer and Reader fields between Proposed shape and Open questions.
3. Worked example updated to include Writer and Reader entries (using the comment-classifier example that was already there).

## Scope

CONVENTIONS.md only. No code, no new files, no agent changes.

## Capability delta

None — this is a convention update, not a new capability.
