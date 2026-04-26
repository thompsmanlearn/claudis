# B-060: Anvil Feedback Thread Visibility

**Date:** 2026-04-26
**Session type:** Lean — single card
**Card:** B-060

## Tasks Completed

- Updated `get_research_bundle` in uplink_server.py: pending feedback select now includes `action_summary`, `action_session`, `action_result_url`; response rendered inline (✅/⏸ icon + session + URL). Added "## Recently Resolved Feedback" section (last 10 processed items, same fields).
- Added `get_feedback_threads` callable (uplink_server.py): returns `{pending, resolved}` for Research tab thread display.
- Added "Feedback History" section to Research tab (Form1/__init__.py): `_load_feedback_threads()` + `_build_feedback_thread_card()`. Renders each item as: header (target_type/target_id, date), content (Bill's message), response line if action_summary not null (✅ or ⏸, font_size 14/13 for visual distinction), session label, clickable result link.
- Uplink restarted cleanly.
- Both `attempt/b060-feedback-visibility` branches merged to main/master and pushed.

## Key Decisions

- Used `font_size=13` (vs 14) to visually dim deferred items — Anvil MD3 has no "muted" role.
- `get_feedback_threads` fetches all feedback (no `target_type` filter) for complete thread view; `get_research_bundle` keeps the existing `in.(agent,anvil_view)` filter for export context.
- Resolved query orders by `processed_at.desc` to show most recently closed threads first.

## Capability Delta

**New:** Research tab displays agent_feedback as full conversation threads — original intent visible alongside what Claude Code did in response. The OS pattern (B-059 write-back schema + B-060 thread visibility) is complete.

**New callable:** `get_feedback_threads` — returns pending + last 10 resolved feedback rows with all write-back fields.

## Lessons Written

0 new lessons (no novel patterns; thread rendering is standard Anvil pattern already in use).

## Branches / Commits

- claudis: `attempt/b060-feedback-visibility` → merged `df6153a`, deleted
- claude-dashboard: `attempt/b060-feedback-visibility` → merged `e0dc236`, deleted
- claudis main: `0618295` (merge) → `eebc88e` (trajectory)

## Usage

Session ~15%, weekly ~100%
