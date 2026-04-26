

B-060: Anvil feedback thread visibility

**Status:** ready
**Depends on:** B-059

### Goal

Make the agent_feedback write-back trail visible in Anvil. Each feedback item should display as a full conversation thread: the original content Bill expressed, then what Claude Code did in response (action_summary, action_session, action_result_url). This converts the feedback table from a one-way intent log into a visible conversation surface — the visibility leg of the OS pattern. Without it, the B-059 write-back trail exists in Supabase but Bill cannot see it.

### Context

- B-059 added action_summary, action_session, action_result_url to agent_feedback (2026-04-26). Old rows have null in these fields — display gracefully (no response line if action_summary is null).
- Visual treatment rule: action_summary starting with "Deferred:" → ⏸ icon, muted/faded text. All other non-null action_summary → ✅ icon, normal weight. Items with null action_summary (pre-B-059 legacy rows) → no response line.
- action_result_url, when present, renders as a clickable link.
- The bundle export (get_research_bundle) currently includes a Pending Feedback section with unprocessed rows. It needs two updates: (1) include the three new fields in those rows, (2) add a "Recently Resolved Feedback" section showing the last 10 processed items with action_summary and action_session.
- The Research tab currently does not render feedback history at all — only the submission boxes. This card adds the thread view.

### Done when

- get_research_bundle returns action_summary, action_session, action_result_url for each feedback row in the Pending section
- get_research_bundle includes "## Recently Resolved Feedback" section: last 10 processed items, each showing target, content, action_summary, action_session (and linked action_result_url if present)
- Research tab renders submitted feedback items as threads: original content + response below it
- ✅ / ⏸ icons and visual distinction between acted and deferred items are implemented
- Uplink restarted cleanly after callable changes
- Branches attempt/b060-feedback-visibility on both claudis and claude-dashboard merged to main/master

### Scope

Touch:
- `~/aadp/claudis/anvil/uplink_server.py` — get_research_bundle + any callable that returns feedback rows
- `~/aadp/claude-dashboard/client_code/Form1/__init__.py` — Research tab feedback display

Do not touch:
- agent_feedback schema (complete in B-059)
- Other dashboard tabs (Fleet, Sessions, Lessons, Memory, Skills, Artifacts)
- LEAN_BOOT.md or bootstrap skill
- Domain-specific Trigger buttons (B-062+)
- Export generalization to other tabs (B-061)
- Retroactive backfill of action_summary on old rows

B-061a: Bring close-session.md into claudis version control

**Status:** ready

### Goal

Copy ~/aadp/mcp-server/.claude/skills/close-session.md (and bootstrap.md) into the claudis repo so load-bearing rules are version-controlled. Currently these files sit outside git — a rule added to close-session.md can disappear silently with no history. Documented as a gap in DEEP_DIVE_BRIEF Section 12.

### Context

- Live skill files are at ~/aadp/mcp-server/.claude/skills/ — Claude Code loads them from there and that path must not change.
- The claudis repo already has a skills/ directory (agent-development, system-ops, etc.) but those are CATALOG skills, not Claude Code session skills. A new subdirectory (e.g. claudis/claude-skills/) or a note in an existing location is needed.
- The right sync pattern is: claudis is the canonical source → cp to mcp-server path after edit (same as stats-server pattern). Or: edit in place at mcp-server, cp to claudis for version control. Either works; pick one and document it in CONVENTIONS.md.
- After this card, DEEP_DIVE_BRIEF Section 12 gap entry ("close-session.md not version-controlled") can be removed.

### Done when

- close-session.md and bootstrap.md committed to ~/aadp/claudis/ (new subdirectory or alongside existing skills)
- CONVENTIONS.md updated with the sync pattern (which direction, when to sync)
- DEEP_DIVE_BRIEF Section 12 gap entry removed
- Commit pushed to main

### Scope

Touch:
- ~/aadp/claudis/ (new directory for Claude Code session skills)
- ~/aadp/claudis/CONVENTIONS.md
- ~/aadp/claudis/DEEP_DIVE_BRIEF.md (remove Section 12 gap entry)

Do not touch:
- ~/aadp/mcp-server/.claude/skills/ contents (live copies stay where Claude Code expects them)
- Skill file content (copy as-is; content changes are separate work)
