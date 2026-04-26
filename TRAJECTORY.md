# TRAJECTORY.md

*Short. Read every session. Bill edits Current project, Back burner, and Destinations from Anvil. Claude Code rewrites "Where we are" and Handoff at session close. Handoff caps at 3 entries.*

---

## Current project

**Anvil UI** — primary control surface for monitoring, directing, reviewing. Includes data-scouting agents that write structured Supabase rows (source URLs + rich metadata) for Anvil to surface.

**Where we are:**
- Fleet: 9 active agents (10th — autonomous_growth_scheduler — paused); `webhook_url` column added, 3 on-demand agents populated
- Boot chain: 11 steps — live-state ping (step 9), lesson retrieval from ChromaDB (step 10), execute (step 11)
- Anvil UI complete: 35 callables, all 5 UI gaps closed; dashboard covers fleet, sessions, lessons, memory, skills, artifacts
- ChromaDB loop: boot step 10 confirmed working on LEAN_BOOT path; coverage gap found — step 10 absent from Bill-initiated (bootstrap) sessions. lesson_injector is the primary incrementer (counts 8–30, valid). B-053 queued to close the coverage gap.

**Project arc next:** Fix boot step 10 coverage gap (B-053), then validate the full loop closes across both entry paths. GT-4/GT-5 lesson rewrites pending. After loop is verified end-to-end, move toward ChromaDB semantic retrieval for research pipeline.

---

## Handoff (pick up here)

**2026-04-25:** B-052 complete. Primary finding: boot step 10 (lesson retrieval) absent from all Bill-initiated sessions — coverage gap. lesson_injector accounts for all existing times_applied counts (8–30, valid, Sentinel path). Boot 2/5 GT vs injector 3/5 GT; Haiku expansion is the delta. GT-4 and GT-5 missed by both: lesson write quality issue (titles don't embed near retrieval-quality queries).
- **Next action:** Execute B-053 — add step 10 to bootstrap skill + switch boot query to Haiku expansion. DIRECTIVES.md set to `Run: B-053`.
- **Watch:** After B-053, run a Bill-initiated session and confirm audit_log shows memory_search at boot and close-session step 8 increments at least one lesson.

**2026-04-25:** B-048 complete. LEAN_BOOT is now the single boot path; live-state ping runs at step 9 before execute. developer_context_load deprecated; session_notes archived.

---

## Destinations

**Current:** Bill has a functional interface for monitoring, directing, reviewing the system.

**Next up:** System better leverages ChromaDB.

**Back burner:**
- System organizes and surfaces Bill's personal knowledge (Life OS).
- System detects and recovers from its own failures.
- System receives intentions and autonomously researches, builds, executes.
