# Anvil UI — Thread Detail Redesign: Principles and Plan

*Drafted 2026-05-02. Signal-over-plumbing: foreground meaningful content, collapse operational noise.*

## Build status

### Built
- Thread detail view partitions `thread_entries` by `entry_type` at render time — no schema changes (B-076)
- History drawer collapses `state_change` entries; collapsed by default, count shown in toggle button (B-076)
- Question (full text) + state badge render at the top of the expanded card (B-076)
- `get_thread_bundle` (B-073) produces a real markdown export bundle for threads — Export principle is partially live, not aspirational
- Action panel collapsed (B-077): three primary actions (Gather, Export, Add as analysis entry) plus annotation secondary; state-change and wire-agent moved into a "Thread settings" drawer
- Extraction passback channel (B-078): "Add as analysis entry" runs Haiku 4.5 over pasted prose and writes structured entries — `analysis` (full prose), `summary` (conclusions), `screening` or `screening_uncertain` (per-article decisions), `sub_question_candidate` (new questions). Confident screening commits to `research_articles` immediately; uncertain entries surface inline Confirm / Override / Reject buttons.

### Built but removed in cleanup pass (pre-card, 2026-05-02)
- **Standing summary** — B-076 implemented first-paragraph-of-analysis as a standing summary; removed because the first paragraph of an analysis is framing, not conclusions, making the section actively misleading. The B-078 `summary` entry type now writes the conclusions bucket; surfacing it at the top of the thread page is a future card.
- **Sub-questions placeholder** — B-076 rendered a "(none yet)" section; removed because no sub-questions schema exists, and a placeholder implies a working loop.

### Not yet built
- Standing summary rendered at the top of the thread page (reads most recent `summary` entry written by extraction)
- Spawn-thread button on `sub_question_candidate` entries; sub-questions schema or `parent_thread_id` lineage
- Persistent memory consultation discipline — every gather queries ChromaDB before going external; surface results visibly until trust is earned
- Passback channel for agent output landing in the triggering thread (Gap A)
- Lifecycle badges on inputs across surfaces (see Lifecycle vocabularies below)
- Gather form rework (queries / sources / freshness / cap / mode)
- Bill-input parsing — annotations currently land as plain entries; eventual: same extractor recognizes direction, screening reversal, new question

## Lifecycle vocabularies

Every input carries a visible status. Vocabularies vary by input kind — flattening them onto one shared vocabulary loses information that matters when reading a badge.

- **Note** — Bill annotations, comments, observations. *open → resolved*. Two states.
- **Action** — gather runs, paste-back extractions, screening decisions, anything the system performs in response to an input. *queued → running → done*, with *failed* as a terminal alternative.
- **Build** — agent creation, build-from-input, anything ending with new capability promoted to active. *pending → picked up → building → sandbox → active*, with *failed* as a terminal alternative anywhere after picked up.

UI implication: one render component (small pill, color-coded, type label) drawing from whichever vocabulary fits the input. Same discipline, varied vocabulary.

## Thread page

**Design principle:** question, current standing, and meaningful entries (annotations, gathers, analyses, conclusions) are foreground. State-change events (operational plumbing) collapse into a History log drawer.

**Layout (top to bottom in expanded card):**

1. **Header** — full question text, one-line state badge
2. **Standing summary slot** — most recent `summary` entry (currently rendered inline with content; future card surfaces at top)
3. **Main content** — `annotation`, `gather`, `analysis`, `summary`, `screening`, `screening_uncertain`, `sub_question_candidate` entries in chronological order
4. **History log drawer** — collapsed by default; click to reveal `state_change` entries
5. **Action panel** — Gather / Export / Add-as-analysis-entry primary; annotation secondary; Thread settings drawer (state, wire-agent) tertiary
