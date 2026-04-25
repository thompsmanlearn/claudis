# Session: 2026-04-25 — Anvil UI Gap Closure + ChromaDB Loop

**Type:** Bill-initiated lean session
**Directive:** B-049 (Create PROJECT_STATE.md), then open-ended Anvil UI + ChromaDB improvements

---

## Tasks Completed

1. **B-049** — Created `PROJECT_STATE.md` at `~/aadp/claudis/PROJECT_STATE.md`. Full callable inventory (33→35), UI gap list, component map. Updated existing stale file (it already existed from a prior session with good structure).
2. **Artifact comments** — Added `comment_box` TextBox to artifact expand view; wired to `rate_artifact(id, rating, comment)` callable. Input disables after submit.
3. **Error log resolve** — Added `resolve_error_log(error_id, notes=None)` callable to uplink_server.py. Added notes TextBox + Resolve button to error log cards in Memory tab.
4. **Work queue detail** — Updated `get_work_queue` to fetch `input_data`, `created_by`, `assigned_agent`; fixed sort order to `priority.asc`. Replaced flat labels with expandable cards in `_load_queue`.
5. **Per-agent invocation** — Added `webhook_url` column (nullable text) to `agent_registry`. Populated for `agent_health_monitor`, `lesson_injector`, `session_health_reporter`. Added `invoke_agent` callable. Added ▶ Run button to agent cards (active agents with webhook_url only).
6. **ChromaDB boot retrieval** — Added step 10 to LEAN_BOOT.md: query `lessons_learned` with directive keywords, surface top 5, apply relevant ones, track IDs for `times_applied` increment at close.
7. **Lesson write quality** — Updated close-session Step 7 with quality checklist (title must state pattern not instance, trigger condition required, no session-specific refs, no duplicates, keywords in body). Added supabase_id capture, ChromaDB metadata with supabase_id, link-back UPDATE.
8. **times_applied tracking** — Updated close-session Step 8 to reference boot-tracked lesson IDs explicitly; SQL uses Supabase ID not title.

---

## Key Decisions

- **Per-agent invocation via stored webhook_url** — rejected dynamic derivation from n8n workflow nodes (fragile). Stored URL is explicit, readable, and doesn't break on node rename.
- **Boot retrieval over mid-session tracking** — mid-session `times_applied` tracking adds bookkeeping overhead during execution that outweighs the value. Boot-time retrieval closes the main gap; revisit if `never_applied` stays high.
- **PROJECT_STATE.md not added to REFERENCE.md load chain** — discussed but deferred. Only valuable when maintained; adding the REFERENCE.md instruction requires also ensuring close-session updates it. Left as human-readable reference for now.
- **Stale directive fallback not built** — discussed, agreed it's worth doing. Not implemented this session; next session should pick it up if DIRECTIVES.md is updated with a card for it.

---

## Capability Delta

**What the system can do now that it couldn't at session start:**
- Trigger on-demand agents (agent_health_monitor, lesson_injector, session_health_reporter) directly from Anvil dashboard
- Resolve error log entries with notes from Anvil dashboard
- See work queue task payloads, creator, and assigned agent inline in Fleet tab
- Add comments when rating agent artifacts
- Surface relevant lessons from ChromaDB before executing each session directive
- Write lessons with quality structure that improves semantic retrieval

---

## Lessons Written

4 lessons (see Step 7 below)

---

## Branches

**claudis:** attempt/boot-lesson-retrieval, attempt/error-log-resolve, attempt/per-agent-invocation, attempt/work-queue-detail — all merged to main, deleted.
**claude-dashboard:** attempt/artifact-comments, attempt/error-log-resolve, attempt/per-agent-invocation, attempt/work-queue-detail — all merged to master, deleted.

---

## Commit Hashes (claudis main)

- `fd427b8` — B-049: create PROJECT_STATE.md
- `5318520` — feat: add resolve_error_log callable
- `874601b` — feat: get_work_queue expanded fields + sort fix
- `dd4110d` — feat: add invoke_agent callable; webhook_url in get_agent_fleet
- `e7f0412` — docs: PROJECT_STATE.md gap closure updates
- `c72f2e0` — docs: close work queue detail gap
- `3fd8a51` — docs: PROJECT_STATE.md all gaps closed, schema additions
- `67c60ca` — feat: boot lesson retrieval step 10
- `6eabb11` — close-session: TRAJECTORY.md update
