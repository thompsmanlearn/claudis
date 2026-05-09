# Session: 2026-05-08 — B-100: Sub-question spawning — recursive research

## Directive
Build the spawn mechanism: sub-questions become child threads with parent linkage.

## What Changed
- **DDL on threads**: Added parent_thread_id uuid FK referencing threads(id).
- **system_config**: Added auto_spawn_sub_questions='false' flag.
- **anvil/uplink_server.py**: Added three callables:
  - spawn_thread_from_sub_question(parent_thread_id, sub_question_entry_id, inherit_charter_sections): creates child thread, marks sub-question as spawned, inherits charter sections if requested
  - write_child_findings_to_parent(child_thread_id): writes child's summary as analysis entry on parent
  - get_thread_family(thread_id): returns parent + children for a thread
- **Form1/__init__.py**: 
  - Spawn button on unspawned sub_question_candidate entries (↗ Spawn as child thread)
  - Parent/children section at bottom of thread view (parent link, children list, write-findings button for closed children)

## Smoke Test
- Created child thread (a64b48e1) from sub-question cda4329d on parent thread e0560a85
- parent_thread_id correctly set ✓
- Sub-question marked spawned in metadata ✓
- get_thread_family would return parent=e0560a85 for child, and children=[a64b48e1] for parent

## What Was Learned
Auto-spawn is intentionally defaulted off (system_config flag). The manual spawn path is the right default — let the grader rubric develop confidence before enabling automatic spawning. The write_child_findings_to_parent callable is wired to a button in the UI; it could also be called automatically when a child's grader verdict = 'complete' (future card).

## Unfinished
Auto-spawn (tier 2, grader-recommended) deferred per card scope. Will implement when manual spawn pattern is tested in real use. The "write findings to parent automatically on child completion" path is a natural next card.
