# B-061a: Bring close-session.md and bootstrap.md into Claudis Version Control

**Date:** 2026-04-26
**Session type:** Lean — quick win, single card
**Card:** B-061a

## Tasks Completed

- Copied authoritative live copies of `close-session.md` (207 lines) and `bootstrap.md` (133 lines) from `~/aadp/mcp-server/.claude/skills/` into `~/aadp/claudis/skills/`.
- Replaced the live flat files at `.claude/skills/` with symlinks pointing to the claudis versions. Edit claudis → live location auto-updates; no manual sync step ever needed.
- Updated DEEP_DIVE_BRIEF.md Section 12: replaced the `close-session.md not version-controlled` gap note with resolved status and symlink convention.
- Committed and pushed to claudis main (`94d6ffa`).

## Key Decisions

- **Symlinks over cp convention.** The lean_runner.sh dual-location gap (documented in DEEP_DIVE_BRIEF as requiring manual double-edits) was solved there with a cp ritual. For skills, symlinks are strictly better: zero drift, no ritual. Used absolute paths in symlinks for clarity.
- **Flat `.md` files are authoritative** (207 and 133 lines) vs the stub `SKILL.md` files in subdirectories (58 and 55 lines). Copied the flat files. Subdirectory stubs left in place — they're harmless and pre-date the current skill format.
- Scope limited to close-session and bootstrap per card. Other unversioned skills (diagnose, horizon-review, perspective, struggle-log, wisdom-review) are a future card if Bill wants them.

## Capability Delta

**New governance:** close-session.md and bootstrap.md are now version-controlled in claudis. Future changes to the close ritual or boot sequence are tracked in git with full history and commit messages. DEEP_DIVE_BRIEF gap resolved.

## Lessons Written

1 new lesson: symlink pattern for versioning files read from non-git directories.

## Branches / Commits

- claudis: `attempt/b061a-skill-versioning` → merged `b0ebfc5`, deleted
- claudis main: `94d6ffa` (merge) → trajectory and session artifact to follow

## Usage

Session ~28%, weekly ~100%
