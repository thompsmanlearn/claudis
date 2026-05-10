## B-125: Establish two-pass review convention for architecture cards
Status: ready
Depends on: B-124

### Goal
Create a working convention where cards that touch architecture or set new patterns get reviewed by Claude Code before execution, with Opus revising in response, and only the resolved proposal reaching Bill. Bounded implementation cards stay as straight execution. The goal is real collaboration between Opus and Claude Code in the design phase, not after, so flaws get caught before code lands and Bill's decisions are made on stress-tested proposals.

This card establishes the convention itself — the lightweight infrastructure and the language. It does not retrofit existing work.

### Context
Decided in design conversation 2026-05-10 between Bill, Opus, and Claude Code:

- The three-way collaboration is real. Opus has perspective and reasoning time; Claude Code has ground truth and can act; Bill has judgment and continuous memory.
- The biggest project risk is over-aspiration — building structure that doesn't get validated.
- Friction for Bill is the constraint to minimize. He should see resolved proposals, not exchanges.
- The two-pass convention applies to architecture cards. Bounded fixes don't need it.

The heuristic for which cards go through review (Claude Code can refine, but this is the starting frame):
- Goes through review: any card that creates a new agent, a new table, a new UI surface, or a new pattern (a new convention, new file type, new workflow shape).
- Straight execution: bounded fixes (bug fixes, updates to existing lessons, adding a field to an existing table, polish, retries, restoration jobs like B-123).

The flow for review-required cards:
1. Opus produces a design sketch — not a full card. Problem, proposed shape, open questions. Roughly 200 words.
2. Bill pastes the sketch to Claude Code as a "design review" prompt (not an executable card).
3. Claude Code reviews against current system state, responds in roughly the same length — what's right, what's off, what changes the proposal needs. May propose a different shape entirely.
4. Bill pastes Claude Code's response back to Opus.
5. Opus revises the design and produces the final card with the review-shaped changes baked in.
6. Bill decides whether to send the card. If yes, paste to Claude Code as a normal directive.

Bill sees the design sketch and the resolved card. He does not need to read the review exchange unless he wants to.

### Done when

1. A new file ~/aadp/claudis/CONVENTIONS.md (if it exists, append; if not, create) contains a section titled "Two-pass review for architecture cards" that documents:
   - The heuristic above for which cards need review
   - The flow above for review-required cards
   - A clear note that any of the three actors can request a review on a card that wouldn't normally need one
   - The standard for what counts as resolved: Opus and Claude Code both agree the design is buildable as written, OR the disagreement is named explicitly in the card under a "Resolved with disagreement" section so Bill can decide

2. A new section in LEAN_BOOT.md (or wherever fits best — Claude Code's call) that briefly tells future Claude Code sessions: "Cards may arrive with a 'Design reviewed by Claude Code' marker indicating they've been through the two-pass process. Cards without this marker that match the architecture-card heuristic — stop before building and request a design review from Bill."

3. The first design sketch format is documented as part of the CONVENTIONS.md section, with one worked example. Doesn't need to be elaborate — just enough that the next sketch I write has a model to follow.

4. Commit the changes to claudis main and push.

### Scope
Touch: ~/aadp/claudis/CONVENTIONS.md, ~/aadp/claudis/LEAN_BOOT.md
Do not touch: any code, any existing card, any other doc

### Invitation to Claude Code

This card is establishing a convention that affects how you work. You're the one who'll be living with it. Two paths:

- If you want to change things within scope — clearer wording, better section names, a different file location that fits the system better, fixing my mistakes about what exists — make those changes and proceed. Note what you changed and why in the session artifact.

- If you want to change things structurally — different heuristic for which cards need review, different flow, different number of passes, you think we're solving the wrong problem, or anything else that changes the shape of the convention — stop and send Bill an output message describing what you'd change and why. Bill will paste it to Opus and we'll work through it before you build.

The distinction: scoped changes happen quietly and get noted. Structural pushback comes back to the loop before code lands.
## B-126: Reader-writer discipline in two-pass review
Status: ready
Depends on: B-125
Supersedes: previous B-126 draft (VALIDATION.md approach — abandoned)

### Goal
Add reader-writer discipline as a standard concern in the two-pass review convention. Any card that creates a writer (a thumbs-up button, a new table, a logging hook, a new artifact format) should name its reader — what consumes the output and acts on it. If the reader doesn't exist yet, that's allowed, but it must be named as a follow-on card or explicitly deferred.

The point is to catch dead-end writers during design, not after they've accumulated. This is a refinement of the two-pass review, not a new file or tracking system.

### Context
Decided in design conversation 2026-05-10 between Bill, Opus, and Claude Code, replacing an earlier draft of B-126 that proposed a VALIDATION.md file. Bill pointed out that the real discipline isn't a tracking file after the fact — it's designing the reader alongside the writer in the first place. A thumbs-up that writes to a Supabase table is useless without something that reads the table and uses the signal. Both ends or it doesn't ship.

This is being written through the two-pass convention from B-125, refining that same convention.

The mechanism: reader-writer is a standard question Claude Code asks during design review. Not a hard rule — sometimes building the writer first is deliberate. But if the reader is missing, the review names it, and we either add a follow-on card, defer it explicitly, or rethink whether the writer should ship.

### Done when

1. CONVENTIONS.md §3 (the two-pass review section from B-125) updated with:
   - A new standard question for Claude Code's review: "Where's the reader? What consumes this output and acts on it?"
   - Acceptable answers: a named reader that exists, a named follow-on card that will build it, or an explicit deferral with reasoning. "We'll figure it out later" is not acceptable.
   - One-line note that the design sketch format should name the writer and the reader together when possible.

2. The design sketch format documented in CONVENTIONS.md updated to include a "Reader" field alongside the existing fields. Format something like:
   - Problem
   - Proposed shape
   - Writer (what this card produces)
   - Reader (what consumes it, or follow-on card, or deferred-with-reason)
   - Open questions

3. Commit and push.

### Scope
Touch: ~/aadp/claudis/CONVENTIONS.md only
Do not touch: any code, any other doc, no new files

### Invitation to Claude Code

Same two paths as B-125:

- Scoped changes (better wording, better placement within CONVENTIONS.md, refining the standard question) — make them and proceed.

- Structural changes (you think reader-writer should be a hard rule not a question, the design sketch format should look different, the convention update belongs somewhere else entirely, or you disagree with this approach) — stop and send Bill an output message.

One specific thing: if you think the standard question should be phrased differently to be more useful at review time, change it. You're the one who'll be asking it.

