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
