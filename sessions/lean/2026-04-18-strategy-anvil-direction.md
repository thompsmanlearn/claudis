# Session: 2026-04-18 — strategy-anvil-direction

## Directive
Strategic session with Bill. No build. Topics: system framing, platform integrations, Anvil direction, briefing document gaps, card execution model.

## What Changed
- **BACKLOG.md** — B-026 (Bill: Anvil setup) and B-027 (Claude Code: uplink service + dashboard) added
- **DIRECTIVES.md** — set to `Run: B-026`
- **TRAJECTORY.md** — Destination 5 ratified (Anvil as UI layer); Anvil entry moved from evaluating to active; session timestamp updated
- **DEEP_DIVE_BRIEF.md** — Section 13 (Anvil) added; card format and DIRECTIVES pointer system added to Section 10; stats_server fragility note corrected (now in git)
- **COLLABORATOR_BRIEF.md** — card format guide added

## Key Decisions Made

**Unreal replaces Roblox.** Creative production via Unreal Engine is the platform direction. Game dev is one example domain — system should remain open to any creative or productive domain Bill pursues.

**Telegram deprioritized.** Unreliable, poor desktop reading/typing experience. Anvil replaces it as the primary interface layer. Telegram may return but is back-burner.

**Anvil is the next major integration.** Not just a dashboard — the full interface layer. Phone capabilities (camera, geolocation, push) make it a new input channel, not just an output surface. Camera routes visual input directly into agent pipelines. Geolocation enables context-aware agents.

**Sequential card execution pattern established.** Cards can depend on each other (Depends on: B-NNN). Claude Code closes between builds. Bill checkpoints between cards before the next session launches — not automatic advancement.

**Opus builder's brief is a needed document.** COLLABORATOR_BRIEF.md tells Opus what the system is but not what's reachable and what 2-hour scope looks like. A shorter focused document for card-writing sessions is needed. Not built this session — flag for future card.

## Platform Integrations Identified
Beyond Anvil, platforms worth evaluating for future integration:
- **Replicate** — GPU/generative model API. Image, video, audio generation. No Pi infrastructure. Directly enables asset generation for creative pipelines.
- **Discord** — webhooks, bots, voice. Overlaps with creative/game dev community.
- **Notion** — structured knowledge base with API. Longer-form documents that don't fit ChromaDB.
- **Home Assistant** — ambient context (home/away, time of day, device state) if smart home exists.
- **Anthropic usage API** — real token cost tracking per agent/session type. Enables real tradeoffs on model selection.
- **Publishing platforms** (Itch.io, Unreal marketplace, etc.) — autonomous artifact publishing once creative pipelines mature.

## System Framing Refined
Best description: **a personal intelligence infrastructure that compounds in Bill's direction.** Each session, each lesson, each capability added makes the next thing easier and more aligned with what Bill actually wants. Goal: Bill states an intention, system does most of the work of executing it, Bill directs and judges quality. The Pi is a compute constraint, not a concept constraint.

The most important missing capability: **intention decomposition** (Vector 3, not started). System executes well but cannot decompose a novel goal into sequenced subtasks autonomously. All other vectors depend on this eventually.

## What's Next
B-026: Bill creates Anvil account, enables Uplink, adds key to .env, confirms Pi connects. This is a Bill action — no Claude Code session needed. When done, trigger B-027.

## Lessons Applied
None pre-loaded were directly relevant to strategic conversation.
