# arxiv_aadp_pipeline — ArXiv → AADP Design Pipeline

**Status:** sandbox  
**Built:** 2026-04-05  
**Workflow:** bZ35VinkRjRT7gYi  
**Webhook:** POST /webhook/arxiv-aadp  
**Schedule:** Mon/Wed/Fri 15:00 UTC (8AM Pacific)  

## What it does

Fetches arXiv preprints on four topics narrowly targeted at AADP's open design questions:
- `agent evaluation framework`
- `LLM memory retrieval`
- `tool use language model`
- `multi-agent coordination`

Fetches 4 papers/topic (16 candidates), scores each with a Haiku prompt that asks not just "is this relevant?" but "what should AADP do differently based on this?" — the `implication` field in the output.

Writes findings scoring ≥7/10 (up to 4 per run) to:
- **ChromaDB** `research_findings` with `source=arxiv_aadp_pipeline` (distinct from daily_research_scout entries, queryable separately)
- **Supabase** `research_papers` with `topic_tags` including `arxiv_aadp_pipeline`

Sends Telegram digest: title, implication sentence, link.

## Difference from daily_research_scout

| | daily_research_scout | arxiv_aadp_pipeline |
|---|---|---|
| Sources | arXiv + HN + Reddit + GitHub | arXiv only |
| Topics | 7 rotating AADP topics | 4 fixed agent-systems topics |
| Scoring prompt | General AADP relevance | Design implication for AADP |
| Output field | reason | reason + implication |
| Schedule | Daily | Mon/Wed/Fri |

## Stats server endpoint

`POST http://host.docker.internal:9100/run_arxiv_aadp`  
`{"force": true}` to bypass idempotency check.

Idempotency tracked via `system_config.arxiv_aadp_last_run`.

## What was discovered on first run (2026-04-05)

4 papers scored ≥7/10:
1. **MemSifter** [9/10] — outcome-driven proxy reasoning for memory retrieval. Implication: replace naive semantic search in ChromaDB with proxy reasoning, particularly relevant on Pi hardware.
2. **Memory in the Age of AI Agents** [9/10] — taxonomy of agent memory systems. Implication: systematically evaluate dense vs. sparse vs. hierarchical compression for Supabase+ChromaDB.
3. **Multi-Agent Collaboration for Automated Research** [9/10] — empirical comparison of coordination patterns. Implication: benchmark hierarchical vs. peer-to-peer vs. blackboard for AADP swarm.
4. **SpecOps: Automated AI Agent Testing** [8/10] — automated testing in real-world environments. Implication: implement automated testing harness for n8n workflows.

## Bugs fixed during build

- `research_papers.status` check constraint only allows `discovered|abstract_reviewed|queued_for_deep_review|reviewed|archived` — not `scored`. Fixed in both `run_arxiv_aadp` and `run_daily_research` (same latent bug in daily scout).
- `agent_registry.agent_type` check constraint doesn't include `researcher` — used `scout` instead.
