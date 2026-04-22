# PROTECTED.md — Resources Requiring Explicit Approval Before Modification

Do not modify any resource listed here without Bill's explicit approval in the current session.
When in doubt, ask before touching.

---

## Load-Bearing Agents — do not pause

`agent_registry.protected = true` is the source of truth. Do not duplicate the list here.

```sql
SELECT agent_name FROM agent_registry WHERE protected = true ORDER BY agent_name;
```

**claude_code_master** is a registry marker with no workflow — it cannot be paused or triggered. The protected flag exists to prevent it from being confused with a running agent.

---

## n8n Workflows

| Workflow | ID | Why Protected |
|----------|----|---------------|
| Telegram Command Agent | `kddIKvA37UDw4x6e` | Primary Telegram interface — breaking it severs Bill's primary control channel |

---

## Files

| File | Why Protected |
|------|---------------|
| `~/aadp/claudis/DIRECTIVES.md` | Bill's standing instructions — only Bill edits |
| `~/aadp/mcp-server/.env` | All API credentials — changes affect every service |

---

## Services

| Service | Why Protected |
|---------|---------------|
| MCP server (`~/aadp/mcp-server/server.py`) | All Claude Code tool access routes through this; restart breaks active sessions |

---

*Updated when new protected resources are identified. Cross-referenced from all SKILL.md files
and LEAN_BOOT.md startup sequence.*
