# Session Artifact: B-124 — Put stats_server under version control

**Date:** 2026-05-10
**Card:** B-124
**Status:** Complete

---

## What was done

Initialized a git repository at `~/aadp/stats-server/` so the running stats server is now under version control. Committed the current state of `stats_server.py` (post-B-123 restore, 245386 bytes) along with `requirements.txt`, `.gitignore`, and `README.md`.

```
Commit: d28f88c  Initial commit: put stats_server under version control (B-124)
```

---

## Decision: own repo vs symlink

**Chosen: own git repo at `~/aadp/stats-server/`.**

Symlink was the lesson-recommended default (`lesson_symlink_versioning_non_git_dirs_2026-04-26`), but two constraints ruled it out:

1. **Whole-directory symlink breaks the venv.** The systemd service uses `ExecStart=/home/thompsman/aadp/stats-server/venv/bin/python stats_server.py`. The venv lives only in the deploy dir and cannot be version-controlled. Replacing `~/aadp/stats-server/` with a symlink would destroy the venv path.

2. **File-level symlinks can't satisfy `git log` from the deploy dir.** With only `stats_server.py` symlinked, `~/aadp/stats-server/` is still not a git repo, so `git log` returns "not a git repository."

Own repo satisfies all done-when criteria directly and requires no changes to the service or its paths.

---

## Sync pattern going forward

Two separate git repos. Manual sync required:

```bash
# After editing in claudis canonical:
cp ~/aadp/claudis/stats-server/stats_server.py ~/aadp/stats-server/stats_server.py
sudo systemctl restart aadp-stats
cd ~/aadp/stats-server && git add stats_server.py && git commit -m "sync: <description>"
```

---

## Done-when verification

- [x] `~/aadp/stats-server/stats_server.py` under git version control (own repo)
- [x] `git log` from deploy directory returns commit d28f88c showing current state
- [x] `.gitignore` excludes venv/, __pycache__/, *.bak, .env files
- [x] `README.md` explains service, deploy path, and version control decision
- [x] `systemctl is-active aadp-stats` → active (no service disruption)
- [x] `lesson_stats_server_deploy_path_2026-04-26` updated in Supabase + ChromaDB to reflect two-repo pattern

---

## Lessons applied

- `lesson_symlink_versioning_non_git_dirs_2026-04-26` — consulted; ruled out due to venv constraint
- `lesson_mcp_server_unversioned_risk_2026-04-12` — this card closes the exact gap that lesson identified
