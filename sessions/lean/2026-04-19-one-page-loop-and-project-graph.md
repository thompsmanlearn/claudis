# Session: 2026-04-19 — One-page loop + project graph

## Directive
Build the one-page loop and project graph infrastructure. Prove the full direction→session→site-update cycle.

## What Changed

- **thompsmanlearn.github.io** — repo created, GitHub Pages live. `index.html` (dynamic, generated from live data) and `status.json` (machine-readable state for desktop sessions).
- **generate_site.py** — standalone script queries Supabase for agent/lesson counts, reads session artifacts and DIRECTIVES.md, generates full index.html and status.json, commits and pushes. Called by lean_runner.sh on successful session close.
- **lean_runner.sh** — wired to call generate_site.py after successful session. Site now auto-updates at every session close.
- **EmbedControl Anvil form** — standalone form for iframe embedding. Five elements: heartbeat (ping()), session status (get_lean_status()), direction input (write_directive()), start button (trigger_lean_session()), output display (get_session_artifacts(1)). Pushed to claude-dashboard master.
- **Hash routing in Form1** — `#EmbedControl` in URL opens EmbedControl form instead of dashboard. `allow_embedding: true` set in anvil.yaml.
- **iframe wired** — index.html embeds `https://inborn-rotating-anole.anvil.app#EmbedControl`.
- **Loop proven** — Bill typed "Test from site. Hello from Bill" in the direction box, hit Write Directive. DIRECTIVES.md updated on Pi. Full direction→system path confirmed working.
- **aadp_projects + aadp_project_nodes tables** — project graph schema in Supabase. Projects have: name, goal, status, metadata. Nodes have: type, status, dependencies (uuid[]), acceptance_criteria, context, session_budget, parent_id, output.
- **"Document AADP on the Site" project** — 8 nodes written to Supabase: home page refinement (done), fleet page, capabilities page, architecture page, session log page, direction log page, navigation/multi-page structure, site polish. Dependencies wired: nav depends on all content pages; polish depends on nav.
- **Project graph rendered on site** — progress bar, node list with status icons. Updates automatically each session close.

## What Was Learned
- `generate_site.py` calling Supabase directly via urllib (no third-party deps) works reliably from lean_runner.sh venv context.
- `projects` table name was taken by a prior unrelated schema — used `aadp_projects` / `aadp_project_nodes` instead.
- Hash routing in Anvil via `anvil.js.window.location.hash` works cleanly before `init_components` is called.

## Unfinished
- Project nodes 2–8 not yet executed (intentional — graph visible, cycling not started).
- `update_site()` uplink callable still exists but is superseded by `generate_site.py` running directly. Can be removed or left dormant.
- TRAJECTORY.md not updated this session — context pressure. Update at next session open.
