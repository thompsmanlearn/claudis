# Session: 2026-04-16 — processed-content-agent

## Directive
B-022: Build a n8n workflow that checks the `processed/` directory in the claudis GitHub repo
for new or updated markdown files, parses them, and writes content to the `resources` table
with status `processed`. New Questions sections trigger a Telegram notification.

## What Changed

**stats_server.py** — added three new functions before `if __name__ == "__main__":`:
- `_parse_processed_md(content, filename)` — regex parser for the standard processed/ format (Title H1, Source, Thread, Date, Summary H2, Key Takeaways H2, New Questions H2)
- `_match_thread(thread_ref, threads)` — matches thread reference string to inquiry_threads.id via domain_name exact → partial → description substring → single-thread fallback
- `run_processed_content_agent()` — POST `/run_processed_content_agent` endpoint: lists GitHub processed/ directory, deduplicates by source_name and URL, fetches new files, parses, matches thread, upserts to resources

**n8n workflow** — `Processed Content Agent` (id: `PsJgcUyK4MwHnrfc`), active
- Dual-path pattern (Schedule + Webhook), 10 nodes
- Schedule: cron `0 */6 * * *` (every 6 hours)
- Webhook: POST `http://localhost:5678/webhook/processed-content-agent`
- Each path: HTTP Request → Check New Questions (Code) → Format Telegram (Code) → Send Telegram (HTTP)
- Check New Questions returns [] if new_questions empty, stopping chain silently

**agent_registry** — `processed_content_agent` registered and promoted to `active`
- workflow_id: `PsJgcUyK4MwHnrfc`, type: reader, schedule: every 6 hours

**resources table** — test row inserted (later cleaned up during testing):
- title: "Multi-Agent Coordination Patterns for Game AI"
- url: https://arxiv.org/abs/2024.01234
- thread_id: c831712e (game-development)
- status: processed, source_name: 2026-04-16-multi-agent-coordination.md

**processed/** — test file `2026-04-16-multi-agent-coordination.md` committed and pushed (commit 50bb54d)

## What Was Learned

- `agent_registry.agent_type` has a CHECK constraint — valid values: analyst, critic, developer, publisher, reader, router, scout. `agent_register` MCP tool gives opaque 400; use SQL directly.
- `resources` table has no unique constraint on url or source_name — deduplication must be handled in application logic before calling _sb_upsert. Without a unique constraint, Prefer: resolution=merge-duplicates is effectively INSERT.
- The dual-path n8n pattern (two parallel trigger→HTTP→Code→HTTP chains) is the established approach for schedule+webhook workflows. Do not attempt to merge paths in n8n — duplicate node pairs are simpler and more debuggable.
- GitHub `/contents/{path}` returns 404 (not empty array) when the directory has no files — handle with urllib.error.HTTPError check.
- Stats server restart is required after code changes; `sudo systemctl restart aadp-stats.service` + healthz check before testing.
- n8n restart (`docker restart n8n`) is required after activating a webhook-triggered workflow or the webhook 404s.

## Unfinished

- No unique constraint on resources.url — if a resource is manually inserted without source_name, URL-based dedup is the only fallback. Consider adding `CREATE UNIQUE INDEX resources_url_unique ON resources(url) WHERE url IS NOT NULL` in a future session.
- Test file `2026-04-16-multi-agent-coordination.md` remains in processed/ and in resources. It serves as the seed example of the expected markdown format.
- Only one inquiry thread (game-development) exists. Thread matching will use single-thread fallback for any file that doesn't match by domain_name — fine for now, but may need revisiting when more threads are added.
