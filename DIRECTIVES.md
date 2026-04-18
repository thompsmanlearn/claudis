Add stats_server.py and supporting infrastructure files to version control.
stats_server.py is 3,205 lines at ~/aadp/stats-server/stats_server.py. It contains inject_context_v3.1, run_research_synthesis, /trigger_lean, /lessons_applied, all ChromaDB proxy endpoints, and all GitHub operations. It is the single highest fragility in the system — disk-only, not in git.
Steps:

Read stats_server.py. Identify any hardcoded secrets, API keys, tokens, or credentials. The file already reads from ~/aadp/mcp-server/.env for most keys, but verify there are no inline secrets that snuck in.
If inline secrets are found, refactor to read from .env. Test that the server starts and responds: curl localhost:9100/healthz should return {"status":"ok"}.
Copy stats_server.py into the claudis repo at claudis/stats-server/stats_server.py. Include the systemd unit file from /etc/systemd/system/aadp-stats.service.
Also capture: the Supabase RPC function DDL for increment_lessons_applied_by_id and increment_lessons_applied. Query the live database for their definitions and save to claudis/stats-server/supabase_rpcs.sql.
Add .gitignore entries to prevent .env or any secret-bearing files from being committed.
Verify: sudo systemctl restart aadp-stats, confirm it comes up, curl localhost:9100/healthz, then hit /inject_context_v3 with a test payload to confirm the full chain works.
Commit and push to main.

Do not refactor, reorganize, rename, or improve stats_server.py. The goal is to get the working production code into git exactly as it runs today, minus any inline secrets. No cleanup, no optimization, no "while we're here" improvements.
