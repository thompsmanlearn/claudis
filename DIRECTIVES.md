## Goal
Write the research SKILL.md with reviewed content.

## Context
Content drafted on desktop using lessons from references/lessons.md.
Write exactly as provided.

## Done when
- skills/research/SKILL.md replaced with content below
- Committed and pushed
- Session artifact written

## Scope
Touch: skills/research/SKILL.md, sessions/lean/
Do not touch: everything else

## Content to write

# Skill: Research

## Purpose
Investigating topics, discovering papers, synthesizing findings, 
and managing the knowledge stored in ChromaDB and Supabase 
(lessons_learned, research_findings). This skill covers the full 
research pipeline: discovery, ingestion, storage, and retrieval 
quality.

## When to Load
- Running arXiv or Semantic Scholar literature scans
- Synthesizing findings into research_findings or lessons_learned
- Writing or updating lessons in ChromaDB
- Debugging retrieval quality (high distances, irrelevant results)
- Operating the research pipeline or research_synthesis_agent

## Core Instructions

### Paper Discovery

#### Citation graph + Haiku filtering (standard pattern)
1. Get top-N references by citation count from seed paper via 
   Semantic Scholar: `GET https://api.semanticscholar.org/graph/v1/
   paper/ArXiv:{arxivId}?fields=title,year,citationCount,
   references.title,references.year,references.citationCount`
2. Sort by citationCount — highly-cited papers have better 
   descriptions, giving Haiku more signal
3. Format as numbered list, ask Haiku to pick the 3 most 
   AADP-relevant with one-sentence reasons
4. ~2 seconds, ~$0.001 per run

#### Rate limits
Semantic Scholar returns 429 on the second call within 60 seconds. 
Cache results locally. The recommendations endpoint 
(`POST /recommendations/v1/papers`) hits the same limit. Do not 
re-fetch in the same session.

### Writing Lessons for ChromaDB

#### Problem-description style, not reference style
Lead with the failure mode in natural language, then root cause 
and fix, then tool names and syntax last. Lessons that lead with 
tool names and syntax return distances 1.74–2.18 for natural 
queries — too far for reliable retrieval. Exception: procedure 
documents searched by name, where keyword density matters more.

#### Prepend synthetic questions before embedding
When a lesson returns distances above 1.0, prepend 2-3 natural 
language questions the lesson should answer. This creates 
multi-view embeddings matching diverse query patterns. Expect 
0.1–0.3 distance improvement. Generate with Haiku: "Generate 3 
natural language questions this lesson answers."

### Retrieval Quality

#### Multi-query expansion beats reranking
inject_context_v2 generates 3-4 specific technical phrases from 
task context, queries ChromaDB with each, then unions and dedupes 
by best distance. This proxy reasoning expands the search surface 
and outperforms naive similarity. Reranking (a second Haiku pass) 
is less impactful until lessons exceed ~300.

#### Retrieval logging for future adapter training
Every memory_search call should log 
`(query, collection, doc_id, distance, was_relevant)` to 
retrieval_log. After ~1,500 labeled pairs, a linear adapter on 
all-MiniLM-L6-v2 can improve retrieval accuracy by up to 70%. 
retrieval_log is already wired in server.py as of 2026-04-14.

## Cross-Skill Warnings
- If research uncovers a lesson about agent behavior → write the 
  lesson here, but load agent-development to act on it.
- If ChromaDB queries return errors or timeouts → load triage. 
  Research skill assumes healthy infrastructure.
- See skills/PROTECTED.md before modifying any retrieval pipeline 
  components.

## Known Failure Modes
- Semantic Scholar 429 from re-fetching in the same session 
  (see references/lessons.md: rate limits)
- Lessons with poor retrieval distance due to syntax-heavy writing 
  (see references/lessons.md: lesson quality)
- zero_applied count rising because lessons exist but aren't 
  retrievable (check embedding quality and synthetic Q: lines)
- Research synthesis agent output quality dropping without obvious 
  cause (check if input lessons have drifted in format)
