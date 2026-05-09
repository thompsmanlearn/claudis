# ADR: Research Orchestrator

**Date:** 2026-05-08
**Status:** Active

## Decision

The research orchestrator is a multi-step pipeline running in stats_server as `/run_research_cycle`. It reads a thread's charter, queries memory, plans and executes web searches, fetches promising URLs, synthesizes findings, and writes structured entries back to the thread.

## Cycle Structure

1. **Read charter** — parse sections from the thread's most recent `charter` entry
2. **Memory pass** — query ChromaDB (research_findings, lessons_learned, reference_material) + Supabase research_articles + prior thread entries
3. **Plan searches** — Haiku generates 3-7 specific queries based on charter + memory gaps
4. **Execute searches** — Brave Search API via `/web_search`; apply source preference and disqualifying criteria filters
5. **Fetch URLs** — `/web_fetch` for top-scored results; cap at 8 per cycle
6. **Synthesize** — Sonnet produces: synthesis prose, criteria assessment, sub-questions, summary, self-assessment
7. **Write entries** — gather, analysis, summary (if conclusions), sub_question_candidates, cycle_metadata
8. **Grade** — call `/grade_research_cycle` (B-097); verdict gates the next cycle

## Models

- **Planner:** Haiku 4.5 (cost ~$0.001/cycle)
- **Synthesizer:** Sonnet 4.6 (cost ~$0.02-0.10/cycle depending on source volume)

## Cost Discipline

- Cost cap: $0.50/cycle — cycle stops with partial output if hit
- Max fetches: 8 URLs per cycle
- Max sources per synthesis: 8
- Memory pass: no external API calls, ChromaDB only

## Authorization

- **Tier 1** — all read operations (search, fetch, memory query, thread entry writes)
- **Tier 2** — any action beyond read-only (form submission, POST to external services) — cycle pauses with approval annotation

## Entry Types Written

| Type | Content |
|---|---|
| `gather` | URL list with titles/snippets from search results |
| `analysis` | Synthesis prose + memory contribution + charter advancement |
| `summary` | One-sentence conclusion (only if synthesis produces one) |
| `sub_question_candidate` | 0-3 unanswered sub-questions from the cycle |
| `cycle_metadata` | Cycle stats (searches, fetches, verdict) in metadata JSONB |

## Grader Integration (B-097)

After writing entries, the orchestrator calls `/grade_research_cycle`. Verdict:
- `continue` — good progress, another cycle warranted
- `complete` — success criteria met, thread → closed
- `pause` — surface to Bill
- `fail` — no usable output

## Extending the Orchestrator

- New memory source: add a query block to `_memory_pass()`
- New entry type: add a write block to `_write_cycle_entries()`
- Different model: change `_ORCHESTRATOR_MODEL` constant
- Life OS domains: the orchestrator is domain-agnostic; charter scoping drives domain focus
