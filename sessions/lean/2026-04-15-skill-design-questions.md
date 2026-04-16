# Session: 2026-04-15 — Skill Design Questions

## Directive
Answer seven design questions about the skill system before writing skill content. Read the
scaffold session artifact, examine CATALOG.md, and reason from direct operating experience.

## What Changed
- No files modified. This was a thinking session.
- Answers written below; all counter-proposals explicitly stated.

## What Was Learned

### Q1: Is "Applies when / Provides" enough for reliable skill selection?
No. Current descriptions match explicit task names but miss implicit triggers (mid-task
problem states). Need a third column — "Also triggers when" — covering diagnostic entry
points like "execution returns 500 and you can't isolate the layer." Without it, the right
skill won't load during the cases that cost the most.

### Q2: Can you judge relevance from 1-2 sentence descriptions?
Yes, if sentences are concrete about scope and allow ruling a skill out. Current failure:
communication's "any artifact Bill will read" is too broad — it matches almost everything
and will cause spurious loads. Fix: narrow to distinctive cases ("Telegram alerts and session
artifacts where format errors reach Bill directly").

### Q3: Are five skills the right boundaries?
Counter-proposal: four skills, with one split handled internally.

- **Merge agent-development + api-integration.** Every agent task requires Supabase UPSERT,
  n8n workflow ops, and Claude API calls. The boundary isn't real at this system's scale.
  One skill with two sections (building agents / API patterns) serves better than two skills
  loaded simultaneously every time.

- **Split system-ops internally.** Reactive diagnosis (triage logic) and proactive ops
  (runbook execution) are different cognitive modes. Don't make them separate skills, but
  label sections explicitly so the right mode is entered.

Result: agent-development (merged), research, system-ops (internally split), communication.

### Q4: What's the practical context cost of loading a skill?
~600-1000 tokens per skill at medium fill density. Negligible against 200K context. The real
cost is loading the wrong skill due to overlapping selection criteria — 1600 tokens of noise
per false match. Implication: fill skills densely. Underfilling forces improvisation, which
is what the skill system exists to prevent.

### Q5: What work types aren't covered by the five?
Three gaps:
1. **Cross-layer diagnosis** — tracing a failure from n8n execution → MCP tool → Supabase
   row. Not system-ops (services are healthy), not api-integration (tools work individually).
   This is the most cognitively expensive recurring task and has no skill home.
2. **Data integrity / store management** — consistency checks between ChromaDB and Supabase,
   orphan enumeration, backfill patterns. Recurred in store-sync-repair session; no home.
3. **Lean session scoping** — interpreting DIRECTIVES.md, deciding what to defer, applying
   the "2 hours / no approval needed" rule. Covered implicitly by LEAN_BOOT behavioral
   conventions but not surfaced as a skill.

### Q6: What do I do now when I lack needed knowledge mid-task?
Four behaviors, in rough order of frequency:
1. Read the relevant file/code directly — reliable but slow (discover vs. recall)
2. Query error_log or lessons_learned semantically — uneven hit rate (zero_applied problem)
3. Proceed on a guess with confidence-prefix uncertainty marking
4. For tool-specific gotchas (n8n empty array, Supabase UPSERT quirks) — rely on project
   memory, but retrieval isn't guaranteed

Failure mode: proceeding confidently on a pattern with forgotten edge cases. Skills should
prioritize "non-obvious things you will get wrong" — that's the highest-value content.

### Q7: What institutional knowledge matters most in autonomous mode?
Priority order:
1. **What must not be touched without approval.** Protected resources list (TCA workflow
   kddIKvA37UDw4x6e, etc.) currently scattered across LEAN_BOOT + CONTEXT. Should be
   surfaced at the top of every skill via Cross-Skill Warnings.
2. **Escalation ladder when blocked.** No explicit protocol: retry once → write error_log
   → Telegram alert (if Telegram-touching work) → write session note and stop. Currently
   "use judgment," which produces inconsistent behavior.
3. **Lean vs. sentinel mode behavioral differences.** Known but re-derived each session.
   A single block in the skill or a lean-mode preamble section would stop the re-derivation
   cost.
4. **Cost structure.** Which operations are expensive (Claude API calls, external APIs) vs.
   free (Supabase reads, ChromaDB queries). Pi budget constraints are real; skills should
   surface cost warnings prominently.

## Unfinished
- SKILL.md content not yet written (by design — this session answered prerequisites).
- Counter-proposals (merge agent-dev+api-integration, add "Also triggers when" column,
  cross-skill protected-resources warnings) need Bill review before acting.
- No mechanism yet for auto-loading skills into sessions.
