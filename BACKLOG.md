
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
