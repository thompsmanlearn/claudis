# Project Node: Node 4: Catch-all

## Goal

Catch-all audit pass. Goal: ensure no root-level .md in ~/aadp/claudis/ is missed.

Step 1: Run `ls ~/aadp/claudis/*.md` and list every file found.

Step 2: These files are covered by nodes 1, 2, and 3:
  Node 1: CONTEXT.md, CONVENTIONS.md, TRAJECTORY.md, DIRECTIVES.md, BACKLOG.md, LEAN_BOOT.md
  Node 2: CARRY_HEALTH.md, CARRY_PROPOSALS.md, CARRY_QUESTIONS.md, COLLABORATOR_BRIEF.md, DEEP_DIVE_BRIEF.md
  Node 3: PROJECT_STATE.md, INQUIRIES.md, USERS_MANUAL.md, bootstrap.md, anvil-redesign-principles-and-plan.md

Step 3: For every file NOT in the lists above, perform the reader audit using the same grep targets:
  ~/aadp/claudis/sentinel/lean_runner.sh
  ~/aadp/claudis/LEAN_BOOT.md
  ~/aadp/mcp-server/.claude/skills/bootstrap.md
  ~/aadp/stats-server/stats_server.py
  ~/aadp/thompsmanlearn.github.io/generate_site.py
  ~/aadp/claudis/anvil/uplink_server.py
Classify as MACHINE-READ / MAYBE-HUMAN-READ / NO READER FOUND.

Run: mkdir -p ~/aadp/root_doc_audit
Write findings to ~/aadp/root_doc_audit/node4.md.
If no uncovered files remain, write a confirmation that all 16 files are accounted for.

REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this SQL:
UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='c766b0fc-7ddc-4b6d-bcae-2174fa8b0aba';
Confirm result shows status: ok before this session closes.


## Context
List all root .md files in claudis, exclude those covered by nodes 1/2/3, classify whatever remains. No deps — runs in parallel with nodes 1/2/3.

## Node ID
c766b0fc-7ddc-4b6d-bcae-2174fa8b0aba
