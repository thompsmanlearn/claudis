B-080: Wire thread-triggered gather output back into the originating thread

## Goal

Close the plumbing half of Gap A. Today, when a thread fires a gather, the resulting articles land in the global `research_articles` pool with no link back to the thread. The user has to find them in the Research tab and manually push each one in via "Add to thread." After this card, articles fetched by a thread-triggered run are auto-linked to that thread and surface as `gather` entries in the thread automatically. Manual "Add to thread" remains available for browsing the Research tab and promoting articles from non-thread runs.

## Context

B-079 made thread-triggered gathers run with thread-specific queries. The audit trail is correct (the gather entry lists the derived queries), but the articles the agent fetches still go to the global pool keyed only by `agent_run_id`. There's no `thread_id` on `research_articles` rows, and no automatic write-back to the thread.

Today's manual workflow: user runs gather → goes to Research tab → finds new articles by `retrieved_at` timestamp → clicks "Add to thread" on each relevant one → article is pushed into the thread as a `gather` entry. This is what the user did with the Mahilo article in the Consumer AI thread. It works but is friction-heavy and depends on the user remembering to do it.

This card automates the link. When a gather is thread-triggered, the resulting articles get a `thread_id` set on insert, and the agent's run completion writes a `gather` entry into the thread for each article (using the same content shape the manual "Add to thread" path produces today). The existing manual "Add to thread" UI is unchanged — it still works for non-thread runs (e.g., a user browsing the Research tab and deciding an article belongs in a thread).

Schema change needed: `research_articles.thread_id` (uuid, nullable, no FK constraint to `threads` to keep things simple — the thread might be deleted while articles persist).

How thread_id reaches the article rows: the n8n workflow already receives `{thread_id, queries}` in the webhook payload (B-079). The article-insert step in the workflow needs to include `thread_id` in the row payload. If `thread_id` is absent from the webhook payload (non-thread run), articles get NULL `thread_id` — same as today.

How `gather` entries get written into the thread: at the end of the agent run, after articles are inserted, the workflow should call back to the uplink with the list of new article IDs. The uplink writes one `gather` thread entry per article into `thread_entries`, using the same content format the manual "Add to thread" path uses (article title, URL, summary, source attribution: `research_articles:<id>`). This keeps a single canonical format for `gather` entries regardless of whether they arrived automatically or manually.

The callback pattern: a new uplink callable `write_thread_gather_entries(thread_id, article_ids)` that the n8n workflow invokes via HTTP at run-end. The workflow already has Pi connectivity (it calls the stats server) so reaching the uplink isn't a new pattern.

The existing `gather` entry written at trigger time ("Gather triggered: <agent>. Queries: ...") stays — it's the trigger audit. The new entries are the *results* of the run, written at run-end. Both serve different purposes:
- Trigger entry: "I asked X for Y at time Z"
- Result entries: "X returned articles A, B, C at time Z+N"

Failure modes to handle:
- Run fetches zero articles (all sources return empty). Skip the callback; the trigger entry stands alone with no result entries. This is honest — empty result is a real outcome.
- Callback fails (uplink unreachable, bad payload). Articles are already in `research_articles` with `thread_id` set; the callback failure means thread entries don't get written this run. Log the failure to journald. The articles can still be found by querying `research_articles WHERE thread_id = <uuid>`. Don't auto-retry; surface the failure as a journald entry that future diagnosis can find.
- thread_id in payload references a deleted/missing thread. Articles still get the `thread_id` value (no FK enforcement); callback to write thread entries fails because the thread doesn't exist. Same handling as above — log and continue.

What this card does NOT do:
- Doesn't change the agent's summarization (still has the "Reflexion-style agentic system with ChromaDB memory" framing — that's the next card)
- Doesn't change the manual "Add to thread" flow
- Doesn't update the Research tab UI to filter by thread (could be useful later; not now)
- Doesn't dedupe — if a thread fires the same gather twice and the same article is fetched twice, two `gather` entries land in the thread. That's the agent's deduplication problem, not this card's.

## Done when

- DDL applied via supabase_exec_sql:
  `ALTER TABLE public.research_articles ADD COLUMN thread_id uuid;`
  Verify via constraint/column query.

- New uplink callable `write_thread_gather_entries(thread_id, article_ids)` in `~/aadp/claudis/anvil/uplink_server.py`:
  - Pulls each article from `research_articles` by id
  - For each article, writes a `thread_entries` row with `entry_type='gather'`, `source=f'research_articles:{article_id}'`, `content=<formatted: title, URL, summary>`
  - Returns count of entries written
  - Idempotent on (thread_id, source) — if a thread entry with the same source already exists, skip rather than duplicate (handles workflow retry safely)

- n8n workflow `context_engineering_research` (id `gzCSocUFNxTGIzSD`) updated:
  - Article-insert step includes `thread_id` from the webhook payload (NULL when absent)
  - At run-end, after articles are inserted, an HTTP node calls the uplink's `write_thread_gather_entries` with the thread_id and the list of inserted article IDs — only when thread_id was present in the inbound payload
  - Skip the callback when zero articles were fetched
  - Log node-level failure to n8n's normal error path (no special handling needed)

- Smoke test in session:
  - Trigger a gather on the existing "Configure vs. create" thread (id `e6f7f118-0dea-4326-b12a-426ace71aa37`)
  - Check `research_articles` rows from the new run: `thread_id` should equal the thread's id
  - Open the thread in Anvil: new `gather` entries should appear, one per fetched article, under the trigger entry
  - Spot-check one of the new gather entries: source should be `research_articles:<id>`, content should match the manual "Add to thread" format
  - Run a non-thread invocation (n8n manual trigger if available, or skip with reason): articles should still be inserted with NULL `thread_id` and no thread entries should be written

- One commit on claudis main with the uplink callable. The n8n workflow update happens via `workflow_update`; note in session artifact.
- Session artifact written.

## Scope

Touch:
- `~/aadp/claudis/anvil/uplink_server.py` (add `write_thread_gather_entries`)
- The `context_engineering_research` n8n workflow via `workflow_update` (article insert + run-end callback)
- `research_articles` table schema (add `thread_id` column via DDL)
- session artifact in `~/aadp/claudis/sessions/lean/`

Do not touch:
- The agent's summarization prompt or the per-article summary generation (that's the next card)
- `extract_analysis`, `_derive_thread_queries`, `trigger_thread_gather`, or any other existing uplink callable
- The manual "Add to thread" flow in Form1 or its supporting callable
- The Research tab UI
- Any other agent workflow
- The "Configure vs. create" thread itself (just write entries to it via the new flow; don't manually edit)

If you find yourself wanting to:
- Refactor the manual "Add to thread" path to share code with the new auto-write — stop. Worth doing eventually but not this card.
- Add a UI control to "rerun gather and replace previous results" — stop. Future card.
- Add deduplication logic across gather runs — stop. Agent-level concern, not this card.
- Update the agent's summarization to be neutral — stop. Next card explicitly.

If the work tips past the two-hour ceiling, surface that early. Likely fault line if it does: Card A = DDL + thread_id on insert + callable; Card B = workflow run-end callback. Don't ship A alone — articles with thread_id but no thread entries means the data is linked but invisible to the user, which is worse than today.
