# Session: 2026-04-19 — site-loop-test

## Directive
Write a session artifact describing what AADP is, what was built today (the GitHub Pages site at thompsmanlearn.github.io, the EmbedControl Anvil form, and the direction loop), and what the system can do right now. Under 300 words.

## What Changed

**GitHub Pages site (thompsmanlearn.github.io):** A public-facing landing page for AADP. Gives the project a home — something Bill can share with collaborators or reference externally.

**EmbedControl Anvil form:** An Anvil form component that embeds in the GitHub Pages site. Provides an interactive control surface accessible from any browser without requiring the Anvil app directly.

**Direction loop:** A wiring between the site, the Anvil form, and the AADP backend — closing the loop so Bill can submit direction from the public site and have it route into the system (work_queue or equivalent).

## What AADP Is

AADP (Autonomous Agent Development Platform) is a self-improving agent system running on a Raspberry Pi 5. It consists of ~25 agents orchestrated via n8n, backed by Supabase (structured data) and ChromaDB (semantic memory). The system receives direction from Bill, decomposes it into tasks, executes autonomously, and accumulates lessons. The long-term goal: Bill states an intention and the system researches, builds, and executes without step-by-step direction.

## What the System Can Do Right Now

- Receive direction via Telegram or the Anvil dashboard
- Route tasks to work_queue and execute them autonomously on a schedule
- Monitor agent health, detect stale/failed agents, and alert Bill
- Ingest arXiv papers, synthesize research findings, and store them semantically
- Display fleet status, sessions, lessons, memory, and skills via the Anvil dashboard
- Embed a control surface in a public GitHub Pages site (as of today)

## Unfinished

- Feedback consumer agent: negative feedback patterns → Telegram alert or work_queue item
- Roblox pipeline: blocked on Bill's Roblox account + one Studio session
- Intention decomposition: design doc (ADR) not yet written
