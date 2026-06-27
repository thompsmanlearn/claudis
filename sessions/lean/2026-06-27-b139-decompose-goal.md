# 2026-06-27 — B-139: decompose_goal callable

**Directive:** B-139
**Code commit:** (see below)

## What was built

Added `decompose_goal(goal, revision_notes='', prior_project_id=None)` callable to `anvil/uplink_server.py`.

- Calls Opus 4.8 (streaming, adaptive thinking) with a system prompt encoding lean-session capabilities, node type vocabulary (write/build/polish), and the evidence-printing convention
- Parses Opus JSON response (3–7 nodes)
- INSERTs into `aadp_projects` with `status='draft'`
- INSERTs nodes into `aadp_project_nodes` in order; each node's `dependencies` = `[prev_node_id]` (linear chain); node 1 has `[]`
- Returns `{project_id, project_name, nodes: [{id, name, type, context, acceptance_criteria}]}`
- `revision_notes` + `prior_project_id` → fetches prior node list, includes it in prompt; always creates a NEW project

Also altered `aadp_projects` CHECK constraint to allow `status` values: `draft`, `planning`, `active`, `paused`, `complete`, `abandoned`.

## Capability Delta

**Before:** No way to decompose a goal into structured project nodes. `aadp_projects` + `aadp_project_nodes` tables existed but had no writer.

**After:** `decompose_goal` callable is the writer. Anvil dashboard (B-140) is the named reader that will surface the plan for Bill to review and launch.

**Reader:** B-140 (Projects tab) — explicitly scoped in backlog.

## Verification (grader evidence)

Call 1 output (verbatim from test run):

```
project_id: e375de34-6752-4e4c-84b8-a1e13653f51c
project_name: Transformer Attention 2024 Research Summary
node count: 5

  Node 1: [build] Search and identify candidate papers
    criteria: Run web/API searches for 2024 transformer attention papers. Print verbatim: full search queries used, raw result listings...
  Node 2: [build] Rank and select top three by citations
    criteria: Compare citation counts from search results. Print verbatim: a ranked table...
  Node 3: [write] Extract key details per paper
    criteria: For each of 3 papers, print verbatim: title, authors, venue, citation count, abstract text...
  Node 4: [write] Write summary document
    criteria: Write summary.md and print its full file contents verbatim (cat output)...
  Node 5: [polish] Verify accuracy and citations
    criteria: Re-check each paper's citation count. Print verbatim: each claim, the source value, and PASS/FAIL...

DB project status: draft (expected: draft)

Linear chain verification:
  Node 1 deps: [] OK
  Node 2 deps: ['25823219-0b40-4b34-a186-9f1b74821950'] OK
  Node 3 deps: ['12102bd4-388a-4ee6-b9a1-b5e7cbd7af2f'] OK
  Node 4 deps: ['493ee91f-68e3-4c56-9747-5718be92f4e4'] OK
  Node 5 deps: ['9d24ba38-68c3-446b-87a0-93c53d4061a0'] OK
```

Call 2 (revision):

```
project_id: fd5d69bf-7337-44d1-83ba-83a3ab9f9726 (differs from call 1: True)
project_name: Top 3 Transformer Attention Papers 2024
node count: 5
  Node 1: [build] Find candidate paper titles   ← revised per notes
```

All done criteria met.
