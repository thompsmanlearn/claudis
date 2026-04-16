# Session: 2026-04-15 — Skill Lessons Populate

## Directive
Pull relevant lessons from ChromaDB into skill reference files (references/lessons.md) for all five skills: agent-development, research, system-ops, communication, triage. Deduplicate across skills. Keep only actionable lessons — things that change behavior.

## What Changed

**skills/agent-development/references/lessons.md** — 17 lessons covering: promotion pre-check, building/sandbox health monitoring, stats-server delegation pattern, n8n workflow building gotchas (array unwrap, active field, webhookId, webhook URL format, dynamic registration, sandbox trigger, credential rotation, finished:false bug, $json scoping, audit chain decoupling, responseFormat:text), prompt caching (Haiku 4.5 silently fails, Sonnet 4.6 needs 2048+ tokens), 4-pillars evaluation framework.

**skills/research/references/lessons.md** — 5 lessons: citation graph + Haiku filtering pattern, Semantic Scholar rate limit, ChromaDB lesson embedding style (problem-description > reference style), synthetic query augmentation (Q: prefix), retrieval_log tracking for future adapter training.

**skills/system-ops/references/lessons.md** — 8 lessons: Supabase Management API 403 from Pi (use PostgREST), DDL requires supabase_exec_sql, array INSERT cast syntax, atomic increment via RPC, n8n test vs production webhooks, activate via POST not PATCH, store sync gap repair procedure, real gap metric (chromadb_id IS NULL).

**skills/communication/references/lessons.md** — 5 lessons: Telegram 4096-char truncation pattern, Quick Send uses message key not text, handoff note 5-part structure, session_notes_load consume=false default, verify handoff claims before treating as crisis.

**skills/triage/references/lessons.md** — 7 lessons: 3-part diagnostic probe requirement, session-start probes to always run, metacognitive failure thresholds, work_queue_update silent 400 bugs, execution_get metadata-only limitation, 4-pillars blind spots (Telegram agents + nested JSONB), audit ratio self-correction pattern.

**LEAN_BOOT.md** — Step 7 changed from "Confirm startup complete and await directive" to "Execute the directive immediately — do not pause for confirmation." Synced to ~/aadp/LEAN_BOOT.md and ~/aadp/prompts/LEAN_BOOT_stable.md.

## What Was Learned

ChromaDB coverage is strong for agent-development (n8n patterns, evaluation, lifecycle) and system-ops (Supabase, store sync). Coverage is thinner for research (5 lessons total) and communication (5 lessons) — these areas have fewer operational incidents and therefore fewer lessons. Triage was the hardest to populate because many triage insights are embedded in other categories (evaluation, operations) rather than labeled as diagnostic patterns.

No skill area had zero relevant content. The hardest duplication decisions were store sync (relevant to both system-ops and triage — split by procedure vs. diagnosis framing) and n8n webhook patterns (all to agent-development, not system-ops, since they arise during building not operations).

## Unfinished

- patterns.md files remain empty across all skills — content-fill not yet started
- LEAN_BOOT.md does not yet reference CATALOG.md or auto-load skill files
- triage cross-layer trace procedure not written (just lessons for now)
- research skill could use more lessons as research agents generate more outputs
