# BACKLOG.md — AADP Lean Session Backlog

*Cards B-001 through B-021 archived to Google Docs on 2026-04-16*

## B-022: Build Processed Content Agent

**Status:** ready
**Depends on:** B-017

### Goal
Build an n8n workflow that checks the `processed/` directory in the claudis GitHub repo for new or updated markdown files, parses them, and writes the content to the `resources` table in Supabase with status `processed`.

### Context
Phase 3, Card 1 of the Capability Amplifier. Architecture spec has the design under "Processed Content Agent."

When Bill and Opus have a desktop session and process a scouted resource, the output is a markdown file dropped in `processed/` following this standard format with sections: Title (as H1), Source (URL), Thread (which inquiry thread), Date, Summary (H2), Key Takeaways (H2), and New Questions (H2).

The agent should:
- Use the GitHub API to list files in `processed/` and detect new/changed files (compare against what's already in `resources` with status `processed`, matching by URL or filename).
- Parse the markdown format to extract title, source URL, thread reference, summary, and key takeaways.
- Match the thread reference to an `inquiry_threads` row (by description or domain_name).
- Upsert to `resources`: status=processed, summary and key_takeaways populated.
- If a "New Questions" section exists, send them to Bill via Telegram for review (not auto-added to INQUIRIES.md).
- Schedule: runs every 6 hours + manual webhook trigger.

### Done when
- n8n workflow exists and is activated
- A test file placed in `processed/` is picked up, parsed, and written to `resources` with status=processed
- Thread matching works against the seed thread
- New Questions section triggers a Telegram notification
- Session artifact documents workflow structure, test file used, and resulting database row

### Scope
Touch: n8n (new workflow), Supabase `resources` table (inserts/updates), Telegram (send only for new questions), GitHub API (read only), sessions/lean/
Do not touch: BACKLOG.md, DIRECTIVES.md, INQUIRIES.md, processed/ directory contents, existing workflows, other Supabase tables

## B-023: Build Resource Inbox Web Page
Status: ready
Depends on: B-016
Goal
Build a single-page web app hosted on GitHub Pages that displays scouted resources as scrollable cards with star/dismiss buttons that write feedback directly to Supabase.
Context
This is the steering wheel. The current Telegram digest is a bad review interface. Bill needs a page he can open on his phone or desktop, scroll through new finds, star what's interesting, dismiss what isn't, and move on. That interaction IS the feedback loop — no Telegram replies, no GitHub files, no ceremony.
Technical approach: single HTML file with vanilla JS (or minimal React). Reads from Supabase REST API using the anon key with RLS policies for read access on resources, inquiry_threads. Writes to feedback_log on star/dismiss. No build step. Host on GitHub Pages from the claudis repo (gh-pages branch or docs/ folder).
Each resource card shows: title, source, one-line Haiku assessment, link to original, star button, dismiss button. Group or filter by inquiry thread. Newest first. Dismissed items disappear from the default view.
RLS policies needed: anon read on resources, inquiry_threads, refinements. Anon insert on feedback_log. No delete/update for anon.
Done when

Page is live on GitHub Pages and accessible from Bill's phone and desktop
Scouted resources display as cards with title, assessment, source link
Star button writes thumbs_up to feedback_log with correct resource_id and thread_id
Dismiss button writes dismiss to feedback_log and hides the card
Page loads current data from Supabase on each visit
Supabase RLS policies are in place (read resources/threads, insert feedback)
Session artifact documents the URL, RLS policies, and tested interactions

Scope
Touch: GitHub Pages setup, new HTML/JS file(s), Supabase RLS policies, sessions/lean/
Do not touch: existing n8n workflows, BACKLOG.md, DIRECTIVES.md, stats_server.py

Now let's fill it with content worth looking at. Here's the next card:

## B-024: Add YouTube Source to Resource Scout

Status: ready Depends on: B-018
Goal

Add YouTube as a second source to the Resource Scout agent, scanning for AI + Blender, AI + UE5, and AI + game dev videos using the YouTube Data API.
Context

Reddit produced 5 results on the first scan, mostly mediocre. YouTube is where the real game dev workflow content lives — tutorials, tool demos, workflow walkthroughs. The YouTube Data API returns metadata only (title, description, duration, channel, link) — no need to download or watch anything. The scout stores the link, Haiku scores relevance, and Bill reviews on the inbox page.

Use the YouTube Data API v3 search endpoint. Search queries should cover the active inquiry threads — start with queries like "AI Blender workflow," "AI generated 3D models UE5," "Meshy Blender Unreal," "AI game dev tools 2026." Deduplicate against existing resources by URL. Score with Haiku the same way Reddit posts are scored. Store as resource_type "video" with duration in metadata.

The API key should be stored in .env. If there's no YouTube API key yet, the card should document what's needed and Claude Code can use the existing Google API key if one exists, or flag it for Bill.
Done when

    YouTube search is integrated into the Resource Scout workflow (or a parallel workflow)
    At least 3 search queries run covering the seed interest
    Results are deduplicated against existing resources
    Haiku scores each result and items scoring 3+ are written to resources with resource_type=video
    First run produces results visible on the inbox page
    Session artifact documents queries used, results count, and any API key setup needed

Scope

Touch: Resource Scout n8n workflow (or new parallel workflow), Supabase resources table (inserts), .env (YouTube API key if needed), sessions/lean/ Do not touch: inbox page, BACKLOG.md, DIRECTIVES.md, other workflows, RLS policies

## B-025: Add stats_server.py to Version Control

**Status:** ready

### Goal
Add stats_server.py and supporting infrastructure to the claudis repo. The file is disk-only and is the highest single fragility in the system. Get the working production code into git exactly as it runs today.

### Context
stats_server.py (3,205 lines) contains inject_context_v3.1, run_research_synthesis, /trigger_lean, /lessons_applied, all ChromaDB proxy endpoints, and all GitHub operations. It has never been committed. If the Pi fails, it must be reconstructed from session artifacts. The Supabase RPC functions it calls are similarly undocumented.

The file already reads all credentials from ~/aadp/mcp-server/.env — no inline secrets found in audit (2026-04-17). The only hardcoded value is Bill's Telegram chat_id (8513796837), which is not a credential.

### Done when
- claudis/stats-server/stats_server.py matches the running production file exactly
- claudis/stats-server/aadp-stats.service contains the systemd unit
- claudis/stats-server/supabase_rpcs.sql contains DDL for increment_lessons_applied_by_id and increment_lessons_applied
- claudis/stats-server/.gitignore prevents .env from being committed
- sudo systemctl restart aadp-stats comes up clean
- curl localhost:9100/healthz returns {"status":"ok"}
- POST localhost:9100/inject_context_v3 with test payload returns a context_block
- All committed and pushed to main

### Scope
Touch: claudis/stats-server/ (new directory), sessions/lean/
Do not touch: stats_server.py itself (copy only, no edits), DIRECTIVES.md, BACKLOG.md, existing n8n workflows, .env
