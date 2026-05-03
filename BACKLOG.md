B-083: Surface most recent summary entry at top of thread page

## Goal

The redesign called for a "Standing summary slot" near the top of the thread page — a short distillation of conclusions so far, visible without scrolling. B-076 reserved the slot but rendered nothing meaningful. B-076's first attempt (first-paragraph-of-analysis) was removed in cleanup because it was misleading. B-078 added the `summary` entry type, which extraction now writes whenever desktop Claude produces conclusions. Three populated threads have real `summary` entries waiting to be surfaced.

This card connects the two: when a thread renders, find the most recent `summary` entry and display its content in a labeled block at the top of the thread, between the header and the main content. If no `summary` entry exists, render nothing — no placeholder, no header.

## Context

`_load_thread_entries` in `~/aadp/claude-dashboard/client_code/Form1/__init__.py` is where the thread page renders. The function partitions entries by type at render time (B-076 pattern). It currently builds: header → main content → history drawer → action panel.

This card adds one more partition: extract the most recent entry where `entry_type='summary'` (sorted by created_at DESC, take first). If found, render it in a labeled block right after the header (question + state badge) and before the main content list.

Render shape:
- A small section header: "Standing summary"
- The summary entry's content, rendered as it currently is in the main content list (the entry has bullet-style content like "- conclusion one\n- conclusion two\n..."; just render the text)
- A subtle divider after, before the main content begins
- The summary entry should NOT also appear in the main content list — it's already visible at the top, no point duplicating. Filter it out from the main content rendering.

What "most recent" means: highest `created_at` among entries where `entry_type='summary'`. If a thread has multiple summary entries (because multiple analyses were pasted over time), only the latest is shown at the top. The others remain in the main content list (this is the only exception to the "filter from main content" rule above — filter only the one being shown at top, not all summaries).

Edge cases:
- Zero summary entries → render nothing. No section header, no placeholder. The thread page goes header → main content directly, as it does today.
- One summary entry → that one is shown at top, and is filtered out of main content.
- Multiple summary entries → most recent shown at top and filtered from main content; older ones stay in the chronological flow.
- Summary entry exists but its content is empty/whitespace → treat as if no summary; render nothing at top.

Visual style: match the existing entry rendering aesthetic. Don't introduce new fonts, colors, or component roles. Use a Label with `role='title'` for "Standing summary" and `role='body'` for the content, consistent with how other section labels render in the form.

## Done when

- `_load_thread_entries` extracts the most recent non-empty `summary` entry for a thread.
- If found, renders it as a labeled "Standing summary" block immediately after the header section and before the main content list.
- The same summary entry is filtered out of the chronological main content list (so it doesn't appear twice).
- Older `summary` entries (if any) remain in the chronological main content list.
- If no qualifying summary entry exists, no block renders and no placeholder appears.
- Smoke test in session: open the existing Source expansion thread (id `946033c2-6acb-4164-8db2-3c60d4a8f9dd`). Verify the standing summary block appears at the top with the four bullet conclusions from the 18:40:26 summary entry. Verify the same content does NOT also appear in the main content list below.
- Open the existing TEST: B-072 verification thread (id where present) or another thread with no summary entries. Verify no Standing summary block renders and no placeholder appears.
- One commit on claude-dashboard master with the Form1 changes. Pushed.
- Session artifact written.

## Scope

Touch:
- `~/aadp/claude-dashboard/client_code/Form1/__init__.py` (modify `_load_thread_entries` only — add the summary extraction, render the top block, filter from main content)
- session artifact

Do not touch:
- Any other Form1 function
- `_build_thread_actions` or any action panel logic
- The History drawer
- Any uplink callable
- Any database schema
- The `summary` entry type or how it's written (B-078 is fine)
- Any other tab or form

If you find yourself wanting to:
- Add a "regenerate summary" button — stop. Future card.
- Show summary metadata (when written, by whom) — stop. Keep it clean; the entry already exists in the audit trail below.
- Add a config toggle for "show standing summary" — stop. Always on; if user doesn't want it, that's feedback.
- Truncate long summaries with a "more" button — stop. If summaries get too long, that's a prompt-tightening problem, not a render problem.

Two-hour ceiling: this is small. Likely 30-60 lines added/modified in `_load_thread_entries`. If it tips past two hours, something has gone sideways — surface it.
