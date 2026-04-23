# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet pruned 2026-04-22: 10 active agents, 9 protected
- Boot chain rewritten: CONVENTIONS.md, LEAN_BOOT.md, CONTEXT.md, TRAJECTORY.md
- Anvil backend has 33 callables; UI has known gaps

**Project arc next:** Close UI gaps — work queue detail, error log resolve, site status + regenerate, artifact comments, per-agent invocation.

---

## Handoff (pick up here)

**2026-04-22:** Boot chain restructure. CONVENTIONS.md, LEAN_BOOT.md, CONTEXT.md, TRAJECTORY.md rewritten.
- **Still open:** Close-session skill Step 3 needs update (stop appending trajectory logs; rewrite current state instead). `PROJECT_STATE.md` not yet created — intended to hold project decomposition details outside the boot chain.
- **Then:** Return to Anvil UI — see project arc next.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
