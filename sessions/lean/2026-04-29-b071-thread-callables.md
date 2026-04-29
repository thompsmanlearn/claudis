# B-071: Thread Architecture — Write Callables

**Card:** B-071
**Date:** 2026-04-29
**Session type:** Lean — directed card execution

---

## Tasks Completed

- Supabase trigger `update_thread_last_activity()` + `thread_entry_activity_trigger` created — fires on `thread_entries` INSERT, updates parent thread's `last_activity_at = now()`
- Six uplink callables registered in `anvil/uplink_server.py`:
  - `create_thread(title, question, bound_agent=None)` — inserts thread, writes initial state_change entry
  - `add_thread_entry(thread_id, entry_type, content, source, embed, metadata)` — inserts entry, optionally embeds in ChromaDB `thread_entries` collection
  - `update_thread_state(thread_id, state, close_reason)` — reads old state, patches thread, writes transition entry
  - `wire_thread_agent(thread_id, agent_name)` — validates webhook_url, patches bound_agent, writes entry; agent_name=None unwires
  - `get_threads(state='active')` — filtered by state, ordered by last_activity_at desc; state=None returns all
  - `get_thread_entries(thread_id)` — chronological entry list
- Two private helpers added: `_validate_agent_webhook()`, `_insert_thread_entry()` (shared embed + chromadb_id backfill logic)
- Uplink restarted; reconnected successfully
- Smoke test: 10/10 steps passed; DB and ChromaDB clean after teardown

---

## Key Decisions

- **Shared `_insert_thread_entry` helper**: all callers that write thread_entries (create_thread, update_thread_state, wire_thread_agent, add_thread_entry) route through it. Centralises embed logic and chromadb_id backfill — prevents each caller from having to duplicate it.
- **chromadb_id = Supabase row UUID**: clean and unique; no need for a separate ID namespace.
- **embed=False for state_change entries written by callables**: state transitions don't need semantic retrieval; skipping ChromaDB avoids noise in the thread_entries collection.
- **Trigger, not callable code, for last_activity_at**: future writers (agents, scripts) get the invariant for free. Noted in commit message as a process observation — this should have been in B-070's substrate.

---

## Capability Delta

**New:** Thread working surface is fully operational from code. Any caller can create a thread, append entries (with or without ChromaDB embedding), transition state, and wire an agent — all via uplink callables. B-072 (Anvil UI) can now be built directly on top of `get_threads` and `get_thread_entries` without any additional backend work.

**New:** Supabase trigger pattern established for denormalized timestamp maintenance — `update_thread_last_activity` is a reusable template for similar "last touched at" columns in future tables.

---

## Lessons Written

1 lesson — see Step 7.

---

## Branches / Commits

- Branch: `attempt/b071-thread-callables` (merged, deleted)
- Merge commit: `a833f87` — B-071 thread callables
- TRAJECTORY.md: `c811a40`

---

## Usage

Session ~20%, weekly ~%
