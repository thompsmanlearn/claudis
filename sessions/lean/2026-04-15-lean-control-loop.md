# Session: 2026-04-15 — lean control loop setup

## Directive
Establish a lean-mode control loop using the GitHub repo as the communication surface. Three deliverables: DIRECTIVES.md (Bill's control channel), sessions/lean/ artifact directory, and LEAN_BOOT.md updated with startup sequence, behavioral conventions, and session close format.

## What Changed
- `~/aadp/claudis/DIRECTIVES.md` — created. Bill's standing instructions file. Claude Code reads this at every lean session start after git pull. Never modified by Claude Code unless Bill explicitly asks.
- `~/aadp/claudis/sessions/lean/.gitkeep` — directory created for lean session artifacts.
- `~/aadp/LEAN_BOOT.md` — updated in place (not git-tracked; lives on Pi only). Added:
  - Startup Sequence (5 steps: git pull → DIRECTIVES → CONTEXT → TRAJECTORY → ready)
  - Behavioral Conventions (8 one-liners: confidence-prefix, branch-per-attempt, Telegram format, Would Bill Approve, default to attempting, dual-output, context economy, privacy)
  - Session Close section with artifact format and commit message convention
  - Expanded infrastructure tables (session_notes, system_config, capabilities, agent_templates collection)
  - Stats server purpose clarified (filesystem ops, git, GitHub API proxy, /run_research_synthesis)
  - Protected workflow noted (Telegram Command Agent kddIKvA37UDw4x6e)
  - Gmail and Google Calendar MCP namespaces added
- Committed and pushed DIRECTIVES.md + sessions/lean/.gitkeep to main (commit ecd5592).

## What Was Learned
LEAN_BOOT.md was accurate but thin — it described the scaffolding without operational knowledge. A lean-mode instance lacking CONTEXT.md and TRAJECTORY.md can use all tools but can't place requests in context, doesn't know active work, and is missing conventions that directly change its behavior (confidence-prefixing, Telegram format, the "Would Bill Approve?" test). The startup sequence fix closes this gap in ~4 tool calls at session start.

LEAN_BOOT.md is not git-tracked — it lives only on the Pi at ~/aadp/. Changes to it have no version history. Low priority for now but worth noting.

## Unfinished
Nothing from this directive. Pending from TRAJECTORY.md: architecture_review agent (workflow 7mVc61pDCIObJFos) is next candidate for promotion now that n8n API key is live.
