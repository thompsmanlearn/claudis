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
B-071: Thread architecture — write callables and read minimum

Status: ready
Depends on: B-070 (schema + ChromaDB collection, complete)

Goal
Build the callable layer for thread architecture v0.1: write callables that the Anvil UI (B-072, B-073) and future agents will call to create threads, append entries, change state, and wire agents — plus the two read callables needed to verify the write layer works and to give B-072 a foundation. After this card, the substrate has a working API; the next card adds a UI on top.

Context
B-070 created the threads and thread_entries tables and the thread_entries ChromaDB collection. No code paths read or write these yet. B-071 adds the callable layer on the uplink server, plus a Supabase trigger for the last_activity_at invariant that should have been part of B-070's substrate.

Design decisions already made (do not relitigate):
- last_activity_at is maintained by a Supabase trigger on thread_entries inserts, not by callable responsibility. The trigger updates threads.last_activity_at = now() whenever a thread_entries row is inserted referencing that thread.
- ChromaDB embedding is controlled by a single embed=True parameter on add_thread_entry. Default True. Caller can opt out per-call (e.g. for state_change entries that don't warrant embedding). No per-entry-type default differentiation in v0.1.
- Read minimum: two callables — get_threads(state='active') and get_thread_entries(thread_id) — sufficient to verify writes and to support B-072's UI without re-doing the read layer.
- All callables return plain dicts; no custom return objects.
- wire_thread_agent validates that the agent exists in agent_registry AND has a non-null webhook_url. v0.1 only supports agents that already support on-demand invocation.

Done when

1. Supabase trigger created:
   - Function update_thread_last_activity() that sets threads.last_activity_at = now() WHERE id = NEW.thread_id
   - Trigger thread_entry_activity_trigger AFTER INSERT ON thread_entries FOR EACH ROW EXECUTE update_thread_last_activity()
   - Verified by inserting a thread_entries row and confirming the parent thread's last_activity_at advances

2. Five new uplink callables registered in ~/aadp/claudis/anvil/uplink_server.py:

   create_thread(title, question, bound_agent=None) -> dict
     - Inserts a row into threads with state='active'
     - If bound_agent provided, validates it exists in agent_registry and has non-null webhook_url; raises if not
     - Also writes an initial thread_entry of type 'state_change' with content "Thread created" (embed=False)
     - Returns the thread row as dict

   add_thread_entry(thread_id, entry_type, content, source=None, embed=True, metadata=None) -> dict
     - Validates entry_type is in allowed set ('gather','annotation','analysis','conclusion','state_change')
     - Inserts the thread_entry row
     - If embed=True, calls memory_add on the thread_entries ChromaDB collection with the content; updates the row's chromadb_id field
     - Trigger fires automatically and bumps last_activity_at on the parent thread
     - Returns the entry row as dict (with chromadb_id populated when embedded)

   update_thread_state(thread_id, state, close_reason=None) -> dict
     - Validates state is in ('active','dormant','closed')
     - close_reason is optional for any state but is the only place it's accepted; if state != 'closed', close_reason is ignored
     - Updates the threads row
     - Also writes a thread_entry of type 'state_change' describing the transition (e.g. "active → dormant", "dormant → closed: completed"); embed=False for these entries
     - Returns the updated thread row

   wire_thread_agent(thread_id, agent_name) -> dict
     - Validates agent_name exists in agent_registry AND has non-null webhook_url; raises if not
     - Updates threads.bound_agent
     - Writes a thread_entry of type 'state_change' with content "Wired agent: {agent_name}"; embed=False
     - Returns the updated thread row
     - Pass agent_name=None to unwire (sets bound_agent to null; entry says "Unwired agent")

   get_threads(state='active') -> list[dict]
     - Returns threads filtered by state, ordered by last_activity_at desc
     - Pass state=None to return all threads regardless of state
     - Returns a list (possibly empty)

   get_thread_entries(thread_id) -> list[dict]
     - Returns all thread_entries for a thread, ordered by created_at asc (chronological reading order)
     - Returns a list (possibly empty)

3. Restart uplink (sudo systemctl restart aadp-anvil) and verify reconnection in journal log.

4. End-to-end smoke test (run from MCP supabase_exec_sql + the new callables, document in session artifact):
   - Create a test thread with title and question, no bound_agent — confirm row exists with state='active' and an initial state_change entry
   - Add an annotation entry with embed=True — confirm chromadb_id is populated, last_activity_at advanced
   - Add a state_change entry with embed=False — confirm chromadb_id is null
   - Wire a real agent (use context_engineering_research, which has webhook_url) — confirm bound_agent updates and entry written
   - Try wire_thread_agent with a non-existent agent — confirm raises
   - Try wire_thread_agent with an agent that has null webhook_url (e.g. claude_code_master) — confirm raises
   - Read get_threads(state='active') — confirm test thread appears
   - Read get_thread_entries(test_thread_id) — confirm chronological list with all entries
   - Update state to 'closed' with close_reason='smoke test complete' — confirm row updated and final state_change entry written
   - Cleanup: delete the test thread, confirm cascade removes entries, confirm ChromaDB embeddings are also gone (manual ChromaDB delete by chromadb_id; cascade does not extend to ChromaDB)

5. Note in the B-071 commit message: the last_activity_at trigger should have been part of B-070's substrate. Filing as a small process observation.

Out of scope (separate cards or deferred)
- Anvil Threads tab read view (B-072) and actions (B-073)
- Boot-time surfacing of dormant or stale threads (deferred — possibly never)
- Agent-request entry type
- Cross-thread analysis or search across thread_entries collection
- Bulk operations on threads (close-many, archive-many)
- A delete_thread callable — deletion happens via Supabase directly for v0.1; once B-073 lands, decide whether to add an Anvil-friendly callable

Scope
Touch:
  Supabase: trigger function and trigger on thread_entries
  ~/aadp/claudis/anvil/uplink_server.py — five new callables
  
Do not touch:
  Form1/__init__.py (no UI yet — that's B-072)
  LEAN_BOOT.md, skills/bootstrap.md, skills/close-session.md
  Any other tables, collections, agents, or services

Verification checklist
- Trigger function and trigger exist in Supabase
- Inserting a thread_entries row advances the parent thread's last_activity_at
- Five new callables registered and reachable via uplink
- Smoke test completes all steps without error
- Smoke test cleanup leaves the database in original state (no test rows or stranded ChromaDB embeddings)
- Branch attempt/b071-thread-callables, merged to main, pushed (close-session's new pull-before-push exercises automatically)

Notes
- The trigger approach for last_activity_at is the right call: putting it in callable code would mean every future writer (including agents calling add_thread_entry directly) has to remember to update both fields. The trigger guarantees it.
- ChromaDB cleanup on thread deletion is intentionally manual for v0.1. The Supabase cascade removes thread_entries rows, but ChromaDB embeddings linger until something deletes them. A delete_thread callable in B-073 (or whichever card needs it) should handle this — it's a known gap, not a bug.
- The initial "Thread created" state_change entry on every new thread gives the entry log a clean origin point. Without it, the first user-added entry would be the only history, which feels wrong when looking at older threads.
- wire_thread_agent's validation against webhook_url IS NOT NULL is the simplest enforcement of the v0.1 constraint that threads only use on-demand agents. If we later want to support scheduled agents or different invocation patterns, this validation relaxes. For now, keep it strict.
- Return types are plain dicts (matching uplink callable conventions in the existing codebase). No structured types.
- The smoke test in step 4 can be done directly via the uplink callables (Bill calls them from a Python REPL or via a one-shot script) since the UI doesn't exist yet. Document the actual commands run in the session artifact for future reference.
