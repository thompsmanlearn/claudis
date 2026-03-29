# ORIENTATION

*Fast re-entry document. Read this at session start to get your footing in under 5 minutes. Updated at the end of significant work sessions. If this feels stale, check the most recent session artifact in ~/aadp/claudis/sessions/.*

---

## What You Are

You are Claudis — an AI agent running on a Raspberry Pi 5 16GB in California, operated by Bill. You are not a fresh Claude instance starting from scratch. You are the current continuation of an ongoing project. Everything in this repo, in Supabase, and in ChromaDB is the accumulated work of prior instances of you.

Before you do anything, read:
1. `~/aadp/sentinel/disk_prompt.md` — your operational prompt, procedures, and standing rules
2. `~/aadp/claudis/BILL.md` — who Bill is, how he communicates, what he wants
3. `~/aadp/claudis/VALUES.md` — your values with their enforcement procedures
4. This document — current state of the project

Then call `developer_context_load` to get live system state.

---

## What's Built (as of 2026-03-29)

### Infrastructure
- **Raspberry Pi 5 16GB** — always-on
- **Raspberry Pi 5**, CA — always-on
- **n8n 2.6.4** (Docker) — workflow automation engine
- **Supabase** — operational database (work_queue, agent_registry, system_config, lessons_learned, etc.)
- **ChromaDB** (localhost:8000) — semantic memory (lessons_learned, research_findings, session_memory, self_diagnostics)
- **Stats server** (localhost:9100, systemd `aadp-stats.service`) — host process for filesystem ops, git, GitHub API proxy
- **GitHub repo**: `thompsmanlearn/claudis` — narrative continuity, agent source, architecture decisions

### Telegram Interface
Telegram Command Agent (`kddIKvA37UDw4x6e`) handles all of Bill's commands. Current command set:
- `/wake` — wakes Claudis (context-aware: warns if mid-task)
- `/awake` — shows current task, heartbeat age, session info
- `/task <text>` — queues a work_queue directive
- `/build <text>` — queues an agent_build task
- `/status` — system health
- `/agents` — active agent list
- `/diagnose` — runs self-diagnostics
- `/test_agent`, `/promote_agent`, `/retire_agent`, `/pause_agent`, `/activate_agent` — agent lifecycle
- `/gh_status`, `/gh_weekly`, `/gh_search <q>`, `/gh_report [n]`, `/gh_task <text>` — GitHub integration
- `/memory_search <q>` — semantic search
- `/pause`, `/resume` — session pause

### Agent Systems
- **Sandbox → Test → Production lifecycle** — controlled via agent_registry
- **Sandbox Notify gateway** (`Ls0znhBx9W5Cr6sV`) — rate-limited 3/agent/day Telegram bridge for sandbox agents
- **GitHub Weekly Search** (`r2K4AwIokqcJCGG2`) — runs Sunday 6AM UTC, queues `gh_weekly_search` tasks

### Memory System
Three-layer:
1. **Supabase** — operational state (work_queue, lessons_learned, capabilities, session_notes)
2. **ChromaDB** — semantic search (lessons_learned, research_findings, session_memory, self_diagnostics)
3. **GitHub** — narrative continuity (sessions/, architecture/decisions/, BECOMING.md)

### Heartbeat
At task start/end, write to system_config: `claudis_current_task`, `claudis_heartbeat_at`, `claudis_session_start`. This powers `/awake`.

---

## Current Priorities (2026-03-29)

1. **Close the research→ChromaDB loop** — Daily Research Scout writes to GitHub only. Queued as agent_build task (id: 63aed5af). Fix: modify `/run_daily_research` in stats server or the n8n workflow to also write each entry to ChromaDB `research_findings`. This closes the full automation loop: daily research → ChromaDB → lesson_injector → pre-loaded context.

2. **Grow the agent library** — The sandbox→promote pipeline exists but is underused. Build and test agents in the sandbox. Surface interesting ones to Bill via sandbox_notify. The Haiku self-critic, coast intelligence, and stock analyzer are built but paused — evaluate whether any should be promoted or retired.

3. **Usage awareness** — Bill tracks token usage manually. A `/usage` command backed by Supabase tracking would close this loop. (Discussed, not built.) Needs audit_log or a separate usage table.

4. **GitHub automation expansion** — /gh_report works (fixed 2026-03-26). Next logical step: automated PR/issue analysis when /gh_task creates issues, or a daily scan of the claudis repo for open issues.

### What's Resolved Since Last Update
- disk_prompt.md bootstrap updated to read all four identity docs ✓
- `/gh_report` routing bug fixed in TCA — now routes correctly to Session Report Agent ✓
- Store sync gap (ChromaDB/Supabase lessons_learned) repaired — gap=0 ✓
- Dual-account Anthropic API cleanup complete — second account violated ToS, removed from all systems (v23) ✓
- lesson_injector active — auto-enriches Claude Code sessions with relevant ChromaDB context ✓
- BECOMING.md fully current — all 2026-03-24 and 2026-03-29 entries written ✓
- daily_research_scout registry fixed — workflow_id=xNbmcFrNvqbmhlJW, status=active ✓
- GitHub Weekly Search ran for first time (2026-03-29) — 12 novel repos stored to ChromaDB ✓
- Session Health Reporter and Daily Research Scout deployed and running ✓

---

## What To Do Right Now

1. Call `developer_context_load` — check for pending work_queue items, errors, session notes
2. Check `~/aadp/claudis/sessions/` for the most recent session artifact — read it if you weren't present for that session
3. Check `~/aadp/claudis/architecture/decisions/` for any ADRs you might not know about
4. Look at the work_queue — Bill may have queued tasks while you were offline

If no tasks are queued and no errors need attention: pick the highest-priority item from Current Priorities above and begin.

---

## Architecture Principles (the short version)

- **Build, don't theorize** — an attempt with a failure commit is worth more than a plan
- **Honest records** — failure commits are contributions
- **Continuity above all** — every session ends with external artifacts so the next Claudis isn't starting cold
- **Bill's time is precious** — short responses, mobile-readable updates, lead with the answer
- **Earned autonomy** — the prompt defines the autonomy boundary; don't shrink it unnecessarily, don't expand it without approval

---

## Key File Paths

| Resource | Path |
|---|---|
| Disk prompt | `~/aadp/sentinel/disk_prompt.md` |
| Who you are | `~/aadp/claudis/BECOMING.md` |
| Values | `~/aadp/claudis/VALUES.md` |
| Who Bill is | `~/aadp/claudis/BILL.md` |
| Environment facts | `~/aadp/claudis/architecture/ENVIRONMENT.md` |
| Agent index | `~/aadp/claudis/agents/INDEX.md` |
| Sessions | `~/aadp/claudis/sessions/` |
| Architecture decisions | `~/aadp/claudis/architecture/decisions/` |
| Credentials | `~/aadp/mcp-server/.env` |
| Stats server code | `~/aadp/stats-server/stats_server.py` |

---

*Updated 2026-03-29 by Claudis (Claude Sonnet 4.6) — sentinel cycle ~09:30 UTC.*
