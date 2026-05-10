# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Lean mode: sentinel timer disabled, `autonomous_growth_scheduler` deactivated. Desktop scopes cards; Claude Code executes.
- **Chapter 1 complete (B-084–B-093):** Foundation patterns.
- **Chapter 2 complete (B-094–B-101):** Research orchestrator.
- **Chapter 3 complete (B-106–B-112):** Cleanup + ChromaDB leverage.
- **Post-chapter additions (B-113–B-114):** Execution disciplines in CONVENTIONS. Comment-driven card loop live — B-115-cmt executed (first comment-generated card complete).
- **System review complete (2026-05-09):** B-115-cmt executed, pipeline verified end-to-end, 5 agents retired, "Document AADP on the Site" project closed. Two revision findings queued as annotations: grader blind spot for data-only cards, card generator missing schema context.
- Thread architecture complete (B-070–B-083): all live.
- **B-117 complete (2026-05-10):** Thread research agent with Brave live in sandbox. /web_search first wired. 14 findings + 3 cycle_summaries written to test thread. B-116 (charter UI) was already complete.
- Fleet: 9 active + 1 sandbox (thread_research_agent).
- **Next:** B-118 (Gather trigger), B-119 (auto-wiring), then Chapter 4 when Bill decides.

**Project arc next:** System review, then Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-10 (B-117):**
- **What I was doing:** B-117 — thread research agent with Brave. Built `/run_thread_research` in stats_server.py; wired n8n sandbox workflow; registered thread_research_agent; reclassified /web_search partial in consumer_manifest.json. B-116 (charter UI) was already complete — dependency pre-satisfied. Expanded thread_entries.entry_type CHECK constraint to include `finding` and `cycle_summary`. Added Form1 rendering for both types.
- **What I learned:** thread_entries.entry_type has a DB CHECK constraint — not just a code-level validation set. Adding new entry types requires both DDL and uplink_server._THREAD_ENTRY_TYPES update. stats_server.py has no logger — remove all `log.` calls, failures are silent. Haiku screener works correctly but charter success criteria need to match what web searches actually return — broad academic criteria screen out most web results.
- **Continue:** B-118 (Gather trigger in Anvil UI). B-119 (auto-wiring). Two unprocessed annotations in agent_feedback (grader blind spot, card generator schema). Pending agent_build work_queue item (SpecOps GUI testing, 2026-05-03) needs build card or discard.
- **Left better:** Brave Search wired for first time. Thread research agent functional in sandbox with real charter + real findings.

**2026-05-09 (B-113–B-114 + system review prep):**
- **What I was doing:** B-113 (Karpathy execution disciplines → CONVENTIONS + close-session scope check). B-114 (comment-driven card loop — /generate_card_from_comment Sonnet endpoint, annotate() trigger, /export_comment_driven_results, Fleet tab "✏️ Comment work" button + per-agent indicator, USERS_MANUAL.md). Also: DEEP_DIVE_BRIEF Section 7/8 accuracy pass, removed Fleet thumbs-up/down.
- **What I learned:** stats_server doesn't import pathlib at module level — use os.path. annotate() was fire-and-forget for classify_annotation; changed to synchronous read so card gen trigger can check result.
- **Continue:** Covered by system review entry above.
- **Left better:** Full comment→card→execute→grade→export loop live. Execution disciplines codified.

**2026-05-08 (Chapter 3: B-106–B-112):**
- **What I was doing:** Chapter 3 — cleanup + ChromaDB leverage. B-106 (retire context_engineering_research), B-107 (auto-cycle approval gate), B-108 (lean_runner.sh symlink), B-110 (session_memory verified + backfilled), B-111 (/lesson_stats), B-109 (curation pass — 10 candidates, greeter_bot retired), B-112 (doc wrap).
- **What I learned:** inject_context_v3 already queries session_memory — the gap was missing close-session writes. agent_registry has no last_used column. system_config value is JSONB. live uplink_server.py runs from claudis directly.
- **Continue:** B-113 and B-114 executed same day. See above entries.
- **Left better:** ChromaDB leverage patterns established; session_memory backfilled; /lesson_stats live.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
