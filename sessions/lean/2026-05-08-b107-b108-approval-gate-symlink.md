# Session: 2026-05-08 — B-107/B-108: Auto-cycle approval gate + lean_runner.sh symlink

Code commit: 5b26824 (merged ec60b85)

## B-108: lean_runner.sh symlink

Replaced `~/aadp/sentinel/lean_runner.sh` (live copy) with a symlink to
`~/aadp/claudis/sentinel/lean_runner.sh` (canonical). Stats server's hardcoded
path still resolves. Symlink pattern codified in CONVENTIONS.md. DEEP_DIVE_BRIEF
Section 12 entry marked resolved.

## B-107: Auto-cycle approval gate

### What Changed
- **sentinel/lean_runner.sh**: `projects` query now includes `name` field. When
  all project nodes are done, instead of auto-PATCHing `aadp_projects.status=complete`,
  writes an `agent_feedback` annotation: `target_type='project_completion'`,
  `intent_type='question'` (in metadata). Fallback: `auto_cycle_completion=true`
  in system_config restores old behavior (default false, inserted this session).
- **anvil/uplink_server.py**: Added `confirm_project_complete(project_id, notes)` and
  `reject_project_completion(project_id, reason)` callables. Former PATCHes project
  to complete and writes state_change annotation. Latter leaves project active and
  records rejection reason.
- **system_config**: `auto_cycle_completion = false` inserted.
- **DEEP_DIVE_BRIEF.md**: Section 12 gaps marked resolved; auto-cycle description
  updated; lean_runner.sh entry updated to reflect symlink.

### Smoke Test
- lean_runner.sh: `bash -n` syntax check passed.
- Real project "Document AADP on the Site" (a1b2c3d4) has 8/8 nodes done — exactly
  the condition B-107 guards. Ran annotation path manually: annotation id=ac6a351a
  written with target_type=project_completion. auto_cycle_completion=False confirmed
  from config. Annotation is live in agent_feedback and visible to Anvil attention queue.
- Anvil restarted cleanly with new callables loaded.

### Lessons Applied
None pre-loaded were directly triggered.
