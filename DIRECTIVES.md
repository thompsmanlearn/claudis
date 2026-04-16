## Goal
Create the skill system directory structure and catalog.

## Context
We're building a skill system so Claude Code can load relevant 
procedural knowledge on demand. Design is documented in the 
April 15 context handoff. This card is scaffolding only — 
structure and stubs, no skill content yet.

## Done when
- Directory exists: ~/.claude/skills/ with five subdirectories:
  agent-development, research, system-ops, api-integration, communication
- Each subdirectory has: SKILL.md (stub with title and empty sections: 
  Purpose, When to Load, Core Instructions, Cross-Skill Warnings, 
  Known Failure Modes) and a references/ directory with empty 
  lessons.md and patterns.md
- CATALOG.md exists at ~/.claude/skills/CATALOG.md with all five 
  entries indexed (skill-name, path, "Applies when", "Provides" — 
  use best judgment for the descriptions based on CONTEXT.md)
- Everything committed and pushed

## Scope
Touch: ~/.claude/skills/ (new), ~/aadp/claudis/sessions/lean/ (artifact)
Do not touch: LEAN_BOOT.md, DIRECTIVES.md, any n8n workflows, 
MCP server, Supabase, agents
