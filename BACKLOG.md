

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

B-061: Generalize Export across all dashboard tabs

Status: ready
Depends on: B-057 (Research bundle export pattern), B-060 (feedback thread rendering)

Goal
Every meaningful tab in the Anvil dashboard gets an Export button that copies a structured markdown bundle of the current view's state to the clipboard, ready to paste into a desktop Claude session for analysis. This generalizes the pattern proven by B-057 (Research bundle export) so Bill can ask desktop Claude to analyze any part of the system he doesn't yet understand — Lessons, Memory, Sessions, Fleet, Errors, Skills, Artifacts.

Context
B-057 built get_research_bundle() and an Export button on the Research tab. Bill confirmed the pattern works end-to-end (export → paste to desktop Claude → desktop Claude analyzes → revised guidance flows back as Claude Code direction). The pattern needs to generalize so Bill is not limited to research as the only thing he can analyze.

Each domain bundle is a markdown blob with YAML frontmatter and structured sections. The format adapts to the domain but follows a consistent shell:

  ---
  bundle_type: <domain>
  generated_at: <iso8601 utc>
  view_filter: <whatever filter the user had applied>
  row_count: N
  ---

  ## Summary
  Short paragraph describing what's in this bundle and what desktop Claude
  can usefully do with it.

  ## <Domain-specific sections>
  ...

  ## Recently Resolved Feedback
  (when applicable — pulled from agent_feedback for this domain)

The "Summary" section is small but important: it tells desktop Claude the shape of the data and the kind of analysis Bill might want. For example, the Lessons bundle's summary should say "Use these to identify lessons that are stale, duplicated, poorly worded, or never relevant."

Concrete changes per tab:

LESSONS TAB
Callable: get_lessons_bundle(filter='recent', limit=50)
Honors current filter: recent / top_used / never_applied / broken / search.
Includes per-lesson: id, title, category, content (truncated to ~500 chars with "[truncated]" marker if longer), confidence, times_applied, created_at, age_days, chromadb_id present yes/no.
Summary section: explains the filter view and what to look for (Bill flagged Never Applied as confusing — the bundle should make that view legible to desktop Claude).

MEMORY TAB
Callable: get_memory_bundle(collection=None)
If collection=None: returns a bundle of collection stats (name, doc count, sample document titles or first 100 chars).
If collection specified: returns up to 30 documents from that collection with their metadata.
Summary section: tells desktop Claude this is a snapshot for assessing collection health, retrieval quality, or cruft.

SESSIONS TAB
Callable: get_sessions_bundle(limit=10)
Recent session artifacts in chronological order.
For each: filename, date, directive, what changed (first 3 bullets), what was learned (first 3 bullets), unfinished items.
Summary section: framed for retrospectives ("which sessions ran well, which got stuck, are there patterns").

FLEET TAB
Callable: get_fleet_bundle()
All agents grouped by status (active, paused, retired, building, sandbox, broken).
For each: name, description, schedule, last update, recent feedback count, recent feedback content (last 3 items with their action_summary).
Summary section: framed for fleet health review and finding dead-weight agents.

ERRORS VIEW (Memory tab → Error Log)
Callable: get_errors_bundle()
Unresolved errors with full context: workflow, node, error_type, error_message, timestamp, age_hours.
Summary section: framed for triage ("which need immediate attention, which are noise").

SKILLS TAB
Callable: get_skills_bundle()
All skills with: name, trigger keywords, times_loaded, last_loaded, content excerpt (first 500 chars).
Summary section: framed for assessing skill coverage and retrieval triggering quality.

ARTIFACTS TAB
Callable: get_artifacts_bundle(agent_name=None, artifact_type=None, limit=30)
Honors current filter.
Per artifact: agent, type, created_at, content excerpt, rating, comment.
Summary section: framed for output quality review.

Each tab gets a ⬇ Export button in its header next to existing controls. Click → calls the appropriate get_X_bundle() callable → tries clipboard write → falls back to a TextArea modal if clipboard not available, matching the Research tab pattern.

Done when
- 7 new uplink callables registered (lessons, memory, sessions, fleet, errors, skills, artifacts)
- Each tab has a working Export button
- All bundles include the consistent header (bundle_type, generated_at, filter, row_count) and a Summary section
- Bundles for tabs that have associated agent_feedback rows include a "Recently Resolved Feedback" section
- A test export from each tab, pasted into a markdown viewer, renders cleanly with no broken structure
- Branch attempt/b061-export-generalize on both repos, merged to main/master, pushed

Scope
Touch:
  ~/aadp/claudis/anvil/uplink_server.py — add 7 new callables
  ~/aadp/claude-dashboard/client_code/Form1/__init__.py — add Export buttons to 7 tabs

Do not touch:
  Database schema (no new tables or columns)
  Existing callables (additive only)
  Bundle ingestion path (this is export only — re-import is a future card)
  Domain-specific Trigger buttons (those are B-062+)

Notes
- Keep bundle sizes reasonable. Truncate long content with markers. The goal is paste-into-chat usable, not exhaustive — desktop Claude can ask follow-up questions.
- Match the Research tab's clipboard-then-fallback pattern exactly. Don't reinvent.
- Skip tabs that genuinely have no useful export shape. If you decide a tab doesn't merit one, document why in the session artifact rather than building a useless button.
- The "Summary" section for each bundle is the smallest and most overlooked part. Get it right — it's what makes desktop Claude useful immediately rather than spending the first paragraph asking what kind of analysis Bill wants.
