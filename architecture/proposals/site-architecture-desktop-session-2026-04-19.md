# Site Architecture — Desktop Session 2026-04-19

*Drafted by Opus desktop session with Bill. Captured by Claude Code.*

---

## The Vision

The system should be able to take on complex, multi-session projects and cycle through them autonomously — making progress, documenting what it's doing on a public site, and incorporating direction from Bill when he gives it. Bill does not want to be a bottleneck. The default is: keep moving, document decisions, let Bill steer when he chooses to.

---

## Three Layers

**Supabase — single source of truth.**
Project state, session logs, decisions, findings — all in Supabase. The site renders from Supabase data. Claude Code reads and writes Supabase directly through MCP tools. No mirroring or syncing — Supabase is the database, the site is the frontend.

**GitHub Pages — display layer.**
Static HTML committed to `thompsmanlearn/thompsmanlearn.github.io`. At session close, Claude Code queries Supabase for current project state, generates updated HTML pages, and pushes to the site repo. The site updates automatically on push. Also maintains `status.json` at root — compact machine-readable state for desktop sessions to fetch.

**Anvil — interactive layer.**
Small, focused embeddable forms (not the full dashboard). Embedded as iframes in static site pages. Primary form: `EmbedControl` — direction input, session status, heartbeat, start button, output display. Desktop sessions (Opus) can read the site via web_fetch to see current project state and draft direction for Bill.

---

## What Was Built (2026-04-19, Session 1)

- `thompsmanlearn/thompsmanlearn.github.io` repo created with GitHub Pages
- `index.html` — one-page site: system overview, last 3 sessions, current directive, embed placeholder
- `status.json` — machine-readable state at site root
- `EmbedControl` Anvil form — five elements: heartbeat, session status, direction input, start button, output display
- `allow_embedding: true` set in anvil.yaml
- Uplink callables: `get_site_status()`, `update_site()`

**Loop is proven when:** Bill reads the site, types direction, hits start, sees output in same place — without navigating elsewhere.

---

## What Comes Next

1. **Bill publishes EmbedControl** — gets the embed URL, updates index.html iframe placeholder
2. **Test the full loop** — direction → session → output visible on site
3. **Project graph schema** — `projects` + `project_nodes` tables in Supabase
4. **Decompose "document AADP"** into ~8 project nodes; Bill reviews before cycling starts
5. **First autonomous cycling attempt** — agent works through nodes, updates site after each
6. **Wire `update_site()` to session close** — via lean_runner.sh or session-close skill
7. **Expand to multi-page structure** — fleet page, capabilities page, direction log

---

## Key Design Decisions

- **No framework, no build step** — plain HTML + CSS. Agent commits raw files, they just work.
- **Decomposition requires human review** — the first project graph is reviewed by Bill before cycling starts. After that, cycling is autonomous.
- **Stop signal via Supabase** — a `project_abort` flag the agent checks at each checkpoint. STOP button in EmbedControl writes this flag.
- **status.json for desktop sessions** — compact state file avoids web_fetch noise from full HTML page.
- **EmbedControl is not the dashboard** — it's a focused control surface embedded in the site. The Anvil dashboard remains unchanged for operations.

---

## Bill's Principles (from this session)

- "I tend to over-complicate." Start simple. Get the loop working before adding sophistication.
- "I don't want to create too many wait-for-my-approvals." The agent makes its best call and keeps moving. Bill steers, doesn't approve every step.
- The first project is AADP documenting itself — domain known, data live, building the site exercises the exact architecture being built.
