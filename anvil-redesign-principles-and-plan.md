# Anvil UI — Thread Detail Redesign: Principles and Plan

*Drafted 2026-05-02. Signal-over-plumbing: foreground meaningful content, collapse operational noise.*

## Build status

### Built

- Thread detail view partitions `thread_entries` by `entry_type` at render time — no schema changes
- History drawer collapses `state_change` entries; collapsed by default, count shown in toggle button
- Question (full text) + state badge render at the top of the expanded card

### Built but removed in cleanup pass (pre-card, 2026-05-02)

- **Standing summary** — B-076 implemented first-paragraph-of-analysis as a standing summary; removed because the first paragraph of an analysis is framing, not conclusions, making the section actively misleading
- **Sub-questions placeholder** — B-076 rendered a "(none yet)" section; removed because no sub-questions schema exists, and a placeholder implies a working loop

### Not yet built

- Action panel collapse: five flat controls should become Gather / Export / Paste analysis + annotation, with state changes moving into the History drawer
- Structured paste-back parsing: distinguish Bill-input from desktop-Claude-product in pasted analyses
- Sub-questions schema and spawn-thread button
- Persistent memory consultation discipline (surface relevant ChromaDB lessons on thread open)
- Passback channel for agent output landing in the triggering thread (Gap A)
- Lifecycle badges on inputs (e.g. research article promotion status)
- Gather form rework (current trigger is fire-and-forget; no preview or confirmation)

---

## Thread page

**Design principle:** question, current standing, and meaningful entries (annotations, gathers, analyses) are foreground. State-change events (operational plumbing) collapse into a History log drawer.

**Layout (top to bottom in expanded card):**

1. **Header** — full question text, one-line state badge
2. **Standing summary slot** — most recent `summary`-type entry (not yet modeled; blank until introduced)
3. **Main content** — `annotation`, `gather`, `analysis`, `conclusion` entries in chronological order
4. **History log drawer** — collapsed by default; click to expand and reveal `state_change` entries
5. **Action panel** — below entries; pending redesign to primary-action-first layout

**Sub-questions** — placeholder removed; will be re-introduced when schema models them (spawn-thread button, sub_questions join table or `parent_thread_id` on `threads`).
