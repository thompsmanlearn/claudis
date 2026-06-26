# Project Node: Node A: Scratch file write

## Goal
1. Use the Bash tool to append the line "auto-cycle-test: Node A complete" to ~/aadp/auto_cycle_test.txt (create the file if it does not exist).
2. Confirm the line was written by reading the file.
3. REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this exact SQL:
   UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='72f49312-1a3a-49ad-9316-db0ef37bc9d6';
   Confirm the result shows status: ok before this session closes.

## Context
First node in the auto-cycle walk test (A→B→C). No dependencies.

## Node ID
72f49312-1a3a-49ad-9316-db0ef37bc9d6
