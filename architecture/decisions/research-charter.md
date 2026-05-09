# ADR: Research Charter Format

**Date:** 2026-05-08
**Status:** Active

## Decision

A research charter is a structured thread entry (`entry_type='charter'`) that defines what a research thread is trying to accomplish. The orchestrator reads the charter to scope its cycle. The grader reads the charter to evaluate whether the cycle advanced the question.

## Why a Charter

Without a charter, the orchestrator has no specification to grade against. Cycles produce output but there's no way to know if that output answers the question or constitutes completion. The charter is the success specification.

## Charter Format (Markdown template)

```markdown
## Question
[The actual research question, sharpened to one or two sentences.]

## Scope
**In:** [what topics, sources, timeframes are in scope]
**Out:** [what is explicitly excluded]

## Success Criteria
- [Concrete, verifiable criterion 1]
- [Criterion 2]
- [Criterion 3 — aim for 3-5]

## Disqualifying Criteria
- [What would make a finding irrelevant or low-quality]
- [E.g. "marketing content without technical specifics"]

## Initial Sub-Questions
- [Specific search query or narrow question to start with]
- [2-5 sub-questions derived from the main question]

## Source Preferences
**Prefer:** [peer-reviewed papers / official docs / primary sources / etc.]
**Avoid:** [SEO content / paywalled sources / outdated material / etc.]

## Time Bounds
[Recency requirements, or "no time constraint"]

## Memory Check
[Has this been researched before? What do we already know?
This is filled in by the system after add_charter() calls /consult_memory.]
```

## Storage

- Lives as a `thread_entries` row with `entry_type='charter'`
- The most recent charter is shown at the top of the thread page
- Older charters remain in the chronological entry list with a "superseded" label
- Charter content is parsed by the orchestrator via section headers (`## Section Name`)

## Desktop Session Workflow

See `skills/research/charter-creation.md` for the guided procedure.

## Parser Contract

The orchestrator parses charter sections by matching `## Section Name` markdown headers. Section content is everything between that header and the next `##` header. Section names must match exactly (case-insensitive):
- `Question`, `Scope`, `Success Criteria`, `Disqualifying Criteria`
- `Initial Sub-Questions`, `Source Preferences`, `Time Bounds`, `Memory Check`
