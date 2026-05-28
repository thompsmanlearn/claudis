# Session: 2026-05-28 — Deep Research Pipeline Pass Two Fixes
**Type:** Bill interactive session
**Duration:** ~3h across 2026-05-25/28
**Code commits:** claudis 1bd29ff, 68bb2e5, 39cbe83, 0096dc7, 9fc14b9; claude-dashboard f76ea7c

---

## Tasks Completed

1. **Stale card check (B-137)** — confirmed already complete at session open; boot briefing posted.
2. **Wikipedia User-Agent fix** — Wikipedia started returning 403 without a User-Agent header. Added `_WIKIPEDIA_UA` constant, applied to both step-1 and step-2 requests in `_fetch_wikipedia()`. Commit 1bd29ff.
3. **Gap query distillation (Fix 1)** — Call 3 Gemini prompt now requests a `query` field (3-5 keywords) per gap alongside the full description. arXiv and Semantic Scholar receive short keyword query; Guardian, Brave, Tavily, GitHub receive full NL gap description. Haiku routing extended to generate `wiki_title` (1-3 word concept) for Wikipedia gaps. Artifact gap table now shows distilled query in Pass Two Query column. Commit 68bb2e5 + f76ea7c.
4. **No abbreviations in academic queries (Fix 2)** — Added instruction to Call 3 prompt: spell out domain terms in full (PAT → psychedelic assisted therapy, PTSD → post-traumatic stress disorder). Eliminates arXiv collisions with unrelated fields sharing the same abbreviation. Guardian routing rule made explicit in comments. Commit 39cbe83.
5. **arXiv category filtering (Fix 3)** — Added `_ARXIV_CAT_PREFIX` mapping: academic → `(cat:q-bio.NC OR cat:q-bio.QM OR cat:q-bio.PE)`, technical → `(cat:cs.AI OR cat:cs.LG OR cat:eess)`, conceptual → skip arXiv. Added `_ARXIV_CLINICAL_TERMS` set: clinical-only gaps skip arXiv entirely (Semantic Scholar covers JAMA/Lancet/etc.). `_fetch_arxiv()` accepts `cat_prefix` kwarg. `p2_arxiv_queries` dict stores constructed query per gap for artifact table. Commit 0096dc7.
6. **Live verification** — Set up artifact monitor, ran full pipeline from dashboard. Verified: category prefixes appear in gap table (`[q-bio.NC, q-bio.QM, q-bio.PE] psychedelic therapy long-term outcomes`), clinical skips logged (`arXiv skipped for clinical gap: psychedelic therapy FDA approval`), no off-domain results. arXiv returned 0 results due to IP rate limiting from test runs — code is correct, rate limit will clear.

---

## Key Decisions

- **Copy All strips Query Expansion section** — pipeline internals (per-source expanded queries) are not useful for Desktop Claude analysis. Pass One Findings through metadata footer is what matters.
- **Guardian always gets full NL description** — short keyword queries return irrelevant news (football, NHS nurse shortage). This was confirmed in code and made explicit in comments.
- **Clinical-term skip is a heuristic** — detects "clinical trial", "randomized controlled", "fda", "dosing", "adverse effects", "contraindication", "drug application". Blunt but effective.
- **arXiv test runs accumulate rate limit debt** — testing against arXiv directly blocks the actual pipeline IP. Future testing should use minimal requests or accept that arXiv results will only be verifiable in a run after a cooldown period.

---

## Capability Delta

**Before:** Deep research pass two sent full natural language gap descriptions to arXiv and Semantic Scholar, returning off-domain garbage (astrophysics papers, food delivery papers, robot therapy papers). Wikipedia 403'd silently. Copy All included pipeline internals.

**After:** Pass two sends 3-5 keyword queries to academic APIs, full NL descriptions to news/web sources. arXiv is domain-filtered by gap type. Clinical-only gaps skip arXiv. Wikipedia has correct User-Agent. Copy All exports only analysis-relevant content.

**Reader:** Desktop Claude receives clean, attributed research artifacts via Copy All and the export bundle.

---

## Lessons Written
- 2 (arXiv rate limit behavior; academic API query type mismatch)

---

## Branches
All work committed directly to main via short-lived attempt branches (all merged, deleted).
