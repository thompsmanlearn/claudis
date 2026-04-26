# 2026-04-26 B-056: Research Tab + Run Button Fixes

**Session type:** Lean  
**Card:** B-056 — Anvil Research tab with on-demand button and feedback loops  
**Date:** 2026-04-26

---

## What Was Asked

Build the Research tab in the Anvil dashboard (Card 3 of the research micro-version): article cards from research_articles grouped by run, rating/comment/status controls, Run research button with polling, two feedback boxes writing to agent_feedback, six new uplink callables. Also: update the GitHub Pages site to embed the full dashboard instead of EmbedControl.

---

## What Changed

- **Research tab in Anvil** (claude-dashboard cdce549): New tab between Memory and Skills. Article cards show title (Link), source, query tag, summary, 👍/👎 toggles, comment box (saves on blur), status dropdown (writes on change). Articles grouped by agent_run_id — newest run expanded, older collapsed. Feedback section at bottom: two TextArea boxes writing to agent_feedback via submit_agent_feedback_v2.

- **6 new uplink callables** (claudis e268c6e): get_research_articles, rate_research_article, comment_research_article, set_research_article_status, submit_agent_feedback_v2, get_research_run_summary.

- **invoke_agent fire-and-forget** (claudis 7a17453): The 15-second timeout caused "HTTPConnectionPool read timed out" because the n8n webhook holds the connection until the workflow completes (~18s). Fixed by spawning a daemon thread for the POST and returning immediately. The UI's 60-second polling picks up new articles independently.

- **run_context_research batch dedup + deeper fetch** (claudis 6485e68): The original code fetched only 1 result per source per query, so after one run the dedup well was exhausted. Fixed to fetch 5 per source per query (~50 candidates), batch-dedup against all existing URLs in one Supabase query, insert up to 10 fresh articles per run. First fixed run: inserted 4, skipped 2 dupes, capped 0.

- **GitHub Pages iframe** (thompsmanlearn.github.io 2bd9f31): Replaced `#EmbedControl` hash with bare URL — full dashboard now loads in the embed. Height raised from 480px to 900px. EmbedControl form still exists in claude-dashboard, accessible at `#EmbedControl`, nothing deleted.

- **B-057 and B-058 queued** (claudis f51a81b): Bundle export (Card 4) and boot-time feedback pickup (Card 6). Directive set to B-057. Card 5 (GitHub embed) marked complete.

---

## Key Decisions

- **Fire-and-forget for invoke_agent:** Considered raising timeout to 120s; chose background thread instead. Background thread means the callable returns in ~0.1s regardless of workflow duration, and doesn't tie up an Anvil RPC slot. The 120s fallback timeout on the thread handles runaway workflows without silent hanging.

- **Batch dedup over per-URL queries:** Original code made one Supabase GET per candidate URL. With 50 candidates that's 50 network round-trips. Replaced with one GET for all existing URLs (limit 2000) — O(1) Supabase calls regardless of candidate count.

- **10-article cap per run:** Per Bill's spec. Keeps human review tractable. `capped` field in response signals when the well has more than 10 unseen articles.

- **Link without target='_blank':** Anvil's client-side Link component doesn't accept target kwarg. Removed it; links open in same tab.

- **EmbedControl not deleted:** Noted as retirable — form + hash router entry can be removed in one PR. Callables it uses (ping, get_lean_status, get_autonomous_mode, set_autonomous_mode) all still used by Form1. Reported to Bill for decision.

---

## Capability Delta

**Before:** Dashboard had no research surface. research_articles existed but no UI to view, rate, or trigger. GitHub site showed minimal EmbedControl panel.

**After:** Bill can open the Research tab, see articles grouped by run, rate/comment each, trigger a new run from the dashboard (returns in ~1s, articles arrive within 60s), leave directional feedback for the agent or the UI. The GitHub Pages site shows the full dashboard. run_context_research no longer exhausts after one run.

---

## Lessons Written

2 (see step 7):
- lesson_anvil_link_no_target (Anvil Link component doesn't accept target kwarg)
- lesson_n8n_webhook_fire_and_forget (long-running n8n webhooks need fire-and-forget)

---

## Branches and Commits

- claudis main: e268c6e, 7a17453, 6485e68, f51a81b, f659e35
- claude-dashboard master: 40bf70d, cdce549
- thompsmanlearn.github.io main: 2bd9f31
- Attempt branches attempt/b056-research-tab deleted from both repos after merge

---

## Usage

Session ~55%, weekly ~65%
