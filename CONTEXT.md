# CONTEXT.md

*System facts. Read after CONVENTIONS.md at session start.*

## Hardware

Raspberry Pi 5, 16GB RAM, always-on.

## Services

| Service | Location | Role |
|---|---|---|
| n8n 2.6.4 | localhost:5678 (Docker) | Workflow automation |
| Supabase | Remote SaaS | Operational database |
| ChromaDB v0.5.20 | localhost:8000 (Docker) | Semantic memory |
| Stats server | localhost:9100 (systemd: aadp-stats) | Filesystem ops, git, GitHub API proxy |
| Anvil uplink | systemd: aadp-anvil | Outbound websocket to Anvil cloud |

Credentials: `~/aadp/mcp-server/.env`.

## MCP namespaces

- `mcp__aadp__*` — core AADP tools
- `mcp__claude_ai_Gmail__*`, `mcp__claude_ai_Google_Calendar__*` — Google (auth may be pending)

Load tool schemas via ToolSearch before calling.

## Repo

GitHub: `thompsmanlearn/claudis` → `~/aadp/claudis/`
