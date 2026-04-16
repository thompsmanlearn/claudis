## Goal
Move skills into the repo and fix LEAN_BOOT auto-start.

## Context
Two issues from the scaffold session:
1. ~/.claude/skills/ is outside the claudis repo — not versioned, 
   not backed up, not visible on GitHub. Move to ~/aadp/claudis/skills/.
2. LEAN_BOOT.md doesn't trigger the startup sequence automatically 
   when read. The instruction needs to make clear: reading this file 
   IS the trigger — run the sequence immediately, don't wait.

## Done when
- Skills directory moved to ~/aadp/claudis/skills/
- CATALOG.md paths updated to match new location
- LEAN_BOOT.md updated so reading it triggers startup sequence 
  without manual nudge
- Stable backup updated: cp LEAN_BOOT.md to 
  ~/aadp/prompts/LEAN_BOOT_stable.md
- All changes committed and pushed

## Scope
Touch: ~/aadp/claudis/skills/, LEAN_BOOT.md, CATALOG.md, 
  ~/aadp/prompts/LEAN_BOOT_stable.md, sessions/lean/ (artifact)
Do not touch: DIRECTIVES.md, n8n workflows, MCP server, agents## Goal
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
