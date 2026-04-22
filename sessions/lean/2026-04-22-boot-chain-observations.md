# Session: 2026-04-22 — Boot Chain Observations
*Input to boot chain restructure. Not a session artifact in the normal sense — no card executed,
no system changed. This file captures analysis that surfaced during a long research/governance
session and would be lost at context close.*

---

## 1. The Boot Chain As It Currently Exists

### Execution order and file roles

**Step 1: `LEAN_BOOT.md`** (trigger file, read by the user before the session starts)
- Intended job: startup protocol. Tell Claude Code what to read and in what order.
- Also contains: behavioral conventions, Telegram formatting rules, a full infrastructure
  quick-reference table, an MCP tools table, and instructions for resuming autonomous mode.
- What it succeeds at: the boot sequence itself is clear and the trigger-on-read behavior is
  explicit. The dual-form directive (inline vs. pointer) is well-specified.
- Where it fails: it has accumulated non-protocol content. Behavioral conventions, infra
  reference, MCP tool index, and autonomous-mode restart instructions don't belong in a
  startup script. They make the file longer and increase the probability that a future instance
  misses something in the protocol section while reading reference material.

**Step 2: `skills/PROTECTED.md`**
- Intended job: list resources that require explicit approval before modification.
- Actual content: three sections — n8n workflows (TCA), files (.env, DIRECTIVES.md), services
  (MCP server). Now also has an "Agent Registry" section pointing to agent_registry.protected
  as the source of truth for load-bearing agents (added 2026-04-22).
- What it succeeds at: correctly scopes "do not touch" to specific named resources.
- Where it fails: it was being maintained in parallel with DEEP_DIVE_BRIEF §8's protected-agent
  list, causing three-way drift (PROTECTED.md, DEEP_DIVE_BRIEF, agent_registry all disagreed).
  That was resolved today. The remaining risk: the file is read every boot but its content
  changes rarely — a lighter pointer to the registry + a short list of the genuinely static
  protected resources would serve the same purpose at lower token cost.

**Step 3: `DIRECTIVES.md`**
- Intended job: hold the current session's task.
- Actual content: currently `Run: B-046` — a pointer to a completed card. Should be updated
  at session close to point at the next pending card.
- What it succeeds at: the two-form design (inline prose or `Run: B-NNN` pointer) is clean.
- Where it fails: no validation. If DIRECTIVES.md is stale (pointing at a completed card) or
  if the pointer points at a non-existent card, Claude Code will discover this only when it
  reads BACKLOG.md. No indication in DIRECTIVES.md itself of when it was last updated.

**Step 4 (conditional): `BACKLOG.md`**
- Loaded only when DIRECTIVES.md contains a `Run: B-NNN` pointer.
- Intended job: card queue. Source of the actual directive when the pointer form is used.
- What it succeeds at: self-contained card format with Goal, Context, Done when, Scope.
- Where it fails: the entire file is loaded every time a pointer is resolved, even if it
  contains 40+ cards. DEEP_DIVE_BRIEF §3 notes this explicitly: "Context cost of BACKLOG.md:
  The full file is loaded every time the pointer form is used." The archive-at-top-of-file
  convention mitigates this but is not enforced — the file currently has 3 active cards
  (B-044, B-045, B-046) and the total file length is not tracked anywhere in the boot chain.
  Currently 102 lines; acceptable, but will grow.

**Step 5: `skills/CATALOG.md`**
- Intended job: skill routing table. Match directive against "Applies when" / "Also triggers
  when" columns; load matching skill files.
- What it succeeds at: the tabular format is scannable and the trigger columns provide enough
  signal for judgment-based matching.
- Where it fails: the match is entirely judgment-dependent. There is no ground truth on whether
  a skill was correctly loaded for a given session. `times_loaded` and `last_loaded` in
  skills_registry are intended to track this but were explicitly noted as not-yet-incremented
  in B-041 (deferred). The routing works in practice but has no feedback loop.

**Step 6 (conditional): Skill files under `skills/`**
- Each matched skill is a separate file: `system-ops/SKILL.md`, `anvil/REFERENCE.md`, etc.
- These are the most targeted files in the boot chain — loaded only when relevant.
- What they succeed at: when loaded, they contain concrete operational knowledge (exact API
  patterns, known failure modes, runbook steps) that prevents re-discovering known gotchas.
- Where they fail: they are not surfaced to the boot chain if no skill matches. For sessions
  that don't trigger a recognized pattern, Claude Code proceeds with only the base files —
  no mechanism to inject relevant knowledge from skills that "almost" matched.

**Step 7: `CONTEXT.md`**
- Intended job: system facts and operational context. Answers "where am I."
- Actual content: hardware, services table, MCP tool namespaces, Supabase tables, ChromaDB
  collections, repo structure, agent system, how to work with Bill.
- What it succeeds at: the services table and MCP namespace summary are genuinely useful at
  session start. The "Working with Bill" section captures collaboration style accurately.
- Where it fails: see §4 (stale content). Also contains Bill's "four operating principles"
  which are behavioral guidance, not system facts — misplaced. The Supabase table list and
  ChromaDB collections list duplicate detail that also appears in DEEP_DIVE_BRIEF §7, which
  is not in the boot chain.

**Step 8: `TRAJECTORY.md`**
- Intended job: destinations, active vectors, operational state.
- What it succeeds at: destinations are stable and clarifying. The "Operational State" section
  efficiently captures Lean Mode status, what's stopped, and how to resume.
- Where it fails: per-session update logs are accumulating inside each active vector. A vector
  that has had 8 session updates reads like a changelog. The original purpose — "current state
  of this vector" — is buried under chronological narrative. A reader has to scan the whole
  vector entry to find the current milestone, which is always at the end. This will worsen
  with each session.

---

## 2. Duplication Map

### Behavioral conventions

`LEAN_BOOT.md` §"Behavioral Conventions" contains:
- Confidence-prefix rule
- Branch-per-attempt
- Telegram 750-char, answer-first format
- "Would Bill Approve?" test
- Default to attempting (2-hour rule)
- Dual-output convention
- Context economy
- Privacy (first name only)

`CONVENTIONS.md` contains all of these plus more (Session Close Ritual, Work Priority and
Autonomy, each with failure-traced WHY and what-breaks-without-it explanations).

**The problem:** LEAN_BOOT.md has a shorter version of the same rules. CONVENTIONS.md has the
canonical expanded version with reasoning. But CONVENTIONS.md is NOT in the boot chain — it
exists in the repo but nothing in the boot sequence instructs Claude Code to read it.

**Who should own it:** CONVENTIONS.md is the right home. LEAN_BOOT.md should drop its
behavioral conventions section entirely and reference CONVENTIONS.md, or CONVENTIONS.md should
be added to the boot chain as a named step. Currently a Claude Code session never reads
CONVENTIONS.md unless it happens to explore the repo.

### Infrastructure tables (services, Supabase, MCP tools)

`LEAN_BOOT.md` §"Infrastructure Quick-Reference" contains:
- Pi file paths table
- Supabase tables list
- ChromaDB collections list
- n8n port/URL info
- GitHub repo reference
- MCP tools table (all 25+ tools)

`CONTEXT.md` contains:
- Services table (overlapping)
- MCP tool namespaces (abbreviated version)
- Supabase tables list (overlapping)
- ChromaDB collections (overlapping)

`DEEP_DIVE_BRIEF.md` §7 contains:
- Full services map with container/port/start mechanism/config location
- Full Supabase schema (column-level detail)
- ChromaDB collections with counts
- Stats server endpoints
- n8n credential IDs

Three files contain overlapping infrastructure facts at different levels of detail.
The MCP tools table in LEAN_BOOT.md is the only complete quick-reference — CONTEXT.md has
namespaces only, DEEP_DIVE_BRIEF has descriptions without the full tool list.

**Who should own it:** One canonical reference at the level of detail needed for session work.
LEAN_BOOT.md's quick-reference tables are the right format for session use — CONTEXT.md's
overlap could be reduced to a pointer. DEEP_DIVE_BRIEF is the right home for schema-level
detail that's only needed when doing DDL or debugging.

### Protected agent lists

Before today this session: three sources disagreed — agent_registry.protected, DEEP_DIVE_BRIEF
§8, and PROTECTED.md. Resolved 2026-04-22: agent_registry is now SOT, DEEP_DIVE_BRIEF §8 and
PROTECTED.md both point to it. The duplication risk remains because DEEP_DIVE_BRIEF §8 still
has the Active Production Agents and Platform Infrastructure tables, which will drift from
agent_registry unless updated at each governance session.

### Session close ritual

`LEAN_BOOT.md` §"Session Close" describes the session artifact format and commit message
convention, and mandates site regeneration before every session ends.

`CONVENTIONS.md` §"Session Close Ritual" says "Run the close-session skill at every session
end. Treat it as a first-class deliverable."

`DEEP_DIVE_BRIEF §3` describes the session artifact format with the five-section template
(Directive, What Changed, What Was Learned, Lessons Applied, Unfinished).

Three files describe what to do at session close, at three different levels of detail, and
they don't fully agree. LEAN_BOOT.md specifies the artifact filename format and site
regeneration. CONVENTIONS.md points at the close-session skill. DEEP_DIVE_BRIEF describes
the artifact template. None of them is the single authoritative reference.

### Telegram formatting rules

`LEAN_BOOT.md`: "750 chars max, answer first, no preamble, mobile-readable"
`CONTEXT.md` §"Working with Bill": "750 characters max per message, mobile-readable, no
preamble. Lead with: status or answer — then explanation if needed"
`CONVENTIONS.md` §"Communication Formatting": same rule with the WHY (Bill reads on his phone)

Three files. CONVENTIONS.md is the right home (it has the reasoning). The other two should
drop the rule or reference CONVENTIONS.md.

### Repo structure

`LEAN_BOOT.md`: references `~/aadp/mcp-server/server.py`, `~/aadp/sentinel/scheduler.sh`, etc.
`CONTEXT.md`: references the claudis repo structure
`DEEP_DIVE_BRIEF §13`: full repo tree with subdirectory breakdown

Redundant at different levels of detail. LEAN_BOOT.md has the file paths needed for session
work; DEEP_DIVE_BRIEF has the full tree. CONTEXT.md has an intermediate summary that adds
noise without adding clarity.

---

## 3. Content in the Wrong File

### CONTEXT.md: Bill's four operating principles

Under §"Working with Bill":
> **Bill's four operating principles:** Orient, Take stock, Find one improvement, Prepare next session.

This is a description of how Bill thinks about sessions, not a system fact. It belongs in
DEEP_DIVE_BRIEF §2 "Working with Bill" (where tone, access, and collaboration style live),
not in the operational facts file.

### LEAN_BOOT.md: "Resuming Autonomous Mode" instructions

The last section of LEAN_BOOT.md contains the exact commands to re-enable the sentinel timer
and reactivate the growth scheduler. This is an operational runbook snippet, not a startup
protocol item. A lean session should never need to resume autonomous mode — that's Bill's
decision from the Anvil dashboard. The section belongs in system-ops/SKILL.md or TRAJECTORY.md
§"Operational State" (which already has the "To resume:" instructions, creating a duplicate).

### TRAJECTORY.md: per-session changelog embedded in vector descriptions

Each active vector has accumulated timestamped update entries:
> "Session 2026-04-13 (context-economy) update: ..."
> "Session 2026-04-14 (explore) update: ..."

These are chronological session logs embedded inside a doc meant to describe *current* state.
The vectors have become hard to read — the current milestone is always the last bullet, buried
under 6+ prior updates. The update history belongs in session artifacts (which exist) or in
git history, not inline in TRAJECTORY.md. TRAJECTORY.md should contain: destination, current
state (one paragraph), next milestone, validation metric. Nothing else per vector.

### LEAN_BOOT.md: behavioral conventions (duplicating CONVENTIONS.md)

As noted in §2, LEAN_BOOT.md contains behavioral rules that are better expressed in
CONVENTIONS.md. The LEAN_BOOT.md versions are shorter and lack the WHY reasoning that makes
CONVENTIONS.md useful. If CONVENTIONS.md were in the boot chain, LEAN_BOOT.md could drop its
entire behavioral conventions section.

---

## 4. Stale Content

### LEAN_BOOT.md: "Default to attempting" behavioral convention

The current text:
> **Default to attempting:** if under 2 hours and no approval needed, start it

This was flagged in the gap analysis as a convention that needs revisiting. The 2-hour ceiling
and the "start without asking" default may no longer reflect Bill's preference — he prefers
"substantial back-and-forth before action" per DEEP_DIVE_BRIEF §2. The two rules are in
tension and it's unclear which one governs. CONVENTIONS.md has the fuller "Work Priority and
Autonomy" section which is more nuanced. The LEAN_BOOT.md version is the short, potentially
outdated one.

### CONTEXT.md: agent count

> Current fleet: ~25 agents as of 2026-04-12.

After the 2026-04-22 governance pass, the active fleet is 10 agents (9 protected + 
architecture_review). The "~25" figure is stale by a factor of 2.5. This session also
corrected the protected list in DEEP_DIVE_BRIEF §8, but CONTEXT.md was not updated and still
carries the old count.

### DIRECTIVES.md: points at completed card

Currently contains `Run: B-046`, which was completed this session (2026-04-22). Should be
updated to point at the next pending card or cleared. A future session starting against this
DIRECTIVES.md would execute an already-complete card. The boot chain has no mechanism to
detect this.

### DEEP_DIVE_BRIEF §8: was updated this session

The protected-agent list replacement and active-fleet table updates were applied 2026-04-22
(commit e663006). That section is now current. The "Last updated: 2026-04-22" date was set.
Other sections still carry 2026-04-18 dates — whether they're stale depends on what changed.
§5 (Capabilities Inventory) has a note that capabilities table "may be empty" — it now has
90 rows (confirmed in B-045). §12 (Known Gaps) still lists Anvil uplink silent disconnects as
open — that was closed by B-045 and B-046 this session.

### DEEP_DIVE_BRIEF §12: "Anvil uplink silent disconnects" still listed as an open gap

The §12 entry says:
> "Anvil uplink silent disconnects. The websocket can die without the systemd service noticing...
> B-031 adds a watchdog. Until then, if the dashboard stops responding..."

B-031 was completed (watchdog deployed). B-045 made `/ping` websocket-accurate. B-046 added a
30-second systemd timer that restarts on 503. This item is closed. §12 was not updated this
session.

### TRAJECTORY.md: operational state references deactivated "/oslean Telegram command"

> `/oslean` Telegram command removed 2026-04-18 — lean sessions triggered from Anvil dashboard only.

This is correct and already documented. But there may be stale vector entries that haven't
been updated since the lean mode pause in mid-April. TRAJECTORY.md §"Active Vectors" Vector 1
next milestone says "Feedback consumer — add agent_feedback summary to morning_briefing" — but
that was actually completed in B-035 (2026-04-18). The trajectory wasn't updated to reflect
that milestone as done.

---

## 5. Load-Bearing vs. Pullable-on-Demand

### Genuinely load-bearing at session start (must be in boot chain)

**What a fresh session needs before it can take any action:**
- The task (DIRECTIVES.md / BACKLOG.md) — without this, nothing can start
- What not to touch (PROTECTED.md) — must be read before any action
- What tools exist and where to find them (LEAN_BOOT.md infra table, CONTEXT.md services) —
  needed for tool calls
- Current system state at a glance (TRAJECTORY.md operational state, CONTEXT.md) — prevents
  acting on stale assumptions
- Behavioral rules that affect how to act (CONVENTIONS.md — currently NOT in boot chain) —
  prevents repeating known mistakes

**What is currently in the boot chain but could be pulled on demand:**
- Full Supabase table schemas (DEEP_DIVE_BRIEF §7) — only needed when doing DDL or debugging
  a specific table. Currently not in boot chain, correctly.
- Per-skill reference material (skill files) — correctly conditional, only loaded when matched.
- BACKLOG.md full content — loaded every time a pointer is used, but only the pointed-at card
  is needed. A mechanism to extract just the target card would halve the token cost in pointer-
  form sessions.
- LEAN_BOOT.md's "Resuming Autonomous Mode" section — never needed in a lean session.
- LEAN_BOOT.md's behavioral conventions section — if CONVENTIONS.md were in the boot chain,
  this redundant shorter version could be removed.

**What is NOT in the boot chain but probably should be:**
- `CONVENTIONS.md` — the behavioral rules with WHY reasoning. Every session should read this.
  Currently discoverable only through exploration. A session that doesn't explore the repo
  never reads it, and can't apply the rules correctly.

**What is NOT in the boot chain and correctly so:**
- DEEP_DIVE_BRIEF.md — too large (820 lines) for every session. Correct to keep it as a
  reference document for desktop sessions and deep dives, not as a boot-chain item.
- COLLABORATOR_BRIEF.md — for desktop sessions, not Claude Code.
- Session artifacts — too numerous. Pulled on demand by the close-session skill.
- Skill SKILL.md files when not matched — correct.

### Token cost estimate of current boot chain (rough)

Based on file sizes observed this session:
- LEAN_BOOT.md: ~800 tokens (estimated from 169 lines)
- PROTECTED.md: ~350 tokens (35 lines, now with agent registry section)
- DIRECTIVES.md: ~10 tokens (one line)
- BACKLOG.md: ~1,200 tokens (102 lines — when pointer form triggers it)
- CATALOG.md: ~300 tokens (11 lines table)
- Skill files: ~400–800 tokens each (when loaded, typically 1–2 per session)
- CONTEXT.md: ~700 tokens (estimated from 72 lines)
- TRAJECTORY.md: ~1,500 tokens (estimated from 98 lines, heavy due to per-session changelog)

Total typical lean session boot: ~5,500–6,500 tokens before any task work begins. TRAJECTORY.md
is the largest single item and growing. BACKLOG.md will grow as cards accumulate before archiving.

---

## 6. Other Observations for the Restructure

### CONVENTIONS.md is the highest-value missing piece

It exists. It's well-written. It has reasoning. It's not in the boot chain. This is the most
actionable gap — adding it as a named boot-chain step (or folding it into LEAN_BOOT.md) would
give every session the behavioral rules that currently only appear in LEAN_BOOT.md in degraded
form. The restructure should resolve this explicitly: either CONVENTIONS.md is in the boot chain
(preferred), or LEAN_BOOT.md's conventions section is replaced by the canonical CONVENTIONS.md
content with reasoning, or a decision is made that conventions are only needed for specific
session types.

### TRAJECTORY.md needs a structural split, not just pruning

The per-session changelog problem won't be solved by pruning the existing entries — they'll
accumulate again. The fix is a structural rule: TRAJECTORY.md vectors contain only current
state (one paragraph, one next milestone, one validation metric). Session history goes in
session artifacts. The close-session ritual should update TRAJECTORY.md by replacing the
current-state paragraph, not by appending a timestamped entry to it.

### The boot chain has no mechanism to detect a stale directive

If DIRECTIVES.md points at a completed card and no one updates it, the next session executes
the completed card again. The card's Done-when criteria will all be true, so the session will
produce a "nothing to do" outcome — but it will have consumed a full session budget and
possibly touched files it shouldn't have re-touched. A simple convention (lean_runner.sh or
the close-session ritual sets DIRECTIVES.md to a known-empty or next-card state) would prevent
this. Currently there is no enforcement.

### DEEP_DIVE_BRIEF is not in the boot chain but gets referenced in CONTEXT.md

CONTEXT.md's repo structure section says the repo contains `DEEP_DIVE_BRIEF.md — this document`.
That phrasing implies DEEP_DIVE_BRIEF is the file you're reading, which is wrong — you're
reading CONTEXT.md. This is probably a copy-paste artifact from when DEEP_DIVE_BRIEF was written.
A future instance reading CONTEXT.md might be confused about whether it has read the brief.

### MCP tools table in LEAN_BOOT.md is the only complete tool index

No other boot-chain file lists all MCP tools with what they do. CONTEXT.md has namespace names
only. This means the MCP tools table in LEAN_BOOT.md is load-bearing for tool discovery — a
session that doesn't know `work_queue_add` exists won't use it. If LEAN_BOOT.md is restructured
to be a shorter protocol file, the tools table needs a new home (a dedicated tools reference
file, or added to CONTEXT.md at the appropriate level of detail).

### The BACKLOG.md archival convention is under-enforced

The convention is: archive completed cards in batches, add a note at the top. Current state:
B-044 through B-046 are the active cards; earlier cards are archived. But there's no tracking
of when to archive — no card count trigger, no file-size limit, no session close check. In
practice, archiving happens when someone notices the file is getting long. At the current rate
(lean sessions completing 1–2 cards/week), the file will grow slowly — but the restructure
should define the archival trigger explicitly so it doesn't depend on noticing.
