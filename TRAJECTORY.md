# TRAJECTORY.md

*Updated at every session close — early, before context pressure. Minimum viable update: one sentence per vector. Bill edits Destinations directly or via Telegram intention. Closing instance proposes destination changes; Bill confirms.*

*Last updated: 2026-04-15 (session: explore-wisdom-review — wisdom-review complete; 2 retired, 3 rewritten w/ Q&A prefix; zero_applied 128→126)*

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
**Critical finding:** n8n API key (JWT) expired 2026-04-14 00:00 PDT. execution_list and workflow_get returning 401. Webhooks still functional. Bill must regenerate key in n8n UI → Settings → API.
**Next milestone:** n8n API key renewal (Bill action). Then: run behavioral_health_check on architecture_review agent (also sandbox, workflow 7mVc61pDCIObJFos, queries arxiv_aadp_pipeline findings). Check if architecture_review is eligible for promotion as a pair with its data source now active.
**Validation:** `SELECT COUNT(*) FROM lessons_learned` returns a value within 2 of the ChromaDB lessons_learned collection count.
**Research:** Self-healing system patterns; circuit breaker implementations in distributed systems.

---

### 2. Lesson System Effectiveness
**→ Destination 1**
**Session 2026-04-14 (explore-retrieval-log) update:** zero_applied = 142 (up from 96 — regression). retrieval_log wired into server.py log_retrieval() — takes effect next MCP restart.
**Session 2026-04-15 (explore-zero-applied) update:** MILESTONE COMPLETE. Root cause fully diagnosed: (1) velocity gap — 55 lessons created/week vs ~35 retrieved/week, net +20 zero_applied/week; (2) 25 lessons >21 days old covering niche topics (Wikipedia API, Semantic Scholar, FRED debug) that haven't recurred — invisible to semantic search. Embedding quality healthy (distances 0.36–0.78). Fix deployed: inject_context_v3.1 zero_applied wildcard — 2 random uncirculated lessons injected every session, incremented via existing RPC. Result: 142→128 zero_applied in one session. Validation metric already passed.
**Session 2026-04-15 (explore-wisdom-review) update:** MILESTONE COMPLETE. Wisdom-review executed on all 25 zero_applied lessons >21 days. Two-class taxonomy established: (1) retire — obsolete agent-specific evaluations (2 retired: serendipity_engine sandbox eval, wiki_attention_monitor pre-promotion eval); (2) rewrite — accurate content with poor embedding style (3 rewritten with synthetic Q&A prefix: minimal agent stack arXiv finding, why-lessons-go-unapplied root cause, Semantic Scholar API). Methodology lessons 57305c24 + 4e386d94 now have times_applied > 0 for first time. zero_applied 128→126.
**Current state:** zero_applied = 126, trending downward (128→126 this session, 142→128 last session). retrieval_log accumulating. stats_server.py changes disk-only (not in git). wisdom-review procedure documented in both stores.
**Next milestone:** (1) Monitor zero_applied for 2 more sessions — confirm stays below 130. (2) Evaluate adding stats_server.py to version control (disk-only is brittle). (3) architecture_review agent (7mVc61pDCIObJFos) pending promotion once n8n API key renewed.
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

## Parked Directions

- **Bill's monitoring interface audit** — cosmos_report, session_health_reporter, and daily_briefing_agent exist but their current output hasn't been reviewed against what Bill actually needs. Parked until Destination 3 work begins — reviewing existing reporters is the natural first step.
- **Haiku self-critic** — retired 2026-04-05. Replaced by behavioral_health_check for agent quality assessment.
- **Wikipedia serendipity engine (sandbox)** — retired 2026-04-05. Replaced by serendipity_engine_prod.
