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
