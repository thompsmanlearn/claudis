# /attempts

Branch-per-attempt storage. Each attempt gets its own branch opened before work starts.

**Naming:** `attempt/YYYY-MM-DD-short-description`

**Lifecycle:**
- Branch opened with first commit: hypothesis, confidence, expected learning regardless of outcome
- Work happens on the branch
- Branch closed with a close-note commit: what happened, failure type if failed, corrective direction
- Default: auto-archived after 14 days if not merged
- To preserve: apply `signal:keep` tag during close — means the failure revealed something structurally non-obvious

**Triage rule:** Signal requires one deliberate action. Default is archive. Unmerged branches are the failure record.
