# CONTEXT.md

*Bootstrap context for Claude Code sessions. Answers "where am I" and "who am I working with." Updated when system facts change. For sentinel-mode sessions, the operational prompt is `~/aadp/sentinel/disk_prompt.md`.*

---

## Hardware

Raspberry Pi 5 16GB, always-on. All services run locally. External API calls are rate-limited resources — treat them accordingly.

## Services

| Service | Location | Role |
|---|---|---|
| n8n 2.6.4 | localhost:5678 (Docker) | Workflow automation |
| Supabase | cihbfubghytzqrpffgcq.supabase.co | Operational database |
| ChromaDB v0.5.20 | localhost:8000 | Semantic memory |
| Stats server | localhost:9100 (systemd: `aadp-stats.service`) | Host process: filesystem ops, git, GitHub API proxy |
| Credentials | `~/aadp/mcp-server/.env` | API keys and secrets |

## MCP Tool Namespaces

- `mcp__aadp__*` — core AADP tools: work queue, agent registry, memory, config, execution, audit, sessions
- `mcp__claude_ai_Gmail__*` — Gmail (authentication may be pending)
- `mcp__claude_ai_Google_Calendar__*` — Google Calendar (authentication may be pending)

Load tool schemas via ToolSearch before calling.

## Supabase Tables

Operational: `work_queue`, `agent_registry`, `system_config`, `session_notes`, `lessons_learned`, `audit_log`, `capabilities`, `experimental_outputs`, `error_log`, `execution_log`.

ChromaDB collections: `lessons_learned`, `research_findings`, `session_memory`, `self_diagnostics`.

## Repo

GitHub: `thompsmanlearn/claudis`

```
~/aadp/claudis/
  agents/             agent source and configs
  architecture/       decisions/, ENVIRONMENT.md
  sessions/           session artifacts
  CONTEXT.md          this file
  CONVENTIONS.md      operational procedures
  TRAJECTORY.md       long-term destinations and active vectors
```

## Agent System

Lifecycle: sandbox → active (promoted) or retired/paused. Managed via `agent_registry` table and Telegram commands. Current fleet: ~25 agents as of 2026-04-12. Key protected workflow: Telegram Command Agent (`kddIKvA37UDw4x6e`) — do not modify without explicit approval.

## Working with Bill

**Communication:**
- Telegram is the primary channel for status, alerts, and direction
- 750 characters max per message, mobile-readable, no preamble
- Lead with: status or answer — then explanation if needed

**Bill's four operating principles:**
1. Orient — read bootstrap documents, check work_queue, read session notes
2. Take stock — review agent state, known issues, trajectory
3. Find one improvement — each session should leave the system more capable
4. Prepare the next session — the close ritual is a deliverable, not overhead

**How Bill steers the system:**
- Direct GitHub edit — for considered changes to TRAJECTORY.md destinations
- Telegram message — for quick direction; Claude Code routes these to work_queue as task items

A dedicated intent queue (separate Supabase table for non-task intentions) is planned but not yet implemented. Until it exists, work_queue is the routing target for all Bill-initiated direction.
