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
- **B-119 complete (2026-05-09):** Auto-wiring live. Charter save scores agents via capability_tags; wires best match (≥0.7) or queues build_request in agent_feedback. Telegram notification on wire. Form1 shows result inline.
- Fleet: 9 active + 1 sandbox (thread_research_agent).
- **Next:** B-118 (Gather trigger), then Chapter 4 when Bill decides.

**Project arc next:** System review, then Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-09 (B-119):**
- **What I was doing:** B-119 — auto-wiring. Added `capability_tags text[]` to agent_registry (DDL + seed for all 10 agents). Added `_score_agent()` and `_auto_wire_thread()` to uplink_server.py. `save_charter()` now calls auto-wire after writing charter and returns `{**thread, '_auto_wire': result}`. Form1 unpacks `_auto_wire` and shows inline result. Telegram notify on wire; `agent_feedback.metadata.intent_type='build_request'` if no match. inject_context_v3 returned 500 at boot — used ChromaDB fallback.
- **What I learned:** `agent_feedback` has no top-level `intent` column — intent lives in `metadata` JSONB as `intent_type` (B-086 classifier writes it there). Stats server `/inject_context_v3` may 500 — always have the ChromaDB memory_search fallback ready.
- **Continue:** B-118 (Gather trigger in Anvil UI). Two unprocessed annotations in agent_feedback (grader blind spot, card generator schema). Pending agent_build work_queue item (SpecOps GUI testing, 2026-05-03) — needs build card or discard.
- **Left better:** Charter save now auto-wires agents. No manual intervention needed for threads with matching source preferences.

**2026-05-10 (B-117):**
- **What I was doing:** B-117 — thread research agent with Brave. Built `/run_thread_research` in stats_server.py; wired n8n sandbox workflow; registered thread_research_agent; reclassified /web_search partial in consumer_manifest.json. B-116 (charter UI) was already complete.
- **What I learned:** thread_entries.entry_type has a DB CHECK constraint. stats_server.py has no logger — remove all `log.` calls. Haiku screener works but charter success criteria need to match what web searches actually return.
- **Continue:** Covered by B-119 entry above.
- **Left better:** Brave Search wired for first time. Thread research agent functional in sandbox.

**2026-05-09 (B-113–B-114 + system review prep):**
- **What I was doing:** B-113 (execution disciplines → CONVENTIONS). B-114 (comment-driven card loop). System review: pipeline verified, 5 agents retired, two annotations queued.
- **What I learned:** stats_server doesn't import pathlib at module level. annotate() needs synchronous classify_annotation read for card gen trigger.
- **Continue:** Covered by entries above.
- **Left better:** Full comment→card→execute→grade→export loop live.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
