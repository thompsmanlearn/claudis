Retire the thread system

The thread system was never functional. Retire it cleanly.

Done when:

1. Threads tab removed from Form1/__init__.py — tab button, panel, and all methods: _build_threads_layout, _load_threads, _create_thread_clicked, _threads_filter_changed, _reload_threads, _build_thread_card, _load_thread_entries, _build_thread_actions, and any helper closures and state variables (_threads_state_filter, _threads_loaded) that only serve threads.

2. Thread callables removed from uplink_server.py — all functions from create_thread through set_watch_state (~lines 2096–2950) that exclusively serve the thread system. Do not remove get_feedback_threads (line 1151) — it is used by the Research tab. Do not remove _insert_thread_entry if anything non-thread calls it (verify first).

3. thread_research_agent retired — UPDATE agent_registry SET status = 'retired' WHERE agent_name = 'thread_research_agent'.

4. Supabase tables left intact — do not drop threads, thread_entries, or any other table.

5. Commit pushed to main.

Scope: client_code/Form1/__init__.py, anvil/uplink_server.py, agent_registry row. Do not touch: Research tab, get_feedback_threads, any other tab, any Supabase tables.
