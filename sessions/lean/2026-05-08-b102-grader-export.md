# Session: 2026-05-08 — B-102: Grader evaluation export

## Directive
Build the export feature deferred from B-087: uplink callable + Anvil "Copy for Opus" button.

## What Changed
- **anvil/uplink_server.py**: Added `export_grader_review(review_id)` callable.
  Returns structured markdown block with: metadata, verdict, full rationale, per-criterion assessment (met/not-met + evidence), input_snapshot contents, and a footer prompt for desktop AI analysis.
- **Form1/__init__.py**: Added "📋 Copy for Opus" button to each grader_review card in the Grader tab.
  - Calls export_grader_review(), attempts clipboard copy via navigator.clipboard
  - Falls back to a visible TextArea for select-all-copy if clipboard API unavailable
  - Export button below the override buttons on each review card

## Smoke Test
Exported review 6233f065 (B-084, verdict=PAUSE):
- Markdown produced: 2120 chars ✓
- Rationale: full text explaining HEAD~3 window issue ✓
- 4 criteria with ❌ + evidence excerpts, 1 with ✅ ✓
- Input snapshot: card_id, done_when, artifact_path, artifact_length, git_diff_summary ✓
- Footer: "Paste into a desktop AI session and ask: 'Was this verdict correct?...'" ✓

## Unfinished
Nothing. The export is complete. Part 3 (calibration pass) is a desktop Opus session task — not a Claude Code card.
