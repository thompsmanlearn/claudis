B-081: Neutralize summarization in context_engineering_research

## Goal

Remove the "Reflexion-style agentic system with ChromaDB memory" framing from per-article summaries. The agent currently treats every article as raw material for AADP architecture decisions and shapes its summary accordingly. With thread-aware gathering live (B-079, B-080, B-080a), articles now arrive in threads asking different questions — and the agent's pre-shaped lens makes summaries point in the wrong direction. Fix: summaries describe what the article says and what's notable about it, neutrally. The relevance lens gets applied later by extraction or desktop Claude, in the context of the thread that gathered it.

## Context

Today every summary follows the pattern: short article description → key technique/pattern → "For a Reflexion-style agentic system with ChromaDB memory, this matters because..." paragraph. The third paragraph is mechanical; it appears even when the article has nothing to do with agents, ChromaDB, or memory (see today's summaries on digital marketing, NHS open source policy, navigation websites). The agent forces the frame.

Diagnostic from 2026-05-03: a thread asking about non-technical agent users was given articles summarized for a Reflexion-augmented system architect. The reasoning chain that desktop Claude or the extractor would want to follow gets pre-empted by an unrelated lens.

The agent's prompt lives in the n8n workflow gzCSocUFNxTGIzSD, in the Haiku summarization node. Find it, rewrite it.

What the new prompt should produce:

- A 2-3 paragraph summary of the article
- Paragraph 1: what the article says — the central claim or finding, neutrally
- Paragraph 2: the key technique, pattern, or argument the article rests on
- Paragraph 3 (optional): what's notable, surprising, or contested about the claim — only if the article actually has a notable angle. Do not force this paragraph. If the article is straightforward, two paragraphs is fine.
- No "for a Reflexion-style system" framing
- No "for AADP" framing
- No mention of ChromaDB, memory architecture, or agent-system implications unless the article itself is about those things
- No prescriptive "this means you should..." framing — describe, don't direct

The summarization prompt should also include an explicit instruction that the agent's job is to summarize articles for any reader, not for a specific system or use case. The relevance judgment happens downstream.

What this card does NOT do:

- Doesn't change query derivation (B-079 is fine)
- Doesn't change article fetching (B-080 plumbing is fine)
- Doesn't change the agent's source list (still HN, arXiv, dev.to, GitHub, lobste.rs, Medium)
- Doesn't retroactively rewrite the 31 already-summarized articles. The orphaned articles in the threads stay as they are. Only new gather runs after this card produce neutral summaries.
- Doesn't add a "summary style" config option. The change is in-place.

## Done when

- The Haiku summarization node in workflow gzCSocUFNxTGIzSD has its prompt rewritten per the contract above. Worth reviewing the prompt with Bill before committing — paste the new prompt in chat for confirmation before workflow_update fires.
- Smoke test: trigger a gather on either Configure vs. create or Consumer AI. Wait for new articles to land. Spot-check 3 of the new summaries — none should mention Reflexion, AADP, or ChromaDB unless the article itself is about those subjects.
- Lesson written: a generic-capability vs. consumer-specific-lens framing — when an agent's only consumer was a specific system, baking that system's frame into the agent felt right; once the agent has multiple consumers (threads with different questions), the frame becomes a leak. The fix is to keep the agent generic and apply the lens at the consumption site.
- Session artifact written.

## Scope

Touch:
- n8n workflow gzCSocUFNxTGIzSD (summarization prompt rewrite)
- session artifact

Do not touch:
- Existing research_articles rows (no retroactive rewriting)
- Any uplink callable
- Any other workflow
- Schema
- Form1 in claude-dashboard

If you find yourself wanting to:
- Add a "regenerate summary" button to retroactively re-summarize old articles — stop. Future card if the old summaries become friction.
- Make the summarization prompt configurable per-thread — stop. Adds surface area without proven need.
- Add a separate "AADP relevance score" field — stop. The lens belongs at the consumer, not the agent.
