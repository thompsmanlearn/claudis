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
