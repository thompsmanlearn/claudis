# B-131: Desktop Claude Export

**Session type:** Lean / directive execution
**Date:** 2026-05-17
**Directive:** B-131 — Redesign Desktop Claude Export

---

**Before:** Two export callables existed (`get_working_bundle`, `get_audit_bundle`), both returning sysadmin-flavoured markdown. No export shaped for a collaborator asking "what has the system been thinking about?"

**After:** `get_desktop_bundle()` callable live in `uplink_server.py`. "Export for Desktop Claude" button on Home tab. Export covers: active threads with most recent summary expanded, up to 10 research articles with full URLs, up to 5 session artifacts with Capability delta, unprocessed fragilities from agent_feedback, store counts. Both existing exports unchanged.

---

## Tasks completed

- Read LEAN_BOOT.md startup sequence; executed all 11 boot steps
- Stale-card check: `get_desktop_bundle` absent from uplink_server.py — card not complete, proceeded
- Skills resolved: anvil (0.95), agent-development (0.65); loaded REFERENCE.md and SKILL.md
- Live-state ping: 7 active agents, 0 errors, 1 pending task (agent_build), hardware nominal
- Lesson injection: 5 lessons retrieved; applied `retrieved_at` for research_articles, confirmed TracerProvider init already present
- Branched `attempt/b131-desktop-export` in both repos
- Added `get_desktop_bundle()` to `~/aadp/claudis/anvil/uplink_server.py` (221 lines)
- Added "Export for Desktop Claude" button + `_home_export_desktop_clicked` handler to `Form1/__init__.py`
- Syntax-checked both files; live-tested all 4 queries against real data
- Merged and pushed both repos; restarted aadp-anvil; confirmed uplink connected

## Key decisions

- Placed button in Home tab alongside existing exports (card said "Workspace tab" — no such tab exists; Home is where the other exports live)
- Summary entries queried per-thread (one Supabase call each) rather than batched — simpler, fewer rows, acceptable latency for an occasional export
- Fragility filter: `target_type IN ('agent','skill','capability')` — matches card spec exactly; `processed = false` per PostgREST syntax

## Capability delta

**New:** System can generate a Desktop Claude-shaped export. Bill can paste `get_desktop_bundle()` output into a take-stock conversation and Desktop Claude sees: active thread questions + latest summaries, recent research with full URLs, session capability deltas, known fragilities, store counts.

## Lessons written

1 lesson (see Step 7): UI tab name mismatch between backlog cards and actual Anvil dashboard.

## Branches and commits

| Repo | Branch | Commit |
|---|---|---|
| claudis | attempt/b131-desktop-export | dd616d5 |
| claudis | main (merge) | 8fb3337 |
| claudis | main (trajectory) | 13a72aa |
| claude-dashboard | attempt/b131-desktop-export | 0414d3c |
| claude-dashboard | master (merge) | 730aae2 |

Code commit: 8fb3337 (claudis), 730aae2 (claude-dashboard)
