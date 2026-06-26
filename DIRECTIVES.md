# Project Node: Node 5: Collation

## Goal

Collation pass only. Do NOT perform new analysis or grep — only read and arrange existing output.

Step 1: Read all four audit files:
  ~/aadp/root_doc_audit/node1.md
  ~/aadp/root_doc_audit/node2.md
  ~/aadp/root_doc_audit/node3.md
  ~/aadp/root_doc_audit/node4.md

Step 2: Write ~/aadp/root_doc_audit/SUMMARY.md with this structure:

# Root Doc Reader Audit — SUMMARY

## MACHINE-READ
[every file classified as MACHINE-READ, with which scripts reference it, from the node reports]

## MAYBE-HUMAN-READ
[every file classified as MAYBE-HUMAN-READ, with the reasoning from the node reports]

## NO READER FOUND
[every file with no reader found]

Do not add judgment, recommendations, or decisions about what to cut. Bill and a desktop session will read this bundle and decide.

REQUIRED FINAL STEP — mark this node done. Run mcp__aadp__supabase_exec_sql with this SQL:
UPDATE aadp_project_nodes SET status='done', updated_at=NOW() WHERE id='611f9811-cb54-4239-af0c-9a33b0f0dac1';
Confirm result shows status: ok before this session closes.


## Context
Collate node1-4 audit files into SUMMARY.md under three buckets. No new analysis — pure assembly. Depends on all four predecessors.

## Node ID
611f9811-cb54-4239-af0c-9a33b0f0dac1
