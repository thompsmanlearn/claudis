System review session. Three chapters + post-chapter work just landed. Examine, test, and revise before moving to Chapter 4.

Read TRAJECTORY.md, USERS_MANUAL.md, and architecture/decisions/comment-driven-cards.md first.

Then work through these in order — do not skip unless you find a blocker that requires redirecting:

1. **Verify B-114 pipeline end-to-end.** B-115-cmt is in BACKLOG.md (a Sonnet-generated correction for architecture_review's description). Execute it: update the agent_registry description and schedule fields to reflect the actual run history. Then run the grader against it. Does it pass? The done-when criteria are in the card.

2. **Test the comment-driven export.** Call export_comment_driven_results() (via /lesson_stats or directly). Verify the B-115-cmt entry appears with the original comment, card text, and grader verdict bundled correctly. Report the export output in the session artifact.

3. **Work the curation queue.** 9 agents flagged as paused with no workflow_id in agent_feedback (action_session=capability_curator). For each, make a recommendation: retire (default — no workflow means nothing to restore) or note a reason to keep. Use the retire_agent() callable for any you retire in-session. Surface the full list and your decisions in the artifact.

4. **Resolve "Document AADP on the Site" project.** A project_completion annotation exists (id: a1b2c3d4-0001-0000-0000-000000000000, all 8 nodes done). Bill hasn't confirmed or rejected. Check the project nodes — are they actually done? If yes, call confirm_project_complete(). If unclear, surface the question in the artifact for Bill.

5. **Health check.** Run the standard health queries: unresolved errors, lesson store integrity (chromadb_id IS NULL count), session_memory entry count, /lesson_stats. Report findings. If anything is broken, fix it.

6. **Revision pass.** After steps 1–5, list anything that needs follow-up: cards to write, patterns that are fragile, gaps in the new B-114 pipeline based on what you saw during execution. Surface these as annotations or a brief list in the artifact — don't build them in this session without Bill's confirmation.

Scope: fix what you find in steps 1–4 directly. For step 6, surface only — don't expand scope mid-session. Two-hour ceiling.
