# Session: 2026-05-09 — B-114: Comment-driven card generation and execution loop

claude-dashboard commit: (this session)
claudis commit: (this commit)

## What Changed

**stats-server/stats_server.py** (canonical + live):
- `_next_card_number()`: scans sessions/lean/ + BACKLOG.md for highest B-NNN, returns max+1
- `POST /generate_card_from_comment`: reads agent_feedback row, fetches target context (agent_registry/skills_registry/capabilities), calls Sonnet to generate a backlog card, appends to BACKLOG.md with origin marker, updates agent_feedback.metadata with generated_card_id. Returns {card_id, card_text}.
- `POST /export_comment_driven_results`: queries agent_feedback for rows with generated_card_id in metadata, fetches grader verdicts and BACKLOG.md card text, returns structured markdown bundle.

**claudis/anvil/uplink_server.py**:
- `annotate()`: classify_annotation now read synchronously; if intent in {correction, gap}, confidence ≥ 0.8, target_type in {agent, skill, capability} → fires /generate_card_from_comment in background thread (non-blocking). Returns card_gen_triggered flag.
- `export_comment_driven_results(since_date, agent_name)`: new callable wrapping the export endpoint.
- `get_comment_driven_activity()`: returns {agent_name: {card_id, date}} for fleet indicators.

**claude-dashboard Form1/__init__.py**:
- `_load_agents()`: fetches get_comment_driven_activity() alongside fleet; passes to _build_agent_card.
- `_build_agent_card(agent, cmt_activity=None)`: shows "✏️ Modified {date} from comment → {card_id}" indicator when comment-driven work exists.
- Fleet header: added "✏️ Comment work" button wired to _export_comment_work_clicked (renders export bundle in TextArea).

**Documentation**:
- `architecture/decisions/comment-driven-cards.md`: ADR with trigger conditions, architecture, risk/mitigation table, framing guide.
- `CONVENTIONS.md`: added comment-driven cards convention.
- `DEEP_DIVE_BRIEF.md`: added to Governance capabilities.
- `USERS_MANUAL.md`: new file. How to leave comments that generate cards vs. notes.

## Smoke Test

Filed "architecture_review description says biweekly but only ran once" comment on architecture_review agent.
- Classifier: intent=correction, confidence=0.95 ✓
- Card generation: B-115-cmt generated, appended to BACKLOG.md with origin marker ✓
- agent_feedback.metadata updated with generated_card_id=B-115-cmt ✓
- Card text: "Correct architecture_review description and schedule fields to reflect actual run history" ✓
- (Grader/execution not verified in this session — auto_cycle is off; card will execute at next manually-triggered session)

## Scope check (Step 4a)

No scope drift. All items in the done-when were implemented. One observation: "Comment button" referenced in the directive didn't pre-exist in the Fleet tab — I built it in the previous session (B-114, which is now the current session number). This session correctly builds on that foundation.

## Lessons Applied
- lesson_conditional_routing_design_2026-03-23: sketched the trigger logic (intent conditions) before touching the code; caught the background-threading requirement early.
