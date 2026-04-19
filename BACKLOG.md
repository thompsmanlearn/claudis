
B-041: Skills tab on Anvil dashboard

Status: ready Depends on: B-036
Goal

Add a Skills tab to the Anvil dashboard so Bill can see which Claude Code skills exist, how often they're being loaded, and review their content. Skills are a key part of the system's knowledge infrastructure but currently have zero visibility — they're markdown files in a repo directory, routed by a text file (CATALOG.md). This tab makes them a managed, observable resource.
Context

Skills live at ~/aadp/claudis/skills/ with subdirectories per domain: agent-development, system-ops, communication, research, triage, anvil. Routing is defined in CATALOG.md — keyword matches trigger skill loading. There is no structured data about skills anywhere. This card creates that structure. Create a skills_registry table in Supabase: CREATE TABLE skills_registry (id uuid DEFAULT gen_random_uuid() PRIMARY KEY, name text UNIQUE NOT NULL, description text, trigger_keywords text[], file_path text NOT NULL, times_loaded int DEFAULT 0, last_loaded timestamptz, created_at timestamptz DEFAULT now(), updated_at timestamptz DEFAULT now()); Populate the table from the existing skill files and CATALOG.md routing rules as part of this card. Content is not stored in the table — it's read from the file system on demand via an uplink callable. This avoids syncing file content into Supabase. Tracking times_loaded increments would require a change to the boot chain's skill loading step. If wiring that into the boot chain is complex, defer it to a follow-up card and just populate the registry and build the tab in this one. The tab navigation pattern exists from prior tabs (Fleet, Sessions, Lessons, Memory). Anvil skill reference at skills/anvil/REFERENCE.md. See ADR at architecture/decisions/anvil-curation-surface.md, Skills section.
Done when

    skills_registry table exists in Supabase with the schema above
    Table populated with all existing skills from ~/aadp/claudis/skills/
    Skills tab exists on the dashboard showing: name, description, trigger keywords, times_loaded, last_loaded
    Tapping a skill shows its full content (read from file system via uplink callable)
    Uplink callables registered: get_skills(), get_skill(name) (returns content from file)
    Usable at phone width
    Both repos committed and pushed (claudis main, claude-dashboard master)

Scope

Touch: Supabase schema (new table), ~/aadp/claudis/anvil/uplink_server.py, ~/aadp/claude-dashboard/client_code/Form1/__init__.py Do not touch: Skill file content, CATALOG.md routing logic, stats_server.py, agent workflows

## B-042: Autonomous project node cycling
Status: ready
Depends on: none
Goal
Cycle through the remaining 7 nodes of the "Document AADP on the Site" project autonomously. For each node: mark it in_progress in aadp_project_nodes, build the page content, update generate_site.py if a new page template is needed, mark the node done, regenerate the site, and move to the next unblocked pending node. Continue until all nodes are complete or a node genuinely requires Bill's input — in which case, write the question to the site's Current Focus section and stop cleanly.
Context
The one-page loop is proven as of 2026-04-19. generate_site.py regenerates index.html and status.json from live Supabase data and pushes to the GitHub Pages repo. lean_runner.sh calls it automatically on session success. The project graph is in aadp_projects and aadp_project_nodes tables in Supabase — 8 nodes total, 1 complete (home page refinement), 7 pending. The site repo is at ~/aadp/thompsmanlearn.github.io. The Anvil embed is live at https://inborn-rotating-anole.anvil.app#EmbedControl. Desktop sessions read the site via https://thompsmanlearn.github.io and status.json to give Bill strategic direction. Agent data comes from agent_registry, lessons from lessons_learned, session artifacts from ~/aadp/claudis/sessions/lean/. Architecture decisions are in ~/aadp/claudis/architecture/decisions/. Bill does not want approval gates between nodes — keep moving, document decisions, let Bill steer via the direction input if he disagrees.
Done when

All 8 nodes in aadp_project_nodes have status done
Site has working multi-page navigation (or single-page sections) covering: fleet, capabilities, architecture, session log, direction log
Each page/section renders from live Supabase data where applicable
generate_site.py handles all pages in a single run
Site regenerated and pushed after final node
Session artifact written

Scope
Touch: ~/aadp/thompsmanlearn.github.io/ (all site files), aadp_project_nodes table (status updates), generate_site.py
Do not touch: Anvil dashboard (Form1), uplink_server.py, lean_runner.sh, agent workflows, PROTECTED.md resources

B-043: Auto-cycle between sessions
Status: ready
Goal
When a lean session completes successfully and the active project has remaining unblocked pending nodes, automatically trigger the next lean session. The system should cycle through a project graph without human intervention until all nodes are done, a node fails, or Bill sets a stop flag. Also: add sentinel/lean_runner.sh to version control — it's disk-only and at risk.
Context
lean_runner.sh already calls generate_site.py on success. The project graph is in aadp_projects and aadp_project_nodes. A node is unblocked when all its dependencies have status done. The trigger endpoint is localhost:9100/trigger_lean. Bill does not want approval gates between nodes — the system should keep moving. A stop mechanism is needed: check a flag in Supabase (e.g., system_config key auto_cycle_enabled) before triggering. Bill can set this to false from the Anvil dashboard or site to pause cycling. DIRECTIVES.md should be auto-populated with the next node's context before triggering.
Done when

lean_runner.sh checks for unblocked nodes after successful session close
If unblocked node exists and auto-cycle is enabled, sets DIRECTIVES.md and triggers next session
Stop flag in system_config respected — if false, session ends normally without re-triggering
lean_runner.sh committed to claudis repo
Session artifact written

Scope
Touch: lean_runner.sh, ~/aadp/claudis/ (to add lean_runner.sh), system_config table
Do not touch: Anvil dashboard, uplink_server.py, generate_site.py, agent workflows
