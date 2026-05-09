# USERS_MANUAL.md

*How to use AADP from Bill's perspective. Complements CONVENTIONS.md (rules for Claude Code) and DEEP_DIVE_BRIEF.md (architecture reference). This document is about what Bill does and what happens as a result.*

---

## Leaving comments

Comments on agents, skills, and capabilities are filed via the Fleet tab Comment button. What happens depends on the content:

### Comments that generate cards automatically

If the classifier (Haiku, confidence ≥ 0.8) reads your comment as a **correction** or **gap**, a backlog card is generated and queued for execution without any approval step. The grader is the safety mechanism — if the generated card produces bad work, the grader pauses it.

Examples that generate cards:
- "The description says it runs biweekly but it hasn't run since April" → correction
- "This agent is missing the ability to handle X" → gap

### Comments that go to the attention queue only

If the classifier reads your comment as a note, question, or direction (or confidence is below 0.8), the comment surfaces in the attention queue for manual handling.

Examples that stay in the queue:
- "Noticed this ran slowly today" → observation
- "Worth watching whether X improves" → question
- "Should we add Y eventually?" → direction

### How to choose

If you want action: describe what's wrong or what's missing directly.
If you just want a note: use "noticed," "worth watching," or "wondering about" — these route to observational intents.

---

## Reviewing comment-driven work

The Fleet tab has a "✏️ Comment work" button that exports a bundle: original comment, generated card, grader verdict, and commit SHA. Paste the bundle into a desktop Claude session to review the work at your cadence.

Agent cards in the Fleet tab show "✏️ Modified YYYY-MM-DD from comment → B-NNN-cmt" when recent comment-driven work has happened.

---

## The attention queue

The attention queue surfaces:
- Unprocessed annotations (comments, feedback)
- Grader pauses and fails
- Project completion requests (auto-cycle)
- Curation candidates (agents/skills flagged for retirement)

Work items requiring your decision are Tier 2: the system surfaces them and waits. Work items you've already acted on are marked processed.

---

## Directing work

Write a directive in the Anvil dashboard or site direction input. Claude Code reads it at the next session start. Keep it specific: "Read X and tell me Y" or "Run: B-NNN" for a specific card.

For complex work, use a desktop AI session (Opus/Sonnet) to research and write backlog cards, then bring the cards to Claude Code for execution.
