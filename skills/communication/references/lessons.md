# Lessons — Communication

Curated from ChromaDB lessons_learned 2026-04-15. Actionable only.

---

## Telegram

**Telegram rejects messages >4096 characters with HTTP 400.**
Any node formatting Telegram output must truncate before sending. Pattern:
```js
const MAX_LEN = 4000;
if (text.length > MAX_LEN) { text = text.slice(0, MAX_LEN) + '\n… (truncated)'; }
```
Add immediately before the return in the Format node. Bug surfaces when monitored data grows (agent registry expansion, large lesson/error lists).
*(2026-03-30)*

**Quick Send workflow (MZiMX0byl3ciD922) expects `message` key, not `text`.**
Using `$json.body.text` delivers "undefined" silently. Correct: `$json.body.message`. All callers (stats server `_send_telegram`, agents using Quick Send) must use the `message` key.
*(2026-03-29)*

---

## Session Artifacts

**Handoff note specificity is the difference between continuity and cold-start.**
A generic note ("check work queue") breaks the continuity chain. Structure the handoff as a letter to the next instance: (1) what I was doing, (2) what I learned about the system, (3) what to continue, (4) what I leave better, (5) token usage note. Specificity — naming the exact workflow, table, or bug — is what makes the next session effective.
*(2026-03-25)*

**session_notes_load defaults to `consume=false`. Pass `consume=true` explicitly in bootstrap.**
The tool is safe-default (non-destructive peek). If bootstrap loads notes without `consume=true`, old notes accumulate. Each session writes a new note but never consumes prior ones. 17 notes accumulated over 7 days, adding ~8,143 tokens of stale context to DCL. Detection: `SELECT COUNT(*) FROM session_notes WHERE consumed = false` — if >3, notes are accumulating.
*(2026-04-13)*

**Verify handoff claims against live data before treating them as a crisis.**
A prior session's handoff claimed ChromaDB had only 3 lessons — the next session opened with a stated crisis. Actual count: 107. The prior session had a transient read error during close. Pattern: any handoff claiming an unexpectedly low count should trigger a verification query (`memory_list_collections` + Supabase `COUNT`), not an investigation.
*(2026-04-01)*
