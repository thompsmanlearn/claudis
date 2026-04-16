# DIRECTIVES.md
*Bill's standing instructions for the current work period. Claude Code reads this at every lean session start after git pull. Claude Code does not modify this file unless Bill explicitly asks.*



## Goal
Smoke test the lean session control loop.

## Context
This is the first real test of the lean boot system. 
Nothing needs to be built or changed.

## Done when
- Startup sequence completed (git pull, sync, read all foundation docs)
- MCP server responds (run any simple tool call — e.g. list work queue)
- Session artifact written to sessions/lean/ and pushed to GitHub
- Artifact confirms: which docs were read, whether MCP responded, 
  any issues encountered

## Scope
Touch: sessions/lean/ (artifact only)
Do not touch: everything else
---

