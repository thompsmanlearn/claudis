## Goal
Update skill system structure based on design review answers.

## Context
Read sessions/lean/2026-04-15-skill-design-questions.md first.
Design decisions made after reviewing your answers:

1. Merge agent-development + api-integration into one skill 
   (agent-development). Two sections internally, one skill to load.
2. Add "Also triggers when" column to CATALOG.md for problem-state 
   entry points (e.g. "500 error and unclear which layer").
3. Create skills/PROTECTED.md — single source for resources that 
   must not be modified without Bill's approval. LEAN_BOOT.md 
   references it during startup. Do not duplicate in each SKILL.md.
4. Add a new skill: triage — cross-layer diagnostic reasoning 
   when something is broken and you don't know what layer. 
   Distinct from system-ops (which stays as runbooks for known 
   procedures).

Final skill list: agent-development, research, system-ops, 
communication, triage.

## Done when
- api-integration directory removed, its catalog content merged 
  into agent-development
- triage directory created with stub SKILL.md and references/
- CATALOG.md updated: five skills, three columns 
  (Applies when / Provides / Also triggers when)
- skills/PROTECTED.md created with TCA workflow (kddIKvA37UDw4x6e) 
  and any other protected resources you know of from CONTEXT.md
- LEAN_BOOT.md updated to read PROTECTED.md during startup 
  (add as step between current steps 2 and 3)
- Stable backup updated
- All changes committed and pushed
- Session artifact written

## Scope
Touch: ~/aadp/claudis/skills/, LEAN_BOOT.md, CATALOG.md, 
  ~/aadp/prompts/LEAN_BOOT_stable.md, sessions/lean/
Do not touch: DIRECTIVES.md, n8n workflows, MCP server, agents
