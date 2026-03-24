# ADR: GitHub Integration Task Handlers

**Date:** 2026-03-24
**Status:** Implemented
**Prompt version:** v12

---

## Context

Phase 2 added nine Telegram `/gh_*` commands and a weekly GitHub search agent. Those components surface data and queue work — but Sentinel had no handlers for the resulting `work_queue` task types. Three task types needed handlers before they could compound into useful behavior.

## Decisions

### gh_weekly_search

**What it does:** Weekly GitHub scan (n8n `r2K4AwIokqcJCGG2`) runs Sunday 6AM UTC, searches `topic:mcp-server` and `topic:claude-tools OR topic:n8n-nodes`, queues up to 20 repos as a `gh_weekly_search` work_queue item.

**Handler approach:** Semantic dedup against ChromaDB `research_findings` (threshold 0.4). Novel repos stored to ChromaDB with full metadata. Top 5 novel by stars sent to Bill via Telegram.

**Why 0.4:** Tighter than general search thresholds (0.8) because repo names + short descriptions are sparse text — high similarity at 0.3 means genuinely same or related project.

**Why ChromaDB not Supabase:** `research_findings` is already the semantic store for discovered resources. Supabase has no equivalent table. This keeps all "things Claudis found" discoverable via `memory_search`.

### gh_report

**What it does:** Bill sends `/gh_report [n]` → TCA queues `gh_report` task → Sentinel reads last n session files from filesystem, passes to Haiku, sends synthesis to Telegram.

**Handler approach:** Direct filesystem read (not stats server) because Sentinel has MCP filesystem access and doesn't need the HTTP indirection. Stats server's `gh_report` endpoint is retained for direct Telegram calls via the monitoring path — the two paths are independent.

**Why Haiku:** Session artifacts are ~2-3KB each; 5 sessions ≈ 15KB. Well within Haiku's context. Synthesis is summarization, not reasoning — Haiku is the right cost point.

**750-char output target:** Telegram truncates long messages poorly. 750 chars ≈ one screenful on mobile without scrolling.

### gh_task

**What it does:** Bill sends `/gh_task <text>` → TCA queues `gh_task` task → Sentinel creates GitHub Issue + queues a `directive` work_queue item → notifies Bill with issue URL.

**Why two writes (Issue + directive):** GitHub Issue is the public record and Bill's reference. The `directive` work_queue item is what Sentinel actually executes. Creating both from one command keeps them linked (`issue_url` in directive's `input_data`) while not conflating the tracking system (GitHub) with the execution system (Supabase work_queue).

**Auth:** Same `GITHUB_TOKEN` (PAT, repo scope) used for push credentials. Issues API is within that scope — no separate credential needed.

**Title splitting:** First sentence heuristic (`.?!` or 80 chars). Favors short, action-oriented issue titles. If Bill writes a single short instruction, the whole thing becomes the title — no body needed.

## What was NOT done

- `from-telegram` label is not pre-created in the GitHub repo. Sentinel will create it on first use (GitHub API creates unknown labels automatically as plain text labels). No action needed.
- Rate limiting: GitHub Issues API allows 5000 requests/hour for authenticated PATs. Not a concern.
- `/gh_task` does not support multi-line input via Telegram. Long tasks should use `/task` (plain work_queue) or be submitted as `/build` requests. This is by design — keep `/gh_task` for things that warrant a public issue record.
