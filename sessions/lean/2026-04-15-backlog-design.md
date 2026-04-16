# Session: 2026-04-15 — backlog-design

## Directive
Clean DIRECTIVES.md of terminal output corruption. Design a multi-session card 
backlog system based on today's 10+ lean sessions.

## What Changed
- `DIRECTIVES.md` — stripped all corruption (195 lines of prior session terminal 
  output), replaced with this session's clean card.

## Design: Multi-Session Card Backlog

### Problem Statement
After 10+ cards today, the pattern is clear: the card format (Goal/Context/Done 
when/Scope) works well, but three things break at scale:

1. **Bill holds the arc.** Each card assumes knowledge of prior cards. A cold-start 
   session tomorrow has no idea what ran before or what it produced.
2. **The paste workflow corrupts.** DIRECTIVES.md is fragile when Bill pastes 
   multi-screen content from a terminal. Today's corruption cost a full session card.
3. **No dependency expression.** Card order encodes dependencies implicitly — nothing 
   blocks a card from running before its prerequisite completes.

### Design

#### File: `BACKLOG.md` at repo root

DIRECTIVES.md stays as-is: one active card, plaintext, ≤50 lines. 

BACKLOG.md is the queue. Cards live there permanently — completed cards stay as 
history with their artifact links. Bill maintains this file; Claude never edits it.

**Card format:**
```
## B-NNN: Title
**Status:** ready | blocked | done
**Depends on:** B-NNN (omit if none)
**Artifact:** sessions/lean/YYYY-MM-DD-descriptor.md (fill in after done)

### Goal
One sentence.

### Context
What Claude needs that isn't in the code or git history.
If this card follows another, cite: "See artifact: sessions/lean/YYYY-MM-DD-X.md"

### Done when
- Checkbox items

### Scope
Touch: ...
Do not touch: ...
```

**Status values:**
- `ready` — can execute now, no blockers
- `blocked` — depends on a card that isn't done yet
- `done` — completed; artifact link filled in

#### Eliminating the paste step

Add to LEAN_BOOT.md startup step 4: if DIRECTIVES.md contains only `Run: B-NNN` 
(single line), read BACKLOG.md, find that card, and execute it directly.

This means Bill's entire input for a session is one line: `Run: B-007`. No pasting, 
no corruption risk. Bill edits BACKLOG.md in advance (on desktop, with full editor 
support) and then triggers via the short pointer.

DIRECTIVES.md continues to support full card content for ad-hoc sessions where Bill 
doesn't want to commit to BACKLOG.md first.

#### How a card references prior work

Cards that depend on prior output include in their Context section:
```
See artifact: sessions/lean/2026-04-15-communication-skill.md
```

Claude reads that file at session start before executing. No Bill re-explanation. 
The artifact is the handoff — which is why session artifact quality matters.

This is the "dual-output" principle from LEAN_BOOT.md made concrete: every session 
produces output for the consumer (the deliverable) and output for the system's future 
(the artifact that next sessions cite).

#### How Bill picks the next card

BACKLOG.md has cards in order. Bill scans `ready` cards — no arc needed, no memory 
required. The card's Goal line is the decision surface. Pick one, write `Run: B-NNN` 
in DIRECTIVES.md, start a lean session.

For sequenced work (e.g., skill-writing sprint), Bill can mark 5 cards ready, and 
each day's session picks the next ready one. The `Depends on:` field makes blockers 
explicit without Bill tracking them mentally.

#### What this doesn't solve (intentionally deferred)

- **Automatic BACKLOG.md updates** — Claude could mark cards done and fill artifact 
  links. Deferred: BACKLOG.md is Bill's file. Autonomous writes to it feel like scope 
  creep and could create conflicts if Bill edits concurrently.
- **Card prioritization** — order in the file is priority. No tagging, no scoring. 
  If this becomes insufficient, add it then.
- **Multi-card sessions** — one card per session enforces focus. If a session 
  naturally completes two cards, write the second card's work into the first card's 
  artifact. Don't complicate the runner.

### Earned Complexity Assessment

Everything above is grounded in today's observed failures:
- Corruption → eliminate paste step (Run: B-NNN)
- Arc-holding → artifact citation in Context
- Implicit dependencies → Depends on: field
- Context-switch to pick next card → scan ready cards in BACKLOG.md

Nothing here is speculative. All three failure modes were observed today.

### Proposed first use

Retroactively document today's completed cards in BACKLOG.md as B-001 through 
B-010 (all status: done, artifacts linked). This gives the system a starting state 
and validates the format before committing to it for new work.

## What Was Learned
- The card format works. The delivery mechanism (pasting into DIRECTIVES.md) is the 
  weak link, not the format itself.
- `See artifact:` as a context reference is the minimal viable solution to the 
  arc-holding problem. It leverages work already being done (session artifacts) 
  without adding new infrastructure.
- BACKLOG.md should be Bill's file, not Claude's. Autonomous edits to a planning 
  document create coordination overhead that outweighs the convenience.

## Unfinished
- BACKLOG.md not yet created (out of scope for this session — Bill to create with 
  today's cards as B-001..B-NNN once design is confirmed).
- LEAN_BOOT.md not yet updated with `Run: B-NNN` short-pointer behavior (Bill to 
  approve design first, then a lean card to implement it).
