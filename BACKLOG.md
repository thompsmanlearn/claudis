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
