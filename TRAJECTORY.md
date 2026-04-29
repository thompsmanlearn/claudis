# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Threads tab live in Anvil (B-072): read-only view between Research and Skills tabs; state filter, collapsed cards, lazy-loaded entries, entry-type icons; 2 test threads seeded
- Thread stack complete (B-070 + B-071 + B-072): schema, callables, Anvil UI all live — ready for B-073 actions
- Fleet: 10 active agents, unchanged; lesson curation stable
- Note: stats-server deploys from ~/aadp/stats-server/ — must cp from claudis/stats-server/ after edits

**Project arc next:** B-073 — Anvil Threads tab actions (annotate, gather, state change, wire agent).

---

## Handoff (pick up here)

**2026-04-29 (B-072):**
- **What I was doing:** B-072 — Anvil Threads tab read view: 198 lines added to Form1/__init__.py; Threads tab between Research and Skills; state filter, collapsed cards, lazy-loaded entries, entry-type icons; 2 test threads + 7 entries seeded.
- **What I learned:** Anvil client Python supports `datetime.fromisoformat()` and `datetime.now(timezone.utc)` for relative timestamps. Edit tool cannot match files with literal `\uXXXX` Python string escapes (JSON encoding converts them to characters before matching) — use Bash+Python for those edits.
- **Continue:** B-073 — Threads tab actions (annotate inline, state change dropdown, wire-agent dropdown, gather button). Design decisions deferred to Bill after seeing the read view.
- **Left better:** Threads fully visible in Anvil for the first time; complete read-view of thread architecture now operational.
- **Usage:** session ~%, weekly ~%

**2026-04-29 (B-071):**
- **What I was doing:** B-071 — Thread write callables: 6 uplink callables + last_activity_at Supabase trigger. Smoke test passed (10/10). Merged and pushed.
- **What I learned:** Supabase trigger for denormalized timestamps (last_activity_at) is the right pattern — putting it in callable code means every future writer has to remember; trigger guarantees it automatically.
- **Continue:** B-072 — Anvil Threads tab read view (get_threads + get_thread_entries callables already available).
- **Left better:** Thread callable layer live; threads are now a usable working surface from code.
- **Usage:** session ~20%, weekly ~%

**2026-04-29 (B-074 Option A):**
- **What I was doing:** B-074 — Adding `git pull --rebase` before first push in close-session.
- **What I learned:** `git pull --rebase` fails with "unstaged changes" if called before staging — rule belongs after staging, not before.
- **Continue:** B-071 — thread write callables.
- **Left better:** close-session v30 now pulls before pushing; divergence failure mode permanently fixed.
- **Usage:** session ~%, weekly ~%

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
