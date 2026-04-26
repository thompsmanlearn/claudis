# Research Micro-Version — Milestone Record

**Completed:** 2026-04-26
**Cards:** B-054, B-055, B-056, B-057, B-058 (+ GitHub Pages embed fix, informally Card 4)
**Status:** Complete — end-to-end round-trip proven

---

## What was built

A 6-card arc proving that a human can direct research, review results, give feedback, export context for deeper analysis, and have that feedback close the loop into the next session — all within the existing AADP infrastructure.

**Card 1 (B-054) — Schema.** Two new Supabase tables: `research_articles` (agent writes here) and `agent_feedback` (human feedback persists here, generic enough to reuse for any agent or Anvil view). Schema was intentionally loose — no foreign keys, provenance as free text, `processed` boolean rather than a status enum. Kept simple to let the remaining cards build without back-edits.

**Card 2 (B-055) — Research agent.** `context_engineering_research` n8n workflow: on-demand webhook trigger, 5 hardcoded search queries, fetch top 5 per source, deduplicate by URL, cap at 10 articles per run, summarize each with Haiku. Agent registered in `agent_registry` with `workflow_id` and `webhook_url`.

**Card 3 (B-056) — Anvil Research tab.** Full UI: article cards grouped by run, rating/comment/status controls, "Run research" button invoking the agent via `invoke_agent()`, two feedback boxes (one for the agent, one for the UI view) writing to `agent_feedback`. Six new uplink callables. Status line showing last-run timestamp and article count.

**Card 4 (informal) — GitHub Pages embed.** EmbedControl retirement replaced with a simpler iframe embedded in the Anvil UI. Shipped as part of the B-056 session.

**Card 5 (B-057) — Bundle export.** `get_research_bundle()` callable returns a single markdown string for a run: frontmatter, one section per article with optional rating/comment, and a Pending Feedback section for unprocessed `agent_feedback` rows. Export button in the tab header copies to clipboard or surfaces a TextArea fallback. Bundle is the handoff format for desktop Claude analysis.

**Card 6 (B-058) — Boot-time feedback pickup.** Both `LEAN_BOOT.md` (step 10) and `bootstrap.md` (step 3) now query `agent_feedback` for unprocessed rows at session start, surface them in the boot summary as `## Pending Feedback`, and instruct immediate marking when acted on. Surfacing ≠ acting — sessions whose directive is unrelated leave rows unprocessed.

---

## What it proved

**The round-trip works.** Human triggers research via Anvil button → agent fills `research_articles` → human rates/comments in Anvil → human exports markdown bundle via Export button → pastes into desktop Claude session for deeper analysis → directional feedback written back via Anvil feedback boxes → next lean session reads feedback at boot and acts on it. No gap in the chain.

**Supabase as the integration bus.** Every handoff point in the loop is a Supabase table row. Anvil reads and writes through uplink callables; the research agent writes through its own PostgREST calls; boot-time pickup queries directly. The loose schema (no FK, nullable processed fields) held up without back-edits across all 6 cards.

**Generic feedback table scales.** `agent_feedback` with `(target_type, target_id)` is already being used for `agent`, `anvil_view`, and will work for `lesson`, `card`, or any future target without schema changes.

---

## Key lessons

**Broader queries get genuinely different articles.** The original 5 queries were narrow topic phrases (e.g., "context engineering for LLM agents"). Replacing them with broader categorical terms (autonomous agent, agent dashboard, vector memory, n8n orchestration, Reflexion/ExpeL) produced 10 fresh articles with 0 duplicates on the next run. Narrow exact-phrase queries on arXiv often return 0; broad terms are more robust.

**Fetch-depth and cap are independent controls.** `PER_RUN_CAP=10` limits how many articles land in `research_articles` per run (quality gate). `fetch_depth` (how many results per source per query) is a separate dial. Conflating them causes confusion — both need to be tuned independently.

**Surfacing feedback ≠ acting on it.** B-058 explicitly separates the two: boot reads feedback and includes it in the summary; execution acts on it when the directive is relevant. A session directed at something else should leave feedback rows unprocessed. This distinction prevents feedback from forcing scope creep.

**arXiv exact-phrase matching fails for HN-style queries.** Queries written as human-readable phrases (e.g., "agent dashboard patterns") return 0 results on arXiv. This is acceptable — arXiv is better for academic searches; for HN-style topics, web search nodes handle them correctly.

**stats-server deploy path is ~/aadp/stats-server/, not claudis/.** Edits to the stats-server source in the claudis repo must be copied after editing (`cp` step). This is a recurring friction point; future sessions should verify the live binary before assuming claudis/ is canonical.

---

## Why this pattern exists

Future Claude reading this: the `research_articles` + `agent_feedback` + bundle export pattern is the mechanism for keeping Bill in the loop on what the system is learning and doing without requiring him to be present at agent runtime. Bill reviews when he has time, rates what's useful, leaves directional feedback, and the next session incorporates it. The research agent is not trying to be autonomous — it's trying to give Bill a useful, reviewable digest.

The `processed` flag on `agent_feedback` is the key invariant: a row is only marked processed when a session has *acted* on it, not when it has been *read*. Reading is cheap; action is the signal.
