# ADR: Anvil Curation Surface and Cross-Agent Artifact System

**Date:** 2026-04-18
**Status:** Accepted
**Author:** Bill + Desktop Session (Opus)

---

## Problem

The system accumulates knowledge continuously — lessons, research findings, session artifacts, agent outputs — but Bill has no efficient way to see what's there, judge its quality, or shape it. Without a curation surface, knowledge decays unchecked. The dashboard currently serves as a control panel (agent status, triggers, directives) but not as a place where Bill's judgment meets the system's output.

Separately, agents operate as isolated pipelines. Each fetches, processes, and writes without awareness of what other agents have produced. The arxiv agent doesn't know the Pi has been thermal-throttling. The morning briefing aggregates status but doesn't synthesize across agent outputs. The compounding value — connections between what different agents know — only happens in Bill's head.

These are two faces of the same gap: the system produces knowledge but has no shared layer for that knowledge to flow through, be judged, and improve.

---

## Direction

### 1. Anvil evolves from control panel to curation surface

The dashboard grows a tab structure. Each tab gives Bill visibility into a domain of system knowledge and lets him act on it — approve, reject, edit, delete, boost, flag. Every action Bill takes becomes signal that improves the system.

### 2. Cross-agent artifact convention

Agents declare their inputs and outputs. A shared artifact layer lets agents read each other's recent outputs through structured queries, not expensive semantic search. Synthesis happens in agents whose explicit job is synthesis, not through every agent scanning everything.

### 3. Data logging as byproduct, not extra step

Every agent that produces output should log structured data to Supabase as a natural part of its workflow. This data has zero context cost (it sits in tables until queried) and becomes queryable history. Only distilled insights earn a place in ChromaDB where they influence future sessions.

---

## Tab Structure

### Fleet (exists)

Agent status, activate/pause controls, feedback. Already working. The feedback consumer is the missing downstream piece — the `agent_feedback` table captures ratings and comments but nothing reads them yet. The morning briefing is the natural consumer: add a "agents with recent negative feedback" section alongside error counts and health status.

### Sessions

Live visibility into Claude Code sessions and access to completed session output.

**Live view:** Requires sessions to write progress as they go. A `session_status` Supabase table with fields: `session_id`, `card_id`, `phase` (booting / reading_context / executing / committing / writing_artifact), `current_action` (text), `started_at`, `updated_at`. The lean runner or boot chain writes phase transitions. Uplink callable `get_session_status()` reads it. The tab shows current state and a running log.

**History:** Session artifacts already land in `~/aadp/claudis/sessions/lean/`. A callable `get_session_artifacts(limit)` lists recent artifacts and returns content. The tab shows a chronological list with drill-down.

**Status indicator (B-033):** Immediate prerequisite. Shows idle/running next to the Trigger button. Must land before the full Sessions tab.

### Lessons

Curation surface for the lesson corpus. The data is already in Supabase (`lessons_learned`) and ChromaDB (`lessons_learned` collection).

**Views:**
- Recent lessons (quality review — are new lessons well-written, failure-mode-first?)
- Most applied (sorted by `times_applied` desc — what's actually influencing sessions?)
- Never applied (`times_applied = 0` — bad lessons or uncirculated?)
- Broken (`chromadb_id IS NULL` — invisible to semantic search)
- Search (semantic search against the ChromaDB collection from the browser)

**Actions per lesson:**
- Thumbs-up: boost confidence score
- Thumbs-down: flag for revision or removal
- Edit: fix wording, update content
- Delete: remove from both Supabase and ChromaDB

**Callables needed:** `get_lessons(filter, sort, limit)`, `search_lessons(query)`, `update_lesson(id, fields)`, `delete_lesson(id)`

### Memory

Direct browsing of ChromaDB collections and key Supabase tables.

**ChromaDB browser:** Pick a collection, see documents, search semantically, view metadata, delete stale entries. The seven collections (lessons_learned, reference_material, research_findings, session_memory, error_patterns, self_diagnostics, agent_templates) each have different content and different staleness profiles.

**Supabase browser:** Filtered table views for key tables — research_papers, error_logs, experimental_outputs, work_queue. Not a generic SQL console. Curated views with sensible defaults and filters.

**Callables needed:** `get_collection_stats()`, `browse_collection(name, limit, offset)`, `search_collection(name, query)`, `delete_document(collection, doc_id)`, `get_table_rows(table, filters, limit)`

### Skills

Management surface for Claude Code skills. Skills are currently files in the repo (`~/aadp/claudis/skills/`), routed via CATALOG.md.

**Approach:** Create a `skills_registry` Supabase table mirroring the file system: `name`, `description`, `trigger_keywords`, `file_path`, `content`, `times_loaded` (default 0), `last_loaded`, `created_at`, `updated_at`. The tab shows all registered skills, how often they're triggered, and lets Bill view/edit content and routing rules.

**Callables needed:** `get_skills()`, `get_skill(name)`, `update_skill(name, fields)`

**Tracking:** Skill loading should increment `times_loaded` so Bill can see which skills are earning their keep.

### Artifacts (depends on cross-agent convention)

Shows what agents produced recently, what type, whether another agent consumed it, whether Bill has reviewed it.

**Depends on:** The `agent_artifacts` table and the agent input/output declaration convention being in place. Design this tab after the convention is built and at least two agents are producing artifacts.

---

## Cross-Agent Artifact Convention

### Agent input/output declarations

The `agent_registry` table already has `input_types` and `output_types` fields (text arrays). These are probably not meaningfully populated. Populating them creates a dependency graph: the system knows which agents produce what and which agents consume what.

Example declarations:
- `arxiv_aadp_pipeline`: input_types `[]`, output_types `["research_papers"]`
- `research_synthesis_agent`: input_types `["research_papers", "agent_feedback"]`, output_types `["research_digest"]`
- `morning_briefing`: input_types `["system_status", "error_logs", "agent_feedback", "research_digest"]`, output_types `["daily_briefing"]`
- `weather_agent`: input_types `[]`, output_types `["weather_log"]`

### Shared artifact table

```sql
CREATE TABLE agent_artifacts (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_name text NOT NULL,
    artifact_type text NOT NULL,
    content jsonb NOT NULL,
    summary text,
    confidence float DEFAULT 0.5,
    consumed_by text[] DEFAULT '{}',
    reviewed_by_bill bool DEFAULT false,
    bill_rating int CHECK (bill_rating IN (1, -1)),
    bill_comment text,
    created_at timestamptz DEFAULT now()
);
```

`artifact_type` matches the values in `output_types`. `consumed_by` is updated when another agent reads the artifact.

### Routing: structured queries, not universal search

Agents do not browse. Each agent queries only the artifact types listed in its `input_types`, filtered to records created since its last run. The query pattern:

```sql
SELECT * FROM agent_artifacts
WHERE artifact_type = ANY('{research_papers,agent_feedback}')
AND created_at > '2026-04-17T00:00:00Z'
ORDER BY created_at DESC
LIMIT 20;
```

This is a cheap indexed query. No semantic search, no scanning everything.

**Semantic search is reserved for synthesis moments** — when an agent is explicitly trying to find connections it couldn't predict. The research synthesis agent scoring relevance, the architecture review looking for papers that match system problems. Not routine data retrieval.

### Data logging convention

Every agent that produces output writes a row to `agent_artifacts` as the final step of its workflow. The row contains structured content (jsonb), a human-readable summary, and the artifact type. This is the agent's handoff — both to other agents and to Bill's curation surface.

Additional domain-specific tables (like `weather_log`, `research_papers`) can coexist for detailed data. The artifact table is the cross-cutting summary layer, not a replacement for domain tables.

---

## Context Cost Management

**Supabase tables have zero context cost.** They exist until queried. Log freely.

**ChromaDB collections have indirect context cost.** They get searched during injection and results enter session context. Only distilled insights — lessons, reference material, error patterns — should go here. Raw data stays in Supabase.

**The boot chain must stay lean.** The brief points to this ADR. Cards reference specific sections. The ADR detail is pulled only when a session needs it. This prevents the vision from inflating CONTEXT.md or TRAJECTORY.md.

**inject_context_v3 task-type routing extends to artifacts.** The routing table already controls which ChromaDB collections are searched per task type. The same principle applies to artifact queries — a card about Anvil development doesn't need yesterday's arxiv findings.

---

## Sequencing

These are not card numbers — they're a logical dependency order. Each becomes one or more cards when it's time to build.

1. **B-033: Session status indicator** — already written. Immediate prerequisite for Sessions tab and safe concurrent-session use.
2. **Feedback consumer** — add agent feedback summary to morning briefing. Closes the existing gap with minimal new infrastructure.
3. **Lessons tab** — highest curation value. Data already exists. Bill can immediately start reviewing and improving lesson quality.
4. **Agent input/output declarations** — populate the registry fields. Prerequisite for the artifact convention.
5. **Artifact table and logging convention** — create the table, update 2-3 agents to write artifacts. Prove the pattern.
6. **Sessions tab** — live session visibility. Requires session-side changes to write progress.
7. **Memory tab** — ChromaDB and Supabase browsing.
8. **Skills tab** — skills registry and management.
9. **Artifacts tab** — depends on the convention being live with real data flowing.

---

## What This Changes

The system moves from "Bill directs, agents execute, knowledge accumulates unchecked" to "agents execute and leave structured artifacts, other agents build on those artifacts, Bill curates the whole thing from a single surface." The curation loop — Bill sees output, judges quality, feeds signal back — is the mechanism that prevents knowledge decay and keeps the system calibrated to what Bill actually values.

The cross-agent artifact flow is the mechanism that turns isolated pipelines into a system that makes better sense of the world over time. Not by building a clever orchestrator, but by giving agents declared interfaces and letting structured data flow between them.
