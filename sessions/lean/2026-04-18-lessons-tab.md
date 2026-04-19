# Session: 2026-04-18 — lessons-tab

## Directive
B-036: Add a Lessons tab to the Anvil dashboard for browsing, searching, and curating the lesson corpus.

## What Changed
**uplink_server.py** — 4 new callables:
- `get_lessons(filter, limit)` — Supabase query for recent/most_applied/never_applied/broken views
- `search_lessons(query)` — ChromaDB semantic search with Supabase join for full metadata + distances
- `update_lesson(lesson_id, delta)` — read-modify-write confidence (clamped 0.0–1.0)
- `delete_lesson(lesson_id, chromadb_id)` — removes from Supabase + ChromaDB (best-effort on ChromaDB)

**client_code/Form1/__init__.py** — dashboard restructured with tab navigation:
- Fleet/Lessons tab buttons at top; Fleet is default, Lessons lazy-loads on first switch
- Lessons tab: 5 view buttons (Recent, Top Used, Never Applied, Broken, Search)
- Per-lesson card: title, category, times_applied, confidence, date + 👍👎🗑️ actions
- Search view: ChromaDB semantic search with distance score shown per result
- Thumbs show updated confidence after action; delete hides card immediately

Both repos committed and pushed (claudis ea746f5, claude-dashboard af871b7). Uplink restarted and connected.

## What Was Learned
- lessons_learned schema: id (uuid), title, category, content, confidence, times_applied, source, created_at, updated_at, chromadb_id
- ChromaDB query returns IDs in ranked order; Supabase batch-fetch by chromadb_id preserves that order via re-join
- Anvil tab navigation via visibility toggle on ColumnPanel is sufficient — no native tab widget needed

## Unfinished
Nothing. All B-036 done-when criteria met.
