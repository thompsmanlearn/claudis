# LEAN_BOOT.md

*Reading this file is the trigger. Execute the startup sequence immediately. Do not wait for a directive or user prompt.*

You are Claude Code operating the AADP on a Raspberry Pi 5. Bill directs; you execute. Lean Mode: autonomous loop suspended. Bill states the session goal in his first prompt.

---

## Startup Sequence

1. `git pull` on `~/aadp/claudis/`. If pull fails, Telegram Bill that directives may be stale and STOP.
2. `cp ~/aadp/claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md`.
3. Read `~/aadp/claudis/skills/PROTECTED.md`.
4. Read `~/aadp/claudis/CONVENTIONS.md`.
5. Read `~/aadp/claudis/DIRECTIVES.md`. If it contains `Run: B-NNN`, read that card from `~/aadp/claudis/BACKLOG.md` — the card is the directive.
6. Read `~/aadp/claudis/skills/CATALOG.md`. Match the directive against the "Applies when" columns. Read matching `SKILL.md` files. Do not auto-load `references/*.md` — pull those on demand. Confirm: `Loading: [skills]. Proceeding.` or `No skills matched. Proceeding.`
7. Read `~/aadp/claudis/CONTEXT.md`.
8. Read `~/aadp/claudis/TRAJECTORY.md`.
9. Execute the directive. Do not pause for confirmation.

If LEAN_BOOT.md is corrupted, restore from `~/aadp/prompts/LEAN_BOOT_stable.md`.

---

## Session Close

Run the close-session skill at session end. Procedure: `~/aadp/mcp-server/.claude/skills/close-session.md`.

Regenerate the site before ending:

```
cd ~/aadp/mcp-server && source venv/bin/activate && python3 ~/aadp/thompsmanlearn.github.io/generate_site.py
```
