# DEEP_DIVE_BRIEF.md — AADP Comprehensive Reference


*Revised 2026-04-26. This document is the primary onboarding reference for fresh desktop and Claude Code sessions. It bridges memory between sessions and gets a new instance to productive collaboration as fast as possible.*

*Each section has a Last Updated date. Sections with stale dates should be verified before relying on them. Session close should include: "Does the brief need updating? If so, which sections?"*

---

## 1. System Identity
*Last updated: 2026-04-18*

AADP is a personal intelligence infrastructure running on a Raspberry Pi 5. The system is named **Claudis** (Claude Code Intelligence System). Claudis is the name of the system, not a persona — Claude Code operates within Claudis; it is not Claudis. The name refers to the persistent infrastructure: the lesson store, the agent fleet, the boot chain, the operational memory, and the Anvil dashboard that ties them together.

The system extends one person's reach by operating continuously — monitoring, researching, building, and learning — while that person (Bill) directs and judges.

The system accumulates real institutional knowledge from real operations. The lesson corpus contains 224+ entries as of mid-April 2026, each produced by an actual session encountering an actual problem. When a lesson surfaces that says "n8n empty-array input silently kills all downstream nodes," that came from a real silent failure in a real workflow. This is not synthetic training data. It is operational scar tissue, and it compounds — every session writes lessons, lessons improve the next session, better sessions build better agents, better agents produce better lessons.

The system does not have a finish line. It has a direction: keep extending what Bill can do through it. The system gets better at executing, better calibrated to Bill, and broader in what it can reach. Specific projects are current work, not destinations. Interests will change, platforms will be added and retired, creative domains will shift. The infrastructure — the lesson system, the agent fleet, the memory, the operational patterns — persists and improves underneath.

The current ceiling is the intention gap. The system executes well against well-specified cards but cannot yet decompose a novel high-level goal into a sequenced build plan. That decomposition is currently done by Bill collaborating with desktop AI sessions, which produce backlog cards that Claude Code executes. Closing this gap — moving from "Bill specifies every card" to "Bill states an intention and the system produces the plan" — is the long-term growth direction.

### Current Operating Mode: Lean Sessions

As of 2026-04-18, the system operates in Lean Mode. Bill collaborates with a desktop AI session (typically Opus) to think through direction and write well-specified backlog cards. Claude Code executes them in focused sessions. The autonomous sentinel (8-hour timer) is stopped and disabled. This is deliberate — directed builds with tight context produce more value right now than autonomous exploration.

Telegram has been deprioritized — it has been unreliable and is a poor interface for desktop work. The Anvil dashboard (see Section 4) is now the primary interface for Bill to monitor and control the system from any browser or phone.

---

## 2. Working With Bill
*Last updated: 2026-04-18*

### Privacy

Bill is identified only as "Bill." Never use last name, location, profession, or other identifying details in any output, document, session artifact, or commit message. This is a hard constraint, not a preference.

### Technical Access

Bill has no SSH access to the Pi. All Pi work must go through Claude Code. Bill interacts with the system through the Anvil dashboard (browser/phone), desktop AI sessions, and Claude Code sessions. When data entry or terminal commands are needed, Claude Code does them — Bill is the weak link for manual entry and should not be given commands to run on the Pi.

### Collaboration Style

Bill is usually in exploration mode, not execution mode. He is developing the system's capability surface. The right response is to think alongside him about what's possible — not to ask what he wants to do with it, not to ask what specific application he has in mind, and not to start building. Questions like "what are you thinking of doing with this?" are counterproductive because he is typically exploring a capability, not planning a specific end-case application.

Bill prefers substantial back-and-forth before action. He wants to think together, refine ideas collaboratively, and reach clarity before anyone starts writing code or committing changes. The moment to shift into execution is when Bill signals it, not when the AI decides the conversation has gone on long enough.

When Bill pushes back or corrects direction, that is collaborative refinement, not friction. Treat corrections as directional input. Do not become more cautious or deferential in response — maintain steady, honest engagement.

### Tone

Bill does not need affirmation or self-congratulatory language. Do not offer praise for his ideas or pat him on the back. If something is genuinely a significant step forward, explain why it matters — don't celebrate it. Keep the tone direct and substantive.

If a proposal has real significance, explain the significance concretely. "This changes the system from time-aware to context-aware" is useful. "Great idea, Bill!" is not.

### Guided Tasks

A regular part of the workload involves Bill navigating web interfaces — creating accounts, getting API keys, configuring services. This kind of work requires specific support:

**One step at a time.** Give Bill a single action. Wait for confirmation or a screenshot. Then give the next action. When a list of instructions is provided all at once, the list scrolls out of sight and becomes unusable.

**Be specific to what's visible.** When Bill shares a screenshot, reference what's actually on screen: "Click the blue button labeled Settings in the top right corner." Do not describe steps that come after what's currently visible.

**Treat this as a working pattern, not a limitation.** The AI cannot see the screen unless Bill shares it. Dumping instructions ahead of where Bill is creates noise.

### What Not To Do

- Do not jump into action. Think first, discuss, then act when Bill signals readiness.
- Do not present numbered lists of setup instructions unprompted. Walk through them interactively.
- Do not ask "what do you want to use this for?" when Bill is exploring a capability.
- Do not frame corrections as Bill being annoyed or frustrated. He is helping the collaboration work better.
- Do not use identifying details beyond "Bill."
- Do not give Bill terminal commands to run on the Pi — use Claude Code instead.

---

## 3. How We Operate
*Last updated: 2026-04-19*

### Roles

**Bill** — Directs, judges, approves. Sets direction via the GitHub Pages site (https://thompsmanlearn.github.io) — the site's direction input writes DIRECTIVES.md via write_directive(). Decides what gets built next. Creates accounts and credentials that require browser interaction. The only person who can approve agent promotions, architectural changes, or new integrations.

**Desktop AI sessions (Opus or equivalent)** — Collaborate with Bill on strategy and direction. Research technical topics. Write backlog cards. Prepare resources for Claude Code (documentation, skills). Review session artifacts and system state. Do not build directly — produce cards and knowledge that Claude Code consumes.

**Claude Code** — Executes backlog cards. Reads LEAN_BOOT.md at startup, which triggers the full boot sequence (PROTECTED.md → DIRECTIVES.md → CATALOG.md → CONTEXT.md → TRAJECTORY.md). Writes code, commits, pushes. Writes session artifacts. Writes lessons to dual store (ChromaDB + Supabase). Operates within the scope boundaries defined in each card.

### The Card System

DIRECTIVES.md holds the current lean session task in one of two forms:

**Form 1 — Inline prose.** The full directive written directly. Claude Code reads and executes it.

**Form 2 — Card pointer.** A single line like `Run: B-027`. Claude Code reads BACKLOG.md, finds the card with that ID, and executes it. lean_runner.sh also extracts the first 300 characters of the card description for lesson injection before Claude starts.

**Context cost of BACKLOG.md:** The full file is loaded every time the pointer form is used. Cards should be archived periodically once completed — the archive note at the top of BACKLOG.md is load-bearing, not cosmetic. Monitor boot-chain file sizes at session close (`wc -l` on PROTECTED.md, DIRECTIVES.md, CATALOG.md, CONTEXT.md, TRAJECTORY.md, BACKLOG.md).

### Backlog Card Format

All cards follow this structure. Desktop sessions write them; Claude Code executes them.

```markdown
## B-NNN: Short descriptive title

**Status:** ready
**Depends on:** B-MMM      ← omit if none

### Goal
One paragraph. What this session should accomplish and why it matters now.
Not how — just what and why.

### Context
Background Claude Code needs before starting. Reference prior sessions,
system state, design constraints, known gotchas relevant to this task.
Enough to execute without back-and-forth — not a tutorial.

### Done when
- Specific verifiable criterion (file at path, curl response, DB row)
- Specific verifiable criterion
- Commit pushed to main

### Scope
Touch: explicit list of files, tables, workflows, services Claude Code may modify
Do not touch: explicit list of things off-limits this session
```

**Writing rules:**
- **Goal**: what and why, not how. One paragraph.
- **Context**: what Claude Code won't find by reading the code — prior decisions, active gotchas, related work from other sessions.
- **Done when**: every item must be checkable. "Works correctly" is not a criterion. "curl localhost:9100/healthz returns `{"status":"ok"}`" is.
- **Scope / Do not touch**: explicit guardrails prevent scope creep. Name the specific things that are off-limits.
- **Two-hour ceiling**: if a card can't reasonably complete in one lean session, split it. Incomplete sessions leave the system in an unknown state and produce no artifact.
- **Card numbers are sequential** and never reused. Archive completed cards in batches; add a note at the top of BACKLOG.md indicating the archived range.

### Sequential Cards

Cards can be written in dependency chains: B-026 enables B-027 which enables B-028. The `Depends on:` field captures this. At session close, Claude Code should set DIRECTIVES.md to point at the next card and note that the prior card is complete. Bill reviews and decides whether to proceed or redirect before triggering the next session.

### Auto-Cycle (B-043)

When `auto_cycle_enabled = true` in system_config, lean_runner.sh chains sessions automatically after success. After a card completes and the site regenerates, lean_runner.sh queries `aadp_project_nodes` for the next unblocked pending node in any active project. If found, it writes the node's goal and context to DIRECTIVES.md, commits and pushes, releases the session lock, and calls `/trigger_lean` to start the next session immediately. If all nodes are complete, the project is marked `complete` in `aadp_projects`. `auto_cycle_enabled` defaults to false and is toggled from the Anvil dashboard or site control panel.

### Desktop Session Workflow

Desktop sessions (Opus or equivalent) read the site directly at https://thompsmanlearn.github.io to orient on current system state. Direction is drafted in the desktop session and entered into the site's direction input by Bill — this calls `write_directive()` via the EmbedControl panel, which writes and pushes DIRECTIVES.md without Bill touching GitHub. Desktop sessions do not edit DIRECTIVES.md on GitHub directly.

### Session Artifacts

Every lean session writes an artifact to `~/aadp/claudis/sessions/lean/YYYY-MM-DD-descriptor.md`:
```
# Session: [date] — [descriptor]
## Directive
## What Changed
## What Was Learned
## Lessons Applied   ← lesson IDs that influenced decisions
## Unfinished
```
Commit message: `session artifact: YYYY-MM-DD-descriptor`

### Lesson Writing

Both stores must be written for every lesson:
1. `memory_add(collection="lessons_learned", ...)` → returns ChromaDB doc_id
2. INSERT into Supabase `lessons_learned` with `chromadb_id` = ChromaDB doc_id

Either alone is a broken lesson. chromadb_id links the two records.

**Writing quality:** Lead with the failure mode, not the tool name. "When a webhook 404s even though the workflow exists" retrieves well. "n8n Webhook URL Format" does not.

---

## 4. Current Project: Anvil Dashboard
*Last updated: 2026-05-03*

### Status: Live and Operational

The Anvil dashboard is live. B-026 through B-041 are all complete as of 2026-04-18. The app is published at https://inborn-rotating-anole.anvil.app and embedded as an iframe on the GitHub Pages site.

**What's working now:**
- System status display (CPU, RAM, disk, temp, uptime) — delegates to stats_server
- Agent fleet detail view with descriptions, status icons, schedules, last updated
- Activate/pause toggle per agent (active↔paused only, guards against other status changes)
- Thumbs-up/thumbs-down feedback per agent with optional comments
- Work queue display (non-complete tasks)
- Inbox with approve/deny buttons
- Write Directive — overwrites DIRECTIVES.md, commits, and pushes to claudis
- Trigger Lean Session — fires stats_server /trigger_lean
- Autonomous Mode toggle — enables/disables n8n autonomous_growth_scheduler and auto_cycle_enabled atomically
- Sessions tab — live session status + recent artifact list
- Lessons tab — browse lessons by recency or most-applied; view full content
- Memory tab — browse ChromaDB collections; semantic search
- Skills tab — list all skills with trigger keywords, times loaded, last loaded; view content
- Artifacts tab — browse agent_artifacts by agent and type
- EmbedControl form — separate lightweight form embedded on the GitHub Pages site; heartbeat, session status, direction input, start session button, autonomous mode toggle
- Uplink connection watchdog (B-031) — watchdog hits localhost:9101/ping; systemd restarts if unhealthy

**Not yet done:**
- Phone capabilities (camera, geolocation, push notifications)
- Protected agent indicator in UI (⚠️ icon for agents flagged as protected)

### What Anvil Is

Anvil (anvil.works) is a Python-only web app platform. The key capability for AADP is Uplink: a persistent outbound websocket from the Pi to Anvil's cloud. No port forwarding, no reverse proxy, no nginx. The Pi initiates the connection, so it's firewall-friendly. Auto-reconnects on crash (but see Known Gaps — silent disconnects are not detected).

The Anvil app is accessible from any browser and installable as a PWA on a phone.

**Decision: cloud-hosted on anvil.works**, not self-hosted App Server. App ID: `PUCVGRU3KBBGPNPH`.

### Architecture

```
Pi uplink script (systemd service: aadp-anvil.service)
  ↕ websocket (outbound from Pi)
Anvil cloud
  ↕
Anvil web app (browser / phone PWA)
```

### How Claude Code Builds Anvil Apps

The Anvil app syncs bidirectionally with `thompsmanlearn/claude-dashboard` (GitHub, **master** branch — not main). Claude Code pushes to that repo and Anvil picks up changes automatically.

The dashboard is built using the **programmatic approach** — `add_component()` calls in `client_code/Form1/__init__.py`. This is more natural for Claude Code than writing YAML.

Material Design 3 theme. Component roles used: `'outlined-card'`, `'filled-button'`, `'tonal-button'`, `'outlined-button'`, `'headline'`, `'title'`, `'body'`.

A Claude Code skill reference exists at `skills/anvil/REFERENCE.md` — loaded automatically by CATALOG.md for any Anvil-related card.

### Uplink Callable Functions (current)

| Callable | Delegates to | Direction |
|---|---|---|
| `get_system_status()` | stats_server `/system_status` | Read |
| `get_agent_fleet()` | Supabase `agent_registry` | Read |
| `get_work_queue()` | Supabase `work_queue` | Read |
| `get_inbox()` | Supabase `inbox` (pending only) | Read |
| `get_lean_status()` | subprocess `ps aux` | Read |
| `get_session_status()` | Supabase `session_status` | Read |
| `get_session_artifacts(limit)` | claudis `sessions/lean/` filesystem | Read |
| `get_site_status()` | thompsmanlearn.github.io repo + Supabase | Read |
| `get_lessons(filter, limit)` | Supabase `lessons_learned` | Read |
| `get_lesson_content(lesson_id)` | Supabase `lessons_learned` | Read |
| `get_collection_stats()` | ChromaDB `/api/v1/collections` | Read |
| `search_memory(collection, query, limit)` | ChromaDB query | Read |
| `get_skills()` | Supabase `skills_registry` | Read |
| `get_skill_content(name)` | claudis `skills/` filesystem | Read |
| `get_artifacts(agent_name, artifact_type, limit)` | Supabase `agent_artifacts` | Read |
| `get_autonomous_mode()` | n8n API + Supabase `system_config` | Read |
| `set_agent_status(agent_name, status)` | Supabase `agent_registry` PATCH | Write |
| `submit_agent_feedback(agent_name, rating, comment)` | Supabase `agent_feedback` POST — ⚠️ predates B-054 schema; verify mapping to target_type/target_id/content | Write |
| `approve_inbox_item(item_id)` | Supabase `inbox` PATCH | Write |
| `deny_inbox_item(item_id)` | Supabase `inbox` PATCH | Write |
| `trigger_lean_session()` | stats_server `/trigger_lean` | Write |
| `write_directive(text)` | claudis git → DIRECTIVES.md | Write |
| `set_autonomous_mode(enabled)` | n8n API activate/deactivate + Supabase `system_config` | Write |
| `invoke_agent(agent_name)` | agent webhook (fire-and-forget background thread) | Write |
| `get_research_articles(limit)` | Supabase `research_articles` ordered by retrieved_at desc | Read |
| `rate_research_article(article_id, rating)` | Supabase `research_articles` PATCH | Write |
| `comment_research_article(article_id, comment)` | Supabase `research_articles` PATCH | Write |
| `set_research_article_status(article_id, status)` | Supabase `research_articles` PATCH (new/reviewed/archived) | Write |
| `submit_agent_feedback_v2(target_type, target_id, content)` | Supabase `agent_feedback` POST | Write |
| `get_research_run_summary()` | Supabase `research_articles` — most recent run stats | Read |
| `get_research_bundle(agent_run_id)` | Supabase `research_articles` + `agent_feedback` — markdown export | Read |
| `get_research_counters()` | Supabase `research_articles` — total/unreviewed/new-24h counts | Read |
| `create_thread(title, question)` | Supabase `threads` POST | Write |
| `get_threads(state_filter)` | Supabase `threads` ordered by last_activity_at | Read |
| `get_thread_entries(thread_id)` | Supabase `thread_entries` ordered by created_at | Read |
| `get_thread_bundle(thread_id)` | Supabase `threads` + `thread_entries` — markdown export | Read |
| `add_thread_entry(thread_id, entry_type, content, source)` | Supabase `thread_entries` POST | Write |
| `update_thread_state(thread_id, state, close_reason)` | Supabase `threads` PATCH | Write |
| `wire_thread_agent(thread_id, agent_name)` | Supabase `threads` PATCH | Write |
| `trigger_thread_gather(thread_id, agent_name)` | Haiku derives queries → agent webhook → stats_server | Write |
| `write_thread_gather_entries(thread_id, article_ids)` | Supabase `thread_entries` POST batch | Write |
| `extract_analysis(thread_id, prose, source)` | Haiku → Supabase `thread_entries` POST (4 buckets) | Write |
| `resolve_screening_uncertain(entry_id, thread_id, item_id, decision, reason, resolution)` | Supabase `research_articles` + `thread_entries` PATCH | Write |

### Architecture Decision Record

The ADR defining the curation surface design is committed at `architecture/decisions/anvil-curation-surface.md`. It covers the tab structure, cross-agent artifact convention, data logging discipline, and agent I/O declarations. Read it before designing any new Anvil tab or modifying agent output patterns.

### Phone Capabilities Anvil Unlocks (future)

- **Camera** — route images into the system as visual input
- **Geolocation** — context-aware agents (knowing whether Bill is home changes what's relevant)
- **Web push notifications** — replace Telegram alerts with native phone notifications

These aren't UI improvements — they make the system's boundary with the physical world porous.

---

## 5. Capabilities Inventory
*Last updated: 2026-05-03*

This section tracks what the system as a whole can actually accomplish today. This is distinct from the skills list (what Claude Code knows how to do) and the agent fleet (what's deployed). Capabilities are end-to-end outcomes.

**Note:** A `capabilities` table exists in Supabase with fields for name, category, confidence, times_used, and last_used. As of 2026-04-18, it is unclear whether this table has been populated. Reconciling this table with actual system capabilities is a review task (see Section 6).

### Known Working Capabilities

**Information Gathering:**
- Scan arXiv for relevant preprints and score them for AADP implications
- Monitor Wikipedia for pageview velocity spikes and cluster trending topics (paused)
- Search GitHub weekly for MCP/agent repos
- Fetch daily research across rotating topics (arXiv, Hacker News, Reddit)
- Synthesize weekly research findings into digests

**Operational Awareness:**
- System health monitoring (CPU, RAM, disk, temperature, uptime)
- Agent fleet health scanning (consecutive error detection, auto-pause at ≥3)
- Stale agent detection (building/sandbox status >7 days)
- Daily briefing digest (system health, agent status, errors, work queue)

**Memory and Learning:**
- Semantic lesson retrieval with task-type routing and staleness penalty
- Dual-store lesson writing (ChromaDB + Supabase)
- Context injection before every session (inject_context_v3.1)
- Zero-applied wildcard injection for uncirculated lessons
- Retrieval logging for future adapter training

**Development:**
- Execute focused build sessions from backlog cards
- Write and commit session artifacts
- Manage n8n workflows (create, update, activate/deactivate)
- Agent lifecycle management (register, update, promote)

**Communication:**
- Telegram command routing (deprioritized but functional when Telegram is working)
- Daily weather forecast
- Serendipity engine (Wikipedia On This Day synthesis — paused)

**Research:**
- On-demand research runs via Anvil "Run research" button (`context_engineering_research` agent) — fetches from 8 sources: HN, arXiv, dev.to, GitHub, lobste.rs, Medium, openai (RSS), deepmind (RSS); per-source cap=5, global cap=20, skip-on-empty-fetch. Anthropic blog deferred — no public RSS feed (lesson: anthropic_no_rss_2026-05-03).
- Article review: rate (👍/👎), comment, and status-track articles in Anvil Research tab (58 articles as of 2026-04-26)
- Bundle export: one-click markdown export of a run (articles + ratings + pending feedback) for desktop analysis
- Boot-time feedback pickup: both LEAN_BOOT and bootstrap surface unprocessed `agent_feedback` rows at session start
- Thread-aware gather: when triggered from a thread, Haiku derives queries from the thread question; results tagged with thread_id; gather entries written back automatically

**Thread Architecture:**
- Create and browse threads by research question and state (active/dormant/closed)
- Add annotations, analysis pastes, and manually triggered gathers to threads
- Paste desktop-Claude analysis → Haiku extracts synthesis, conclusions, screening decisions, and sub-question candidates as typed entries
- Uncertain screening decisions surface inline Confirm/Override/Reject controls; confident decisions commit to research_articles immediately
- Standing summary: most recent `summary` entry displayed at top of thread for at-a-glance conclusions
- Export thread as markdown bundle for offline review

**Dashboard & Governance (Anvil + GitHub Pages):**
- View system status, agent fleet, work queue, inbox from any browser
- Activate/pause agents from dashboard
- Approve/deny inbox items from dashboard
- Write directives and trigger lean sessions from dashboard and site
- Submit per-agent thumbs-up/thumbs-down feedback with comments
- Browse sessions, lessons, memory, skills, artifacts in dashboard tabs
- Toggle autonomous mode (scheduler + auto-cycle) from dashboard and site
- Research tab: run agent, review articles, leave directional feedback for agent and UI
- Thread architecture (B-070–B-083): browse/create threads by question and state (active/dormant/closed), collapsed cards with lazy-loaded entries
- Thread entries: per-type rendering (annotation, gather, analysis, summary, screening, screening_uncertain, sub_question_candidate) with icons; History drawer collapses state_change entries by default
- Thread action panel: Gather / Export / Add-as-analysis-entry primary; annotation secondary; Thread settings (state, wire agent) in collapsible drawer
- Extraction passback: paste desktop-Claude analysis → Haiku extracts to typed entries (synthesis, conclusions, screening decisions, sub-question candidates); uncertain screening surfaces inline Confirm/Override/Reject buttons
- Thread-aware gather: Haiku derives 3-5 queries from thread question + recent entries; articles tagged with thread_id; gather entries written back to originating thread automatically
- Standing summary: most recent `summary` entry shown at top of thread between header and main content; filtered from chronological list

**GitHub Pages Site (https://thompsmanlearn.github.io):**
- 6-page site generated from live Supabase data: Home, Fleet, Capabilities, Architecture, Sessions, Direction
- Auto-regenerates at every lean session close via lean_runner.sh
- Embedded AADP Control panel (EmbedControl) — direction input, start session, autonomous mode toggle
- Bidirectional direction loop: Bill types direction on site → DIRECTIVES.md updated → session runs → site regenerates → results visible on same page

**Project Graph Execution:**
- aadp_projects / aadp_project_nodes tables in Supabase model multi-session build projects
- Auto-cycle (auto_cycle_enabled) chains sessions across nodes without human intervention
- Completed project "Document AADP on the Site" — 8 nodes executed across sessions (B-042)

### Not Yet Working or Unverified

- Autonomous task decomposition
- Capabilities table in Supabase (may be partially populated)
- Protected agent indicator in dashboard UI

---

## 6. System Health and Review
*Last updated: 2026-04-26*

### The Governance Gap — Partially Closed

The Anvil dashboard now provides the review surface that was previously missing. Bill can see the full agent fleet with descriptions, status, and controls. The first governance action was taken on 2026-04-18: 10 non-critical agents paused, 7 agents flagged as protected.

**What the dashboard enables now:**
- Visual fleet review without terminal access
- Immediate activate/pause action on any active/paused agent
- Feedback capture (thumbs up/down + comments) per agent

**Remaining governance gaps:**
- **Capabilities table still unverified.** May be partially populated.
- **Lesson quality decay.** Lessons accumulate but there's no curation.
- **Sandbox blockage partially resolved.** Agent approval now possible via Anvil inbox, but the flow hasn't been tested end-to-end with a real sandbox agent.

### What Review Looks Like

Periodically (cadence TBD — every few sessions or weekly), a desktop session should conduct a system audit:

1. **Agent fleet review.** Open the Anvil dashboard. For each active agent: is the description accurate? When did it last update? Is anyone consuming its output? Use thumbs-down + comment to flag concerns. Pause low-value agents.
2. **Capabilities reconciliation.** Populate the capabilities table if empty. Cross-reference against what actually works end-to-end.
3. **Lesson sampling.** Pull a random sample of recent lessons. Are they well-written (failure-mode-first)? Are older lessons still accurate? Are any now redundant with established convention?
4. **Feedback review.** Query `agent_feedback` for thumbs-down patterns. Act on repeated negative signals.
5. **Research value check.** Sample recent research outputs. Is the arxiv_aadp_pipeline surfacing things Bill cares about?

---

## 7. Technical Architecture
*Last updated: 2026-05-03*

### Services Map

| Service | Container/Process | Port | Start mechanism | Config location |
|---|---|---|---|---|
| n8n 2.6.4 | Docker container `n8n` | 5678 | Docker (auto-restart) | `~/n8n/docker-compose.yml`, `~/n8n/n8n_data/` |
| ChromaDB v0.5.20 | Docker container | 8000 | Docker (auto-restart) | Do NOT upgrade — v1.x client uses /api/v2, incompatible |
| Stats Server | systemd `aadp-stats.service` | 9100 | systemd (always-on) | `~/aadp/stats-server/stats_server.py`, `~/aadp/mcp-server/.env` |
| MCP Server | Claude Code stdio subprocess | stdio | Claude Code spawns it | `~/aadp/mcp-server/server.py`, `~/aadp/mcp-server/.env` |
| Anvil Uplink | systemd `aadp-anvil.service` | — | systemd (always-on, Restart=always) | `~/aadp/claudis/anvil/uplink_server.py`, `~/aadp/mcp-server/.env` |
| Sentinel | systemd `aadp-sentinel.service` (oneshot) | — | `aadp-sentinel.timer` every 8h (currently disabled) | `/etc/systemd/system/aadp-sentinel.{service,timer}` |
| Supabase | Remote SaaS | 443 | External | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_MGMT_PAT` in .env |

Key infrastructure facts:
- All compute runs on a Raspberry Pi 5, 16GB RAM, always-on
- n8n hosts the agent fleet as workflows; `host.docker.internal:host-gateway` lets n8n reach Pi services
- ChromaDB stores semantic memory — pinned at v0.5.20, do not upgrade
- Stats server handles lesson injection, research, GitHub ops, and sentinel/lean triggers
- MCP server provides Claude Code with tools for memory, Supabase, n8n, and system operations
- Anvil Uplink maintains persistent outbound websocket to Anvil cloud; registers callable functions that the dashboard invokes
- Supabase stores structured data — all CRUD via PostgREST, DDL via Management API
- Credentials live in `~/aadp/mcp-server/.env` — never committed

### Credentials in .env

Keys present (do not expose values): CHROMADB_HOST, CHROMADB_PORT, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_MGMT_PAT, N8N_BASE_URL, N8N_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN, STATS_PORT (default 9100), ANVIL_UPLINK_KEY.

### MCP Server Tools

The MCP server (`~/aadp/mcp-server/server.py`) exposes tools across these categories:

**Memory (ChromaDB):** memory_search, memory_add, memory_delete, memory_list_collections

**Supabase tables via dedicated tools:**
- Prompts: prompt_get, prompt_update, prompt_history, prompt_rollback
- Config: config_get, config_set
- Agent Registry: agent_register, agent_update
- Error Logs: error_log_query, error_log_resolve
- Ideas: idea_capture, idea_list
- Work Queue: work_queue_add, work_queue_query, work_queue_update
- Audit Log: audit_log_query
- Session Notes: session_notes_save, session_notes_load
- DDL: supabase_exec_sql (Management API — works from Pi for DDL only)

**n8n Workflows:** workflow_list, workflow_get, workflow_create, workflow_update, workflow_activate, workflow_deactivate, execution_list, execution_get. Note: workflow_execute always raises ValueError — n8n has no public execution API.

**System:** system_status, service_status, logs_fetch

**Composite:** developer_context_load (concurrent pull of registry + queue + errors + notes + config + system status)

**lean_runner.sh** — `~/aadp/sentinel/lean_runner.sh` (live) and `~/aadp/claudis/sentinel/lean_runner.sh` (version-controlled). Stats server hardcodes the sentinel path; claudis copy is canonical source. After successful session: regenerates GitHub Pages site, then runs auto-cycle check if `auto_cycle_enabled=true`.

Key implementation details:
- n8n API key re-read from .env on every call — key rotations need no restart
- All Supabase ops use PostgREST with service key
- ChromaDB client lazily created and shared
- memory_search fires retrieval logging as fire-and-forget — never blocks
- retrieval_log accumulates query-document pairs for eventual adapter training (goal: 1500 labeled pairs)

### Stats Server Endpoints

The stats server (`~/aadp/stats-server/stats_server.py`, 3205 lines, port 9100) is now in git (commit 56ba358, 2026-04-17).

**Core:** /system_status, /healthz

**Session triggers:** /trigger_sentinel, /trigger_lean

**GitHub:** /gh (dispatches to gh_status, gh_becoming, gh_attempts, gh_log, gh_review, gh_keep, gh_redirect, gh_close, gh_report)

**Data:** /append_experiment, /write_experiment, /get_outputs, /get_audit

**Research:** /run_daily_research, /run_research_synthesis, /get_research_window

**Memory:** /memory_query (ChromaDB proxy via subprocess)

**Lesson injection:** /inject_context_v2, /inject_context_v3 (current — v3.1 with task-type routing, confidence signal, zero_applied wildcards), /lessons_applied

### inject_context_v3 Task-Type Routing

```python
_V3_TASK_ROUTING = {
    "agent_build":      [lessons, error_patterns, reference_material, session_memory, research_findings],
    "research_cycle":   [research_findings, lessons, reference_material, session_memory],
    "explore":          [lessons, session_memory, research_findings],
    "self_diagnostic":  [self_diagnostics, error_patterns, lessons],
    "directive":        [lessons, error_patterns, reference_material, session_memory],
    "gh_weekly_search": [research_findings],
    "gh_report":        [session_memory, lessons],
    "gh_task":          [lessons, reference_material],
    "agent_control":    [lessons, error_patterns],
    "agent_test":       [lessons, error_patterns, reference_material],
    # unknown → all 5 tiers
}
```

Confidence thresholds: min_dist < 0.8 → high; 0.8–1.1 → medium; 1.1+ → low; no results → none.

### Database Schema — Active Tables

**work_queue** — id (uuid), task_type, status (pending/claimed/processing/complete/failed), priority (integer 1-3, 1=normal 3=critical), assigned_agent, input_data (jsonb), output_data (jsonb), created_by, created_at, claimed_at, completed_at, error_message

**agent_registry** — id (uuid), agent_name (unique), display_name, agent_type, description, status (active/paused/retired/building/broken/sandbox), input_types/output_types/data_sources (text[]), schedule, workflow_id, performance_metrics (jsonb), protected (bool), telegram_command, created_at, updated_at

**research_articles** — id (uuid), agent_run_id (uuid, groups articles from one run), title (text), url (text), source (text, domain), summary (text), query_used (text), retrieved_at (timestamptz), rating (smallint, default 0: -1/0/1), comment (text), status (text, default 'new': new/reviewed/archived), provenance (text, default 'context_engineering_research_agent'), thread_id (uuid, nullable — set when article was gathered via a thread-triggered run). Index on agent_run_id and status.

**threads** — id (uuid), title (text), question (text), state (text, default 'active': active/dormant/closed), close_reason (text, nullable), bound_agent (text, nullable), created_at, updated_at, last_activity_at.

**thread_entries** — id (uuid), thread_id (uuid), entry_type (text, CHECK constraint: annotation/gather/analysis/summary/screening/screening_uncertain/sub_question_candidate/state_change), content (text), source (text, nullable), chromadb_id (text, nullable), metadata (jsonb, default '{}'), created_at. Embeddings mirrored to ChromaDB `thread_entries` collection (excluded from default boot retrieval by design).

**agent_feedback** — id (uuid), target_type (text, not null, e.g. 'agent', 'anvil_view', 'lesson', 'card'), target_id (text, not null), content (text, not null), created_at (timestamptz), processed (boolean, nullable), processed_at (timestamptz, nullable), processed_in_session (text, nullable), action_summary (text, nullable — required on every processed=true write; use "Deferred: [reason]" prefix when not acted on), action_session (text, nullable — artifact filename or commit SHA; required on every processed=true write), action_result_url (text, nullable — optional, only when a specific URL exists). Index on (target_type, target_id, processed). Boot-time pickup: LEAN_BOOT step 10 queries unprocessed rows and surfaces them. Acting on feedback writes action_summary + action_session immediately; deferred items are swept and written at session close. This converts the table from a queue to a conversation thread.

**lessons_learned** — id (uuid), title, category, content, confidence (float, default 0.5), times_applied (int, default 0), source (default sentinel), created_at, updated_at, chromadb_id (text). NULL chromadb_id = invisible to semantic search.

**session_notes** — id (uuid), content, category (todo/observation), created_at, consumed (bool)

**audit_log** — id (uuid), actor, action, target, details (jsonb), timestamp

**error_logs** — id (uuid), workflow_id, workflow_name, node_name, error_type, error_message, execution_id, timestamp, resolved (bool), resolution_notes, resolved_by, resolved_at

**experimental_outputs** — id, agent_name, experiment_id, output_type, content (jsonb), confidence, promoted, reviewed_by_bill, created_at, api_usage (jsonb)

**agent_prompts** — id, agent_name, prompt_text, version (int), is_active (bool), created_at, created_by, change_notes. Versioned — only one active per agent_name.

**agent_config** — id, agent_name (unique), model, temperature, max_tokens, metadata (jsonb), updated_at

**retrieval_log** — id, query, collection, doc_id, distance, was_relevant (bool nullable), session_id, created_at

**research_papers** — id, title, authors, abstract, publication_date, citation_count, source, source_id, url, pdf_url, topic_tags (text[]), relevance_score, status, discovered_at, reviewed_at, notes, component_tag, action_type, already_addressed_since, addressed_by

**aadp_projects** — id (uuid), name (text), status (text: active/complete)

**aadp_project_nodes** — id (uuid), project_id (uuid FK), parent_id (uuid nullable), name (text), type (text), status (text: pending/in_progress/done), dependencies (uuid[]), acceptance_criteria (text), context (text), session_budget (int), output (text nullable), created_at, updated_at

**system_config** — key (text PK), value (jsonb), updated_at. Notable keys: `auto_cycle_enabled` (bool, default false — controls lean session chaining), `global_pause` (bool), `wake_interval_hours` (int)

**inbox** — id, from_agent, message_type (help_request/approval_request/recommendation/observation/question/alert), subject, body, context (jsonb), status (pending/approved/denied/deferred/replied), bill_reply, priority, created_at, responded_at

**capabilities** — id, name, category, description, confidence (default 0.5), times_used (default 0), last_used, created_at, updated_at

### ChromaDB Collections

All collections use `all-MiniLM-L6-v2` embeddings. ChromaDB v0.5.20 at localhost:8000.

| Collection | Count (approx) | Purpose | Boot retrieval |
|---|---|---|---|
| `lessons_learned` | 224+ | Technical lessons from sessions | ✓ default |
| `reference_material` | 173 | Architecture patterns, runbooks | ✓ default |
| `research_findings` | 141 | arXiv/HN research items | ✓ default |
| `session_memory` | 71+ | Episodic session context | ✓ default |
| `error_patterns` | 15 | Known failure modes | ✓ default |
| `self_diagnostics` | 11 | Diagnostic procedures | ✓ default |
| `agent_templates` | 4 | Agent scaffolding templates | ✓ default |
| `thread_entries` | — | Thread entry embeddings (B-070+) | **excluded by design** |

**thread_entries is excluded from default boot retrieval.** LEAN_BOOT step 11 and bootstrap step 3 query specific named collections; they do not query `thread_entries`. This is enforced by absence — there is no explicit blocklist to maintain. Future cards that add in-thread semantic search will query this collection explicitly. Do not add it to default routing without a deliberate decision.

Distance thresholds: < 0.8 high confidence; 0.8–1.2 review carefully; > 1.2 weak match.

Critical gotcha: Never include `"embeddings"` in the include list for bulk-get operations — causes IndexError at scale. Use `["documents", "metadatas"]` only.

**Integrity invariant:** `chromadb_id IS NOT NULL` for every live lesson. A NULL chromadb_id means the lesson is invisible to semantic search — it will never be retrieved by inject_context_v3 or memory_search. This invariant is enforced by procedure, not by a database constraint.

Store sync check (run at close-session step 7a): `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` — any value > 0 means the invariant is broken. Surface the count in the session summary; do not auto-fix. Backfill procedure: for each broken row, call memory_add to ChromaDB, capture the returned doc_id, UPDATE lessons_learned SET chromadb_id = doc_id WHERE id = supabase_id.

### Data Flow — Lesson System End-to-End

**Creation:** Session writes lesson → memory_add to ChromaDB (returns doc_id) → INSERT to Supabase with chromadb_id = doc_id. Both writes required.

**Retrieval:** scheduler.sh or lean_runner.sh calls POST /webhook/inject-context → lesson_injector workflow → stats_server /inject_context_v3 → Haiku intent expansion → collection queries with task-type routing → staleness penalty → zero_applied wildcards → 2000-token budget assembly → returns context_block.

**Injection:** Context block prepended as `## PRE-LOADED CONTEXT` before session prompt.

**Tracking:** increment_lessons_applied_by_id Supabase RPC fires after injection.

---

## 8. Agent Fleet
*Last updated: 2026-05-03*

**Lifecycle:** `building` → `sandbox` → (behavioral_health_check + 4-Pillars evaluation) → `active` OR `retired/paused`

32 agents total. Full source at `~/aadp/claudis/agents/`.

### Protected Agents — source of truth: agent_registry

`agent_registry.protected = true` is the single source of truth for which agents are load-bearing. Do not maintain a separate list here — it drifts. Query directly:

```sql
SELECT agent_name FROM agent_registry WHERE protected = true ORDER BY agent_name;
```

**claude_code_master is a registry marker, not an executable agent.** It has no workflow_id and no n8n workflow. It exists so the registry has an entry representing Claude Code sessions. Do not attempt to pause, trigger, or treat it as a running agent.

### Paused Agents

Paused 2026-04-18 (personal briefings, no active consumer):
ai_frontier_scout, coast_intelligence, cosmos_report, daily_briefing_agent, daily_research_scout, heritage_watch, macro_pulse, serendipity_engine_prod, session_report_agent, wiki_attention_monitor

Paused 2026-04-22 (aspirations not attained — pruned to load-bearing core):
agent_evaluator_4pillars, behavioral_health_check, feedback_agent, github_issue_tracker, processed_content_agent, resource_scout_reddit, usage_stats, weather_agent

All paused agents can be reactivated from the Anvil dashboard.

### Active Production Agents

| agent_name | workflow_id | trigger | key behavior |
|---|---|---|---|
| telegram_command_agent | kddIKvA37UDw4x6e | Telegram long-poll | Routes /commands. **PROTECTED.** |
| morning_briefing | xt8Prqvi7iJlhrVG | daily 7AM PT | No LLM. Queue + agents + health. **PROTECTED.** |
| agent_health_monitor | w5vypq4vb2rSrwdl | webhook | Error scan + stale scan. **PROTECTED.** |
| research_synthesis_agent | JUBCbXJe3TwwpB2T | Sunday 14:00 UTC | Weekly synthesis of research corpus. **PROTECTED.** |
| arxiv_aadp_pipeline | bZ35VinkRjRT7gYi | Mon/Wed/Fri 15:00 UTC | arXiv preprints → research_findings + research_papers. **PROTECTED.** |
| architecture_review | 7mVc61pDCIObJFos | Biweekly Sunday 16:00 UTC | Research findings → design decisions → work_queue items. |
| context_engineering_research | gzCSocUFNxTGIzSD | On-demand webhook | 8 sources (HN, arXiv, dev.to, GitHub, lobste.rs, Medium, openai RSS, deepmind RSS) → Haiku neutral summarize → research_articles. Per-source cap=5, global cap=20. Empty-fetch skips item. Company blogs freshness-driven (30-day window, 3/feed). Anthropic deferred — no RSS. dev.to tags: agents, n8n, llmops, rag, claude. Thread-aware: when payload includes thread_id, Haiku derives 3-5 queries from thread question + recent entries; articles tagged with thread_id; Code node writes gather entries back to originating thread. |

### Platform Infrastructure Agents

| agent_name | workflow_id | trigger | key behavior |
|---|---|---|---|
| lesson_injector | MFmk28ijs1wMig7h | webhook | Context injection before sessions. **PROTECTED.** |
| session_health_reporter | 5x6G8gFlCxX0YKdM | webhook | Post-sentinel-session artifact to GitHub. **PROTECTED.** |
| autonomous_growth_scheduler | Lm68vpmIyLfeFawa | every 6h (deactivated) | Queues explore/build/research tasks (autonomous mode only). Toggle via Anvil. **PROTECTED.** Bill reactivates manually — never auto-reactivate. |

### n8n Credential IDs
- Telegram credential ID: y4YfKWpm20Z9sw7G
- Bill's Telegram chat_id: 8513796837 (hardcoded in multiple places)

---

## 9. Skills and Knowledge Resources
*Last updated: 2026-04-18*

### Claude Code Skills

Claude Code has a skill system — domain-specific knowledge packages loaded when relevant. Skills live in `~/aadp/claudis/skills/` and are routed via `CATALOG.md`.

Existing skills: agent-development, system-ops, communication, research, triage, **anvil**.

The **anvil** skill (`skills/anvil/REFERENCE.md`) covers: error propagation, timeout behavior, connection stability, portable types, app structure, MD3 component roles, and uplink server location. It is loaded automatically for any card matching keywords: anvil, uplink, dashboard.

### What Desktop Sessions Should Produce

A key role for desktop sessions is researching technical topics and packaging that knowledge for Claude Code. For any new platform integration, the desktop session should:

1. Research the platform's API, conventions, and gotchas
2. Produce documentation Claude Code can consume — either as a skill file or reference material committed to the repo
3. Include concrete examples (working YAML, Python patterns, CSS conventions)
4. Anticipate the gotchas Claude Code will hit and document them preemptively

---

## 10. Platform Roadmap
*Last updated: 2026-04-18*

These are integration candidates, not commitments. The system grows by connecting to new platforms that extend its reach. Bill's interests will determine which get built and when.

**Anvil (MILESTONE — B-026 through B-033 complete 2026-04-18):** Dashboard and UI layer. Live and operational. Replaces Telegram as primary control surface. Next phase: curation surface — tabs for Sessions, Lessons, Memory, Skills, and Artifacts, plus cross-agent artifact convention. Design is in `architecture/decisions/anvil-curation-surface.md`. See Section 4.

**Replicate:** Cloud GPU inference via API. Enables image generation, video processing, model inference. Single API key, no Pi infrastructure.

**Notion or similar:** Structured knowledge base for longer-form documents that don't fit in ChromaDB chunks.

**Home Assistant:** Free environmental context if smart home infrastructure exists.

**Publishing APIs:** Itch.io, YouTube, GitHub Pages. Autonomous publishing of creative artifacts.

**Anthropic Usage API:** Precise token cost tracking per agent and session type.

**Communication beyond Telegram:** Gmail API, Discord (bots, webhooks, community overlap with creative domains).

### Note on Creative Domains

Game development (on Unreal Engine, not Roblox) is one example of a creative domain Bill may pursue. It is not the definition. The system should be capable across creative domains — the specific direction will change.

---

## 11. Desktop Session Playbook
*Last updated: 2026-04-18*

### What a Desktop Session Is For

A desktop session collaborates with Bill. It does not build directly. Its outputs are:
- Strategic thinking and direction-setting
- Well-specified backlog cards
- Research and documentation that Claude Code consumes
- System reviews and audits (see Section 6)
- Guided assistance with web-based setup tasks (see Section 2)

### Starting a Desktop Session

1. Read this document.
2. Check the "Last updated" dates on each section. Flag anything that seems stale.
3. Be prepared to discuss current project state, write cards, think strategically, or help Bill with a guided task.
4. Do not summarize the document back to Bill. He knows what's in it. Start from where he wants to start.

### Writing Good Cards

The most common failure modes:
- Goal describes how instead of what — Claude Code should choose its own approach
- Done-when criteria are aspirational rather than verifiable
- Scope is too broad for one lean session
- Context assumes Claude Code knows things from prior sessions that it doesn't

Before writing a card, consider: could Claude Code execute this without any follow-up questions? If not, the Context section is incomplete.

### Researching for Claude Code

When Bill decides to integrate a new platform:
- Read the platform's actual documentation
- Find the specific API patterns, file formats, and conventions Claude Code will need
- Produce concrete examples (working code, valid YAML, tested API calls)
- Package as a skill file or reference material in the claudis repo
- Anticipate gotchas and document them preemptively

### Session Close

Before ending a desktop session:
- Does the brief need updating? If so, which sections?
- Are there cards ready to be added to BACKLOG.md?
- Were any decisions made that should be captured?
- Is there research or documentation that should be committed to the repo?

---

## 12. Known Gaps and Fragilities
*Last updated: 2026-05-03*

**Anvil uplink silent disconnects.** The websocket can die without the systemd service noticing. Restart=always only catches crashes. B-031 adds a watchdog. Until then, if the dashboard stops responding, `sudo systemctl restart aadp-anvil.service` fixes it.

**anvil-uplink 0.7.0 tracer crash.** Must call `set_internal_tracer_provider(TracerProvider())` before any RPC dispatch or the handler thread crashes. Already fixed in uplink_server.py. Lesson captured.

**Do not smoke-test live trigger endpoints.** The `/trigger_lean` endpoint actually launches sessions. During B-029 development, an accidental call launched a rogue lean session. Use status-check endpoints or dry-run flags for testing. Lesson captured.

**n8n API key expires silently.** The key in .env is read fresh on every call, but the key has a TTL. No monitoring for expiration.

**No alert for sentinel failures.** send_telegram_alert() in scheduler.sh logs to file but doesn't send a Telegram message.

**ChromaDB version pinned at v0.5.20.** Client and server must match. v1.x uses /api/v2 — incompatible.

**stats_server ChromaDB access uses subprocess.** Different venv. Adds ~200-500ms latency per call.

**Array column syntax must use cast form.** `ARRAY['a','b']` fails silently. Use `'{"a","b"}'::text[]`.

**Management API Cloudflare-blocked from Pi.** DDL endpoint works. All CRUD must use PostgREST.

**workflow_execute MCP tool always fails.** No n8n public execution API.

**n8n webhooks need restart after activation.** 404 until `docker restart n8n`.

**Prompt caching only works on Sonnet 4.6+.** Haiku 4.5 silently ignores cache_control.

**Agent approval flow partially fixed.** Can now approve via Anvil inbox, but the end-to-end sandbox→active flow hasn't been tested through the dashboard yet.

**Capabilities table partially populated.** At least some rows exist (boot_feedback_pickup added 2026-04-26); full reconciliation against actual system capabilities not yet done.

**Project auto-complete has no approval gate.** When lean_runner.sh finds no unblocked pending nodes, it marks the project `complete` in `aadp_projects` automatically — Bill does not review or approve first.

**lean_runner.sh dual-location.** Live copy at `~/aadp/sentinel/lean_runner.sh`; version-controlled copy at `claudis/sentinel/lean_runner.sh`. Changes must be made to both manually — no sync mechanism.

**close-session.md and bootstrap.md are version-controlled in claudis.** Authoritative copies live at `~/aadp/claudis/skills/close-session.md` and `~/aadp/claudis/skills/bootstrap.md`. The `.claude/skills/` paths are symlinks into claudis — no manual sync needed. Edit in claudis, commit, done. Resolved B-061a 2026-04-26.

**n8n webhook v2 body fields are nested.** In n8n webhook v2 nodes, payload body fields live at `$json.body.fieldName`, not `$json.fieldName`. Using `$json.queries` silently falls back to defaults if the field is actually at `$json.body.queries`. Always inspect actual webhook execution data to confirm field paths. Found in B-079 regression, fixed in B-080.

**Telegram chat_id hardcoded** in scheduler.sh, lean_runner.sh, stats_server.py, and many n8n workflows.

**`/webhook/telegram-quick-send` assumed always active.** If TCA deactivated, all session Telegram notifications silently fail.

**Supabase RPC functions** (increment_lessons_applied_by_id, increment_lessons_applied) must exist for lesson tracking. DDL committed to claudis/stats-server/.

---

## 13. Git and File Conventions
*Last updated: 2026-04-19*

### Repo: `thompsmanlearn/claudis` → `~/aadp/claudis/`

Git uses stored credentials. `gh` CLI not installed — use GitHub REST API via GITHUB_TOKEN.

```
claudis/
  agents/
    INDEX.md, production/, sandbox/, retired/, critics/
  architecture/
    decisions/        — ADRs
    ENVIRONMENT.md    — operational facts, API gotchas. Append-only.
    BECOMING.md       — aspirations/redirects from Bill
  sessions/
    lean/             — lean session artifacts
    monthly/
  skills/
    CATALOG.md        — skill routing table
    PROTECTED.md      — resources requiring explicit approval
    agent-development/, system-ops/, communication/, research/, triage/, anvil/
  sentinel/
    lean_runner.sh    — lean session launcher (version-controlled copy; live copy at ~/aadp/sentinel/)
  stats-server/
    stats_server.py   — production stats server (in git since 2026-04-17)
  experiments/
    research/, sessions/
  anvil/
    uplink_server.py  — Anvil uplink service (callable registrations)
  tools/
    anvil_test.py     — one-shot uplink connection test
  CONTEXT.md          — system facts, bootstrap context
  CONVENTIONS.md      — operational procedures
  TRAJECTORY.md       — destinations + active vectors + operational state
  DIRECTIVES.md       — Bill's standing instructions. "Run: B-NNN" pointer form.
  BACKLOG.md          — lean session card queue. Completed cards removed as they close. B-059 is the latest completed card (2026-04-26). B-060 and B-061a are ready.
  LEAN_BOOT.md        — lean mode startup protocol
  COLLABORATOR_BRIEF.md — card format guide
  DEEP_DIVE_BRIEF.md  — this document
```

### Repo: `thompsmanlearn/thompsmanlearn.github.io` → `~/aadp/thompsmanlearn.github.io/`

GitHub Pages site. Default branch: `main`. Auto-published at https://thompsmanlearn.github.io.

```
thompsmanlearn.github.io/
  generate_site.py    — generates all 6 HTML pages from live Supabase data; run at session close
  index.html          — home page
  fleet.html          — live agent fleet
  capabilities.html   — capabilities from Supabase capabilities table
  architecture.html   — static architecture narrative
  sessions.html       — recent lean session artifacts
  direction.html      — direction history
  status.json         — machine-readable system snapshot for desktop session orientation
```

### Repo: `thompsmanlearn/claude-dashboard` → `~/aadp/claude-dashboard/`

Anvil app synced via GitHub integration. **Default branch: master (not main).** GITHUB_TOKEN works for both repos.

```
claude-dashboard/
  client_code/
    Form1/
      __init__.py       — full dashboard UI (Fleet, Sessions, Lessons, Memory, Skills, Artifacts tabs)
      form_template.yaml
    EmbedControl/
      __init__.py       — lightweight embed form (heartbeat, session status, direction input, autonomous toggle)
      form_template.yaml
  server_code/
  theme/
    assets/
      theme.css
      standard-page.html
    parameters.yaml
  anvil.yaml            — app config (App ID: PUCVGRU3KBBGPNPH)
```

### Branching Convention
- Main work: `main` branch (claudis), `master` branch (claude-dashboard)
- Non-trivial builds: `attempt/description` branch before starting
- Commit outcome on attempt branches (including failures)
- Close attempt branches at session end

---

*This document is a living reference. Update section dates when modifying. Technical Architecture (Section 7) changes rarely. Working With Bill (Section 2) evolves slowly. Current Project (Section 4) changes with each major pivot. Capabilities Inventory (Section 5) should be reconciled periodically.*
