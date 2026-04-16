# Session: 2026-04-16 — youtube-scout-build

## Directive
B-024: Add YouTube as a second source to the Resource Scout agent, scanning for AI + Blender, AI + UE5, and AI + game dev videos using the YouTube Data API v3.

## What Changed
- **stats_server.py**: Added `/scout_youtube` POST endpoint. Reads `YOUTUBE_API_KEY` from .env; if absent, returns `{ results: [], skipped: "no_key" }` cleanly. Runs 4 search queries against YouTube Data API v3 (`AI Blender workflow 2026`, `AI generated 3D models UE5`, `Meshy Blender Unreal`, `AI game dev tools 2026`). Deduplicates against `existing_urls` list. Scores with Haiku (same 1–5 prompt as `/score_reddit_resources`). Returns only results scoring ≥ 3.
- **.env**: Added `YOUTUBE_API_KEY=` placeholder with setup instructions (Google Cloud Console, YouTube Data API v3, ~100 units/query, 10k free/day).
- **n8n workflow "Resource Scout — YouTube"** (`fekHI1lKjCmDkTYb`): Active. Schedule every 6h. Webhook `/webhook/resource-scout-youtube`. Delegates all YouTube logic to stats server. Writes resources with `resource_type='video'`, `source_name='youtube'`, `status='scouted'`. Execution 2373 confirmed success on no_key path.

## What Was Learned
- Delegating source-specific API calls to stats_server.py keeps keys out of workflow JSON and makes the scoring logic reusable. The YouTube endpoint reuses the exact Haiku scoring prompt structure from Reddit — no new prompt needed.
- The no_key sentinel path (`skipped: "no_key"`) allows the workflow to stay active and complete silently until the key is added. No manual re-activation needed after Bill sets the key.
- Duration metadata skipped: requires a separate `videos.list` API call per batch and the resources table has no metadata column. Not worth the quota cost until content volume justifies it.

## Unfinished
- **YOUTUBE_API_KEY not set — first real run blocked on this.** Steps to unblock:
  1. Google Cloud Console → APIs & Services → Credentials → Create API Key
  2. Restrict to YouTube Data API v3
  3. Set `YOUTUBE_API_KEY=<key>` in `~/aadp/mcp-server/.env`
  4. Trigger: `curl http://localhost:5678/webhook/resource-scout-youtube`
  5. Check `resources` table for rows with `resource_type='video'`
