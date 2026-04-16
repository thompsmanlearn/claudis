# BACKLOG.md — AADP Lean Session Backlog

## B-001: Smoke test lean control loop
**Status:** done
**Artifact:** sessions/lean/2026-04-15-lean-control-loop-smoke-test.md

## B-002: Move skills into repo and fix LEAN_BOOT auto-start
**Status:** done
**Artifact:** sessions/lean/2026-04-15-skill-system-scaffold.md

## B-003: Create skill directory structure and catalog
**Status:** done
**Artifact:** sessions/lean/2026-04-15-skill-system-scaffold.md

## B-004: Answer seven skill system design questions
**Status:** done
**Artifact:** sessions/lean/2026-04-15-skill-design-questions.md

## B-005: Update skill structure from design review
**Status:** done
**Artifact:** sessions/lean/2026-04-15-skill-system-structure.md

## B-006: Pull ChromaDB lessons into skill references
**Status:** done
**Artifact:** sessions/lean/2026-04-15-skill-lessons-populate.md

## B-007: Write triage SKILL.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-triage-skill-write.md

## B-008: Write agent-development SKILL.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-agent-dev-skill.md

## B-009: Write research SKILL.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-research-skill.md

## B-010: Write system-ops SKILL.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-system-ops-skill.md

## B-011: Write communication SKILL.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-communication-skill.md

## B-012: Clean DIRECTIVES.md and design backlog system
**Status:** done
**Artifact:** sessions/lean/2026-04-15-backlog-design.md

## B-013: Add Run: B-NNN short-pointer to LEAN_BOOT.md
**Status:** done
**Artifact:** sessions/lean/2026-04-15-backlog-bootstrap.md

## B-014: Smoke test Run: B-NNN short-pointer
**Status:** ready

### Goal
Verify that DIRECTIVES.md containing only "Run: B-014" 
correctly triggers Claude Code to read BACKLOG.md and 
execute this card.

### Context
See artifact: sessions/lean/2026-04-15-backlog-bootstrap.md
This tests the LEAN_BOOT.md step 4 change from B-013.

### Done when
- Claude Code found and executed this card from BACKLOG.md
- Session artifact confirms the short-pointer path was used
- Artifact pushed to GitHub

### Scope
Touch: sessions/lean/ (artifact only)
Do not touch: everything else

## B-015: Wire skill selection into LEAN_BOOT.md startup sequence
**Status:** ready
**Depends on:** B-013

### Goal
Add a skill selection step to LEAN_BOOT.md so Claude Code 
matches each directive against CATALOG.md and loads relevant 
skills before executing.

### Context
See artifact: sessions/lean/2026-04-15-skill-design-questions.md
The skill system is built but not connected. CATALOG.md has 5 
skills with "Applies when" and "Also triggers when" descriptions. 
SKILL.md files have full content. But the startup sequence goes 
straight from reading DIRECTIVES.md to executing — no step reads 
the catalog, matches the directive, or loads skills.

The selection step goes between reading the directive (step 4) 
and reading CONTEXT.md (step 5). Logic:
1. Read skills/CATALOG.md
2. Match the current directive against "Applies when" and 
   "Also triggers when" columns using judgment
3. Load matching SKILL.md files (read them into context)
4. If no skills match, proceed without — not every directive 
   needs a skill
5. Brief confirmation: "Loading: [skill names]. Proceeding."

Do not load references/lessons.md or references/patterns.md 
automatically — those are for Claude Code to pull on demand 
during execution if it needs deeper context.

### Done when
- LEAN_BOOT.md updated with skill selection step in the 
  startup sequence
- Stable backup updated
- Verification: after updating LEAN_BOOT.md, run the selection 
  logic against these three test directives and document results 
  in the session artifact:
  1. "Diagnose why the research synthesis agent stopped producing 
     output after yesterday's n8n update"
  2. "Write a new monitoring workflow for sandbox agent staleness"
  3. "Update TRAJECTORY.md with Q2 milestones"
  For each: which skills matched, which column triggered the 
  match, and which were correctly excluded. The third directive 
  should match zero skills — that's the negative case.
- Session artifact captures the updated startup sequence and 
  all three test results

### Scope
Touch: LEAN_BOOT.md, ~/aadp/prompts/LEAN_BOOT_stable.md, 
  sessions/lean/
Do not touch: skills/, CATALOG.md, BACKLOG.md, DIRECTIVES.md, 
  n8n workflows, agents

  B-015: Create Capability Amplifier Supabase Tables
Goal: Create the five Supabase tables for the Capability Amplifier: inquiry_threads, refinements, resources, projects, feedback_log.
Context: Architecture spec is in capability-amplifier-architecture-v2.md (uploaded to this conversation, also available as a session artifact). The data model section has the full schema. These tables are net-new — they don't touch existing AADP tables. Use the system-ops skill for Supabase DDL patterns.
Done when:

All five tables exist in Supabase with correct columns and types
inquiry_threads.parent_id is a self-referencing nullable FK
resources.thread_id, refinements.thread_id, projects.thread_id, and feedback_log.thread_id are FKs to inquiry_threads
feedback_log.resource_id is a nullable FK to resources
inquiry_threads.sparked_by_resource_id is a nullable FK to resources
status columns use text (not enum) — values enforced at application layer
projects.screenshots is jsonb
All tables have created_at defaulting to now()
Session artifact confirms table creation with column listing

Scope: Tables only. No data seeding (that's the next card). No RLS policies yet — add if trivial, skip if not.

## B-016: Create Capability Amplifier Supabase Tables
Status: ready
Depends on: none
Goal
Create the five Supabase tables for the Capability Amplifier: inquiry_threads, refinements, resources, projects, feedback_log.
Context
Architecture spec is in capability-amplifier-architecture-v2.md. The data model section has the full schema. These tables are net-new — they don't touch existing AADP tables. Use the system-ops skill for Supabase DDL patterns.
Done when

All five tables exist in Supabase with correct columns and types
inquiry_threads.parent_id is a self-referencing nullable FK
resources.thread_id, refinements.thread_id, projects.thread_id, and feedback_log.thread_id are FKs to inquiry_threads
feedback_log.resource_id is a nullable FK to resources
inquiry_threads.sparked_by_resource_id is a nullable FK to resources
status columns use text (not enum) — values enforced at application layer
projects.screenshots is jsonb
All tables have created_at defaulting to now()
Session artifact confirms table creation with column listing

Scope
Touch: Supabase (new tables only), sessions/lean/
Do not touch: existing AADP tables, BACKLOG.md, DIRECTIVES.md, skills/, n8n workflows

## B-017: Create GitHub file structure and seed first inquiry thread
Status: ready
Depends on: B-016
Goal
Create INQUIRIES.md and the processed/ directory in the claudis repo. Seed the first inquiry thread in the inquiry_threads table and its initial refinements in the refinements table.
Context
Phase 1, Card 2 of the Capability Amplifier. The trunk thread is: "Game development with Blender and UE5, using AI to skip traditional learning curves."
Initial refinements:

"Not tutorials — AI-assisted workflows and tools"
"More like practical tools I can try today (e.g. Meshy AI) than theory"
"How people are using Claude and other AI for Blender Python scripting and UE5 Blueprints"
"Tool announcements and new releases over educational content"

INQUIRIES.md format (from architecture doc): sections for Active Threads, New Questions, Refinements, Paused.
Done when

INQUIRIES.md exists at repo root with the seed thread and refinements in the documented format
processed/ directory exists at repo root (with a .gitkeep)
One row in inquiry_threads: trunk, parent_id null, status active
Four rows in refinements: one per refinement above, linked to the trunk thread, source = 'github'
All pushed to GitHub
Session artifact confirms file contents and Supabase row IDs

Scope
Touch: INQUIRIES.md (new), processed/.gitkeep (new), Supabase inquiry_threads + refinements tables, sessions/lean/
Do not touch: BACKLOG.md, DIRECTIVES.md, skills/, existing tables, n8n workflows

## B-018: Build Resource Scout Agent — Reddit
Status: ready
Depends on: B-017
Goal
Build an n8n workflow that scans Reddit for AI-related posts in r/blender, r/unrealengine, and r/gamedev, uses Haiku to assess relevance against active inquiry threads, and writes qualifying items to the resources table in Supabase.
Context
Phase 2, Card 1 of the Capability Amplifier. Architecture spec has the full agent design under "Resource Scout Agent." Key points:

Reddit JSON API — public, no auth needed. Append .json to subreddit URLs.
Read INQUIRIES.md (or query inquiry_threads + refinements from Supabase) for active threads and refinements.
For each new post, call Haiku with the prompt template from the architecture doc: active interests + resource title/description → score 1-5, thread match, one-line assessment.
Items scoring 3+ → resources table (status: scouted, linked to matching thread).
Items scoring 1-2 → discarded.
Deduplicate against existing resources rows by URL before calling Haiku.
Schedule: runs every 12 hours. Can be triggered manually.
Use the agent-development skill for n8n workflow patterns and Claude API integration.

Done when

n8n workflow exists, activated, and has run at least once successfully
Workflow reads active threads from Supabase (not hardcoded)
Reddit posts from all three subreddits are fetched and deduplicated
Haiku scoring prompt matches the architecture doc template
At least one scouted resource appears in the resources table with correct fields (url, title, source_name, haiku_assessment, relevance_score, thread_id, status=scouted)
Session artifact documents the workflow structure, first run results, and any items scouted

Scope
Touch: n8n (new workflow), Supabase resources table (inserts only), sessions/lean/
Do not touch: BACKLOG.md, DIRECTIVES.md, INQUIRIES.md, existing n8n workflows, other Supabase tables

## B-019: Build Digest Agent — Daily Telegram Summary
Status: ready
Depends on: B-018
Goal
Build an n8n workflow that queries newly scouted resources from Supabase, groups them by inquiry thread, and sends a formatted Telegram digest to Bill.
Context
Phase 2, Card 2 of the Capability Amplifier. Architecture spec has the design under "Digest Agent." Key points:

Query resources table for items with status scouted since last digest. Track last-digest timestamp in Supabase (new row in system_config or a simple approach — query by scouted_at in the last 24 hours).
Join against inquiry_threads to get thread names for grouping.
Format as Telegram message: thread name header, then each item with title + one-line assessment + link.
Use the communication skill — 750 char target, truncate at 4000. Quick Send key pattern.
Schedule: once daily. Can also be triggered manually via webhook.
If no new resources since last digest, either skip or send a short "nothing new today" message.

Done when

n8n workflow exists, activated, and has sent at least one test digest to Telegram
Message groups resources by thread name
Each item shows title, one-line Haiku assessment, and link
Message respects 750 char target / 4000 char max from communication skill
Schedule set to once daily
Manual trigger via webhook works
Session artifact documents workflow structure and sample message sent

Scope
Touch: n8n (new workflow), Telegram (send only), Supabase resources table (read only), sessions/lean/
Do not touch: BACKLOG.md, DIRECTIVES.md, INQUIRIES.md, existing workflows, other Supabase tables

