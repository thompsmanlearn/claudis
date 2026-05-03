# Session Artifact — B-081: Neutralize summarization in context_engineering_research

**Date:** 2026-05-03
**Card:** B-081
**Branch:** attempt/b081-neutral-summarization-prompt → merged to main

---

## What was done

Rewrote the Haiku summarization prompt in `_summarize_article_haiku` (stats_server.py) to remove the "Reflexion-style agentic system with ChromaDB memory" framing.

**Old prompt (lines 3341–3350):**
```
Write a 2-3 paragraph summary (~150 words) covering:
1. What the article is about and its main claim
2. The key pattern or technique it describes
3. Why it might matter for a Reflexion-style agentic system with ChromaDB memory
No bullet points. Be concise.
```

**New prompt:** Instructs Haiku to summarize for a general reader unfamiliar with the domain. Three-paragraph structure (third optional), with explicit prohibition on Reflexion/AADP/ChromaDB framing and any implied-use-case language. Relevance judgment deferred to downstream consumer (extraction step, desktop Claude, thread context).

---

## Judgment calls

- **Prompt location:** The card said the prompt was in the n8n workflow `gzCSocUFNxTGIzSD`. It is not — the workflow is a thin webhook that calls `/run_context_research` on the stats server. The prompt lives in `stats_server.py:_summarize_article_haiku`. Edit made in the Python file instead.
- **Deploy path:** Edited `~/aadp/claudis/stats-server/stats_server.py`, copied to `~/aadp/stats-server/stats_server.py`, restarted `aadp-stats` service.
- **Default queries:** "Reflexion ExpeL agent system production" remains in the default query set (line 3411). The card explicitly excludes query derivation from scope. Left untouched.

---

## Smoke test

Triggered a gather on thread `1b3a5cd9` (Consumer AI: "What useful tasks can be accomplished with AI agents that a general consumer can create?") with queries: consumer AI agent creation tools, non-technical users building AI agents, AI agent accessibility general public.

- 9 articles inserted
- 3 summaries spot-checked: PhotoG (e-commerce AI marketing) and "AI giants trying to understand LLM+agentic tools" — both clean neutrals, no Reflexion/AADP/ChromaDB framing
- One article (Show HN: Patterns for coordinating AI agents) returned empty content at fetch — Haiku responded asking for the full content. Pre-existing fetch quality issue unrelated to this change.

---

## Lessons written

- `lesson_b081_summarization_prompt_location_20260503`: context_engineering_research's prompt is in stats_server.py:_summarize_article_haiku, not in the n8n workflow.
- `lesson_b081_generic_agent_lens_at_consumption_site_20260503`: When an agent gains multiple consumers with different questions, a baked-in consumer-specific lens becomes a leak. Keep agents generic; apply the lens at the consumption site.

---

## Done-when check

- [x] Prompt rewritten per contract — no Reflexion/AADP/ChromaDB framing, neutral three-paragraph structure
- [x] Smoke test: 3 summaries checked, none mention Reflexion, AADP, or ChromaDB
- [x] Two lessons written (Supabase + ChromaDB)
- [x] Session artifact written
