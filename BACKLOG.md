B-064: Audit lean-boot lesson retrieval against the binding problem

Status: ready
Depends on: none

Goal
Audit the current lean-boot lesson retrieval pipeline and produce a written proposal that addresses the binding problem: abstract lessons stored without their originating episode are likely being retrieved, evaluated as too abstract to act on, and silently discarded. This card produces a proposal Bill reviews before any code changes. No implementation.

Context
Research (Marco Somma, "I Ran 500 More Agent Memory Experiments") demonstrates that abstract skills stored without grounding episodes are ignored at retrieval time — recalled but not used because there is no evidence for the model to act on. AADP's current lessons_learned rows store lesson text + tags + times_applied, which is the impoverished-skill shape. The lean-boot inject_context_v3 call already pulls "Prior Session Context" (session-level grounding), so partial episode binding exists at the session level — but not at the lesson level. The audit should characterise what already works before proposing changes.

Done when

1. Schema and retrieval path documented: what gets stored when a lesson is written (ChromaDB fields + Supabase columns), what inject_context_v3 returns at boot, and what of that makes it into the active session context. Plain prose, concrete field names.

2. Last 10 lessons evaluated: for each, answer whether the lesson alone is enough for Claude Code to know when and how to apply it, or whether the originating episode (card, session log, failure) is needed to make sense of it. Each lesson marked "self-sufficient" or "needs episode" with one-line reasoning.

3. If most lessons are "needs episode," a binding scheme proposed: what additional fields the lesson row should carry (candidates: originating_card_id, originating_session_id, situation — concrete trigger, outcome — what happened, kind — typed category: mistake / convention / anti-pattern / successful-pattern); whether episode data lives inline or in a linked table; how retrieval changes so the boot context receives lesson + situation/outcome without meaningfully bloating context; what a kind field buys at retrieval time.

4. Write-side change proposed: what the close ritual should capture beyond current lesson text when a lesson is written, using the assumed pattern of Claude Code drafting and Bill confirming/editing.

5. Anything else the audit surfaces — including where the current pipeline is already doing something right.

Output
A markdown document with five sections matching the steps above. Concrete examples from actual lesson rows wherever possible. Ends with a "what I'd do first" recommendation: the single smallest change that would test whether richer lessons get used more often.

Out of scope:
- Implementing any changes
- Touching the write pipeline
- Changing retrieval k or distance thresholds
- Schema migrations
- Decay or pruning policy

Scope
Touch:
  Read: ~/aadp/claudis/anvil/uplink_server.py — inject_context_v3 path, lesson storage callables
  Read: Supabase lessons_learned table schema and recent rows
  Read: ChromaDB lessons_learned collection schema
  Read: close-session skill for current write-side lesson capture pattern
  Write: sessions/lean/YYYY-MM-DD-b064-lesson-binding-audit.md — the proposal document

Do not touch:
  Any lesson rows, ChromaDB documents, or uplink callables

Verification checklist
- Proposal document written and committed
- Five sections present, all with concrete examples from actual rows
- "What I'd do first" recommendation included
- Bill has read the document and either approved a follow-on card or rejected with reasons

Notes
- inject_context_v3 already returns "Prior Session Context" — this is session-level grounding that predates this card. Note it explicitly so the proposal doesn't re-propose what already exists.
- times_applied is server-incremented by inject_context_v3 — the audit should check whether high times_applied actually correlates with lessons that look self-sufficient vs. needs-episode.

---

