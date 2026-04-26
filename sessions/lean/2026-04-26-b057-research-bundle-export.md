# B-057: Research Bundle Export

**Date:** 2026-04-26
**Session type:** Lean — directive-driven
**Card:** B-057
**Commits:** claudis e15d6f9, 31a0345 · claude-dashboard ce3c39c

---

## Tasks Completed

- Added `get_research_bundle(agent_run_id=None)` callable to `~/aadp/claudis/anvil/uplink_server.py`
- Added ⬇ Export button to Research tab header in Anvil dashboard
- Restarted aadp-anvil service; confirmed uplink reconnected
- Pushed both repos (claudis, claude-dashboard)

## Key Decisions

- Used PostgREST `or=(processed.is.null,processed.eq.false)` combined with `target_type=in.(agent,anvil_view)` for pending feedback query — single request, no Python-side merging needed
- Callable returns full summaries (no truncation) per card spec
- Clipboard: tries `navigator.clipboard.writeText` first; TextArea fallback if it raises (card noted TextArea is primary test path in Anvil's browser context)
- Export feedback label (`_research_export_fb`) is separate from run feedback label so messages don't interfere
- Frontmatter query_set derived from distinct `query_used` values in the run (dynamic, not hardcoded)

## Capability Delta

**Before:** Research tab could rate, comment, and run the agent. No way to export run context to a desktop session.

**After:** Bill can press ⬇ Export, paste the resulting markdown into a desktop Claude session, and get the full run context — frontmatter (run_id, timestamp, article count, query set), all articles with summaries/ratings/comments, and any pending feedback queued in Anvil — in one shot.

## Verification

Live data confirmed via smoke test:
- Most recent run: `74919087-...`, 4 articles, all rated -1 (👎 shown correctly)
- 4 pending feedback rows surfaced (2 for agent, 2 for anvil_view)
- query_set extracted: `['context engineering for LLM agents']`
- Uplink health ping: `ok`

## Lessons Written

1. PostgREST OR + AND filter combination pattern (see Step 7)

## Applied Lessons (incremented by stats server — skip UPDATE at step 8)

- `60e3b609-bf5f-47fd-87f9-86db88cf2dbb` — TracerProvider init
- `lesson_anvil_client_closure_pattern_2026-04-18` — closure capture
- `lesson_anvil_governance_surface_2026-04-18` — portable types
- `lesson_anvil_link_no_target_2026-04-26` — Link no target kwarg

## Usage

Session ~30% · Weekly ~70%
