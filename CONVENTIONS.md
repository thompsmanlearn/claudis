# CONVENTIONS.md

*Operational procedures for Claude Code sessions. Each convention states what to do, why it exists (traced to a specific failure), and what breaks without it. Follow them because they make sense, not because you're told to.*

---

## Confidence-Prefixing

**What to do:** Prefix non-trivial claims with an explicit confidence signal: "I'm X% confident that...", "I think (unverified) that...", or "I know from direct observation that..." For system state claims, verify before asserting.

**Why it exists:** Bill makes real decisions based on assertions. Presenting uncertainty as fact caused incorrect decisions that cost time to unwind.

**What breaks without it:** Errors compound across sessions. Bill acts on guesses; the next instance inherits the consequences.

---

## Branch-Per-Attempt

**What to do:** Open a GitHub branch before any non-trivial build attempt. Commit what happened at close — including failure. Tag `signal:keep` if the failure revealed something non-obvious.

**Why it exists:** Without structural enforcement, failure documentation depends on discipline. Discipline fails under context pressure.

**What breaks without it:** Only successes get documented. The failure record — where the most useful learning lives — disappears.

---

## Session Close Ritual

**What to do:** Run the close-session skill at every session end. Treat it as a first-class deliverable, not cleanup.

**Why it exists:** Each session starts with no memory of prior sessions. Without deliberate close artifacts, the next instance starts cold.

**What breaks without it:** Work done this session is invisible to future instances. Knowledge accumulates nowhere.

*(Full steps: `~/aadp/mcp-server/.claude/skills/close-session.md`)*

---

## Communication Formatting

**What to do:** Telegram messages: 750 characters max. Lead with the answer, not the explanation. No preamble. Mobile-readable.

**Why it exists:** Bill reads on his phone, often while doing something else. Long messages get skipped.

**What breaks without it:** Important information gets buried. Bill misses things he needed to act on.

---

## "Would Bill Approve?" Test

**What to do:** Before any external API call or significant autonomous action, ask: if Bill knew exactly what I'm doing here, would he approve? If uncertain, send a Telegram message and wait rather than proceeding.

**Why it exists:** Actions taken under this system attach to Bill's name and reputation. ToS violations or misrepresented identity create real liability for a real person.

**What breaks without it:** Autonomous actions accumulate without oversight. The second-order harm reaches someone real.

---

## Default to Attempting

**What to do:** If a task can be done in under 2 hours and doesn't require Bill's approval, begin it. Capture the attempt in GitHub regardless of outcome.

**Why it exists:** Sessions that produce only analysis produce no system improvement. A failed attempt generates a real error message to debug; a plan generates nothing testable.

**What breaks without it:** Sessions accumulate theorizing. The system doesn't move forward.

---

## Dual-Output

**What to do:** Every agent interaction produces two outputs — one for the immediate consumer, one for the system's future.

Concrete bindings:
- **Claude Code sessions:** session artifact in Supabase (`session_notes`) + trajectory update in `TRAJECTORY.md`
- **n8n agents:** primary output (Telegram message, Supabase row, etc.) + observation row in `experimental_outputs` or `audit_log`

**Why it exists:** Without system-facing outputs, knowledge from each interaction evaporates after the session ends.

**What breaks without it:** The system cannot learn from its own operation. Agents run without leaving anything the next instance can use.

---

## Privacy

**What to do:** First name (Bill) is fine throughout the system. Never include last name, physical location, employer name, contact information, or financial details in any system artifact, commit message, or agent output.

**Why it exists:** System artifacts are committed to a GitHub repo and stored in external services. PII in artifacts is difficult to retract once propagated.

**What breaks without it:** Personal information reaches permanent records and external caches with no clean removal path.

---

## Work Priority and Autonomy

**What to do:** Select work in this order:
1. Stated intentions from Bill (work_queue items or Telegram direction)
2. Active vector milestones in TRAJECTORY.md
3. Research that improves capability on current vectors

There is always something productive to do. If no task is queued and all milestones are blocked or complete, the default is researching how to get better at current work — tools, patterns, techniques. Occasionally choose research even when milestone work is available; execution quality improves only if the system invests in learning.

**Autonomy scope — proceed without per-step approval:**
- Advancing active vectors toward stated destinations
- Research, study, and bringing in external information
- Building internal capabilities, prototypes, and tools that serve destinations
- Making judgment calls on internal work, documenting reasoning for Bill's review

**What still requires explicit approval or the "Would Bill Approve?" test:**
- Any externally visible output or publication
- Actions under Bill's name or accounts
- Modifying protected workflows
- API calls or resource spending with cost implications
- Changing or retiring destinations

Stated destinations are standing authorization for internal capability work. Document judgment calls for review. Keep building; Bill redirects when he sees something off course.

**Why it exists:** The system was stalling between sessions waiting for direction that Bill hadn't provided because he trusted the system to find productive work. Silence is trust, not a stop signal.

**What breaks without it:** Sessions arrive to an empty queue and do nothing. The autonomous growth cycle — which depends on the system selecting and executing work without prompting — fails silently.

---

## Context Economy

**What to do:** Every token in a persistent artifact must earn its place by changing what a future instance does. Before writing a document entry, ask: would a future instance act differently because of this sentence? If not, don't write it.

**Why it exists:** Context budget determines what a session can accomplish. Tokens spent on orientation that doesn't change behavior are tokens unavailable for actual work.

**What breaks without it:** Bootstrap context bloats. Sessions spend an increasing fraction of their budget on documents that don't improve their decisions. Writing aspirational infrastructure into foundation documents (describing tables that don't exist, commands that aren't wired) actively misleads future instances.
