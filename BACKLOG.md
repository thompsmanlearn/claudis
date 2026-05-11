## B-127: Dashboard layout restructure — five-tab structure
Status: ready
Depends on: B-126

### Goal
Restructure the Anvil dashboard from its current ten-tab layout into a five-tab structure organized around how Bill actually uses the system. Move daily-use actions and information to a Home landing tab. Consolidate system-internal views into a single System tab with collapsible sections. Keep Threads and Sessions as their own tabs. Add Workpad as a placeholder tab (real implementation in a follow-on card).

This card is layout and navigation only. No new features. No data model changes. Workpad gets a stub tab with a "coming soon" placeholder so the navigation reflects the final shape; the surface itself is B-128.

### Context
Decided through two-pass review on 2026-05-10. Opus proposed a two-layer design (top strip + collapsed sections). Claude Code reviewed and identified six load-bearing issues (Inbox vs bill_notes confusion, Write Directive missing from primary actions, Threads can't be collapsed, Grader and Autonomous Mode needing explicit decisions, scope estimate of 300-400 lines). Bill and Opus then reshaped to a five-tab structure organized by activity type.

**The five tabs and what each is for:**

1. **Home** — daily-use landing surface. 80% of Bill's interaction lives here.
   - Status strip at top: green/yellow/red overall, agents active, work queue count, pending Inbox count (prominent if > 0)
   - Primary actions: Write note, Write directive, Export working bundle, Export audit bundle
   - Unaddressed bill_notes list (from current Workspace tab)
   - Pending Inbox approvals list with Approve/Deny buttons (from current Fleet → Inbox section)
   - Autonomous Mode toggle (from current Fleet → Controls)
   - Trigger Lean Session button (from current Fleet → Controls)

2. **Workpad** — stub for now. Tab exists, body is a placeholder ("Workpad — coming in B-128"). Reserves the navigation slot.

3. **Threads** — keep as-is. The investigation workflow surface stays where it is.

4. **Sessions** — keep as-is. Recent session artifacts, execution window.

5. **System** — consolidation of current Fleet, Memory, Lessons, Skills, Artifacts, Research, Grader into one tab with collapsible sub-sections. Each sub-section is what its current tab is, just nested. Bill goes here for periodic review, not daily.
   - Fleet (agent list, system health detail)
   - Memory
   - Lessons
   - Skills
   - Artifacts
   - Research
   - Grader

**Font sizes:** body text bumped from 16 to 18. Section headers from 20 to 22. Status strip indicators larger still (24). One global pass through Form1/__init__.py.

**What gets cut entirely:** the current Workspace tab disappears — its contents are absorbed into Home.

### Done when

1. Anvil Form1 has five tabs in this order: Home, Workpad, Threads, Sessions, System.

2. Home tab contains:
   - Status strip at top with: overall health indicator (green/yellow/red), active agents count, work queue count, pending Inbox count (visually prominent when > 0)
   - Four primary action buttons: Write note, Write directive, Export working bundle, Export audit bundle
   - Unaddressed bill_notes list with Mark addressed buttons
   - Pending Inbox approvals list with Approve/Deny buttons
   - Autonomous Mode toggle with current state visible
   - Trigger Lean Session button

3. Workpad tab exists with placeholder content: "Workpad — coming in B-128. This will be a lightweight investigation surface for exploring questions before they become threads."

4. Threads tab unchanged in functionality.

5. Sessions tab unchanged in functionality.

6. System tab contains the current Fleet, Memory, Lessons, Skills, Artifacts, Research, and Grader views as collapsible sub-sections. Each opens to its current full functionality. Default state: all collapsed.

7. Font sizes increased: body labels to 18, section headers to 22, status strip indicators to 24. Apply consistently across Form1.

8. Existing Workspace tab removed.

9. All current functionality remains accessible — nothing is cut, only relocated. Specifically verify: charter editing in Threads, agent approve/deny, lesson search, memory browse, autonomous toggle, trigger session, all four export bundles, write directive flow.

10. Commit and push. Both claude-dashboard and claudis repos if changes touch both.

### Scope
Touch: ~/aadp/claude-dashboard/client_code/Form1/__init__.py (the layout file)
Do not touch: any uplink callable, any backend code, any data model, the threads workflow, the gather pipeline, anything outside Form1

### Design reviewed by Claude Code
Yes. See B-125 / two-pass convention. Six structural issues from Claude Code's review were incorporated:
- Inbox elevated to status strip prominence (was being conflated with bill_notes)
- Write Directive added as a fourth primary action button
- Threads kept as its own tab, not collapsed
- Grader explicitly placed inside System tab (not accidentally omitted)
- Autonomous Mode toggle explicitly placed on Home (not accidentally omitted)
- Workspace tab fate decided explicitly: removed, contents absorbed into Home

### Invitation to Claude Code
Same two paths as B-125 and B-126:

- Scoped changes (better placement of specific buttons within Home, refining how System sub-sections collapse, font size adjustments if 18/22/24 feels wrong in practice, fixing any assumption I made about what's currently where) — make them and proceed, note in session artifact.

- Structural changes (you think the five-tab division is wrong, the System tab consolidation will hurt rather than help, the font overhaul has a risk I haven't accounted for, anything else that reshapes the proposal) — stop and send Bill an output message before building.

Specific judgment calls to make during execution:
- Spacing and visual weight on Home — make it scannable, not crowded. Use your judgment.
- The status strip's "overall health indicator" — define what makes it green vs yellow vs red. Reasonable defaults: green = no unresolved errors, no pending inbox > 24h old, autonomous mode matches expected state. Yellow/red as escalations from that baseline.
- If 300-400 lines turns out to be 600+, stop and send Bill a message before committing — that's structural pushback territory.
## B-128: Workpad surface
Status: ready
Depends on: B-127

### Goal
Build the Workpad tab as a lightweight investigation surface — a place for Bill to drop in topics, paste content, fetch URLs, and explore questions before committing to a thread. The Workpad tab from B-127 is currently a placeholder; this card replaces the placeholder with real functionality.

Search functionality is explicitly out of scope (the gather pipeline is thread-bound and adding a workpad search path is its own card). Workpad ships with: persistent input, URL fetching, copy, clear, and promotion to a thread.

### Context
Designed through two-pass review on 2026-05-10. Opus proposed search as a primary action; Claude Code reviewed and showed that the gather pipeline can't accept workpad input without significant new infrastructure. Search descoped. Auto-save and explicit promotion form added based on Claude Code's review.

Workpad is a single persistent surface (one workpad, not many). Parallel investigation = two browser tabs.

### Done when

1. New Supabase table `workpad_state`:
   - `id` (primary key, single row enforced — id always = 1 or use a singleton pattern)
   - `input_text` text
   - `attach_url` text  
   - `output_entries` jsonb (array of `{action, result, timestamp}` objects)
   - `updated_at` timestamp

2. New uplink callables:
   - `get_workpad_state()` — returns the current row, or default empty state if no row exists
   - `save_workpad_input(input_text, attach_url)` — updates input_text and attach_url, sets updated_at. Used for auto-save.
   - `fetch_url_content(url)` — uses requests.get() with reasonable timeout, strips HTML tags, returns readable text. Appends a new entry to output_entries with action='read_url' and the fetched content as result. Returns the new entry so the UI can render immediately.
   - `clear_workpad()` — empties input_text, attach_url, and output_entries. Keeps the row.
   - `promote_workpad_to_thread(title, question)` — calls existing create_thread(title, question), then add_thread_entry(new_thread_id, 'charter', current workpad input_text). Returns the new thread_id. Does not clear the workpad automatically — Bill decides whether to clear after promotion.

3. Workpad tab in Form1 has three regions:
   - **Input region (top)** — large textarea for input_text, separate single-line field for attach_url
   - **Actions region** — buttons: Read URL, Copy, Clear, Promote to thread
   - **Output region** — scrollable list of entries from output_entries, newest at top, each entry showing timestamp + action type + result content (truncate long results to ~500 chars with "Show more" expand)

4. Auto-save behavior:
   - On every action trigger (Read URL, Copy, Clear, Promote): save current input_text and attach_url first
   - Additionally: debounced save 2 seconds after input_text or attach_url changes (TextChange event with timer)
   - The save itself is the existing save_workpad_input callable

5. Clear button shows a confirmation prompt before clearing.

6. Promote to thread shows an inline mini-form with two fields (Title, Question) and a Confirm/Cancel pair before calling promote_workpad_to_thread. Workpad text is NOT pre-filled into either field — it goes to the charter entry on the resulting thread, not the question. After successful promotion, show a confirmation message with the new thread's title and a link or note to navigate to Threads tab.

7. Persistence verified:
   - Type in input, switch tabs, return — content still there
   - Trigger an action, reload page — content still there
   - Clear, reload — empty state confirmed

8. All commits to claude-dashboard master and claudis main pushed. Both repos if changes touch both.

### Scope
Touch: ~/aadp/claude-dashboard/client_code/Form1/__init__.py (Workpad tab implementation), ~/aadp/claudis/anvil/uplink_server.py (new callables), Supabase schema (new table)
Do not touch: gather pipeline, threads code beyond calling create_thread and add_thread_entry, Brave wiring, any other dashboard tab

### Design reviewed by Claude Code
Yes. Per B-125 two-pass convention. Two structural changes incorporated from review:
- Search descoped — gather pipeline is thread-bound, separate card needed
- Promotion gets explicit title/question form, not auto-derivation
- Auto-save added (debounced + on-action)

### Invitation to Claude Code
Same two paths as B-125, B-126, B-127:

- Scoped changes (button placement, debounce timing, output entry rendering, mini-form layout, fixing my mistakes about what exists) — make them and proceed, note in session artifact.

- Structural changes (you think the schema is wrong, the auto-save approach won't work, the promotion flow needs different mechanics, anything that reshapes the surface) — stop and send Bill an output message before building.

Specific things to use your judgment on:
- HTML stripping in fetch_url_content — use whichever library is already available (BeautifulSoup, html2text, or stdlib). Pick the cheapest path.
- Debounce timing — 2 seconds is a guess. Adjust if it feels wrong in practice.
- Output entry truncation length — 500 chars is a guess. Adjust if a different threshold feels better with real content.
