B-072: Anvil Threads tab — read view

Status: ready
Depends on: B-070 (schema), B-071 (read callables get_threads, get_thread_entries)

Goal
Add a Threads tab to the Anvil dashboard that shows active threads at a glance and lets Bill click into any thread to see its full chronological entry log. No actions, no buttons, no creation affordance — just visibility. This is Card 3 of the v0.1 thread architecture (B-070 schema, B-071 callables, B-072 read view, B-073 actions). After this card, Bill can see what threads exist and what's in them; B-073 adds the ability to actually do anything with them.

Context
B-070 created the substrate. B-071 added the callable layer including get_threads(state='active') and get_thread_entries(thread_id). This card surfaces that data in Anvil so Bill can confirm the architecture works against real data and decide what affordances B-073 should add. Read-only intentionally — actions follow once the read view proves the right shape.

Design decisions already made (do not relitigate):
- Threads tab placement: between Memory and Skills (alphabetical-ish, near other "what's in the system" tabs).
- Default view: active threads only, sorted by last_activity_at descending. A small dropdown switches between active / dormant / closed / all.
- Thread cards collapsed by default; click to expand and see entries.
- Entry rendering: chronological top-to-bottom (oldest first), so reading the thread reads like a story.
- Entry types get distinct visual treatment (icon or color tag) so Bill can scan the structure of a thread.

Done when

1. New Anvil tab "Threads" added to Form1/__init__.py, placed between Memory and Skills in the existing tab structure.

2. Tab layout, top to bottom:
   - Header row: title "Threads" on the left, state filter dropdown on the right (default 'active', options: active / dormant / closed / all).
   - Counter line: "{N} active thread(s)" — updates when filter changes.
   - Thread list: thread cards in collapsed state, sorted by last_activity_at descending.
   - Empty state: if no threads match the filter, show "No {state} threads."

3. Thread card (collapsed):
   - Title (large, primary)
   - Question (smaller, secondary, single line truncated if long)
   - State badge (active / dormant / closed) — small colored tag
   - Bound agent name if any, otherwise "no agent wired" in muted style
   - Entry count and last activity date ("12 entries · last active 2 days ago")
   - Click target: clicking the card expands it to show entries.

4. Thread card (expanded):
   - Same header info as collapsed
   - Then a chronological list of entries — oldest first, top to bottom
   - Each entry shows: icon for entry_type, content (truncated to ~600 chars with [truncated] marker if longer), source (small/muted), created_at (relative — "3 hours ago", "yesterday", "April 25")
   - Entry type icons: gather (🔍), annotation (✏️), analysis (🔬), conclusion (✅), state_change (🔁) — feel free to swap if cleaner alternatives exist
   - Collapse on second click of the card header.

5. Behavior:
   - Tab loads call get_threads(state='active') and render.
   - Filter dropdown changes call get_threads(state=...) and re-render.
   - Card expansion lazy-loads entries via get_thread_entries(thread_id) — don't pre-fetch all entries on tab load.
   - Refresh button at the top right of the tab header re-fetches the current view.

6. No new uplink callables. Use the existing get_threads and get_thread_entries from B-071.

7. Verify in Anvil:
   - Tab loads cleanly with the existing test thread (or create a new test thread via supabase_exec_sql before testing if the smoke-test cleanup removed everything)
   - Counter shows correct count
   - Card expansion fetches entries lazily and renders chronologically
   - Filter dropdown works for all four options including 'all'
   - Empty state renders when filter returns no results
   - Refresh button re-fetches

Out of scope (B-073 territory)
- Create-thread affordance (textbox + create button)
- Annotate button per thread (add an annotation entry inline)
- Gather button (trigger bound agent)
- Analyze / Export bundle button (markdown export of thread state for desktop Claude)
- State change dropdown (move thread between active/dormant/closed)
- Wire-agent affordance (select bound agent from a dropdown of webhook-enabled agents)
- Edit thread title or question
- Delete thread

Out of scope (deferred beyond v0.1)
- Search within a thread
- Cross-thread search
- Pinning threads
- Bulk operations
- Thread branching or sub-threads

Scope
Touch:
  ~/aadp/claude-dashboard/client_code/Form1/__init__.py — new Threads tab

Do not touch:
  uplink_server.py (read callables already exist; no new ones needed for v0.1 read view)
  Schema, ChromaDB, agents, skills, brief
  Any other tab

Verification checklist
- Threads tab visible in nav between Memory and Skills
- Tab loads with active threads sorted by last_activity_at desc
- Counter shows correct thread count for current filter
- State filter dropdown switches between active / dormant / closed / all
- Thread cards collapse/expand on click
- Expanded view shows entries chronologically with entry-type icons
- Entry content truncates at ~600 chars with [truncated] marker
- Refresh button works
- Empty state renders cleanly when no threads match
- Branch attempt/b072-threads-read-view on claude-dashboard, merged to master, pushed
- Anvil app picks up master branch automatically (no manual publish step)

Notes
- This card is intentionally read-only. Bill needs to see real thread data to decide what affordances B-073 should add. If something feels missing during use, that's a B-073 input.
- The lazy-load of entries on card expansion matters for scaling — once Bill has 50 threads with hundreds of entries each, pre-fetching everything on tab load would be wasteful. Build the discipline now.
- Material Design 3 component roles match other tabs: outlined-card for thread cards, body for entry text, headline for tab title. Match what's already in Form1/__init__.py.
- The Anvil Link target='_blank' lesson applies — links inside entry content should not pass target. (Captured as a lesson; the existing code in other tabs already follows this.)
- For the test thread to exist when Bill verifies the tab, this card may need to create a test thread + a few entries via supabase_exec_sql at the start, then leave them in place so the tab has something to render. Don't clean those up at session end — they're useful test data going forward. Mark them clearly as test threads (e.g. title prefix "TEST:").

B-073: Anvil Threads tab — actions

Status: ready
Depends on: B-070 (schema), B-071 (write callables), B-072 (read view)

Goal
Add the action affordances to the Threads tab so Bill can create threads, annotate them, change state, wire agents, trigger gather runs, and export bundles for desktop analysis. This completes the v0.1 thread architecture (B-070 schema, B-071 callables, B-072 read view, B-073 actions). After this card, threads are functionally complete — Bill can use them for real work and decide what extensions matter.

Context
B-072 added the read view. The v0.1 design pattern is "input levers + trigger + export" — the same OS pattern proven in the Research tab. This card brings that pattern to threads. All write callables already exist (B-071); this card wires them into UI affordances.

Design decisions already made (do not relitigate):
- Six action affordances: create thread, annotate, change state, wire agent, gather, export bundle.
- Create-thread affordance lives at the top of the tab (above the filter dropdown), so it's discoverable without scrolling.
- Per-thread actions live inside the expanded card view — only visible when a thread is open.
- Gather button only shown when bound_agent is wired and exists in agent_registry with a non-null webhook_url.
- Export bundle uses the established pattern from B-057/B-061: clipboard write attempt, fallback to TextArea modal.
- No state-change ceremony: changing to closed state, close_reason is optional (the textbox can be left empty).
- Wire-agent picker lists only active agents with non-null webhook_url. Empty list shows "No agents available — none have webhook URLs configured."

Done when

1. Create-thread affordance at top of Threads tab:
   - Two text inputs side by side: "Title" (required) and "Question" (required)
   - "Create thread" button — calls create_thread(title, question, bound_agent=None)
   - On success: refreshes the thread list, the new thread appears at top of active filter
   - On validation failure (empty title or question): inline error message, no callable call
   - Inputs clear after successful creation

2. Per-thread expanded card actions (visible only when card is expanded, placed below the entries list):

   **Annotate row:**
   - TextArea for entry content + "Add annotation" button
   - Calls add_thread_entry(thread_id, entry_type='annotation', content=..., source='bill', embed=True)
   - On success: new entry appears at the bottom of the entries list, TextArea clears
   - last_activity_at advances via the trigger; thread re-sorts to top of list on next refresh

   **State change row:**
   - State dropdown (active / dormant / closed)
   - Close reason TextBox (only shown/active when 'closed' selected; optional even then)
   - "Update state" button — calls update_thread_state(thread_id, state, close_reason=...)
   - On success: badge updates, state_change entry appears in entries list
   - If transitioning out of 'closed' state, close_reason is preserved in the previous state_change entry for history

   **Wire agent row:**
   - Dropdown of available agents (active status AND webhook_url IS NOT NULL)
   - "Wire agent" button — calls wire_thread_agent(thread_id, agent_name)
   - "Unwire" button (only shown if currently bound) — calls wire_thread_agent(thread_id, None)
   - Card header updates to reflect new bound_agent
   - state_change entry appears in entries list

   **Gather row (only shown when bound_agent is set AND exists in agent_registry with webhook_url):**
   - "▶ Gather" button — fires the bound agent's webhook
   - Reuses the existing invoke_agent callable; thread_id passed in payload metadata so the agent (eventually) knows it's gathering for this thread
   - "Triggering..." → "✅ Triggered" feedback inline
   - For v0.1, the agent doesn't actually know about threads — Gather just triggers the agent. A later card wires thread-aware gathering. For now, document this gap explicitly: gather output goes to wherever the agent normally writes, not yet into thread_entries automatically.
   - When triggered: writes a thread_entry of type 'gather' immediately with content "Gather triggered: {agent_name} (output not yet wired to thread)" — at least the trigger is recorded in the thread

   **Export row:**
   - "⬇ Export thread" button — calls a new uplink callable get_thread_bundle(thread_id) that returns the markdown bundle
   - Bundle format follows B-057/B-061 conventions: YAML frontmatter (thread_id, title, question, state, created_at, last_activity_at, entry_count, bound_agent), then the chronological entries with type icons and timestamps
   - Same clipboard-then-fallback pattern as Research tab Export

3. New uplink callable get_thread_bundle(thread_id) -> str:
   - Pulls thread + all entries
   - Returns markdown with frontmatter and chronological entry list
   - Each entry shows: icon (matching B-072), entry_type, source, created_at, content (full content, not truncated — desktop Claude needs the full picture)
   - At the bottom of the bundle, include a "## Pending Feedback" section if any agent_feedback rows target this thread (target_type='thread', target_id=thread_id) — establishes a forward-compatible hook even though no feedback is currently filed against threads

4. Behavior details:
   - All actions cause the affected card to refresh entries inline (no full tab reload)
   - All callables already exist or are added in this card (only get_thread_bundle is new)
   - Material Design 3 roles consistent with other tabs

5. Smoke test in session:
   - Create a new thread via the UI; confirm it appears at top of active list
   - Annotate the thread; confirm entry appears chronologically and last_activity_at updates
   - Wire context_engineering_research as the agent; confirm bound_agent updates and gather button appears
   - Click gather; confirm gather entry written and Telegram alert (if any) fires from the agent
   - Change state to dormant with no reason; confirm transition entry written
   - Change state back to active; confirm second transition entry
   - Export the thread; confirm bundle has correct frontmatter and chronological entries
   - Cleanup is optional — leaving real test threads in the system is fine if they're meaningful; otherwise delete

Out of scope (deferred)
- Thread-aware gathering (agent reads thread context and writes results back as gather entries) — meaningful but bigger; needs separate card
- Search within a thread
- Cross-thread search
- Edit existing entries (entries are append-only by design)
- Delete individual entries
- Delete threads from UI (use Supabase directly for now; can be added if it becomes friction)
- Thread-targeted agent_feedback (the bundle has a hook for it but no UI to write it yet)

Scope
Touch:
  ~/aadp/claudis/anvil/uplink_server.py — add get_thread_bundle() callable
  ~/aadp/claude-dashboard/client_code/Form1/__init__.py — add action affordances to Threads tab

Do not touch:
  Schema (no new tables, no new columns)
  Existing callables (write callables from B-071 are unchanged)
  Other tabs
  LEAN_BOOT, bootstrap, close-session

Verification checklist
- Create-thread affordance at top of Threads tab; new threads appear in active filter immediately
- Annotate adds entries chronologically; last_activity_at advances
- State change dropdown handles all transitions; close_reason captured when applicable
- Wire-agent dropdown only lists agents with webhook_url; wire/unwire writes state_change entries
- Gather button only appears when bound_agent is wired; triggers webhook; writes a gather entry recording the trigger
- Export button generates markdown bundle in clipboard or modal fallback
- get_thread_bundle callable returns valid markdown with frontmatter, entries, and the agent_feedback hook section
- All actions inline-refresh the affected card (no full tab reload)
- Smoke test passes end-to-end
- Branch attempt/b073-threads-actions on both repos, merged to main/master, pushed

Notes
- This card lands the v0.1 thread architecture as functionally complete. After it ships, Bill should use threads for one real research effort (probably a fresh research thread, or possibly migrating one of the parked desktop conversations into a thread) and report back what the architecture surfaces or hides.
- The "gather output not yet wired into thread" gap is intentional. The v0.1 question was whether thread architecture is the right primitive. Tightening the agent-to-thread integration is a meaningful subsequent investment that shouldn't expand this card.
- Once Bill uses a real thread, decide what to build next: thread-aware gathering, agent_feedback against threads, cross-thread analysis, or something the use surfaces that we haven't anticipated.
- The agent_feedback hook in the bundle is forward-compatible: future cards can add a "Feedback for this thread" textbox that writes target_type='thread'. The bundle already knows where to surface those entries; just no UI to write them yet.
