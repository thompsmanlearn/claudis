# Session: 2026-04-16 — resource-scout-reddit

## Directive
B-018: Build Resource Scout Agent — Reddit. n8n workflow that scans r/blender, r/unrealengine, and r/gamedev, uses Haiku to assess relevance against active inquiry threads, and writes qualifying items (score 3+) to the resources table.

## What Changed

### n8n
- Workflow **Resource Scout — Reddit** (ID: `exEfZ76ZeJLrYP5V`) created and activated
- Runs every 12 hours (cron: `0 6,18 * * *`) + manual via webhook GET `/resource-scout`
- Architecture: 14 nodes — dual triggers → Get Threads → Get Refinements → fetch 3 Reddit feeds → Get Existing URLs → Build Post Queue → Call Haiku (stats server) → Parse and Filter → Filter Qualified → Write Resource → Summarize for Audit → Write Audit Log

### stats_server.py
- New endpoint `POST /score_reddit_resources` added (line ~2729)
- Accepts `{ posts: [{i, url, title, source_name, selftext, thread_id}], interests: "...", thread_id: "..." }`
- Calls Haiku for batch scoring, returns `{ scores: [{i, score, assessment}], total: N }`
- API key read from .env — never stored in workflow JSON

### Supabase
- 5 resources written in first successful run (exec 2351), 2 with score ≥ 4:
  - "Importing AI Generated Models into UE5 My Actual Workflow..." — score 5
  - "Blender Geometry Nodes to Unreal" — score 5

### agent_registry
- `resource_scout_reddit` registered: status=active, workflow_id=exEfZ76ZeJLrYP5V

## What Was Learned

**n8n HTTP Request node gzip buffer bug (n8n 2.6.4):** When calling external APIs that return gzip-encoded responses, the HTTP Request node stores a zlib stream object in the execution data instead of the decoded text — even with `responseFormat: text` set. The fix: delegate API calls that go outside the Pi network to the stats server. Python's `urllib` handles decompression correctly.

**Stats server HTTP call pattern (n8n → host.docker.internal):** Use `specifyBody: "json"` + `jsonBody` expression with no `responseFormat` option in the HTTP Request node's options. The Research Synthesis Agent pattern (`bodyContentType: "json"`, no responseFormat) is the reference. Using `contentType: "raw"` + `rawContentType` + `body` causes n8n to return the raw IncomingMessage stream object instead of the parsed response body.

**Rate limit on per-post Haiku calls:** Calling Haiku once per post across 75 posts hits the 50 req/min org rate limit immediately. Always batch multi-item scoring into a single API call.

**n8n Code node sandbox limitations (n8n 2.6.4):** Neither `fetch` nor `$helpers` is available. HTTP calls from Code nodes require `require('https')` (potentially blocked too) or delegation to the stats server.

## Unfinished

- Audit log write (Summarize for Audit → Write Audit Log) not verified — write_resource chain completes but need to confirm audit entries exist
- Deduplication across runs verified by code review, not by a second run observation
- stats_server.py change is disk-only (not in git) — consistent with current practice but noted as brittle in TRAJECTORY.md

## Next Expected Card
B-019 (not yet written): likely a processing step that reads scouted resources and enriches them (summary, key_takeaways) or routes them to Bill.
