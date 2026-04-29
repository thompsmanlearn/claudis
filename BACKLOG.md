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
