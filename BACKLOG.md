## B-051: Close the ChromaDB lesson feedback loop

**Goal:** Verify and fix the end-to-end path: boot lesson retrieval → "Applying lesson" flag → close-session `times_applied` increment. Currently all 237 lessons show `times_applied = 0`, which means the loop has never completed a full cycle.

**Rationale:** Lesson retrieval at boot is only useful if the system actually acts on retrieved lessons and the feedback loop closes. Without `times_applied` incrementing, there is no signal for which lessons are valuable, the "Never Applied" view in Anvil is meaningless, and the retrieval query cannot be tuned.

**Scope:**

1. **Diagnose which link is broken.**
   - Check git log on close-session.md and LEAN_BOOT.md to determine when boot step 10 (lesson retrieval) and close-session step 8 (increment) both existed simultaneously. If they only recently overlapped, `times_applied = 0` may just be "no sessions yet" rather than a bug.
   - Run this query to confirm zero is universal: `SELECT COUNT(*) FROM lessons_learned WHERE times_applied > 0;`
   - Read the most recent session artifact in `~/aadp/claudis/sessions/lean/` and check whether any "Applying lesson [id]: ..." lines appear in the record of what happened.

2. **Identify the gap and fix it.**
   There are three candidate failure modes — address whichever the diagnosis confirms:
   - **Threshold too strict:** Boot step 10 says "if it clearly applies" — instances may be too conservative and never flag any lesson as applied. If so, loosen the language in LEAN_BOOT step 10 to: flag any lesson with distance < 1.4 that touches the current task domain, not just ones that are unambiguous.
   - **Close-session step 8 skipped:** Step 8 only increments if lessons were flagged during boot. If boot flags nothing, step 8 silently does nothing. Confirm by checking whether any session artifact records a step 8 increment.
   - **ID chain broken:** Boot step 10 calls `memory_search` which returns ChromaDB IDs. Close-session step 8 requires Supabase IDs, with a fallback `SELECT id FROM lessons_learned WHERE chromadb_id = '...'`. Verify the ChromaDB metadata actually has `supabase_id` populated for a sample of lessons.

3. **Run a verification session.**
   After the fix, this session itself is the test: boot step 10 should flag at least one lesson as applied (this card's work touches ChromaDB, lesson retrieval, and Supabase — multiple lessons in the store are relevant). Close-session step 8 should then increment those rows. Confirm with: `SELECT id, title, times_applied FROM lessons_learned WHERE times_applied > 0 ORDER BY times_applied DESC LIMIT 10;`

4. **Update LEAN_BOOT step 10 and/or close-session step 8 as needed.**
   Commit fixes to claudis repo. Note the verified fix in the session artifact.

**Verification checklist:**
- [ ] Diagnosis complete — specific failure mode identified
- [ ] `SELECT COUNT(*) FROM lessons_learned WHERE times_applied > 0` returns > 0 after this session
- [ ] Session artifact records at least one "Applying lesson [id]: ..." line
- [ ] Close-session step 8 increment confirmed in Supabase
- [ ] Any LEAN_BOOT or close-session changes committed to claudis

**Out of scope:**
- Changing which lessons are written or how they are structured
- Tuning the retrieval query beyond the threshold language fix

---

## B-050: Stale directive fallback with Anvil boot briefing

**Goal:** When the boot directive points to an already-complete card, the new instance detects this, writes a structured state briefing to Anvil (Sessions tab → Boot Briefings section), sends a short Telegram alert pointing there, and waits. Does not autonomously select new work.

**Rationale:** Currently a stale DIRECTIVES.md causes a wasted session — the instance Telegrams Bill and stops, with no useful information. A structured briefing gives Bill the system state needed to write the next directive without starting a new session just to check.

**Scope:**

1. **New Supabase table: `boot_briefings`**
   Columns: `id` (uuid, pk), `content` (text), `directive_seen` (text), `created_at` (timestamptz default now()), `acknowledged` (bool default false).

2. **Two new Anvil callables in `uplink_server.py`:**
   - `post_boot_briefing(content, directive_seen)` — INSERT row into `boot_briefings`, return `{id}`.
   - `get_boot_briefings(limit=10)` — SELECT recent rows ordered by `created_at desc`.

3. **Sessions tab UI — Boot Briefings section:**
   Add to `_build_sessions_layout`: a "Boot Briefings" collapsible section (default open if any unacknowledged). Each briefing card shows `created_at`, `directive_seen`, content, and an "Acknowledge" button that calls a new `acknowledge_boot_briefing(id)` callable (PATCH `acknowledged=true`).
   Add `acknowledge_boot_briefing(id)` as a third callable.

4. **LEAN_BOOT.md — stale card detection + fallback path:**
   After step 5 (read card), add a check: evaluate whether the card's acceptance criteria are already satisfied (read key artifacts, check Supabase where fast). If complete:
   - Compose structured briefing: current directive, TRAJECTORY.md project arc, pending `work_queue` items (count + types), unresolved `error_logs` count, active agent count.
   - Call `post_boot_briefing(content, directive_seen)` via Anvil uplink (or direct Supabase insert if uplink not ready).
   - Telegram: "🔔 Stale directive detected. Boot briefing ready — check Anvil Sessions tab."
   - STOP. Do not execute the stale directive.

**Verification checklist:**
- [ ] `boot_briefings` table exists in Supabase
- [ ] `post_boot_briefing`, `get_boot_briefings`, `acknowledge_boot_briefing` callables registered and reachable
- [ ] Sessions tab shows Boot Briefings section with acknowledge button
- [ ] Starting a new session with DIRECTIVES.md = "Run: B-049" triggers the fallback, populates a briefing row, Telegrams Bill
- [ ] Executing a fresh (incomplete) card skips the fallback entirely

**Out of scope:**
- Autonomous work selection in the fallback path
- Modifying the Telegram command agent or any protected workflow

---

## B-049: Create PROJECT_STATE.md

**Goal:** Create `~/aadp/claudis/PROJECT_STATE.md` — a stable session-start reference for Anvil UI work. The anvil skill CATALOG entry already points to this file ("read PROJECT_STATE.md for current UI gap list and callable inventory"); it doesn't exist yet.

**Rationale:** Every Anvil session currently re-derives the gap list and callable inventory from the codebase. That's wasted context and inconsistent across sessions. PROJECT_STATE.md captures the known state once; sessions update it when they close a gap or add a callable.

**Scope:**

1. **Inventory the 33 Anvil callables**
   Read the uplink server source (`~/aadp/anvil-uplink/` or equivalent) to enumerate all registered callables. List each with: name, what it returns, which UI component consumes it (or "unconnected" if none).

2. **Enumerate the known UI gaps**
   From TRAJECTORY.md + session artifacts: work queue detail view, error log resolve action, site status + regenerate trigger, artifact comments, per-agent invocation. Confirm these are still open by checking the Anvil dashboard source.

3. **Write PROJECT_STATE.md**
   Sections:
   - **Callables** — table: name | returns | UI consumer
   - **UI gaps** — list: gap name | what's missing | suggested callable(s) to wire
   - **Component map** (brief) — which Anvil forms/components exist and what they show
   - **Last verified** — date stamp so stale entries are obvious

4. **Update CATALOG.md anvil skill entry**
   The "read PROJECT_STATE.md" instruction is already there — no change needed unless the file location differs.

**Verification checklist:**
- [ ] PROJECT_STATE.md exists at `~/aadp/claudis/PROJECT_STATE.md`
- [ ] Callables table is complete (all 33 listed)
- [ ] UI gaps list matches current Anvil dashboard state
- [ ] File committed to claudis repo

**Out of scope:**
- Closing any UI gaps (this card is capture only)
- Changing any callables or Anvil code

**Notes:**
- If callable count differs from 33, use the actual count — 33 is from TRAJECTORY.md and may be stale
- This file is living state, not an ADR — update it in close-session when gaps close

---

## B-048: Consolidate developer_context_load into LEAN_BOOT

**Goal:** Eliminate the parallel context-load path. LEAN_BOOT becomes the single boot route, with a lightweight live-state ping appended. Retire developer_context_load.

**Rationale:** developer_context_load only stays accurate if sessions write back to Supabase. With LEAN_BOOT-exclusive operation, the live-state layer rotted (12-day stale heartbeat, stale session notes pointing at B-043 when directive was already B-047, unreconciled registry rows). Two boot paths that can disagree is a bug, not a feature.

**Scope:**

1. **Add Step 10 to LEAN_BOOT.md — "Live state ping"**
   Single read-only Supabase query block returning:
   - Hardware: memory %, CPU %, disk %, temp, uptime
   - Active agents list + any rows with status/workflow_id mismatches flagged
   - Unresolved errors count
   - Pending work queue (count + summary)
   No writes. No session-notes read. Output appended to boot summary.

2. **Reconcile `autonomous_growth_scheduler` registry row**
   Currently `status: active`, `workflow_id: null`. Per memory + prior notes, should remain deactivated. Set `status: inactive` to match reality.

3. **Deprecate developer_context_load**
   - Mark the command/skill deprecated with a pointer to LEAN_BOOT
   - Remove from any docs that reference it as an option
   - Leave the underlying queries available as utilities if useful elsewhere

4. **Retire dead infrastructure**
   - Stop the heartbeat writer (whichever agent or hook owns it)
   - Archive the session_notes table (export to file, then drop or rename to `_deprecated_session_notes`)

5. **Update CONVENTIONS.md**
   Single boot path documented. Remove any language treating developer_context_load as a current option.

**Verification checklist:**
- [ ] LEAN_BOOT Step 10 runs and outputs the four state bullets
- [ ] `autonomous_growth_scheduler` registry row shows `status: inactive`
- [ ] developer_context_load command/skill is marked deprecated
- [ ] Heartbeat writer is stopped (no new rows after this commit)
- [ ] session_notes table archived
- [ ] CONVENTIONS.md reflects single boot path
- [ ] Fresh LEAN_BOOT session completes cleanly with new Step 10

**Out of scope:**
- Redesigning what live-state data is collected (just port what's useful, defer expansion)
- Any changes to DIRECTIVES.md / TRAJECTORY.md mechanics
- Backfilling old session notes anywhere

**Notes:**
- Step 10 should be cheap — target sub-second, one query if possible
- If the registry mismatch detection is non-trivial, scope it as a flag in output rather than a fix; reconciliation can be manual
