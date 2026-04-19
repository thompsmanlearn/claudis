# COLLABORATOR_BRIEF.md

*For fresh Opus 4.6 / Sonnet 4.6 desktop sessions with no prior context. Read this, then ask Bill what help he needs. Updated at lean session close.*

*Last updated: 2026-04-18 (lean session: B-041 skills tab + Opus feedback reconciliation)*

---

## What AADP Is

AADP (Autonomous Agent Development Platform) is a Raspberry Pi 5-based always-on system Bill is building for himself. The long-term intent is that Bill gives the system a high-level intention ("build X") and it autonomously researches, decomposes, builds capabilities, and executes — without Bill directing each step.

Concretely it's three overlapping things:
1. **An agent fleet** — ~25 n8n workflows acting as agents that run on schedule or on-demand
2. **A self-improving system** — agents that detect faults, learn from sessions, and promote each other
3. **A Roblox game dev pipeline** — because that's the specific destination Bill wants to reach (professional-quality Roblox games)

Bill isn't a programmer. Claude Code on the Pi is the primary builder. Bill steers via Telegram, GitHub edits, and directed lean sessions. Desktop Opus/Sonnet is the thinking partner for architecture decisions, directive writing, and work that benefits from stronger reasoning before Claude Code executes.

---

## Hardware and Infrastructure

- **Raspberry Pi 5, 16GB RAM** — always-on, all services run locally
- **n8n 2.6.4** (Docker, localhost:5678) — workflow automation and agent execution
- **Supabase** — primary operational database (hosted, PostgREST API)
- **ChromaDB v0.5.20** (localhost:8000) — semantic memory store, ~214 lessons
- **stats_server.py** (systemd, port 9100) — host process for things n8n can't do: filesystem ops, git, GitHub API proxy, YouTube API calls, ChromaDB queries
- **MCP server** — Claude Code's tooling layer for Supabase, ChromaDB, n8n, audit logging
- **API keys**: `.env` at `~/aadp/mcp-server/.env`

GitHub repo: `thompsmanlearn/claudis` — contains CONTEXT.md, CONVENTIONS.md, TRAJECTORY.md, agent configs, session artifacts.

---

## The Agent Fleet

Agents live in n8n as workflows. Lifecycle: **sandbox → active** (promoted after passing behavioral_health_check) or retired. Managed via `agent_registry` Supabase table and Telegram commands.

Key agents currently active:
- **Telegram Command Agent (TCA)** — protected workflow, the command router. `/approve`, `/reject`, `/run_research_synthesis`, etc. Lean sessions are triggered from Anvil dashboard — `/oslean` removed 2026-04-18.
- **agent_health_monitor** — scans for stale building/sandbox agents, notifies Bill
- **research_synthesis_agent** — weekly synthesis of ChromaDB findings into Supabase
- **arxiv_aadp_pipeline** — pulls recent AI/ML papers, stores findings in ChromaDB
- **architecture_review** (workflow 7mVc61pDCIObJFos) — **active**, confirmed 2026-04-18 (9/10 behavioral health, 100% success rate, runs live reviews against arxiv findings)
- **behavioral_health_check** — quality gate for agent promotion

10 personal-briefing agents paused 2026-04-18 (ai_frontier_scout, coast_intelligence, cosmos_report, daily_briefing_agent, daily_research_scout, heritage_watch, macro_pulse, serendipity_engine_prod, session_report_agent, wiki_attention_monitor). Fleet is lean — active agents are system-critical or pipeline-feeding.

---

## The Lesson System

Every meaningful session produces lessons written to both Supabase (`lessons_learned` table) and ChromaDB (`lessons_learned` collection). Before sessions start, the `lesson_injector` (inject_context_v3.1) does a semantic search against the task description and prepends retrieved lessons as context.

Current state: 214 lessons, `zero_applied` count at ~126 (trending down from 142). A wildcard mechanism injects 2 random uncirculated lessons per session to prevent orphaned lessons from aging out of circulation.

Lean sessions now also receive injected lessons (wired 2026-04-17). Session artifacts should include a "Lessons Applied" section listing lesson IDs that actually influenced decisions — this tracks application rate, not just retrieval rate.

---

## Active Vectors (as of 2026-04-18)

### 1. Fault Detection and Recovery → Destination 4
Health monitoring solid. agent_health_monitor active, store sync gap closed (ChromaDB = Supabase = 214). architecture_review promoted and running live. **Next**: feedback consumer — add agent_feedback summary to morning_briefing; negative patterns → Telegram alert or work_queue item.

### 2. Lesson System Effectiveness → Destination 1
zero_applied at 126, trending down from 142. Wildcard injection covers both autonomous and lean sessions. **Next**: monitor zero_applied for 2 more sessions, confirm stays below 130.

### 3. Autonomous Task Decomposition → Destination 1
Not started. Gap: system schedules tasks autonomously but cannot decompose a high-level Bill intention into concrete subtasks. **Next**: design intention decomposition workflow, write as ADR.

### 4. Roblox Build Pipeline → Destination 2
Lune v0.10.4 installed, .rbxl serialization verified. **Blocked on**: Bill creating a Roblox account + one-time Studio session (Win/Mac) for Universe ID and Place ID. Bill action.

### 5. Anvil Dashboard → Destination 3
B-026–B-041 complete as of 2026-04-18. Dashboard has: Fleet (agent control, feedback), Sessions, Lessons (CRUD + search), Memory (ChromaDB + Supabase), Skills (registry + content viewer). Uplink watchdog running. **Next**: Artifacts tab (B-037/B-038 area — agent_artifacts table has live data from 3 agents); or feedback consumer agent.

---

## How Sessions Work

**Lean mode (current):** Bill edits `DIRECTIVES.md` on GitHub (or via Anvil dashboard Write Directive control), then triggers from the Anvil dashboard (Trigger Lean Session button). `lean_runner.sh` on the Pi: pulls claudis git, resolves the backlog card description, calls lesson injector (25s timeout), prepends context block + lesson tracking instruction, then runs `claude -p --dangerously-skip-permissions --max-turns 200 < prompt_file`. Telegram gets three messages: ack → start → completion/error.

**Autonomous mode (paused as of 2026-04-15):** Sentinel timer fires, Claude Code session starts from `disk_prompt.md`, picks work from TRAJECTORY.md and work_queue, runs for up to 3 hours, closes with artifact + TRAJECTORY.md update. To resume: `sudo systemctl enable aadp-sentinel.timer && sudo systemctl start aadp-sentinel.timer`, then reactivate `autonomous_growth_scheduler` in n8n.

**Session close ritual:** Every session (lean or autonomous) ends by running the close-session skill: write session artifact to `claudis/sessions/`, update `TRAJECTORY.md`, write lessons learned to both stores. The close artifact is a first-class deliverable — without it, the next session starts cold.

---

## Key Conventions

**Confidence-prefixing**: Always signal certainty. "I'm 90% confident", "I think (unverified)", "I know from direct observation." Bill acts on assertions; presenting uncertainty as fact has caused real decision errors.

**Branch-per-attempt**: Git branch before any non-trivial build. Commit even failures, tag `signal:keep` if the failure revealed something non-obvious.

**Would Bill Approve?**: Before external API calls or autonomous actions with visibility, ask this. If uncertain, Telegram and wait.

**Default to attempting**: Sessions that only analyze produce no improvement. Begin tasks under 2 hours that don't require approval.

**Dual-output**: Every agent interaction produces both an immediate output (Telegram, Supabase row) and a system-facing output (session_notes, audit_log, TRAJECTORY.md update).

**Context economy**: Every token in a persistent artifact must change what a future instance does. Don't write aspirational infrastructure (tables that don't exist, commands not yet wired).

**Privacy**: First name (Bill) is fine. No last name, location, employer, or contact info in any artifact.

---

## What Desktop Opus/Sonnet Is Good For

- **Architecture decisions**: ADRs, design tradeoffs, system structure that Claude Code will later implement
- **Directive writing**: Drafting lean session directives for DIRECTIVES.md that are specific enough for Claude Code to execute without back-and-forth
- **Reviewing artifacts**: Reading session outputs, trajectory updates, lesson drafts — giving Bill a second opinion
- **Intention decomposition**: Taking Bill's high-level goals and breaking them into sequenced tasks before they go to Claude Code
- **Thinking partner**: Exploring ideas Bill isn't ready to execute yet, surfacing tradeoffs

The Pi Claude Code instance is resource-constrained (16GB RAM, Raspberry Pi). Complex reasoning that doesn't require file access or tool use is better done here.

---

## What's Working Well

- **Anvil dashboard** — fully operational at phone width. Fleet, Sessions, Lessons, Memory, Skills tabs all live. Primary control surface for lean sessions (directive writing + trigger).
- Lesson system improving (zero_applied 126, down from 142, trend sustained)
- Lean mode with lesson injection covers both lean and autonomous sessions
- Agent health monitoring catches stale builds automatically
- architecture_review agent active — running live reviews against arxiv findings

## What's Still Being Built

- Intention decomposition — the gap between "Bill says build X" and "system executes X autonomously"
- Artifacts tab on dashboard — agent_artifacts table has live data (3 agents writing), tab not yet built
- Feedback consumer agent — agent_feedback table seeded but no agent reads it yet
- Roblox publish pipeline — full path clear, blocked on Bill's one-time Studio setup

---

## How to Be Useful Right Now

Ask Bill what the current directive is. If he's in a lean session, the directive is in `DIRECTIVES.md` (editable on GitHub or via Anvil dashboard). If autonomous mode is running, check TRAJECTORY.md vectors and work_queue. Your job is to either (a) help Bill think through a design decision before it goes to Claude Code, or (b) help Bill write a DIRECTIVES.md entry that is specific, scoped to 2 hours, and leaves the system measurably more capable.

Current open threads: feedback consumer agent, intention decomposition ADR.

---

## How Lean Directives Work (Card Format)

`DIRECTIVES.md` holds the current lean session task. It can be either:

1. **Full prose** — the complete directive written inline. Claude Code reads it and executes directly.
2. **A pointer** — a single line `Run: B-NNN`. Claude Code reads `BACKLOG.md`, finds the matching card, and executes it.

**Context cost:** The full `BACKLOG.md` is loaded when the pointer form is used. Old cards should be archived periodically (see the note at the top of BACKLOG.md) to keep the file small. The archiving practice is load-bearing, not cosmetic.

### Card format (BACKLOG.md)

Cards are numbered sequentially `B-NNN`. Each card follows this structure:

```markdown
## B-NNN: Short descriptive title

**Status:** ready
**Depends on:** B-MMM   ← omit if no dependency

### Goal
One paragraph. What this session should accomplish and why it matters now.

### Context
Background Claude Code needs before starting. Reference prior sessions,
system state, design constraints. Enough to execute without back-and-forth.

### Done when
Bulleted acceptance criteria. Each item should be verifiable:
- Specific file exists at specific path
- curl returns expected response
- Row in Supabase table with expected values
- Commit pushed to main

### Scope
Touch: explicit list of files, tables, workflows Claude Code may modify
Do not touch: explicit list of things that are off-limits this session
```

**Writing good cards:**
- **Goal** answers "what and why" — not "how"
- **Context** answers "what does Claude Code need to know that isn't obvious from the code" — prior decisions, gotchas, related work
- **Done when** must be checkable, not aspirational. "Works correctly" is not a criterion; "curl localhost:9100/healthz returns {\"status\":\"ok\"}" is.
- **Scope** is the guardrail. Explicit "do not touch" prevents scope creep into adjacent systems during execution.
- Two-hour ceiling: if a card can't be completed in one lean session, split it. Incomplete sessions produce no artifact and leave the system in an unknown state.
