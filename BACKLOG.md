B-070: Thread architecture — schema and ChromaDB collection

Status: ready
Depends on: nothing — this is the foundation card for the thread architecture v0.1

Goal
Create the substrate for a thread architecture: a Supabase pair of tables (threads, thread_entries) and a separate ChromaDB collection (thread_entries) that holds entry embeddings but is excluded from default boot retrieval routing. No callables, no UI, no agent wiring yet — just the substrate that subsequent cards build on. This is Card 1 of a 4-card v0.1 (B-070 schema, B-071 write callables, B-072 Anvil read view, B-073 Anvil actions).

Context
Threads are a working surface for sustained, multi-sitting investigations — research, builds, learning, system arcs. Each thread has a question, a state, and an append-only log of entries (gather results, annotations, analysis exports, conclusions, state changes). Threads are exploratory and abandonable; they must not contaminate the system's load-bearing memory (lessons_learned, reference_material). Therefore thread embeddings live in a dedicated ChromaDB collection that is NOT in default boot retrieval routing.

Design decisions already made (do not relitigate):
- Threads live in Supabase (canonical) + ChromaDB (semantic search for in-thread retrieval). Not in DEEP_DIVE_BRIEF, not in any other system-self-knowledge document.
- States: active / dormant / closed (closed covers both completed and abandoned; an optional close_reason field captures why).
- Entry types: gather / annotation / analysis / conclusion / state_change.
- Bound-agent model: one agent_name per thread (nullable; thread can exist without an agent wired). v0.1 only supports agents that already have webhook_url in agent_registry.
- ChromaDB collection name: thread_entries.
- Boot retrieval (LEAN_BOOT step 10, bootstrap step 3) must NOT query thread_entries by default.

Done when

1. threads table exists with columns:
   - id (uuid, primary key, default gen_random_uuid())
   - title (text, not null)
   - question (text, not null)
   - state (text, not null, default 'active', check in ('active','dormant','closed'))
   - close_reason (text, nullable — populated when state transitions to closed)
   - bound_agent (text, nullable — references agent_registry.agent_name; not enforced as FK to keep deletion flexible)
   - created_at (timestamptz, default now())
   - updated_at (timestamptz, default now())
   - last_activity_at (timestamptz, default now() — distinct from updated_at; tracks when the thread was last meaningfully engaged with vs. when its row was edited)

   Index on state (most common filter is active threads) and on last_activity_at desc.

2. thread_entries table exists with columns:
   - id (uuid, primary key, default gen_random_uuid())
   - thread_id (uuid, not null, foreign key to threads(id) on delete cascade)
   - entry_type (text, not null, check in ('gather','annotation','analysis','conclusion','state_change'))
   - content (text, not null)
   - source (text, nullable — e.g. 'agent:context_engineering_research', 'session:2026-04-29-foo', 'desktop_claude:bundle_2026-04-29', 'bill')
   - chromadb_id (text, nullable — populated when the entry is embedded; allows entries to skip embedding if they don't warrant it)
   - metadata (jsonb, default '{}')
   - created_at (timestamptz, default now())

   Index on (thread_id, created_at) for chronological reads of a thread.

3. ChromaDB collection thread_entries created with all-MiniLM-L6-v2 embeddings. Verify it appears in get_collection_stats() output.

4. LEAN_BOOT.md and bootstrap.md verified to NOT query thread_entries by default. Document this exclusion explicitly in DEEP_DIVE_BRIEF Section 7 (Database Schema → ChromaDB Collections), so future cards know thread_entries is segregated by design.

5. Test inserts: one thread row, two thread_entry rows referencing it, one ChromaDB document in thread_entries. Read back. Delete the thread row, confirm cascade removes the entries. Test rows cleaned up after verification.

Out of scope (separate cards)
- create_thread, add_thread_entry, update_thread_state, wire_thread_agent callables (B-071)
- Anvil Threads tab read view (B-072)
- Anvil Threads tab action buttons + bundle export (B-073)
- Boot-time surfacing of dormant or stale threads (deferred — possibly never)
- Graduation of conclusions into lessons_learned (deferred — wait for use to inform pattern)
- Agent-request entry type (deferred — explicitly v0.1 does not support thread-driven agent creation)

Scope
Touch:
  Supabase: DDL via supabase_exec_sql to create threads and thread_entries tables
  ChromaDB: create thread_entries collection
  ~/aadp/claudis/DEEP_DIVE_BRIEF.md (Section 7 only): document thread_entries collection exclusion from default boot retrieval

Do not touch:
  uplink_server.py (no callables yet)
  Form1/__init__.py (no UI yet)
  LEAN_BOOT.md or skills/bootstrap.md (no boot changes — exclusion is by absence, not by added code)
  Any other tables or collections

Verification checklist
- threads table exists with all columns and check constraints
- thread_entries table exists with all columns, check constraint, and FK with cascade
- Indexes created on both tables
- thread_entries ChromaDB collection appears in collection list
- Test insert + cascade delete verified
- DEEP_DIVE_BRIEF Section 7 updated with thread_entries collection note: "Excluded from default boot retrieval. Queried only when working in-thread."
- Branch attempt/b070-thread-schema, merged to main, pushed

Notes
- The cascade delete on thread_entries.thread_id is intentional — when Bill deletes a thread, he wants the entries gone too. ChromaDB cleanup is the responsibility of B-071's callables (the write side). For B-070, manual ChromaDB delete in the test cleanup is fine.
- last_activity_at vs updated_at: updated_at is for any row write (state change, bound_agent change, even title edit). last_activity_at is updated only when a thread_entry is added — it's the "did anything actually happen here" timestamp. This distinction matters for the Anvil view in B-072 ("show active threads sorted by activity") vs. the audit trail.
- The bound_agent field intentionally allows null. A thread without a wired agent is fine — Annotate and Export still work. Gather is the only action that requires an agent.
- close_reason is optional. A closed thread doesn't have to have a reason; a one-word "abandoned" or "completed" or a longer note are all valid.
- The exclusion of thread_entries from boot retrieval is enforced by absence, not by explicit blocklist. LEAN_BOOT and bootstrap query specific collections (lessons_learned, etc.); they simply don't query thread_entries. This is the correct design — no negative configuration to maintain.

---

B-074: Fix claudis git divergence between close-session push and Anvil Write Directive

Status: ready
Depends on: nothing

Goal
Eliminate the recurring failure mode where the local claudis repo diverges from origin, causing `git pull` to fail at the start of the next session. This has happened at least twice: close-session commits the session artifact locally but Anvil writes a new directive to the remote before that commit is pushed, leaving local and origin on divergent histories. Boot then fails with "fatal: Need to specify how to reconcile divergent branches" and requires manual intervention.

Root causes
Two independent failure points, either of which is sufficient to cause the divergence:
1. close-session does not pull before pushing. If anything was pushed to origin between our local commit and our push (e.g. Anvil writing DIRECTIVES.md), the push is rejected — or, depending on config, fails silently. The next session opens with a diverged repo.
2. Anvil's Write Directive callable does not check whether local has unpushed commits before writing to origin. It writes to the remote without knowing whether an in-flight session has a local commit that hasn't been synced yet.

Done when (pick at least one; doing both is preferred)

Option A — close-session pull-before-push (recommended as minimum):
- close-session skill updated to run `git pull --rebase` on ~/aadp/claudis/ immediately before `git push` in the session artifact commit step
- Verified: if origin has new commits at push time, rebase applies cleanly and push succeeds

Option B — Anvil Write Directive pre-flight check:
- The uplink callable that writes DIRECTIVES.md (and/or BACKLOG.md) first checks `git log @{u}..HEAD --oneline` on the Pi
- If unpushed commits exist, the callable returns an error to Anvil instead of writing, and surfaces a message: "Local claudis has N unpushed commits. Push first, then re-issue directive."
- Verified: attempting to write a directive when local is 1 ahead returns an error instead of diverging the repo

Both options can be done in the same session; they are independent changes.

Out of scope
- Changes to LEAN_BOOT.md's recovery procedure (the current "Telegram and STOP" behaviour is correct — this card prevents the failure, not the recovery)
- Changing how Anvil writes to GitHub directly (the Pi-local git repo is the canonical path)

Scope
Touch:
  ~/aadp/claudis/skills/close-session.md — Option A
  ~/aadp/claudis/uplink_server.py (or wherever Write Directive callable lives) — Option B

Verification checklist
- Option A: close-session successfully pulls before pushing; session artifact commits don't leave repo in diverged state
- Option B: Write Directive callable rejects write when local has unpushed commits
- Simulated divergence (commit locally without pushing, then write from Anvil) produces an error, not a diverged repo

Notes
- Filed 2026-04-28 after B-070 session opened with a diverged repo requiring manual `git pull --rebase` to recover.
- B-071, B-072, B-073 are reserved for thread architecture (write callables, Anvil read view, Anvil actions).
- Option A is the higher-priority fix — it's one line in close-session and eliminates the most common path to divergence.
