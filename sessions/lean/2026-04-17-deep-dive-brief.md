# Session: 2026-04-17 — deep-dive-brief

## Directive
Write ~/aadp/claudis/DEEP_DIVE_BRIEF.md — a comprehensive technical reference for the AADP system, built by inspecting actual source files and querying the live system. Covers all 12 sections: infrastructure, data flows, MCP server, stats_server, agent fleet, database schema, ChromaDB collections, lesson system, session mechanics, git conventions, config files, and known gaps.

## What Changed
- Created `~/aadp/claudis/DEEP_DIVE_BRIEF.md` — 776 lines, all 12 sections complete
- Committed and pushed to main (commit 0889686)

## What Was Learned
- stats_server.py is 3205 lines and entirely disk-only (not in git) — this is the single highest fragility in the system, confirmed by direct inspection
- The FastAPI stats sidecar defined in server.py (port 9100 endpoints) appears to be legacy/unreachable — the real stats server is the standalone systemd-managed process
- n8n docker-compose is at `~/n8n/docker-compose.yml` (not `~/aadp/n8n-mcp/`) — the n8n-mcp container is a separate tool (n8n MCP bridge for node documentation)
- ChromaDB collections: 8 collections confirmed live, ag_research_data (8 docs) appears to be legacy
- Supabase has 27+ tables; many (inquiry_threads, projects, refinements, resources, etc.) appear to be from an earlier era and are not actively written by current agents
- The send_telegram_alert() function in scheduler.sh only logs to file — does NOT send Telegram. Silent failure on sentinel errors.

## Lessons Applied
None pre-loaded were directly relevant to documentation-writing, but the ENVIRONMENT.md operational facts (ChromaDB version pin, Supabase Management API Cloudflare block, n8n activation via POST not PATCH) were correctly reflected in the document.

## Unfinished
Nothing — directive fully executed.
