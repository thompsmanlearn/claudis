# /architecture/prompts

Versioned prompt history. One file per version.

**Naming:** `v{N}.md`

**Source of truth:** Supabase `agent_prompts` table, agent_name='claude_code_master'. This folder is the git-versioned backup.

**Rollback:** Read `v{N}.md`, pass to `prompt_update` with change_notes explaining the revert.
