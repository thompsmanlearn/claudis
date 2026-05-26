B-133: Boot Cleanup — Dead Code and Missing Heartbeat
Status: ready
Depends on: none
Goal
Remove dead code from lean_runner.sh, remove a deprecated call from bootstrap, and add a session heartbeat to lean sessions so system_config reflects active state during execution.
Context
Three specific problems found during boot path investigation (2026-05-17):

lean_runner.sh contains a lesson injection block (~lines 90-114) that calls http://localhost:5678/webhook/inject-context. The lesson_injector n8n workflow was deleted in B-130. The call returns 404 on every lean session. The block is dead and should be removed along with the stale comment on line 4 referencing it.
skills/bootstrap.md contains a session_notes_load(consume=true) call. session_notes table was archived 2026-04-25 per CONVENTIONS.md. Dead call, remove it.
Lean sessions show system_config.claudis_current_task = 'idle' for their entire duration. lean_runner.sh writes to session_status (different table) but doesn't update system_config. LEAN_BOOT.md has no heartbeat step either. agent_health_monitor sees 'idle' during active lean sessions. Add a heartbeat update to LEAN_BOOT.md at boot start — sets claudis_current_task to the current directive text (truncated to 80 chars) and claudis_heartbeat_at to now. Use config_set MCP tool. Close-session already resets it to idle.

lean_runner.sh lives at ~/aadp/sentinel/lean_runner.sh — confirm this path before editing. It is a symlink to ~/aadp/claudis/sentinel/lean_runner.sh per CONVENTIONS.md — edit the claudis canonical, the symlink handles the rest.
LEAN_BOOT.md interactive path (Bill types path manually without lean_runner) must keep working after changes. Don't remove anything from LEAN_BOOT.md that only lean_runner duplicates — the interactive path has no pre-enrichment.
Done when

Dead injection block removed from ~/aadp/claudis/sentinel/lean_runner.sh (lines ~90-114 and stale comment on line 4)
session_notes_load(consume=true) removed from skills/bootstrap.md
LEAN_BOOT.md has a new step early in the sequence (after step 1 git pull, before step 4.5 bill_input check): calls config_set to write claudis_current_task = first 80 chars of current directive + claudis_heartbeat_at = now
curl localhost:9100/system_status shows non-idle claudis_current_task during a test lean session
Commit pushed to main

Scope
Touch: ~/aadp/claudis/sentinel/lean_runner.sh, skills/bootstrap.md, LEAN_BOOT.md

B-136: Enforce Capability Delta in session artifacts
Status: ready
Depends on: none
Goal
Make Capability Delta a required section in every session artifact with three mandatory fields. Currently the section exists but is routinely left empty. An artifact without a completed delta cannot be used to verify whether a session produced real value.
Context
Session export from 2026-05-17 shows B-135 with empty Before/After fields. B-130 is the only recent artifact with a complete delta including a named reader. The close-session skill needs to enforce this, not suggest it. Read skills/close-session.md before editing to find the exact location of the artifact template.
Required format for every artifact — all three fields mandatory:
Capability delta
Before: one concrete sentence. "Works correctly" is not acceptable. "Bill can now trigger synthesis without running a lean session" is acceptable.
After: one concrete sentence matching the same standard.
Reader of this change: name a specific person or process and how they encounter the change. "Future sessions" is not acceptable. "Bill — via dashboard Home tab" is acceptable.
If a session made no capability change: write "No capability change this session — investigation only" in the delta section. Empty is not acceptable.
Done when
skills/close-session.md artifact template updated with the three-field Capability Delta format above, marked required, with the acceptability rules stated explicitly. The enforcement language reads: "Do not mark artifact complete until all three fields are filled or the investigation-only exception is stated." One concrete example of a correctly filled delta is included in the template. Commit pushed to main.
Scope
Touch: ~/aadp/claudis/skills/close-session.md
Do not touch: existing session artifacts, LEAN_BOOT.md, any other skill file, any Supabase table
Do not touch: uplink_server.py, any n8n workflows, session_status table writes in lean_runner.sh, close-session heartbeat reset, LEAN_BOOT.md step 11 (live lesson injection)

B-137: Two-Pass Workpad Research Pipeline
Status: ready
Depends on: none
Design reviewed by Claude Code

Goal
Replace Workpad's one-shot Gemini synthesis with a two-pass research pipeline.
Gemini's role shifts from synthesizer to screener and organizer. The artifact
is structured for Desktop Claude to reason over — dense, claim-attributed,
conflicts and gaps explicit. No synthesis layer. Desktop Claude does the
reasoning; Gemini prepares the material.

Context
Current Workpad: Brave + Tavily + GitHub fire in parallel, Gemini synthesizes
combined results, output goes to experimental_outputs. The synthesis step
loses source metadata and pre-interprets before Desktop Claude sees anything.

The right model: Gemini has the context window to screen and organize all raw
results at once. Desktop Claude has the reasoning capability to draw conclusions.
Don't swap their jobs.

The artifact lands in ~/aadp/research_artifacts/ and surfaces in the Desktop
Claude export bundle (get_desktop_bundle() — B-131).

Four Gemini/Haiku calls replace the one synthesis call:
  1. Gemini: query expansion (before retrieval)
  2. Gemini: relevance screening + topic clustering (after pass one)
  3. Gemini: gap identification (drives pass two)
  4. Haiku: gap→source routing

No synthesis call. The artifact contains screened, attributed claims — not
Gemini's interpretation of them.

--- New Sources ---

Semantic Scholar
  URL: https://api.semanticscholar.org/graph/v1/paper/search
  Auth: x-api-key header from SEMANTIC_SCHOLAR_API_KEY env var
  Params: query={q}&fields=title,abstract,year,citationCount,isOpenAccess,
          openAccessPdf,externalIds&limit=5
  Artifact links: openAccessPdf.url when isOpenAccess=true;
                  https://www.semanticscholar.org/paper/{externalIds.CorpusId}
                  otherwise. Always include year and citationCount.

arXiv
  URL: https://export.arxiv.org/api/query?search_query=all:{q}&max_results=5
  No auth. Returns Atom XML — parse with xml.etree.ElementTree.
  Fields: entry/title, entry/summary, entry/author/name, entry/id (abstract URL)
  PDF URL: replace /abs/ with /pdf/ in the abstract URL.
  Always open access — always include PDF link.

Wikipedia
  Two-step — do not derive title directly from query string.
  Step 1 search: https://en.wikipedia.org/w/api.php?action=query&list=search
                 &srsearch={q}&format=json&srlimit=1
  Step 2 fetch:  https://en.wikipedia.org/api/rest_v1/page/summary/{title}
                 URL-encode the title from step 1.
  Return extract (plain text) and content_urls.desktop.page.
  If step 1 returns no results, skip Wikipedia silently.

The Guardian
  URL: https://content.guardianapis.com/search
  Params: q={q}&show-fields=headline,bodyText,webUrl,webPublicationDate,
          sectionName&api-key={GUARDIAN_API_KEY}&page-size=5
  Auth: api-key query param from GUARDIAN_API_KEY env var.
  Always include webUrl and webPublicationDate in artifact.

--- Pipeline ---

Pass one: fire all 7 sources in parallel using Gemini-expanded queries
(see Call 1). Single source failure: log to error_logs (node_name = source
name, workflow_id = 'workpad_deep_research'), continue.

Gemini Call 1 — Query Expansion (before retrieval)
Prompt:
  The user is researching: {query}

  Generate optimized search queries for each source. Return JSON only:
  {
    "semantic_scholar": "query for academic paper search",
    "arxiv": "query for preprint search — use ti: abs: notation if helpful",
    "guardian": "concrete news-framing query",
    "wikipedia": "1-3 word entity or concept name",
    "default": "query for Brave, Tavily, GitHub"
  }

Use default for Brave, Tavily, GitHub. Use source-specific queries for the rest.

Gemini Call 2 — Relevance Screening and Clustering (after pass one)
Prompt:
  The user is researching: {query}

  Below are raw results from 7 sources. Your jobs:
  1. Drop results that are noise, tangential, or duplicate.
  2. Group remaining results into 3-6 topic clusters.
  3. Identify direct factual contradictions between sources.
     State each as: "Source A says X. Source B says Y." Do not resolve.

  Return JSON only:
  {
    "clusters": [
      {
        "topic": "cluster name",
        "findings": [
          {
            "claim": "specific claim or finding",
            "source_name": "brave|tavily|github|semantic_scholar|arxiv|wikipedia|guardian",
            "title": "result title",
            "url": "url",
            "year": null or integer,
            "citation_count": null or integer,
            "is_open_access": null or boolean,
            "pdf_url": null or string,
            "publication_date": null or "YYYY-MM-DD"
          }
        ]
      }
    ],
    "conflicts": [
      {
        "topic": "what the conflict is about",
        "source_a": {"title": "", "url": "", "claim": ""},
        "source_b": {"title": "", "url": "", "claim": ""}
      }
    ]
  }

Gemini Call 3 — Gap Identification (after clustering)
Prompt:
  The user is researching: {query}

  Below are clustered pass one findings. Identify gaps, unanswered questions,
  and weakly-supported claims. Return JSON only:
  {
    "gaps": [
      {
        "gap": "concise description",
        "type": "academic | conceptual | current | technical",
        "priority": "high | medium | low"
      }
    ]
  }

  Type definitions:
  - academic: needs peer-reviewed sourcing or citation evidence
  - conceptual: needs definitional grounding or relationship clarification
  - current: needs recent news or developments
  - technical: needs implementation detail, code, or applied examples

  If total gaps exceed 6, return only high and medium priority items.

Haiku Call — Gap Routing
System prompt:
  You are a routing classifier. Assign each gap to one or more sources by type.
  Route: academic → semantic_scholar, arxiv
         conceptual → wikipedia
         current → guardian
         technical → github, arxiv
  Return the input JSON array with a "sources" field added to each item.
  Return only the JSON array.

Input: gap list from Call 3.

Pass two: for each gap, run retrieval against assigned sources using the gap
description as the query. Use the same source fetch functions as pass one.
If a source returns 0 results for a gap, record that explicitly.

--- Artifact Format ---

Write to ~/aadp/research_artifacts/YYYY-MM-DD-{slug}.md where slug is the
first 40 chars of the query, lowercased, spaces → hyphens.

---
# Research: {query}
{ISO timestamp} | {runtime}s | 7 sources pass one | {n} sources pass two

## Query Expansion
Original: {query}
Semantic Scholar: {expanded}
arXiv: {expanded}
Guardian: {expanded}
Wikipedia: {expanded}
Brave / Tavily / GitHub: {default}

## Pass One Findings

### {Topic Cluster}
- {claim} — [{Title}]({url}) [{source}] [{year}] [{citations}] [[PDF]]({pdf}) or [[Abstract]]({url})
- {conflicting claim} — [{Title}]({url}) ⚡ conflicts with above

### {Topic Cluster}
...

## Gap Analysis
| Gap | Type | Priority | Sources Assigned | Pass Two Query |
|-----|------|----------|-----------------|----------------|
| {gap} | {type} | {priority} | {sources} | {gap description as queried} |

## Pass Two Findings

### Gap: {gap description}
Queried: {sources}
- {finding} — [{Title}]({url}) [{year}] [[PDF]]({pdf_url}) or [[Abstract]]({url})

*No relevant results returned.* [when applicable]

## Conflicts
1. **{topic}**: [{Source A}]({url}) ({year}) says {claim}. [{Source B}]({url}) ({year}) says {claim}.

## Unresolved After Two Passes
- **{gap}**: {n} results returned; none directly addressed {aspect}.
  Closest: [{title}]({url})
[Unresolved = gaps where pass two returned 0 results. Gaps with any results
go in Pass Two Findings; Desktop Claude assesses quality from there.]

---
Query: {query} | {timestamp}
Pass one: Brave {n} | Tavily {n} | GitHub {n} | SemanticScholar {n} | arXiv {n} | Wikipedia {n} | Guardian {n}
Pass two: {source} {n} | ...
Gemini: expansion {in}/{out}tok | screening {in}/{out}tok | gaps {in}/{out}tok
Haiku: routing {in}/{out}tok
---

Inline attribution format:
  Academic:  [{Title}]({url}) [SemanticScholar|arXiv] [{year}] [{n} citations]
             [[PDF]]({pdf_url}) if open access, [[Abstract]]({url}) otherwise
  News:      [{Headline}]({url}) [Guardian, YYYY-MM-DD]
  Web:       [{Title}]({url}) [Brave|Tavily]
  GitHub:    [{repo}]({url}) [GitHub]

--- UI Changes (Form1.py, Workpad tab) ---

Add a "Deep Research" button alongside the existing Search button.
On click: call run_deep_research(query) callable in uplink_server.py.
Display the artifact markdown in the existing results panel.
Existing Search button and its pipeline: unchanged.

--- Desktop Claude Export (uplink_server.py get_desktop_bundle()) ---

Read the 3 most recent files from ~/aadp/research_artifacts/ by mtime.
Include full content in the export bundle under ## Recent Research.
If directory is empty or missing, skip silently.

--- Error Handling ---

Gemini JSON parse failure: log error, abort pipeline, show error in Anvil.
Haiku JSON parse failure: assign each gap to all sources, log warning, continue.
Wikipedia step 1 no results: skip Wikipedia, log at INFO, not error.
Single source failure: log to error_logs, continue.

--- Environment Variables ---

Add to ~/aadp/mcp-server/.env:
  SEMANTIC_SCHOLAR_API_KEY=    (free: semanticscholar.org/product/api)
  GUARDIAN_API_KEY=            (free: open-platform.theguardian.com)

Done when
- "Deep Research" button in Workpad tab; existing Search button unchanged
- All 7 sources fire in parallel on pass one with expanded queries
- Semantic Scholar and arXiv receive different queries from Brave/Tavily
- Wikipedia fires search step before summary fetch — no direct title
  derivation from query string
- Screened findings organized into 3-6 topic clusters, not per-source lists
- Gap table includes exact query string used in pass two retrieval
- Pass two fires only against sources assigned by Haiku routing
- Artifact written to ~/aadp/research_artifacts/ with correct filename
- Desktop Claude export bundle includes ≤3 most recent research artifacts
- Conflicts section populated when Gemini identifies contradictions
- Unresolved section covers only gaps where pass two returned 0 results
- Metadata footer includes Gemini + Haiku token counts and per-source
  retrieval counts
- SEMANTIC_SCHOLAR_API_KEY and GUARDIAN_API_KEY read from env
- Single source failure logs and continues; other sources unaffected
- Artifact contains no Gemini synthesis prose — claims only, with
  inline source attribution

Scope
Touch: uplink_server.py (new run_deep_research callable, new source fetch
       functions, get_desktop_bundle update), Form1.py (Deep Research button),
       ~/aadp/mcp-server/.env (two new API key slots)
Do not touch: existing one-shot Search pipeline, stats_server.py,
              lean_runner.sh, any Supabase tables, any n8n workflows
