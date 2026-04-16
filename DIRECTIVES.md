## Goal
Pull relevant lessons from ChromaDB into skill reference files.

## Context
Read sessions/lean/2026-04-15-skill-system-structure.md first.
All five skills have empty references/lessons.md files. Before we 
draft skill content on desktop, we need the actual operational 
lessons from ChromaDB that belong to each skill.

For each skill, query ChromaDB with 3-5 targeted searches matching 
that skill's "Applies when" and "Also triggers when" descriptions. 
Deduplicate across skills. Write curated results into each skill's 
references/lessons.md with the lesson text and source metadata.

Skills to populate:
- agent-development (include agent AND api/integration topics)
- research
- system-ops
- communication
- triage (cross-layer diagnosis, error tracing, debugging)

Keep each lessons.md to the most actionable lessons — things that 
would change behavior, not general observations. If a lesson is 
trivially obvious, skip it.

## Done when
- All five references/lessons.md files populated with curated 
  ChromaDB lessons
- Each lesson includes enough context to be useful standalone
- No duplicates across skill files
- Session artifact includes: total lessons found, how many kept 
  per skill, any skill areas where ChromaDB had weak coverage
- All changes committed and pushed

## Scope
Touch: ~/aadp/claudis/skills/*/references/lessons.md, 
  sessions/lean/
Do not touch: SKILL.md files, CATALOG.md, LEAN_BOOT.md, 
  PROTECTED.md, n8n workflows, agents
