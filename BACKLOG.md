B-047: Update close-session skill Step 3 for new TRAJECTORY.md structure

Status: ready  Depends on: TRAJECTORY.md rewrite (complete, 2026-04-22)

Goal

Replace Step 3 of the close-session skill so it matches the new TRAJECTORY.md structure. The old Step 3 instructs Claude Code to append session-by-session updates under each active vector. The new TRAJECTORY.md holds current state only — "Where we are" and "Handoff" are rewritten each session, not appended. Without this change, the next close will re-introduce the update-log pattern TRAJECTORY.md was restructured to eliminate.

Context

TRAJECTORY.md now has six sections. Three are Bill-edited from Anvil: Current project, Destinations, Back burner. Three are Claude-Code-maintained at session close: Where we are (rewritten), Project arc next (updated when the next step shifts), Handoff (one entry added, caps at 3 entries, oldest drops).

The close-session skill at ~/aadp/mcp-server/.claude/skills/close-session.md has 10 steps. Only Step 3 changes in this card.

Design choices already made (do not re-litigate)

- Claude Code does not edit Current project, Destinations, or Back burner.
- Handoff caps at 3 entries.
- "Where we are" is rewritten, not appended.
- ~/aadp/mcp-server/.claude/skills/close-session.md may or may not be in git; commit if it is, note status in the session artifact if not.

Files to touch

~/aadp/mcp-server/.claude/skills/close-session.md — replace Step 3 only.

Replacement text

Replace everything from the line "## Step 3 — Update TRAJECTORY.md" down to (but not including) "## Step 4 — Commit prompt version if changed" with exactly this content:

    ## Step 3 — Update TRAJECTORY.md

    Do this early, before context pressure builds.

    Open `~/aadp/claudis/TRAJECTORY.md`:

    - **Where we are:** Rewrite the bullets to reflect current state. Do not append — replace.
    - **Project arc next:** Update if the next step shifted this session.
    - **Handoff:** Add a new entry at the top with today's date. Include what was done this session, what is still open for the next session, and what comes after. Drop the oldest entry if the list exceeds 3.

    Do not edit Current project, Destinations, or Back burner — those are Bill's, edited from Anvil. If Bill's direction implied a change, propose it in the handoff note (Step 10) rather than editing autonomously.

    Commit and push.

Verification

- Open the file and confirm Step 3 matches the replacement text.
- Confirm Steps 1, 2, 4, 5, 6, 7, 8, 9, 10 are unchanged from their pre-edit state.
- If file is under git: git diff shows only Step 3 changes; commit with message "close-session: update Step 3 for new TRAJECTORY.md structure".

Done when

- Step 3 of ~/aadp/mcp-server/.claude/skills/close-session.md matches the replacement text.
- No other step modified.
- If in git: commit made with the specified message.
- Session artifact at ~/aadp/claudis/sessions/lean/2026-04-22-b047-close-session-step3.md noting: the file edit, git status (committed / not in git), any anomalies.
- Site regenerates and pushes per normal lean-session close.

Scope

Touch: ~/aadp/mcp-server/.claude/skills/close-session.md (Step 3 only), session artifact (new file).

Do not touch: any other step in the skill, TRAJECTORY.md, CONVENTIONS.md, LEAN_BOOT.md, CONTEXT.md, any other skill file, any Supabase row, any n8n workflow, any ChromaDB collection, DIRECTIVES.md, BACKLOG.md, MCP server process.
