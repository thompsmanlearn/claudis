# Lessons — Research

Curated from ChromaDB lessons_learned 2026-04-15. Actionable only.

---

## Paper Discovery

**Citation graph + Haiku filtering is the efficient paper discovery pattern.**
(1) Get top-N references by citation count from a seed paper via Semantic Scholar, (2) format as numbered list, (3) ask Haiku to pick the 3 most AADP-relevant with one-sentence reasons. Takes ~2 seconds, costs ~$0.001. Sort by citationCount first — highly-cited papers are well-described, giving Haiku better signal.
Semantic Scholar endpoint: `GET https://api.semanticscholar.org/graph/v1/paper/ArXiv:{arxivId}?fields=title,year,citationCount,references.title,references.year,references.citationCount`
*(2026-03-23)*

**Semantic Scholar rate limit: 429 on second call within 60 seconds.**
Cache results locally. The recommendations endpoint (`POST /recommendations/v1/papers` with `positivePaperIds`) finds semantically similar papers but hits the same rate limit. Do not re-fetch in the same session.
*(2026-03-23)*

---

## ChromaDB Lesson Quality

**Write lessons in problem-description style, not reference/syntax style.**
Lessons written with tool names and syntax as the lead return distances 1.74–2.18 for natural-language queries. Better format: (1) lead with the failure mode in natural language, (2) root cause and fix, (3) tool names and syntax last. Exception: procedure documents searched by name — keyword density matters more than narrative.
*(2026-03-23)*

**Prepend synthetic Q: lines before embedding any lesson.**
When a lesson returns distances above 1.0, the fix is often not rewriting — it's prepending the natural-language questions that lesson should answer. Generate 2-3 questions in plain English and place them before the lesson content. This creates multi-view embeddings that match diverse query patterns (synthetic query augmentation). Expect 0.1–0.3 distance improvement. Use Haiku: "Generate 3 natural language questions this lesson answers."
*(2026-03-23)*

---

## Retrieval System

**inject_context multi-query expansion is more important than reranking.**
inject_context_v2 generates 3-4 specific technical phrases from task context, then queries ChromaDB with each (union, dedup, best distance). This proxy reasoning beats naive similarity by expanding the search surface. Reranking (a second Haiku pass) is a refinement but less impactful than getting the expansion right. Reranking becomes worthwhile when lessons > ~300.
*(2026-04-06)*

**Track retrieval data now; train an embedding adapter later.**
Log `(query, collection, doc_id, distance, was_relevant)` to `retrieval_log` on every `memory_search` call. After ~1,500 labeled pairs, train a linear adapter on top of all-MiniLM-L6-v2 for up to 70% retrieval accuracy improvement (Chroma Research finding). The retrieval_log table is already wired in server.py as of 2026-04-14.
*(2026-03-23)*
