# Project Node: Node 1: Boot-chain docs

## Goal

Perform a reader audit for 6 boot-chain documents in ~/aadp/claudis/.

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
  1. CONTEXT.md
  2. CONVENTIONS.md
  3. TRAJECTORY.md
  4. DIRECTIVES.md
  5. BACKLOG.md
  6. LEAN_BOOT.md

Run: mkdir -p ~/aadp/root_doc_audit
Write findings to ~/aadp/root_doc_audit/node1.md. Include grep evidence per file (which grep targets matched).

REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this SQL:
UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='8be3f7b3-50e0-4331-bf93-d9410c5e8091';
Confirm result shows status: ok before this session closes.

## Context
Classify 6 boot-chain docs: CONTEXT, CONVENTIONS, TRAJECTORY, DIRECTIVES, BACKLOG, LEAN_BOOT. No deps — runs in parallel with nodes 2/3/4.

## Node ID
8be3f7b3-50e0-4331-bf93-d9410c5e8091
