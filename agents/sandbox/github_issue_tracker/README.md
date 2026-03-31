# github_issue_tracker

**Status:** sandbox  
**Type:** scout  
**Built:** 2026-03-31  
**Workflow ID:** F2lRufWUOXAGv5GB  
**Telegram command:** /gh_issues

## Purpose
Scans `thompsmanlearn/claudis` repo for open GitHub issues unactioned for >3 days. Sends Telegram alert with stale issue list. Writes scan report to `experimental_outputs`.

## Trigger
`POST http://localhost:5678/webhook/github-issue-tracker`

## Data flow
Webhook → GitHub API (issues) → Filter stale (>3d) → Telegram alert → experimental_outputs

## First scan result
1 stale issue detected: #1 "Test: /gh_task end-to-end verification" (6 days, label: from-telegram)

## Notes
- Filters out pull requests (GitHub API returns PRs in issues endpoint)
- Uses `$('Filter Stale Issues').item.json` for upstream node data reference
- SUPABASE_SERVICE_KEY and GITHUB_TOKEN are scrubbed — see .env
