# 4-Pillars Agent Evaluator

**Status:** sandbox  
**Workflow ID:** kQ5OALBwexLQS7in  
**Built:** 2026-03-24  
**Type:** critic  

## Purpose

Evaluates AADP agents on 4 quality pillars using Haiku-as-judge. Writes structured JSON evaluation to experimental_outputs.

## Usage

```
POST http://localhost:5678/webhook/evaluate-agent
{"agent_name": "serendipity_engine"}
```

## 4 Pillars

| Pillar | Description |
|--------|-------------|
| behavior_consistency | Does output match stated description/purpose? |
| output_quality | Well-formed, factually plausible, valuable content? |
| reliability | Handles errors/edge cases gracefully? |
| integration_fit | Uses AADP infrastructure and conventions correctly? |

## Output Schema

Written to `experimental_outputs` as `output_type='4pillars_evaluation'`:

```json
{
  "behavior_consistency": {"score": 1-5, "notes": "..."},
  "output_quality": {"score": 1-5, "notes": "..."},
  "reliability": {"score": 1-5, "notes": "..."},
  "integration_fit": {"score": 1-5, "notes": "..."},
  "overall_score": 1-5,
  "recommendation": "promote|keep_sandbox|needs_work|retire",
  "summary": "one sentence"
}
```

## Nodes

1. Webhook → Parse Input → Get Agent Registry → Extract Agent
2. → Get Recent Outputs → Ensure Items (fallback for 0-row case)
3. → Build Eval Prompt → Call Haiku Evaluator → Format Evaluation
4. → Write to Supabase

## Credentials Required

- Supabase service key (in n8n headers)
- Anthropic API key (in n8n headers — same as haiku_self_critic)

## Lessons Learned Building This

- n8n HTTP GET: use `sendQuery + queryParameters` section, not URL expression with `=` prefix
- Always add fallback Code node after HTTP GETs that may return 0 rows
- work_queue valid terminal status is `complete` not `completed`
