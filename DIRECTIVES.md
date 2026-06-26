# Project Node: Node 3: State/process docs

## Goal

Perform a reader audit for 5 state/process documents in ~/aadp/claudis/.

For each document, grep the following files for the document filename (case-insensitive):
  ~/aadp/claudis/sentinel/lean_runner.sh
  ~/aadp/claudis/LEAN_BOOT.md
  ~/aadp/mcp-server/.claude/skills/bootstrap.md
  ~/aadp/stats-server/stats_server.py
  ~/aadp/thompsmanlearn.github.io/generate_site.py
  ~/aadp/claudis/anvil/uplink_server.py

Classify each as:
  MACHINE-READ — filename appears in at least one grep target (cite which)
  MAYBE-HUMAN-READ — not machine-read, but plausibly read by a human or desktop session (explain why)
  NO READER FOUND — nothing references it

Documents to classify:
  1. PROJECT_STATE.md  (~/aadp/claudis/PROJECT_STATE.md — the file being classified, not the grep targets)
  2. INQUIRIES.md
  3. USERS_MANUAL.md
  4. bootstrap.md  (~/aadp/claudis/bootstrap.md — the root-level file; the skill bootstrap.md at mcp-server/.claude/skills/ is a grep target, not this file)
  5. anvil-redesign-principles-and-plan.md

Run: mkdir -p ~/aadp/root_doc_audit
Write findings to ~/aadp/root_doc_audit/node3.md. Include grep evidence per file.

REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this SQL:
UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='1e580d20-2f25-497c-8a67-4cde0ebc4413';
Confirm result shows status: ok before this session closes.


## Context
Classify 5 state/process docs: PROJECT_STATE, INQUIRIES, USERS_MANUAL, bootstrap, anvil-redesign-principles-and-plan. No deps — runs in parallel with nodes 1/2/4.

## Node ID
1e580d20-2f25-497c-8a67-4cde0ebc4413
