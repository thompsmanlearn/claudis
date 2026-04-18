
Here's a prompt designed to get Claude Code to produce the deep-dive brief by actually inspecting the system rather than writing from memory:

DIRECTIVE: Write DEEP_DIVE_BRIEF.md

Write ~/aadp/claudis/DEEP_DIVE_BRIEF.md — a comprehensive technical reference for the AADP system. This is NOT from memory. Inspect every source before documenting it. This document serves two purposes: (1) onboarding a fresh Opus/Sonnet session that needs deep architectural understanding, and (2) a reconstruction reference if the system needed to be rebuilt from scratch on a fresh Pi.

Method: Read first, write second. For each section below, inspect the actual files, configs, and code before writing. Do not describe what you think exists — describe what you find.

Sections to cover:

1. Infrastructure and services map. Read docker-compose or container configs, systemd units, .env files. Document every running service, its port, how it starts, what it depends on, and where its config lives. Include n8n, ChromaDB, stats_server, MCP server, and anything else you find running.

2. Data flow architecture. Trace the actual request/data paths. When an agent executes, what writes where? When a lesson is stored, what's the chain? When lesson_injector fires, what calls what? When a Telegram command arrives, trace it from /oslean through TCA to lean_runner.sh to session completion. Draw these paths from code, not from assumptions. Use text-based flow diagrams where they help.

3. MCP server. Read the MCP server source. Document every tool it exposes, its parameters, what it does, and which services it calls. This is Claude Code's hands — document them completely.

4. stats_server.py. Read the source. Document every endpoint, what it does, what calls it, and what it calls. Include the /trigger_lean flow, GitHub proxy, ChromaDB query endpoints, and anything else you find.

5. Agent fleet — internals. For each active agent in the registry, open the n8n workflow (via API or filesystem) and document: trigger type, what it reads, what it writes, what external services it calls, and its failure mode. Pay special attention to TCA's command routing.

6. Database schema. Query or read the Supabase schema. Document every table, its columns, what writes to it, and what reads from it. Include agent_registry, lessons_learned, work_queue, audit_log, and any others.

7. ChromaDB collections. Query ChromaDB. Document every collection, its embedding model, document count, metadata schema, and what reads/writes to it.

8. Lesson system end-to-end. Trace the full lifecycle: lesson creation (who writes, what format, dual-store write) → storage (Supabase + ChromaDB sync) → retrieval (inject_context_v3.1 semantic search logic, routing, confidence thresholds) → injection (how context block is assembled and prepended) → tracking (times_applied, zero_applied, the new quality signal). Read the actual n8n workflow and injector code.

9. Session mechanics. Read lean_runner.sh line by line. Read the autonomous mode boot sequence (disk_prompt.md, sentinel timer, scheduler). Document the full lifecycle of both session types including the close ritual.

10. Git and file conventions. Document the claudis repo structure, what lives where, branching conventions, what gets committed by sessions vs. by Bill.

11. Key configuration files. List every file that would need to be recreated to rebuild: .env, systemd units, n8n credential IDs, docker configs, crontabs, MCP config. Don't paste secrets — note where they live and what they're for.

12. Current known gaps, fragilities, and undocumented dependencies. Be honest about what's held together with duct tape, what has no error handling, what would break if a service restarted, and what isn't documented anywhere else.

Format: Prose with code blocks and text diagrams where they clarify. No filler. Every sentence should help someone either understand a decision or rebuild a component. Target completeness over brevity — this is the reference doc, not the quick brief.

Commit to claudis when done.
