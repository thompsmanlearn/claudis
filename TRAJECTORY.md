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
- **Thread research pipeline bugs fixed (2026-05-10):** Duplicate findings blocked (cross-cycle dedup via existing source URLs). Memory consultation now fetches charter question from DB (authoritative). thread_research_agent webhook activated; non-200 warning added to gather trigger.
- Fleet: 9 active + 1 sandbox (thread_research_agent).
- **Next:** B-118 (Gather trigger), then Chapter 4 when Bill decides.

**Project arc next:** System review, then Chapter 4 when Bill decides.

---

## Handoff (pick up here)

**2026-05-10 (thread research pipeline bugs):**
- **What I was doing:** Fixed three bugs in the thread research pipeline: (1) duplicate findings — `run_thread_research` now fetches existing finding source URLs before writing, skips cross-cycle dupes; (2) memory consultation wrong query — `consult_memory` now fetches `threads.charter['question']` from DB when thread_id given, ignoring caller-supplied question; (3) gather trigger silent failure — thread_research_agent workflow was inactive, webhook returned error with zero nodes running, swallowed silently; activated workflow + docker restart n8n + added non-200 warning log in `_fire()`.
- **What I learned:** n8n sandbox workflows deactivated after testing still have webhook_url in agent_registry — POST to inactive production webhook fails immediately with no nodes running. fire-and-forget webhook callers must check response status. `consult_memory` must own query derivation; callers can't be trusted to pass the right question.
- **Continue:** B-118 (Gather trigger in Anvil UI). Two unprocessed annotations in agent_feedback. Pending agent_build work_queue item (SpecOps GUI, 2026-05-03).
- **Left better:** Thread research pipeline now correctly deduplicates, uses authoritative charter question, and surfaces webhook failures.

**2026-05-09 (B-119):**
- **What I was doing:** B-119 — auto-wiring. Added `capability_tags text[]` to agent_registry (DDL + seed for all 10 agents). Added `_score_agent()` and `_auto_wire_thread()` to uplink_server.py. `save_charter()` now calls auto-wire and returns `{**thread, '_auto_wire': result}`. Telegram notify on wire; `agent_feedback.metadata.intent_type='build_request'` if no match.
- **What I learned:** `agent_feedback` intent lives in `metadata.intent_type` JSONB (B-086 pattern). Stats server `/inject_context_v3` may 500 — ChromaDB fallback is reliable.
- **Continue:** Covered by entry above.
- **Left better:** Charter save auto-wires agents.


---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
