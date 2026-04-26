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
