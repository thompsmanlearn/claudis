# Session: 2026-05-08 — B-104: Pass commit SHA explicitly to grader

## Directive
Fix the grader's systematic false-pause on historical cards caused by the HEAD~3 git diff window.

## What Changed
- **stats_server.py** (live + canonical):
  - `_get_git_diff_for_card(commit_sha)`: replaces `_get_recent_git_diff()`. When SHA provided, diffs `{sha}^ → {sha}` (the card's actual commit). When omitted, falls back to HEAD~3 with a note in the diff output.
  - `/grade_card`: now accepts optional `commit_sha` parameter. Passes it through to diff function and records it in `input_snapshot.commit_sha`.
- **sentinel/lean_runner.sh** (live + canonical): After successful card completion, captures `git rev-parse HEAD` and passes as `commit_sha` in the /grade_card call. Auto-cycle grading now uses the real commit SHA.
- **anvil/uplink_server.py**: `export_grader_review()` includes `commit_sha` in the rendered markdown header.

## Smoke Test
Graded B-080 with SHA `dbeec58`:
- Before (HEAD~3): PAUSE — "git evidence shows wrong era commits (B-102/B-103)"
- After (real SHA): PAUSE — but for substantive reasons:
  - ❌ Smoke test gap: "A live n8n workflow run with new articles was not confirmed"
  - ❌ Uplink code not in that commit: "git log shows dbeec58 changed only the session artifact markdown"
  - ✅ DDL, callable, n8n workflow, session artifact all confirmed from artifact text

The false-pause reason is gone. The real pause reasons remain. Behavior is correct.

## What Was Learned
The session artifact commit (the git commit that adds the .md file) often comes after the code commits. When /grade_card is called with the artifact commit SHA, the grader may still report the code changes as "not in this commit" — that's technically correct, but misleading for retrospective grading. For auto-cycle use, lean_runner captures HEAD at the end of the session, which should include both code and artifact commits if they're in the same session.
