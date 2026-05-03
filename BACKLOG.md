B-079: Thread-aware query derivation for context_engineering_research agent

## Goal

When a gather is triggered from a thread, the agent should derive its queries from the thread's question and recent entries rather than running against its rotating defaults. Fixes the most upstream half of Gap A: today the agent fetches articles unrelated to what the thread is asking. After this card, a thread-triggered gather pulls material that's actually relevant to the thread question; the agent's existing default queries remain as the fallback for non-thread runs (e.g., if anything still triggers it generically).

## Context

Diagnostic from 2026-05-03: the "Configure vs. create" thread fired its gather and the agent ran its standing query set (`ai, claude, llmops, machine-learning, n8n, programming`) — none of which reflect the thread question ("when a non-technical person uses an agent today, are they actually creating one or configuring a templated agent..."). 15 articles came back; ~14 were noise. The agent wasn't told what the thread was about.

Current gather flow:
- Anvil "Gather" button calls `trigger_thread_gather(thread_id)` in uplink_server.py
- That callable currently fires the agent's webhook with no thread context
- The agent's n8n workflow (`context_engineering_research`, workflow_id `gzCSocUFNxTGIzSD`) reads from a hardcoded query set
- Output lands in `research_articles` with no `thread_id` (problem 3, separate card)

This card adds thread context to the trigger and uses it to derive queries. It does NOT auto-wire output to the thread (that's the next card) and does NOT change summarization (the card after that).

Approach: keep the agent's rotating-default behavior intact for non-thread invocations. When invoked with a `thread_id`, derive a small set of queries (3-5) from the thread's question and most recent annotation/analysis entries via a Haiku call, and pass them as the query set for that run only. Per-source cap and global cap behavior stays the same.

LLM for query derivation: Haiku 4.5 (already in mcp-server venv, already used by extract_analysis). Per Section 12 of DEEP_DIVE_BRIEF, no cache_control.

Query derivation prompt shape (Claudis owns wording):
- Input: thread question, plus up to the 5 most recent annotation/analysis/summary entries (truncated)
- Output: JSON with a single key `queries` whose value is a list of 3-5 short strings (1-4 words each) suitable for hitting HN, arXiv, dev.to, GitHub, lobste.rs, Medium search interfaces
- Constraint in the prompt: queries should be specific to what the thread is asking; do not include the agent's domain framing (no "agentic system" or "ChromaDB" unless the thread question is about those)
- On LLM error or parse failure: fall back to the agent's default rotating queries and log the failure to journald

Where the queries get applied: this is the part that needs care. The agent's n8n workflow currently reads its query set from inside the workflow. Two implementation options:

(a) **Override at trigger time.** `trigger_thread_gather` builds the query list and passes it as JSON in the webhook payload. The n8n workflow is updated to read incoming queries from the webhook payload when present, falling back to its hardcoded set when absent. Smaller change to the agent; localizes thread-awareness to the trigger path.

(b) **Move query derivation entirely into a pre-step inside n8n.** Larger change; not recommended this card.

Use (a). The webhook payload contract becomes:
  `{thread_id: <uuid>, queries: [<str>, <str>, ...]}` for thread-triggered runs
  `{}` (or no payload) for non-thread runs (existing default behavior)

The agent's n8n workflow needs one node added or modified to check for incoming queries; if present, use them; otherwise use the existing default rotation. Document the contract in a comment on the workflow's first node.

The thread entry written by `trigger_thread_gather` (the one that says "Gather triggered: <agent> (output not yet wired to thread)") should now also include the derived queries in its content, so the thread carries an audit trail of what was searched for. Update the entry text to something like:
  `Gather triggered: <agent>. Queries: q1, q2, q3, q4 (output not yet wired to thread)`

If query derivation falls back to defaults due to LLM error:
  `Gather triggered: <agent>. Queries: <defaults — derivation failed: <reason>>`

## Done when

- New helper in `~/aadp/claudis/anvil/uplink_server.py`: `_derive_thread_queries(thread_id) -> list[str]` that pulls the thread question + recent entries, calls Haiku, parses the JSON response, returns the list. On failure: returns the agent's default query set (read from the agent's workflow or a known constant) and logs the reason.
- `trigger_thread_gather` updated to call `_derive_thread_queries`, pass the resulting list in the webhook payload as `queries`, and write the thread entry with the queries inline.
- The agent's n8n workflow `context_engineering_research` (id `gzCSocUFNxTGIzSD`) updated: a node early in the flow reads the webhook payload's `queries` field if present and uses that as the query set for the run; if absent, the existing default rotating queries are used. First node documented with a comment naming this contract.
- Smoke test in session: trigger a thread gather on the existing "Configure vs. create" thread (id `e6f7f118-0dea-4326-b12a-426ace71aa37`) by calling `trigger_thread_gather` from a Claudis Python REPL or an inline test; verify the n8n execution log shows the derived queries running, not the defaults. Check `research_articles` for new rows with `agent_run_id` matching the new run; spot-check that titles look more relevant to the thread question than the previous run did.
- Trigger a non-thread invocation of the agent (use `workflow_execute` is broken; instead use the agent's own webhook with no payload, or n8n's UI "Execute workflow" button if the workflow has a manual trigger) to confirm the default rotating queries still fire when no `queries` field is in the payload. (If non-thread invocation is hard to test in this session, document why and skip — the Anvil button always passes thread context.)
- One commit on claudis main with the uplink changes and any necessary helper code. The n8n workflow update happens via the MCP `workflow_update` tool — this does not commit to claudis directly, but the change should be noted in the session artifact.
- Session artifact written; include the diagnostic context (today's failed gather, what queries fired vs. what queries should have fired) and a short explanation of why this card was prioritized first among the three Gap A fixes.

## Scope

Touch:
- `~/aadp/claudis/anvil/uplink_server.py` (add `_derive_thread_queries`, update `trigger_thread_gather` and the gather entry text)
- The `context_engineering_research` n8n workflow (id `gzCSocUFNxTGIzSD`) via `workflow_update`: add or modify one early node to read `queries` from the webhook payload, falling back to the existing default set
- session artifact in `~/aadp/claudis/sessions/lean/`

Do not touch:
- `extract_analysis` or any other uplink callable
- `research_articles` schema (no `thread_id` column added — that's the next card)
- The agent's summarization prompt (that's the third card)
- Any Form1 code in claude-dashboard (no UI changes needed; the Gather button already passes thread_id)
- Any other agent workflow
- The aadp-anvil systemd service (uplink restart at the end of the session per normal practice; no service changes)

If you find yourself wanting to:
- Add a `thread_id` column to `research_articles` — stop. Next card.
- Rewrite the agent's summarization prompt to drop the "Reflexion-style" framing — stop. Card after that.
- Build a query-derivation UI so Bill can edit the derived queries before they fire — stop. The redesign's "Gather form rework" item covers this; future card.
- Refactor the agent into multiple smaller agents — stop. Out of scope.

If query derivation tips into something larger than a Haiku-call helper (e.g., a separate microservice, a new table, multi-LLM orchestration), surface that early and propose a split. The expected size is ~50 lines of new Python in uplink_server.py plus one node-level edit to the n8n workflow.B-077: Collapse thread action panel to redesign shape

## Goal

Finish the thread page legibility win. B-076 reorganized the display of entries; this card reorganizes the actions below them. The current panel exposes five flat controls (annotate, state, wire, gather, add analysis) with no signal about which to reach for when. The redesign calls for three primary actions — Gather, Export, Paste analysis — plus annotation as a secondary action, with state-change and wire controls moving into a collapsed drawer alongside the History drawer that already exists. After this card, opening a thread shows the partitioned content from B-076 above a clean action surface that matches the design spec.

## Context

Authoritative design: ~/aadp/claudis/anvil-redesign-principles-and-plan.md, "Thread page" section (the four-paragraph block describing top/middle/bottom/actions). The Actions paragraph is the spec.

Current state of _build_thread_actions in ~/aadp/claude-dashboard/client_code/Form1/__init__.py:
- It has a NOTE comment at the top (added in the prior cleanup pass) flagging it as pending its own card. That comment goes away when this card lands.
- It currently builds five controls in a flat layout: annotate, state-change, wire-agent, gather, add-analysis. All visible at once, no grouping.
- It does NOT currently have an Export action. Export is part of the redesign principles (principle 1: "Export. Take the current view's state to a desktop Claude session as a clean bundle.") but no thread-level export exists yet.

This card delivers the layout. Export-the-action wires up to a callable that doesn't exist yet — for this card, the Export button calls a placeholder that returns a stub bundle and shows a "not yet implemented" message in the feedback label. Wiring real export is a future card. Building the button now is correct because the layout it slots into is what we're shipping.

The redesign explicitly collapses state-change and wire-agent into a drawer. Both are still real operations the system needs to expose; they're just not primary. Treat them like the existing History drawer at the bottom of the entries list — a labeled toggle that reveals the controls when opened.

The History drawer pattern from B-076 (▶ History (N) / ▼ History (N), hist_panel.visible toggling) is the reference shape. Match its visual style and toggle behavior so the two drawers feel like one pattern.

## Done when

- _build_thread_actions in Form1/__init__.py renders three primary action buttons in this order: Gather, Export, Paste analysis. Each is a Button with role='filled-button' and its own feedback Label below it. The existing Gather and Add-analysis behaviors carry over unchanged into the new buttons (Gather → existing trigger_thread_gather; Paste analysis → existing add-analysis behavior with the embedded TextArea).
- An Annotation control renders below the three primary actions, visually secondary (role='outlined-button' or role='tonal-button', smaller). Existing annotate behavior carries over unchanged.
- A drawer labeled "▶ Thread settings (state, agent)" renders below the annotation control. Clicking it expands to reveal the existing state-change controls and wire-agent controls, unchanged in behavior. Clicking again collapses. Toggle text flips to "▼ Thread settings (state, agent)" when open. Match the History drawer's pattern from _load_thread_entries.
- An Export button is wired. On click it calls a new uplink callable `export_thread_bundle(thread_id)` that returns a dict with keys `{thread_id, exported_at, stub: True, message}`. The feedback label shows "Stub export — full bundle not yet implemented" and the call is logged. Add the callable to ~/aadp/claudis/anvil/uplink_server.py as a stub returning that dict. No real bundle assembly in this card.
- The NOTE comment at the top of _build_thread_actions is removed.
- The five-flat-controls layout is gone. No control appears twice (i.e., state-change appears in the drawer, not also at the top level).
- One commit on claude-dashboard master with the Form1 changes. One commit on claudis main with the uplink stub. Both pushed.
- Session artifact written.

## Scope

Touch:
- ~/aadp/claude-dashboard/client_code/Form1/__init__.py (only _build_thread_actions and any small helper added for the drawer if needed)
- ~/aadp/claudis/anvil/uplink_server.py (add export_thread_bundle stub)
- session artifact in ~/aadp/claudis/sessions/lean/

Do not touch:
- _load_thread_entries (B-076 work, do not modify)
- The History drawer in _load_thread_entries (reference its pattern, don't refactor it)
- Any other Form1 function
- Any database schema
- Any other uplink callable
- The thread page top section (header, summary handling) — that's a separate concern
- Any other file in either repo

If you find yourself wanting to assemble a real export bundle, write a new entry_type, or refactor anything in _load_thread_entries — stop. That's a future card. This card delivers the action layout and a stub export endpoint. Real export bundling is its own card after we've decided what goes in the bundle.


B-078: Add extraction step for desktop-Claude analysis paste

## Goal

Implement the extraction step that reads desktop-Claude analysis prose and recovers structured implications — a synthesis, short conclusions, screening decisions on items, and candidate new questions. Wire it into the existing "Add as analysis entry" button so that pasting a desktop Claude analysis produces structured output instead of a single opaque blob. Confident extractions commit immediately; uncertain ones surface in the thread for Bill to confirm or override before they land. Closes the loop the redesign needs for the passback channel to function — desktop Claude reasons over content, the system recovers structure.

## Context

Authoritative design: ~/aadp/claudis/anvil-redesign-principles-and-plan.md, "Passback" section. The contract is: desktop Claude writes whatever it writes; Anvil reads it and recovers structure. Header-pattern parsing was rejected as brittle.

Decisions settled in design conversation (2026-05-02):
- Four buckets: synthesis, conclusions, screening decisions, candidate new questions
- Confident screening decisions land in research_articles directly (patch rating + status) AND write a thread_entry as audit
- Uncertain items wait for Bill — render in the thread with confirm/override/reject controls, no commit until Bill acts
- Extraction runs synchronously when Bill clicks "Add as analysis entry" — lets Bill see what was extracted before it commits, supports the trust-building stance
- This card handles desktop_claude paste only. Bill annotations continue to land as plain annotation entries with no extraction. Bill-input extraction is a future card.

LLM: Haiku 4.5 via the existing Anthropic integration. Per Section 12 of DEEP_DIVE_BRIEF, Haiku 4.5 silently ignores cache_control — do not attempt to cache.

Entry types being added (free-form strings on existing thread_entries; no schema migration):
- 'summary' — the conclusions bucket. Most recent 'summary' entry will feed the standing summary at the top of the thread page in a future card. Until then it renders inline with other content.
- 'screening' — audit entry for confident screening decisions and Bill-resolved uncertain ones
- 'screening_uncertain' — held screening decisions awaiting Bill confirmation
- 'sub_question_candidate' — candidate new questions. No spawn-thread button yet (future card); just renders so Bill sees what's queued.

The uncertain-item resolution UI: each 'screening_uncertain' entry renders with three inline buttons — Confirm, Override, Reject. Confirm applies the held decision (patch research_articles, write 'screening' audit entry). Override flips the decision before applying. Reject writes a 'screening' audit entry recording the rejection but does not patch research_articles. The original 'screening_uncertain' entry stays in the thread as audit trail; do not delete it.

Existing things to reuse:
- get_thread_bundle (B-073) format gives a sense of thread state shape — useful for building the extractor's input prompt
- rate_research_article and set_research_article_status callables for committing screening decisions
- The Add-as-analysis-entry click handler in _build_thread_actions is where extraction slots in

Extractor prompt shape (Claudis owns the exact wording):
- System prompt: defines the four-bucket task and the JSON output contract
- User prompt: includes the thread question, the list of items currently in the thread (id + brief description so the extractor can refer to them), and the pasted prose
- Output: JSON with four keys (synthesis, conclusions, screening, sub_questions). Each screening item has {item_id, decision, reason, confidence: 'high'|'low'}. 'high' commits, 'low' is uncertain. Each sub_question has {question, prompted_by (optional), confidence}.

Build status note to also add: while updating anvil-redesign-principles-and-plan.md Build status, add one line under "Built" noting that get_thread_bundle (B-073) already produces a real markdown export bundle for threads — the Export principle is partially live on the threads surface, not aspirational.

## Done when

- New uplink callable `extract_analysis(thread_id, prose, source)` in ~/aadp/claudis/anvil/uplink_server.py:
  - Pulls thread bundle for context (question + entries with ids and brief descriptions)
  - Calls Haiku 4.5 with the four-bucket task prompt
  - Parses JSON response, returns it to the caller
  - On LLM error or JSON parse failure: returns `{error: <message>, raw_output: <text>}` so the caller can fall back

- "Add as analysis entry" button in _build_thread_actions rewired:
  - On click: shows "Extracting…" feedback, calls extract_analysis, then writes entries based on the result
  - Synthesis → thread_entry entry_type='analysis' source='desktop_claude' (the full prose, as before)
  - Conclusions → thread_entry entry_type='summary' source='desktop_claude'
  - Screening confidence='high' → patch research_articles (rating: kept=1/dismissed=-1, status='reviewed') AND write thread_entry entry_type='screening' source='desktop_claude' with the decision in content
  - Screening confidence='low' → write thread_entry entry_type='screening_uncertain' source='desktop_claude' with the held decision in content. No research_articles patch yet.
  - Candidate sub_questions → write thread_entry entry_type='sub_question_candidate' source='desktop_claude' with the question in content
  - On extract_analysis returning an error: fall back to writing the prose as a single 'analysis' entry (preserves current behavior); feedback label shows "Extraction failed: <reason>; analysis saved as plain entry"

- _load_thread_entries renders the new entry types distinguishably (each has its own icon AND a type label so the type is identifiable at a glance):
  - 'summary' — small "Standing summary" sub-label above the content
  - 'screening' — icon and rendered decision
  - 'screening_uncertain' — same render plus inline Confirm / Override / Reject buttons that resolve the held decision per the rules in Context above
  - 'sub_question_candidate' — icon and the question text. No interactive controls on it in this card.

- anvil-redesign-principles-and-plan.md Build status section: one new line added under "Built" about get_thread_bundle.

- One commit on claude-dashboard master (Form1 changes), one commit on claudis main (uplink callable + doc update). Both pushed. Session artifact written.

## Scope

Touch:
- ~/aadp/claudis/anvil/uplink_server.py (add extract_analysis callable)
- ~/aadp/claude-dashboard/client_code/Form1/__init__.py (rewire Add-as-analysis click handler; extend _load_thread_entries with the four new render branches and the uncertain-resolution buttons)
- ~/aadp/claudis/anvil-redesign-principles-and-plan.md (one line in Build status)
- session artifact in ~/aadp/claudis/sessions/lean/

Do not touch:
- thread_entries or research_articles schema (no migration; use free-form entry_type strings)
- The existing Bill annotation flow (continues to write a plain annotation entry; no extraction)
- The History drawer (B-076) or Settings drawer (B-077)
- The standing summary section at the top of the thread page — rendering the most recent 'summary' entry there is a future card. This card writes the data so the future card has something to read.
- Any spawn-thread or sub-question schema work — sub_question_candidate just renders; no interactive controls
- Any other Form1 function or uplink callable

If you find yourself wanting to:
- Add a pending_extractions table — stop. Marker entry_types in thread_entries are intentional.
- Build the spawn-thread button — stop. Future card.
- Render summaries at the top of the thread page — stop. Future card.
- Run extraction on Bill annotations — stop. Future card.
- Cache Haiku calls — stop. Haiku 4.5 ignores cache_control silently.

If the work as scoped tips past the two-hour ceiling, surface that early and propose a split. Likely fault line: Card A = extraction callable + confident commits + writing uncertain entries opaquely; Card B = uncertain-resolution UI. Don't ship Card A alone — uncertain entries with no resolution path is worse than not shipping. If splitting, ship neither until B is also ready, OR fold the resolution UI into A and find scope to drop elsewhere.
