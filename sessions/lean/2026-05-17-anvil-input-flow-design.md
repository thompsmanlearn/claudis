# Anvil UI Input Flow — Design Session

**Session type:** Design discussion (no code built)
**Date:** 2026-05-17
**Participants:** Bill + Claude Code

---

**Before:** No channel for Bill to send input from Anvil that gets acted on at boot before a backlog directive. bootstrap skill status was unclear. Trigger Lean Session button status was unclear.

**After:** Full design settled for Anvil UI input flow. Design summary ready for Desktop Claude to write the card. Two open questions resolved. Two system facts confirmed.

---

## Tasks completed

- Investigated `/bootstrap` skill — confirmed it is the Sentinel boot sequence (skills/bootstrap.md), not an inactive artifact. Overlap with LEAN_BOOT.md is real; unification is still pending Phase 1 work.
- Confirmed Trigger Lean Session button works end-to-end: Anvil → uplink → stats_server `/trigger_lean` → lean_runner.sh → `claude -p --dangerously-skip-permissions` with LEAN_BOOT.md as prompt
- Designed Anvil UI input flow from first principles with Bill
- Resolved all open design questions (see Key decisions)
- Produced design summary for Desktop Claude to write the card

## Key decisions

1. **Three-mode input surface** — Question / Comment / Command. Intent classified at input time by Bill, not inferred by the system. Eliminates need for a classifier.

2. **UI input is top priority at boot** — new LEAN_BOOT.md step inserted between step 4 (CONVENTIONS) and step 5 (DIRECTIVES). Checks `bill_input WHERE status='pending'` before reading DIRECTIVES.md.

3. **Command mode replaces DIRECTIVES.md (Option A)** — overwrites the file entirely, one thing per session. Does not stack with the existing directive.

4. **Question and Comment leave DIRECTIVES.md intact** — existing backlog directive still runs after the question is answered or comment is saved.

5. **Does not replace DIRECTIVES.md/BACKLOG.md system** — backlog cards via Desktop Claude remain the primary build channel. UI input is a supplemental, higher-priority channel.

6. **Response via Supabase + "Check response" button** — no polling. Bill submits, triggers session, waits for Telegram completion notification, then hits Check Response in Anvil to see what Claude Code said.

## Settled card scope

- **New table:** `bill_input` (id, mode, text, status, response, created_at, processed_at) — one row at a time, overwritten on submit
- **LEAN_BOOT.md:** new step between 4 and 5 — reads pending bill_input, processes by mode, writes response, marks processed
- **uplink_server.py:** two callables — `submit_bill_input(mode, text)`, `get_bill_input_response()`
- **Form1/__init__.py:** mode selector + text input + Submit + response panel + copy button, on Home tab
- **Do not touch:** existing DIRECTIVES.md/BACKLOG.md system, existing boot steps, existing export buttons

## Capability delta

No new system capabilities this session — design only. Card not yet written.

## Lessons written

2 lessons (see Step 7): bootstrap skill clarification; Trigger Lean Session mechanics.

## Commits

| Repo | Commit | Note |
|---|---|---|
| claudis | 60bc237 | TRAJECTORY.md update |
