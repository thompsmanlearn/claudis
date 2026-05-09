# Charter Creation — Desktop Session Guide

Use this when Bill has a research question and wants to turn it into a charter for the orchestrator.

## The Goal

Sharpen a fuzzy question into a scoped, criteria-bound charter that the orchestrator can execute and the grader can evaluate.

## Procedure

### Step 1 — Hear the question

Bill states the research question in his own words. Do not rephrase it yet. Ask one clarifying question if the question is ambiguous: "Is this about X or Y?"

### Step 2 — Sharpen the question

Restate the question as one or two concrete sentences. Test: could a researcher know when they've answered it? If not, sharpen further.

### Step 3 — Define scope

Ask: "What's clearly in scope, and what would you want excluded?" Common exclusions: marketing content, specific vendors, outdated material (pre-2022).

### Step 4 — Write success criteria

Aim for 3-5 criteria, each verifiable from a research finding:
- "At least 3 independent sources confirm X"
- "A concrete example of Y in production"
- "A clear answer to the sub-question Z"

Avoid aspirational criteria ("thorough understanding") — they can't be evaluated.

### Step 5 — Disqualifying criteria

What would make a source or finding irrelevant? Examples:
- "Theoretical only, no implementation"
- "Pre-2022 without evidence of current relevance"
- "Marketing content without technical depth"

### Step 6 — Initial sub-questions

Derive 2-5 specific searches from the main question. These become the orchestrator's first cycle plan. Good sub-questions are: concrete, searchable, and non-overlapping.

### Step 7 — Source preferences

Ask Bill: "Any preferred source types?" Common preferences: peer-reviewed papers, official documentation, first-hand accounts. Common avoidances: SEO content, aggregator sites.

### Step 8 — Time bounds

Does recency matter? If so, what's the cutoff? (e.g. "past 12 months", "post-GPT-4 release")

### Step 9 — Assemble and paste

Produce the charter using the template from `architecture/decisions/research-charter.md`. Leave the Memory Check section as `[System will fill in after add_charter() runs]`.

Bill pastes the charter into the thread via the Anvil "Add Charter" action (or calls `add_charter(thread_id, content)` directly). The system immediately runs a memory consultation and fills in the Memory Check section.

## Quality Check

Before finalizing, verify:
- [ ] Question is one or two sentences and concrete
- [ ] At least 3 success criteria, each verifiable
- [ ] At least 1 disqualifying criterion
- [ ] At least 2 initial sub-questions
- [ ] Source preferences stated (even if "no preference")
