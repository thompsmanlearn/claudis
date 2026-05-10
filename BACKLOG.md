## B-124: Put stats_server under version control
Status: ready
Depends on: B-123

### Goal
Bring ~/aadp/stats-server/ under git version control so future edits to stats_server.py are recoverable. The B-123 fix required reconstructing six constants from inference because no history existed. Close that gap so the next breaking edit is a diff revert, not a reconstruction.

### Context
Investigation on 2026-05-10 confirmed `cd ~/aadp/stats-server && git log` returned "no git" — the directory is not a repo. stats_server.py is a critical service (port 9100, runs lesson injection, grader, GitHub ops, session triggers). It has a sync pattern with the canonical copy at ~/aadp/claudis/stats-server/stats_server.py (per the lesson_stats_server_deploy_path_2026-04-26 lesson).

Decision needed during execution: should ~/aadp/stats-server/ be its own repo, OR should the deploy path become a symlink to ~/aadp/claudis/stats-server/ so the existing claudis repo's history covers it? The lesson on file says "Two files in sync, not symlinked." Symlinking would consolidate history but changes the deploy pattern. Pick whichever is simpler and document the choice in the session artifact.

### Done when
- ~/aadp/stats-server/stats_server.py and any other files in that directory are under git version control (either as their own repo or via symlink to a tracked path)
- `git log` from the stats-server deploy directory returns at least one commit showing the current state of stats_server.py
- The .gitignore is appropriate (no .env files, no __pycache__, no logs)
- If a new repo: README.md exists explaining what stats_server is and where it deploys
- If symlinked: confirm the systemd service still finds the file and starts cleanly; restart aadp-stats and verify with `systemctl is-active`
- The lesson_stats_server_deploy_path_2026-04-26 lesson is updated or replaced to reflect the new pattern, whichever was chosen
- Session artifact documents the choice (own repo vs symlink) and why

### Scope
Touch: ~/aadp/stats-server/ (new git init or symlink change), ~/aadp/claudis/stats-server/ if symlinking, lessons collection (update existing lesson)
Do not touch: stats_server.py contents, any other service, any Anvil callable, any other directory
