# Session: 2026-04-16 — capability-amplifier-tables

## Directive
B-016: Create the five Supabase tables for the Capability Amplifier:
inquiry_threads, refinements, resources, projects, feedback_log.

## What Changed

Five new tables created in Supabase (public schema):

**inquiry_threads**
id (uuid PK), parent_id (nullable FK → self), domain_name (text NOT NULL),
description (text NOT NULL), status (text NOT NULL DEFAULT 'active'),
sparked_by_resource_id (nullable FK → resources), created_at, updated_at

**resources**
id (uuid PK), thread_id (FK → inquiry_threads CASCADE), url, title (NOT NULL),
source_name, resource_type, haiku_assessment, relevance_score (numeric),
status (text NOT NULL DEFAULT 'scouted'), summary, key_takeaways,
scouted_at (DEFAULT now()), processed_at

**refinements**
id (uuid PK), thread_id (FK → inquiry_threads CASCADE),
refinement_text (NOT NULL), source, created_at

**projects**
id (uuid PK), thread_id (FK → inquiry_threads CASCADE), title (NOT NULL),
description, what_was_learned, tools_used, screenshots (jsonb),
created_at, is_public (boolean NOT NULL DEFAULT false)

**feedback_log**
id (uuid PK), thread_id (FK → inquiry_threads CASCADE),
resource_id (nullable FK → resources SET NULL), feedback_type (NOT NULL),
feedback_text, created_at

## What Was Learned

The circular FK between inquiry_threads.sparked_by_resource_id → resources
and resources.thread_id → inquiry_threads required a two-step approach:
create inquiry_threads without the sparked_by_resource_id FK, create resources
(which can then reference inquiry_threads), then ALTER TABLE to add the FK
on inquiry_threads. This is the standard pattern for circular FK pairs.

## Unfinished

Phase 1 continues:
- B-017 (expected): Create GitHub file structure (INQUIRIES.md, processed/ dir)
- B-018 (expected): Seed the first inquiry thread (game dev + AI + Blender + UE5)
