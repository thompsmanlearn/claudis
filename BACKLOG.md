B-054: Schema for context engineering research micro-version

Goal: Create the two Supabase tables needed to support an on-demand research agent and a feedback loop. No agent, no UI yet — just the substrate they'll write to.

Rationale: This is Card 1 of a 6-card micro-version proving an end-to-end round-trip: human triggers research → agent writes articles → human rates/comments → human gives directional feedback → next session acts on feedback → human exports bundle for desktop analysis. Schema first lets the remaining cards build cleanly without back-edits.

Scope:

1. Create `research_articles` table with columns: `id` (uuid, primary key, default gen_random_uuid()), `agent_run_id` (uuid, groups articles from the same agent invocation, not a foreign key for now — just a tag), `title` (text, not null), `url` (text, not null), `source` (text, domain or publication name), `summary` (text, 1-3 paragraphs written by the agent), `query_used` (text, the search query that surfaced this article), `retrieved_at` (timestamptz, default now()), `rating` (smallint, default 0, where -1 is thumbs down, 0 is unrated, 1 is thumbs up), `comment` (text, Bill's free-text comment on the article), `status` (text, default 'new', values: new/reviewed/archived), `provenance` (text, default 'context_engineering_research_agent', free text for now, standardize later if needed). Index on `agent_run_id` for group queries and `status` for filtering active/archived.

2. Create `agent_feedback` table — generic enough to be reused by any agent or any Anvil view, not just this one. Columns: `id` (uuid, primary key, default gen_random_uuid()), `target_type` (text, not null, e.g. 'agent', 'anvil_view', 'lesson', 'card'), `target_id` (text, not null, name or ID of the target), `content` (text, not null, the feedback itself), `created_at` (timestamptz, default now()), `processed` (boolean, default false, flipped to true when a session has acted on it), `processed_at` (timestamptz, nullable), `processed_in_session` (text, nullable, session artifact filename or commit SHA that consumed it). Index on (target_type, target_id, processed) — the most common read pattern is "give me unprocessed feedback for target X."

3. Verify: both tables created via supabase_exec_sql; insert one test row into each and read it back; delete the test rows.

Out of scope: the agent itself (Card 2), Anvil UI to display these tables (Card 3), triggering or invocation (Card 3), bundle export (Card 5), boot-time feedback pickup (Card 6), foreign key relationships between the tables (intentionally loose for v1).

Verification checklist: research_articles table exists with all columns and defaults; agent_feedback table exists with all columns and defaults; indexes created; test inserts succeed and reads return expected shape; test rows cleaned up; schema documented in a short note at top of ~/aadp/claudis/PROJECT_STATE.md or a new section so future cards can reference it; branch attempt/b054-research-schema, merged to main, pushed.

Notes: This card is intentionally tiny. The schema is the load-bearing decision; getting it right (and keeping it simple) makes Cards 2-6 easier. Don't add columns we might need. Add them when a card needs them. The provenance field is the start of a pattern that will matter more later — every row in the system should ideally know where it came from. Keep it free-text for now; standardize later.

B-055: Context engineering research agent (n8n workflow)

Goal: Build an n8n workflow that, when triggered by webhook, performs a hardcoded set of web searches on context engineering for agentic systems, summarizes the top results, and writes them to the research_articles table as a single agent run.

Rationale: Card 2 of 6 in the research micro-version. Card 1 created the schema. This card creates the agent that fills it. No UI yet — Card 3 wires the button and the view. Verification for this card is via direct webhook call and Supabase row inspection.

Scope:

1. Register the agent in agent_registry. Name: context_engineering_research. Display name: "Context Engineering Research". Description: "Searches the web for articles on context engineering, agent memory, and related patterns; summarizes results into research_articles." Status: active. Schedule: null (on-demand only). Protected: false. workflow_id will be set after the n8n workflow is created. webhook_url will be populated once the n8n webhook node URL is known, following the same pattern used for the three on-demand agents in B-049.

2. Create the n8n workflow. Workflow name: context_engineering_research. Trigger: Webhook node, POST, path: context-engineering-research. The workflow accepts an optional JSON body { "query_override": "..." } but ignores it for v1 — query is hardcoded. After this card lands, populate agent_registry.webhook_url and agent_registry.workflow_id.

3. Workflow logic:
   - Generate a single agent_run_id (uuid) at the top of the run; all articles from this run share it.
   - Execute a fixed set of web searches. For v1, hardcode these queries: "context engineering for LLM agents", "agent memory hot warm cold tier", "Reflexion ExpeL agent self-improvement", "agent bootstrapping context loading pattern", "ChromaDB retrieval agent lessons learned". Use whatever search mechanism is already wired into n8n (Brave, Serper, SerpAPI — whichever has credentials in .env). If no search node is configured, document that and stop here for Bill to wire one.
   - For each query, take the top 2 results. Total target: ~10 articles per run.
   - For each result: fetch the page (n8n HTTP Request node), extract title, URL, source domain. Generate a 1-3 paragraph summary using a Claude API call (Haiku is fine for v1 — the existing inject_context infrastructure already calls Haiku, reuse the same auth pattern). Summary should be: what the article is about, what pattern or claim it makes, and why it might be relevant to a Reflexion-style agentic system with ChromaDB memory.
   - Insert each result as a row in research_articles with: agent_run_id (the uuid), title, url, source, summary, query_used (the query that surfaced this result), retrieved_at (now), and defaults for the rest (rating 0, status 'new', provenance 'context_engineering_research_agent').

4. Error handling: if a fetch fails for a single result, skip it and continue. Log to error_logs with the URL and error. Don't abort the whole run unless the search step itself fails.

5. Deduplication: before inserting, check whether the same URL already exists in research_articles. If so, skip — don't create duplicate rows across runs. (Same URL can legitimately surface from multiple queries in one run; dedup against everything in the table, not just this run.)

6. Verify:
   - Trigger the webhook manually (curl or via mcp__aadp tool).
   - Confirm new agent_run_id, ~10 rows in research_articles with sensible summaries.
   - Confirm rerunning produces a new agent_run_id but no duplicate URLs.
   - Confirm at least one error path: trigger with a known-bad URL injected somewhere, verify it lands in error_logs and the run continues.

Out of scope: the Anvil view, the Run button, rating/commenting UI, feedback ingestion, scheduling (this is on-demand only), query parameterization (v1 uses hardcoded queries; query_override input is accepted but ignored).

Verification checklist:
- agent_registry row exists for context_engineering_research with status='active', workflow_id set, webhook_url set
- n8n workflow imported, active, webhook reachable
- Manual webhook call returns success and produces ~10 research_articles rows with the same agent_run_id
- Summaries are non-empty and non-trivial (not error messages, not boilerplate)
- query_used populated correctly per row (matches one of the 5 hardcoded queries)
- Second invocation produces new agent_run_id and skips duplicate URLs
- One forced error appears in error_logs without crashing the run
- Branch attempt/b055-research-agent, merged to main, pushed

Notes: This is the largest card in the micro-version. If the search node isn't wired, stop early and report — it's a precondition Bill needs to provide before the agent can work. Haiku for summarization keeps token cost low; if the existing Haiku integration uses a different model, use whatever's already wired. The dedup check is intentional — without it, repeated runs flood the table. The summary prompt should err toward concise (~150 words) rather than comprehensive; this is meant to be skim-able, not a replacement for reading the article.

B-056: Anvil Research tab with on-demand button and feedback loops

Goal: Add a Research tab to the Anvil dashboard that displays articles from research_articles, lets Bill rate and comment on each, exposes two feedback boxes (one for the agent, one for the UI), and includes a "Run research" button that invokes the context_engineering_research agent on demand.

Rationale: Card 3 of 6 in the research micro-version. Cards 1 and 2 created the schema and the agent. This card creates the surface where Bill actually uses them. After this card, Bill can press a button, see articles appear, rate them, leave feedback for the agent and the UI, and have all of that persist in Supabase. Cards 4-6 (embed, export, boot integration) build on this view.

Scope:

1. New Anvil tab "Research" — added to the existing tab structure in ~/aadp/claude-dashboard/client_code/Form1/__init__.py, following the same programmatic-build pattern as the existing tabs. Place between Memory and Skills, or wherever fits the existing nav order best.

2. Tab layout, top to bottom:
   - Header row: title "Research" on the left, "▶ Run research" button on the right.
   - Status line below the button showing last run timestamp and article count from the most recent run (e.g., "Last run: 2026-04-25 14:32 — 10 articles"). Refreshes when the tab loads and after a Run completes.
   - Articles section: cards grouped by agent_run_id, newest run first. Each run is collapsible; the newest run is expanded by default, older runs collapsed.
   - Feedback section at the bottom with two TextBoxes side by side: "Feedback for the agent" and "Feedback for this UI", each with a Submit button below it.

3. Article cards. Each article shows: title (link to URL, opens in new tab), source domain, query_used as a small tag, summary, then an action row with: 👍 button, 👎 button, comment TextBox, status dropdown (new / reviewed / archived). The 👍/👎 buttons set rating to 1 or -1; clicking the same button again resets to 0. The comment TextBox saves on blur (or via a small Save button — pick whichever matches the existing pattern in the Artifacts tab). The status dropdown writes through immediately on change.

4. "Run research" button. Calls invoke_agent('context_engineering_research') via the existing callable. Shows "Triggering…" state while in flight, then "✅ Triggered — articles arriving" on success or "❌ {error}" on failure. After a successful trigger, poll research_articles every 5 seconds for up to 60 seconds; when new rows appear, reload the article section. If 60 seconds elapses with no new rows, show "No new articles yet — refresh manually" and stop polling.

5. Feedback submission. Each Submit button writes a row to agent_feedback. For "Feedback for the agent": target_type='agent', target_id='context_engineering_research', content=<TextBox value>. For "Feedback for this UI": target_type='anvil_view', target_id='research_tab', content=<TextBox value>. After submit: clear the TextBox, show "✅ Saved" feedback inline for ~3 seconds, fade away.

6. New uplink callables in ~/aadp/claudis/anvil/uplink_server.py:
   - get_research_articles(limit=50) — returns articles ordered by retrieved_at desc, joined or grouped client-side by agent_run_id. Include all columns the UI needs.
   - rate_research_article(article_id, rating) — updates rating, returns the updated row.
   - comment_research_article(article_id, comment) — updates comment.
   - set_research_article_status(article_id, status) — updates status. Validate status is one of new/reviewed/archived.
   - submit_agent_feedback_v2(target_type, target_id, content) — writes to agent_feedback. Named v2 to avoid colliding with the existing submit_agent_feedback callable for agent thumbs up/down.
   - get_research_run_summary() — returns the most recent agent_run_id and its article count and timestamp, for the status line.

7. Restart the uplink (sudo systemctl restart aadp-anvil) after adding callables. Confirm reconnection in the journal log.

8. Verify:
   - Tab loads, shows existing articles from the B-055 test run.
   - Rating, commenting, status changes persist (refresh the page; values stick).
   - "Run research" button triggers the agent; new articles appear within 60 seconds.
   - Both feedback boxes write rows to agent_feedback with correct target_type / target_id.
   - Feedback rows are visible via supabase_exec_sql or Memory tab.

Out of scope: GitHub site embedding (Card 4), markdown bundle export (Card 5), boot-time feedback pickup (Card 6), filtering or search within the article list (later if needed), bulk operations on articles (later if needed), parameterizing the search queries (Card 5 territory at earliest).

Verification checklist:
- Research tab visible and loads cleanly
- Article cards render with all fields
- Rating buttons toggle correctly (cycle through -1/0/1)
- Comment box saves and persists
- Status dropdown writes through immediately
- Run button triggers the agent and surfaces new articles
- Both feedback boxes write to agent_feedback with correct target_type/target_id
- All 6 new callables registered, uplink restarted cleanly
- Branch attempt/b056-research-tab on both claudis and claude-dashboard, merged to master/main, pushed

Notes: This card is medium-large because it touches both the uplink server and the dashboard form. Follow the patterns already established by the Artifacts tab (which has very similar mechanics: cards with ratings and comments) and the Fleet Run button (per-agent invocation). Don't reinvent UI primitives — reuse the existing FlowPanel/Button/TextBox patterns. The 60-second polling timeout is a soft cap; if the agent typically takes longer, raise it. The submit_agent_feedback_v2 naming is awkward but avoids breaking the existing thumbs-up callable; we can rename later if the existing one is retired.

B-057: Research bundle export

Goal: Add a get_research_bundle callable to the uplink server that returns a markdown-formatted string ready to paste into a desktop Claude session, and wire an Export button in the Anvil Research tab that surfaces the result so Bill can copy it.

Rationale: Card 4 of the research micro-version (Card 5 — GitHub embed — was completed as part of EmbedControl retirement on 2026-04-26). The bundle closes the loop between the Research tab and a desktop analysis session: Bill rates articles in Anvil, presses Export, pastes the markdown into Claude, and the session has full context — what was fetched, what Bill thought of it, and what directional feedback is waiting to be acted on.

Scope:

1. New callable get_research_bundle(agent_run_id=None) in ~/aadp/claudis/anvil/uplink_server.py. If agent_run_id is None, use the most recent run. Returns a single markdown string with:

   - Frontmatter block: run_id, run_timestamp (retrieved_at of the first article in the run), article_count, query_set (the five QUERIES from run_context_research, read from the DB via query_used values or hardcoded — hardcoded is fine for now).
   - One ## section per article: title, source, URL, query_used, summary. Append "Rating: 👍" or "Rating: 👎" only if rating != 0. Append "Comment: <text>" only if comment is non-empty.
   - A final ## Pending Feedback section listing unprocessed agent_feedback rows where target_type IN ('agent', 'anvil_view') AND processed = false OR processed IS NULL. Each row: "- [target_type: target_id] content". If no pending feedback, omit the section.

2. Export button in the Research tab header row (right side, next to Run research button). Label: "⬇ Export". On click:
   - Call get_research_bundle() with no_loading_indicator.
   - Try anvil.js clipboard write (document.execCommand or navigator.clipboard.writeText). If it fails or raises, fall back to showing the markdown in a TextArea in a new ColumnPanel below the header. Bill can copy from there manually.
   - Show "✅ Copied" or "📋 Ready to copy below" depending on which path ran.

3. Restart the uplink after adding the callable. Confirm reconnection.

4. Verify:
   - Bundle string is valid markdown and includes all expected sections.
   - Export button copies to clipboard or surfaces the TextArea fallback.
   - Pending feedback rows appear in the bundle if any exist with processed=false.

Verification checklist:
- get_research_bundle returns well-formed markdown for the most recent run
- Frontmatter includes run_id, timestamp, article count, query set
- Articles with rating 0 omit the rating line; rated articles include it
- Pending feedback section present when unprocessed rows exist, absent otherwise
- Export button works (clipboard or TextArea fallback)
- Uplink restarted cleanly after callable added

Notes: Keep the callable pure — it only reads, never writes. The clipboard API in Anvil's browser context is inconsistent; the TextArea fallback is the primary path to test. Don't truncate summaries in the bundle — desktop sessions can handle full text and truncation loses context.

B-058: Boot-time feedback pickup

Goal: Update LEAN_BOOT.md and the bootstrap skill to surface unprocessed agent_feedback rows at session start, so feedback Bill left in Anvil is visible before the session executes its directive. Acting on a feedback item marks it processed.

Rationale: Card 6 (final card) of the research micro-version, and the mechanism that closes the feedback loop for all future agent work — not just research. Bill leaves feedback in Anvil (for an agent, for a UI view, for anything with a target_type), and the next session reads it at boot, acts on what's relevant, and marks it consumed. Without this step, feedback rows accumulate silently and never influence behavior.

Scope:

1. Add a new step between the current step 9 (live-state ping) and step 10 (lesson retrieval) in LEAN_BOOT.md. Call it step 9.5 or renumber — renumber is cleaner. New step:

   Query agent_feedback for unprocessed rows:
   ```sql
   SELECT id, target_type, target_id, content, created_at
   FROM agent_feedback
   WHERE processed = false OR processed IS NULL
   ORDER BY created_at ASC;
   ```

   - If rows exist: include them in the boot summary as a labeled "## Pending Feedback" section. List each row as "- [target_type: target_id, created_at] content".
   - After reading the directive (step 5), if any pending feedback has target_type = 'agent' or target_type = 'anvil_view', surface it again as "Feedback to consider during execution:" before proceeding. Do not auto-act — present it as input Bill or the directive may address.
   - When a piece of feedback is acted on during the session, mark it: UPDATE agent_feedback SET processed = true, processed_at = now(), processed_in_session = '<session artifact filename>' WHERE id = '<id>'. Use supabase_exec_sql. Do this immediately after acting, not as a batch at close.
   - If no pending feedback exists, skip the section silently (no "no feedback" placeholder).

2. Apply the same step to the bootstrap skill (~/aadp/mcp-server/.claude/skills/bootstrap.md). Bootstrap is Bill's entry path; LEAN_BOOT is the directive-driven path. Both must check feedback so neither misses it.

3. The processed_in_session field should match the session artifact filename (e.g., "2026-04-26-b058-boot-feedback.md") or, if the artifact isn't named yet at boot, use the card ID (e.g., "B-058").

4. Verify:
   - Boot summary includes Pending Feedback section when unprocessed rows exist.
   - Rows created by the Research tab feedback boxes appear and are marked processed after acting on them.
   - processed_at and processed_in_session are set correctly on the updated rows.
   - No feedback section appears in boot summary when all rows are processed.

Verification checklist:
- LEAN_BOOT.md updated with new feedback step, correctly numbered
- Bootstrap skill updated with the same step
- Boot summary shows pending feedback rows on next lean session
- Acting on feedback sets processed=true, processed_at, processed_in_session
- Rows with processed=true do not reappear in subsequent boots
- Both entry paths (LEAN_BOOT + bootstrap) catch feedback

Notes: This step must be read-only at the point it runs (boot). It should never write processed=true during boot itself — only during execution when feedback is actually acted on. The distinction matters: surfacing ≠ acting. A session that sees feedback but whose directive is unrelated should leave feedback rows unprocessed for the next session.
