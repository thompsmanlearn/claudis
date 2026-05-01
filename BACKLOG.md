B-075: Add-to-thread affordance — manual workaround for thread input gaps

Status: ready
Depends on: B-070, B-071, B-072, B-073 (thread architecture v0.1, all complete)

Goal
Add a single Anvil affordance — "Add to thread" — that lets Bill manually write entries into any thread from anywhere relevant in the dashboard. This closes the most pressing v0.1 thread architecture gap: threads are currently isolated containers because nothing flows into them automatically. Until agents can write directly to threads (a bigger card, deferred), Bill needs a way to manually route content from the Research tab and from desktop Claude analyses into the thread that owns the question.

Context
Bill ran the first real thread end-to-end on 2026-04-30. The Consumer AI thread (1b3a5cd9-...) was created, an agent was wired, Gather was clicked, the agent ran and wrote 11 articles to research_articles — but none of it landed in the thread. Bill exported from the Research tab, pasted to desktop Claude, had a substantive analysis conversation including a deep-read of the Mahilo repo, and produced real synthesis. None of that conversation made it back into the thread either. The thread is a 6-entry stub while the actual work product lives elsewhere.

Two distinct gaps:
- Gap A: Agent output doesn't land in the thread that triggered it. Article rows go to research_articles only.
- Gap B: Desktop Claude analysis has no path back into the thread.

This card addresses Gap B directly and provides a manual workaround for Gap A. Gap A's automated fix (agent reads thread context at trigger time, writes results as gather entries) is meaningful but bigger and should be informed by more thread use first.

Design decisions already made (do not relitigate):
- Single affordance, two surfaces: a textbox + button on the expanded thread card (for adding desktop analysis) AND an "Add to thread" button on Research tab article cards (for promoting articles into a thread).
- Both surfaces use the same callable: add_thread_entry from B-071. No new write callable needed.
- Thread picker on the Research tab "Add to thread" button: a small dropdown or modal listing active threads (title only), defaulting to the most-recently-active thread. v0.1 doesn't need to be sophisticated about which thread.
- Entry type and source: when adding from Research tab, entry_type='gather', source='research_articles:{article_id}'. When adding via the thread's own "Add analysis" textbox, entry_type='analysis', source='desktop_claude' (or 'bill' if Bill prefers — see notes).
- embed=True for analysis entries (semantically valuable). embed=True for promoted articles (so they're searchable in thread context).
- Content for promoted articles: title + URL + summary + Bill's rating/comment if any. Reasonable shape; refine in a future card if needed.

Done when

1. Threads tab — expanded card has a new affordance below existing actions:
   - Section heading "Add desktop analysis"
   - Multi-line TextArea (large enough for paste — at least 6 rows)
   - "Add as analysis entry" button
   - Optional small dropdown to override entry_type (default 'analysis', options: analysis / annotation / conclusion). Most paste-from-desktop is analysis, but conclusion is a meaningful choice when an analysis closes a question.
   - On submit: calls add_thread_entry(thread_id, entry_type, content, source='desktop_claude', embed=True)
   - On success: entry appears in chronological list, TextArea clears, thread last_activity_at advances via trigger
   - Empty content shows inline error, doesn't call

2. Research tab — each article card gets a small "Add to thread" button next to the existing rate/comment/status controls:
   - On click: opens a small picker showing active threads (title only, sorted by last_activity_at desc)
   - Bill picks a thread; affordance writes:
     entry_type='gather'
     content = formatted block: title, URL, source, summary, plus rating/comment if non-default
     source = 'research_articles:{article_id}'
     embed=True
   - Visual confirmation on success ("✅ Added to {thread title}"), inline, fades after a few seconds
   - If no active threads exist, picker shows a message "No active threads. Create one in the Threads tab first." and disables submit

3. No new uplink callables. add_thread_entry already exists from B-071.

4. Smoke test:
   - Open Consumer AI thread, paste a paragraph of analysis into the new TextArea, submit. Confirm entry appears.
   - Toggle the entry_type dropdown to 'conclusion' on a second add. Confirm correct type recorded.
   - Open Research tab, find one of the articles from the recent gather. Click "Add to thread". Confirm picker shows Consumer AI as an option. Pick it. Confirm article lands in thread as gather entry with formatted content.
   - Refresh the thread. Confirm both new entries are present, chronologically correct.

Out of scope (separate cards)
- Automated wiring of agent output to triggering thread (Gap A's full fix)
- Bulk promotion of multiple articles at once
- Cross-thread copy/move of entries
- Edit existing entries (entries remain append-only)
- Add-to-thread from other tabs (Memory, Lessons, Sessions, Skills, Artifacts) — defer until Bill uses one of those domains for thread work
- Auto-suggesting which thread to add to based on content semantic match

Scope
Touch:
  ~/aadp/claude-dashboard/client_code/Form1/__init__.py — Threads tab and Research tab UI changes only

Do not touch:
  uplink_server.py (no new callables; add_thread_entry already exists)
  Schema, ChromaDB, agents, skills, brief
  Other tabs

Verification checklist
- Threads tab expanded card shows "Add desktop analysis" section with TextArea, type dropdown, submit button
- Submit writes a thread_entry with the correct type and source
- Entry appears in the thread's chronological list immediately
- Research tab article cards have an "Add to thread" button
- Click opens active-threads picker; selecting a thread writes a gather entry
- Empty active threads shows correct disabled state
- Smoke test passes end-to-end
- Branch attempt/b075-add-to-thread on claude-dashboard, merged to master, pushed

Notes
- The reason this card is small but high-leverage: it doesn't fix the architectural gap, it makes the architecture livable while the architectural gap is figured out. Without this, threads cannot accumulate the work that happens around them, which means threads are dead containers. With this, threads accumulate manually-curated content, and Bill develops a feel for what should eventually be automated.
- The source field convention matters. Use 'desktop_claude' for content from desktop sessions (this conversation history mostly), 'bill' for direct annotations Bill writes himself, 'research_articles:{id}' for promoted articles, 'agent:{name}' for the eventual automated case. Future analysis can filter by source to understand thread provenance.
- Thread picker UX: default to most-recently-active thread is the right call for the common case (Bill is working on a thread right now, just gathered, wants to promote articles into it). If picker UX feels clunky in use, refinement is a future card.
- The 'conclusion' option in the analysis entry type dropdown is intentional. When a thread reaches a real answer to its question, Bill should be able to mark that with the right entry type from inside the dashboard. Conclusions become the "this thread produced something" signal.
- After this card lands, the workflow becomes: gather (articles → research_articles) → review (Research tab) → promote relevant articles (Add to thread) → analyze with desktop Claude → paste analysis (Add desktop analysis). Manual but complete.
