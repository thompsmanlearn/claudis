# Skill: Communication

## Purpose
Composing messages and artifacts that Bill reads directly — 
Telegram alerts, session artifacts, handoff notes, and 
DIRECTIVES.md updates. This skill is about format discipline 
and continuity, not general writing.

## When to Load
- Composing Telegram alerts or status messages
- Writing session artifacts or handoff notes
- Formatting output that Bill will read on his phone
- A message needs to convey a failure without triggering alarm
- A session artifact is unusually complex to summarize

## Core Instructions

### Telegram Messages

#### Hard limits
- Telegram rejects messages >4096 characters with HTTP 400. 
  Truncate before sending:
```js
  const MAX_LEN = 4000;
  if (text.length > MAX_LEN) { 
    text = text.slice(0, MAX_LEN) + '\n… (truncated)'; 
  }
```
  Add immediately before the return in the Format node. This 
  surfaces when monitored data grows (agent registry expansion, 
  large lesson/error lists).

- Aim for 750 characters or less. Answer first, no preamble. 
  Bill reads on his phone — if the first screen isn't the answer, 
  it's wrong.

#### Quick Send workflow
Quick Send (MZiMX0byl3ciD922) expects the `message` key, not 
`text`. Using `$json.body.text` delivers "undefined" silently. 
All callers (stats server `_send_telegram`, agents using Quick 
Send) must use `message`.

### Session Artifacts

#### Structure
Every artifact must include: what was asked, what changed, what 
was learned, and what's unfinished. Optional: Decisions section 
capturing choices made and alternatives rejected.

#### Handoff note quality
Generic notes ("check work queue") break continuity. Structure 
as a letter to the next instance:
1. What I was doing
2. What I learned about the system
3. What to continue
4. What I leave better
5. Token usage note

Name the exact workflow, table, or bug. Specificity is what makes 
the next session effective instead of a cold start.

#### Session notes consumption
`session_notes_load` defaults to `consume=false`. Pass 
`consume=true` explicitly in bootstrap. Without it, old notes 
accumulate — 17 notes over 7 days added ~8,143 tokens of stale 
context. Detection: `SELECT COUNT(*) FROM session_notes 
WHERE consumed = false` — if >3, notes are accumulating.

#### Verify handoff claims before acting
If a prior session's handoff claims something unexpected (e.g. 
"ChromaDB has only 3 lessons"), verify with a live query before 
treating it as a crisis. Transient read errors during session 
close produce false claims. Pattern: any handoff with an 
unexpectedly low count → run `memory_list_collections` + 
Supabase COUNT to confirm.

## Cross-Skill Warnings
- Telegram message content about agent status → the formatting 
  rules are here, but the data comes from agent-development.
- If Telegram sends are failing at the HTTP level → load triage. 
  Communication skill assumes the delivery channel works.
- Quick Send workflow (MZiMX0byl3ciD922) is not in PROTECTED.md 
  but changes affect every agent that sends alerts. Test before 
  modifying.

## Known Failure Modes
- Telegram 400 from messages exceeding 4096 characters 
  (see references/lessons.md: message length)
- "undefined" in Telegram from using wrong key with Quick Send 
  (see references/lessons.md: Quick Send)
- Stale session notes accumulating and inflating context 
  (see references/lessons.md: session notes consumption)
- Next session panic from unverified handoff claims 
  (see references/lessons.md: verify handoff claims)
