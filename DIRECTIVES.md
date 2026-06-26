# Project Node: Node C: Scratch file verify

## Goal
1. Use the Bash tool to append the line "auto-cycle-test: Node C complete" to ~/aadp/auto_cycle_test.txt.
2. Read ~/aadp/auto_cycle_test.txt and verify all three lines (Node A, Node B, Node C) are present.
3. REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this exact SQL:
   UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='571903b5-60ea-4ff9-b258-77f645c6fa41';
   Confirm the result shows status: ok before this session closes.

## Context
Third and final node in the auto-cycle walk test. Depends on Node B.

## Node ID
571903b5-60ea-4ff9-b258-77f645c6fa41
