## Goal
Clean DIRECTIVES.md and design the multi-session card system.

## Context
Two items:

1. DIRECTIVES.md has terminal output corruption pasted into it 
   from a prior session. Strip everything except the current 
   directive header. Once cleaned, the directive for this session 
   is just this card's content (paste it fresh after cleaning).

2. We've now run 10+ sequential cards through the lean loop in 
   one day. We need a way to structure multi-session projects so 
   Bill doesn't have to hold the full arc in his head. Design a 
   backlog system based on what you've seen work today. Consider:
   - Where does the backlog live? (DIRECTIVES.md? Separate file?)
   - How does a card reference prior work without Bill explaining?
   - How are dependencies between cards expressed?
   - How does Bill pick the next card without context switching?
   - Keep it simple — earned complexity, not speculative.

## Done when
- DIRECTIVES.md cleaned of all corruption, contains only this 
  session's directive
- A concrete backlog design documented, not just ideas
- Design is informed by today's actual experience, not theory
- Session artifact captures the design for future reference

## Scope
Touch: DIRECTIVES.md, sessions/lean/
Do not touch: skills/, LEAN_BOOT.md, n8n workflows, agents
