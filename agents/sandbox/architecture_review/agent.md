# architecture_review — Research-to-Architecture Review

**Status:** sandbox  
**Built:** 2026-04-05  
**Workflow:** 7mVc61pDCIObJFos  
**Webhook:** POST /webhook/architecture-review  
**Schedule:** Biweekly Sunday 16:00 UTC (every other Sunday)  

## What it does

Queries `research_papers` for recent high-scored `arxiv_aadp_pipeline` findings (relevance ≥ 0.7, last 14 days, `already_addressed_since IS NULL`), groups by `component_tag`, calls Sonnet to produce a structured decision review, writes to `experimental_outputs`, queues `work_queue` items for `implement` decisions, sends Telegram digest.

## Output schema (fixed, queryable)

```json
{
  "review_date": "YYYY-MM-DD",
  "window_days": 14,
  "papers_reviewed": N,
  "findings": [{
    "paper_title": "",
    "arxiv_url": "",
    "component_tag": "<enum>",
    "finding": "what the paper proposes",
    "current_implementation": "what AADP does today",
    "gap_measured": true/false,
    "gap_evidence": "specific data or null",
    "decision": "implement|defer|already_addressed|not_applicable|investigate_further",
    "proposed_action": "concrete change or null",
    "defer_reason": "why or null"
  }],
  "actions_taken": [],
  "next_review_date": "YYYY-MM-DD"
}
```

## Decision enum

- `implement` → queues work_queue item for Sentinel
- `defer` → recorded, excluded from next review unless manually reset
- `already_addressed` → writes `already_addressed_since` + `addressed_by` back to research_papers, excluded from all future reviews
- `not_applicable` → recorded only
- `investigate_further` → recorded, resurfaces next review

## Component tag enum

`lesson_injector`, `evaluator`, `session_handoff`, `agent_builder`, `scheduler`, `memory_architecture`, `stats_server`, `research_pipeline`, `none`

## Idempotency

Skips if ran within last 12 days. Override with `{"force": true}`.

## First run (2026-04-05)

3 papers reviewed (MemSifter excluded — already_addressed_since set):
- Memory in the Age of AI Agents → **implement**: memory tier redesign (working/episodic/semantic)
- Multi-Agent Collaboration → investigate_further: 0 coordinating agents vs. paper's findings
- SpecOps → **implement**: extend evaluator with real-time behavioral testing during n8n execution

2 work_queue items created. Next review: 2026-04-20.
