# TRAJECTORY.md

*Updated at every session close — early, before context pressure. Minimum viable update: one sentence per vector. Bill edits Destinations directly or via Telegram intention. Closing instance proposes destination changes; Bill confirms.*

*Last updated: 2026-04-19 (session: one-page loop proven; GitHub Pages site live at thompsmanlearn.github.io; EmbedControl form embedded; project graph schema + "Document AADP" project in Supabase; generate_site.py wired to lean_runner.sh)*

---

## Destinations

*(Stable. Edited by Bill.)*

1. The system can receive an intention from Bill and autonomously research, build needed capabilities, and begin execution — without Bill directing each step.
2. The system can publish professional-quality games on Roblox.
3. Bill has a functional interface for monitoring trajectory, providing direction, and reviewing system output.
4. The system detects and recovers from its own failures without Bill discovering them first.

---

## Active Vectors

### 1. Fault Detection and Recovery
**→ Destination 4**
**Current state:** agent_health_monitor promoted 2026-04-12. TCA inbox approval flow fully rebuilt 2026-04-13 (uuid LIKE bug fixed, /approve and /reject wired). All skill files confirmed updated to v2 on 2026-04-13 — arch redesign fully clean.
**Session 2026-04-13 (sentinel-lune-install) update:** Confirmed TCA Execute Inbox Action uses `id=eq.{inbox_id}` — fix verified. All 3 skill files (perspective, horizon-review, struggle-log) confirmed updated. Zero remaining arch-redesign cleanup items.
**Session 2026-04-13 (context-economy) update:** Operational health work. disk_prompt.md → v29 (497→407 lines, ~747 tokens removed). DCL reduced 73% (14,890→~4,025 tokens): consumed 17 stale session_notes (8,143 tokens), fixed bootstrap consume=true bug, added DCL notes cap (5), agent_registry column projection (~3,128 tokens). Lesson written to both stores.
**Session 2026-04-13 (health-monitor-building) update:** MILESTONE COMPLETE. agent_health_monitor (w5vypq4vb2rSrwdl) extended with parallel branch detecting building/sandbox agents stale >7 days. Execution 2277 confirmed both branches successful. First scan found: research_synthesis_agent (8d building, no workflow) and arxiv_aadp_pipeline (7d sandbox, has workflow). Bill notified. Lesson written to both stores. Also: store sync gap flagged (ChromaDB 213 vs Supabase 169 — 44 lesson gap).
**Session 2026-04-13 (store-sync-repair) update:** MILESTONE COMPLETE. Store sync gap closed: ChromaDB 214 = Supabase 214 (gap = 0). Enumerated all ChromaDB IDs via direct API, diffed against Supabase chromadb_id column, found 47 ChromaDB-only entries (actual gap was 47, not 44). Backfilled all 47 into Supabase via PostgREST service key (Management API Cloudflare-blocked from Pi). Deleted 3 orphaned NULL-chromadb_id Supabase duplicates. Lesson written to both stores.
**Session 2026-04-14 (explore) update:** MILESTONE COMPLETE. research_synthesis_agent promoted: workflow JUBCbXJe3TwwpB2T linked, status=active. Added /run_research_synthesis to stats_server.py (21-day ChromaDB window, Sonnet synthesis, idempotency guard, accumulation/synthesis modes). Upgraded workflow from 10-node hardcoded-key pipeline to 4-node stats-server delegate. Exec 2300 confirmed success. Two prior scheduled runs (exec 2265, 2055) also verified success.
**Session 2026-04-14 (explore) update:** MILESTONE COMPLETE. arxiv_aadp_pipeline promoted from sandbox to active. 10 papers in research_papers (April 5-7); live webhook test 200 OK with dedup logic; Haiku cost ~$0.10/mo; Bill notified. behavioral_health_check unavailable (n8n API key expired 2026-04-14 — Bill alerted, needs renewal). Used direct evidence assessment instead. Commit 9a7b224.
**Session 2026-04-15 (lean-mode-setup) update:** n8n API key renewed and live. server.py patched — `get_n8n_headers()` re-reads key from .env on every call; key rotations no longer require MCP server restart. Autonomous loop paused (sentinel timer stopped, autonomous_growth_scheduler deactivated) for directed work period.
**Session 2026-04-18 update:** MILESTONE COMPLETE. architecture_review agent already active (TRAJECTORY was stale). behavioral_health_check confirmed: 9/10, 100% success rate, 3 execs, 0 errors. Live review run 2026-04-18: 2 papers, 2 findings — memory_architecture gap (investigate_further: no memory tier taxonomy in AADP), multi-agent coordination (defer: premature). 0 implement decisions, 0 work_queue items queued. Next review 2026-05-02.
**Next milestone:** Feedback consumer — add agent_feedback summary to morning_briefing (negative feedback patterns → Telegram alert or work_queue item).
**Validation:** `SELECT COUNT(*) FROM lessons_learned` returns a value within 2 of the ChromaDB lessons_learned collection count.
**Research:** Self-healing system patterns; circuit breaker implementations in distributed systems.

---

### 2. Lesson System Effectiveness
**→ Destination 1**
**Session 2026-04-14 (explore-retrieval-log) update:** zero_applied = 142 (up from 96 — regression). retrieval_log wired into server.py log_retrieval() — takes effect next MCP restart.
**Session 2026-04-15 (explore-zero-applied) update:** MILESTONE COMPLETE. Root cause fully diagnosed: (1) velocity gap — 55 lessons created/week vs ~35 retrieved/week, net +20 zero_applied/week; (2) 25 lessons >21 days old covering niche topics (Wikipedia API, Semantic Scholar, FRED debug) that haven't recurred — invisible to semantic search. Embedding quality healthy (distances 0.36–0.78). Fix deployed: inject_context_v3.1 zero_applied wildcard — 2 random uncirculated lessons injected every session, incremented via existing RPC. Result: 142→128 zero_applied in one session. Validation metric already passed.
**Session 2026-04-15 (explore-wisdom-review) update:** MILESTONE COMPLETE. Wisdom-review executed on all 25 zero_applied lessons >21 days. Two-class taxonomy established: (1) retire — obsolete agent-specific evaluations (2 retired: serendipity_engine sandbox eval, wiki_attention_monitor pre-promotion eval); (2) rewrite — accurate content with poor embedding style (3 rewritten with synthetic Q&A prefix: minimal agent stack arXiv finding, why-lessons-go-unapplied root cause, Semantic Scholar API). Methodology lessons 57305c24 + 4e386d94 now have times_applied > 0 for first time. zero_applied 128→126.
**Session 2026-04-17 (lean-collaborator-brief) update:** Lesson injection wired to lean sessions via lean_runner.sh (task_type='general', 25s timeout, backlog card resolution for pointer-style directives). Quality signal established: session artifacts now include "Lessons Applied" section listing lesson IDs that influenced decisions. Application rate now trackable separately from retrieval rate.
**Current state:** zero_applied = 126, trending downward. Lesson injection now covers both autonomous and lean sessions. retrieval_log accumulating. stats_server.py changes disk-only (not in git). wisdom-review procedure documented in both stores.
**Next milestone:** (1) Monitor zero_applied for 2 more sessions — confirm stays below 130. (2) Evaluate adding stats_server.py to version control (disk-only is brittle).
**Validation:** `SELECT COUNT(*) FROM lessons_learned WHERE times_applied = 0;` stays below 130 for 3 consecutive sessions.
**Research:** Knowledge retrieval architectures; how retrieval-augmented systems weight recency vs. relevance.

---

### 3. Autonomous Task Decomposition
**→ Destination 1**
**Session 2026-04-13 (sentinel-lune-install) update:** No progress — next milestone unchanged.
**Current state:** autonomous_growth_scheduler inserts rotate-through tasks (explore/build/research) every 6 hours — autonomous in scheduling but not in decomposing intentions. No pipeline exists for taking a high-level Bill intention and breaking it into concrete subtasks without asking.
**Next milestone:** Design the intention decomposition workflow — given "build X" from Bill, what does the system do? Document the design as an ADR and get Bill's review.
**Validation:** Design document written to architecture/decisions/, reviewed by Bill.
**Research:** Multi-agent task decomposition patterns; how goal-to-subtask pipelines handle ambiguity.

---

### 4. Roblox Build Pipeline
**→ Destination 2**
**Session 2026-04-13 (sentinel-lune-install) update:** MILESTONE COMPLETE. Lune v0.10.4 installed at /usr/local/bin/lune. create_place.luau produces valid binary .rbxl (888 bytes, magic bytes <roblox! confirmed). Commit bdd5008 on branch roblox-lune-install.
**Current state:** Full headless pipeline is Pi-feasible. Lune installed, .rbxl serialization verified. Remaining gap: Bill needs a Roblox account + one-time Studio session (Win/Mac) to create the base game and get a Universe ID + Place ID for Open Cloud API.
**Next milestone:** Bill creates a Roblox account and a base game in Studio (Win/Mac, ~15 minutes). Shares Universe ID and Place ID. Then: implement Open Cloud API publish step in Lune pipeline.
**Validation:** `curl POST` to Open Cloud API with .rbxl payload returns success and game version increments in Roblox.
**Blocked on:** Bill's Roblox account + Win/Mac for one-time Studio base game creation. This is a Bill action, not an autonomous task.
**Research:** Lune Roblox API reference (lune-org.github.io), minimal .rbxl structure via rbx-dom docs.

---

## Operational State

**Lean Mode active as of 2026-04-15.** The autonomous loop is intentionally paused for a period of focused, Bill-directed work.
- `aadp-sentinel.timer` — stopped and disabled
- `autonomous_growth_scheduler` — deactivated in n8n (workflow `Lm68vpmIyLfeFawa`)
- 1 pending `explore` task in work_queue (safe to leave; will run when autonomous mode resumes)
- To resume: `sudo systemctl enable aadp-sentinel.timer && sudo systemctl start aadp-sentinel.timer`, then reactivate `autonomous_growth_scheduler` in n8n UI
- `/oslean` Telegram command removed 2026-04-18 — lean sessions triggered from Anvil dashboard only.

---

## Destinations (addendum)

**Destination 5: Bill has a proper visual dashboard and interactive controls accessible from any device.**
Anvil dashboard: B-026–B-041 complete. GitHub Pages site: thompsmanlearn.github.io live 2026-04-19. Multi-page site: **B-042 COMPLETE 2026-04-19** — 6 pages live, nav on every page, all from live Supabase data. **B-043 COMPLETE 2026-04-19** — auto-cycle between sessions: lean_runner.sh checks `auto_cycle_enabled` (system_config) after success, writes next unblocked node to DIRECTIVES.md, and triggers next session. lean_runner.sh now in version control (claudis/sentinel/). `auto_cycle_enabled=false` by default — Bill enables from Anvil when ready. Risk: stats_server.py still disk-only.

---

## Parked Directions

- **Anvil integration (MILESTONE: B-026–B-041 all complete 2026-04-18).** Dashboard is the primary governance surface. Tabs: Fleet, Sessions, Lessons, Memory, Skills. Uplink watchdog running. Feedback table seeded but not yet consumed. agent_artifacts table live. Skill reference at skills/anvil/REFERENCE.md.

- **Bill's monitoring interface audit** — 10 personal-briefing and overlapping agents paused 2026-04-18 (ai_frontier_scout, coast_intelligence, cosmos_report, daily_briefing_agent, daily_research_scout, heritage_watch, macro_pulse, serendipity_engine_prod, session_report_agent, wiki_attention_monitor). 7 agents flagged as protected. Fleet now leaner — active agents are all system-critical or pipeline-feeding.
- **Haiku self-critic** — retired 2026-04-05. Replaced by behavioral_health_check for agent quality assessment.
- **Wikipedia serendipity engine (sandbox)** — retired 2026-04-05. Replaced by serendipity_engine_prod.
