# Session: 2026-05-08 — B-103: Semantic memory consultation

## Directive
Upgrade /consult_memory from keyword ilike matching to semantic ChromaDB search for research_articles.

## What Changed
- **DDL**: Added chromadb_id text column to research_articles.
- **stats_server.py** (live + canonical):
  - New endpoint POST /backfill_articles_to_chromadb: batch embeds articles into research_findings ChromaDB collection via Python client subprocess (generates real embeddings). Runs in configurable batch sizes; call repeatedly until has_more=False.
  - New endpoint POST /embed_article: single-article embed for new articles.
  - _memory_pass(): replaced research_articles ilike query with subprocess chromadb query using where={'type': {'$eq': 'research_article'}}. Falls back to keyword ilike if ChromaDB unavailable.

## Backfill
170 articles embedded into research_findings in 9 batches of 20. 0 errors. Collection grew 145 → 315 docs.

## Key Lessons Learned
1. **ChromaDB REST API doesn't generate embeddings.** POST /api/v1/collections/{id}/add via urllib stores documents but doesn't embed them. Only the Python client (chromadb.HttpClient) generates embeddings. Documents added via REST are invisible to semantic query. Must use subprocess pattern (like _chroma_multi_query) for all adds that need semantic search.
2. **Batch subprocess is ~6 seconds per 20 articles.** Individual subprocess per article causes timeouts. Batching to 20 per subprocess call is fast and reliable.

## Recall Comparison
- "ChromaDB vector store embedding retrieval": 0 → 5 results (1 high-relevance)
- "autonomous AI agents scientific research": 0 → 5 results
- Research articles now semantically queryable alongside lessons_learned, research_findings, and reference_material

## Unfinished
/embed_article hook not wired to article insertion pipeline — new articles added by the deprecated context_engineering_research agent won't auto-embed. Since that agent is deprecated, this is not urgent. If a replacement research agent is built, wire it to POST /embed_article after insertion.
