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
