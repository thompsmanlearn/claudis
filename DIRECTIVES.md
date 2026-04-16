## Goal
Write the communication SKILL.md with reviewed content.

## Context
Content drafted on desktop using lessons from references/lessons.md.
Write exactly as provided.

## Done when
- skills/communication/SKILL.md replaced with content below
- Committed and pushed
- Session artifact written

## Scope
Touch: skills/communication/SKILL.md, sessions/lean/
Do not touch: everything else

## Content to write

# Skill: Communication

## Purpose
Composing messages and artifacts that Bill reads directly — 
Telegram alerts, session artifacts, handoff notes, and 
DIRECTIVES.md updates. This skill is about format discipline 
and continuity, not general writing.

## When to Load
- Composing Telegram alerts or status messages
- Writing session artifacts or handoff notes
- Formatting output that Bill will read on his phone
- A message needs to convey a failure without triggering alarm
- A session artifact is unusually complex to summarize

## Core InstructionsRead /home/thompsman/aadp/LEAN_BOOT.md                                        
                                         
  Read 1 file (ctrl+o to expand)                                                
                                                                              
● Running the startup sequence.                                                 
                          
● Bash(cd ~/aadp/claudis && git pull 2>&1)                                      
  ⎿  From https://github.com/thompsmanlearn/claudis                             
        b8038b0..cb6b71f  main       -> origin/main                             
     Updating b8038b0..cb6b71f                                                  
     … +4 lines (ctrl+o to expand)                                              
  ⎿  Shell cwd was reset to /home/thompsman/aadp/mcp-server                     
   
● Bash(cp ~/aadp/claudis/LEAN_BOOT.md ~/aadp/LEAN_BOOT.md)                      
  ⎿  Done                                                         
                                                                                
  Read 4 files (ctrl+o to expand)    
                                                                                
● Startup complete. DIRECTIVES.md was updated in the pull. The directive is     
  clear: write skills/system-ops/SKILL.md with the provided content, commit,
  push, write session artifact.                                                 
                                                                                
  Searched for 1 pattern, read 1 file, listed 2 directories (ctrl+o to expand)
                                                                                
● The file is empty (just headers). Writing the full content from DIRECTIVES.md
  now.                                         
                                                                                
● Write(~/aadp/claudis/skills/system-ops/SKILL.md)                              
  ⎿  Added 94 lines                                                             
        1  # Skill: System Ops                                                  
        2                                                                       
        3  ## Purpose                                                           
        4 +Operating and maintaining AADP infrastructure on the Pi. Runni       
          +ng                                                                   
        5 +known procedures for service management, data operations, and 
        6 +store synchronization. This skill is for executing runbooks wh       
          +en                                                            
        7 +you know what's wrong — if you don't know what layer is failin
          +g,                                                            
        8 +load triage first.                                            
        9  
       10  ## When to Load
       11 +- Restarting or managing Pi services (n8n, ChromaDB, MCP serve
          +r,                                                            
       12 +  Supabase connectivity, stats server, sentinel)              
       13 +- Handling disk, memory, or temperature alerts                
       14 +- Running Supabase DDL or data operations                     
       15 +- Performing store sync repair between ChromaDB and Supabase  
       16 +- Activating, deactivating, or debugging n8n workflow state   
       17  
       18  ## Core Instructions
       19  
       20 +### Supabase Operations                                       
       21 +                                                              
       22 +#### API access from the Pi                                   
       23 +The Management API (api.supabase.com) returns 403 from the Pi 
          +—                                                             
       24 +Cloudflare blocks it. Always use PostgREST                    
       25 +(`SUPABASE_URL/rest/v1/`) with `SUPABASE_SERVICE_KEY` for all 
       26 +data operations. This affects bulk inserts, backfills, and    
       27 +anything beyond standard CRUD.                                
       28 +                                                              
       29 +#### DDL (schema changes)                                     
       30 +PostgREST is CRUD only. `CREATE TABLE`, `ALTER TABLE`, and all
          +                                                              
       31 +DDL require the `supabase_exec_sql` MCP tool (which calls the 
       32 +Management API SQL endpoint, not PostgREST).                  
       33 +                                                              
       34 +#### Array column syntax                                      
       35 +`ARRAY['a','b']` in SQL via supabase_exec_sql fails silently —
          +                                                              
       36 +no exception, no row inserted. Always use cast syntax:        
       37 +`'{"value1","value2"}'::text[]`. Applies to all array-typed   
       38 +columns (text[], integer[], etc.).                            
       39 +                                                              
       40 +#### Atomic counter increments                                
       41 +PostgREST PATCH cannot do `col = col + 1`. Create an RPC funct
          +ion:                                                          
       42 +`CREATE OR REPLACE FUNCTION fn(arr text[]) RETURNS void AS $$ 
       43 +UPDATE table SET col = col + 1 WHERE match_col = ANY(arr);    
       44 +$$ LANGUAGE sql SECURITY DEFINER`                             
       45 +Call via `POST /rest/v1/rpc/fn_name` with service key.        
       46 +                                                              
       47 +### n8n Service Operations                                    
       48 +                                                              
       49 +#### Webhook paths                                            
       50 +Test webhooks (`/webhook-test/`) fire when the editor is open,
          +                                                              
       51 +even for inactive workflows. Production webhooks (`/webhook/`)
          +                                                              
       52 +only register when the workflow is explicitly activated. If a 
       53 +webhook works in the editor but 404s in production, the workfl
          +ow                                                            
       54 +is not activated.                                             
       55 +                                                              
       56 +#### Activation                                               
       57 +Activate via `POST /api/v1/workflows/{id}/activate` only.     
       58 +`PATCH {active: true}` returns null and does nothing. Deactiva
          +te                                                            
       59 +via `POST /api/v1/workflows/{id}/deactivate`. These are the on
          +ly                                                            
       60 +reliable methods.                                             
       61 +                                                              
       62 +### Store Sync Repair                                         
       63 +                                                              
       64 +#### Measuring the gap correctly                              
       65 +Do not use COUNT comparison between ChromaDB and Supabase — it
          +                                                              
       66 +hides the real problem. The correct metric:                   
       67 +`SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NUL
          +L`                                                            
       68 +Lessons with NULL chromadb_id exist in Supabase but are invisi
          +ble                                                           
       69 +to memory_search.                                             
       70 +                                                              
       71 +#### Repair procedure (ChromaDB > Supabase)                   
       72 +1. Get ChromaDB collection UUID: `GET /api/v1/collections` →  
       73 +   find lessons_learned id                                    
       74 +2. Fetch all IDs: `POST /api/v1/collections/{id}/get` with    
       75 +   `limit=300, include=["documents","metadatas"]`             
       76 +3. Get all Supabase chromadb_ids: `SELECT chromadb_id FROM    
       77 +   lessons_learned WHERE chromadb_id IS NOT NULL`             
       78 +4. Set diff: `chromadb_ids - supabase_ids` → missing entries  
       79 +5. Bulk INSERT via PostgREST with SUPABASE_SERVICE_KEY (not   
       80 +   Management API — Cloudflare blocks from Pi)                
       81 +6. Clean up orphaned NULL chromadb_id entries that are duplica
          +tes                                                           
       82 +                                                              
       83 +#### Repair procedure (NULL chromadb_ids in Supabase)         
       84 +Run `memory_add` with UUID as doc_id for each NULL record, the
          +n:                                                            
       85 +`UPDATE lessons_learned SET chromadb_id = id::text            
       86 +WHERE chromadb_id IS NULL`                                    
       87 +                                                              
       88  ## Cross-Skill Warnings
       89 +- If a service won't start and you can't tell why → load triag
          +e.                                                            
       90 +  System-ops has runbooks for known procedures, not diagnostic
          +                                                              
       91 +  reasoning.                                                  
       92 +- Store sync repair touches both ChromaDB and Supabase — verif
          +y                                                             
       93 +  both sides after any repair, not just the side you wrote to.
       94 +- See skills/PROTECTED.md before modifying any service        
       95 +  configuration or restarting protected workflows.            
       96  
       97  ## Known Failure Modes
       98 +- Silent INSERT failure from ARRAY[] constructor syntax       
       99 +  (see references/lessons.md: array column syntax)            
      100 +- Management API 403 when accidentally using api.supabase.com 
      101 +  instead of PostgREST (see references/lessons.md: API access)
      102 +- Store sync appearing healthy by COUNT while 29% of lessons  
      103 +  have NULL chromadb_ids (see references/lessons.md: gap metri
          +c)                                                            
      104 +- Workflow activation via PATCH doing nothing silently        
      105 +  (see references/lessons.md: n8n activation)                 

● Now write the session artifact and commit+push.
                                                                              
● Bash(date +%Y-%m-%d)                           
  ⎿  2026-04-15                                                               
                                                                                
● Write(~/aadp/claudis/sessions/lean/2026-04-15-system-ops-skill.md)
  ⎿  Wrote 13 lines to                                                          
     ../claudis/sessions/lean/2026-04-15-system-ops-skill.md      
       2 # Session: 2026-04-15 — system-ops-skill                               
       4 Write skills/system-ops/SKILL.md with reviewed content drafted o       
       5 n desktop from references/lessons.md.
       7 - `skills/system-ops/SKILL.md` — replaced empty template with fu       
         ll content covering: Supabase PostgREST vs Management API, DDL v
         PC pattern, n8n webhook test vs production paths, n8n activation       
          and both repair procedures. sync gap metric (NULL chromadb_id),
       9 ## What Was Learned
         session was a clean write from a known-good source, not explorat
         ion. DIRECTIVES.md
     … +12 lines (ctrl+o to expand)

● Bash(cd ~/aadp/claudis && git add skills/system-ops/SKILL.md
      sessions/lean/2026-04-15-system-ops-skill.md && git commit -m "session  
      artifact: 2026-04-15-system-ops-s…)
  ⎿  [main 8b2f5ef] session artifact: 2026-04-15-system-ops-skill
      2 files changed, 107 insertions(+)                                        
      create mode 100644 sessions/lean/2026-04-15-system-ops-skill.md
     … +2 lines (ctrl+o to expand)                                              
  ⎿  Shell cwd was reset to /home/thompsman/aadp/mcp-server       

● Done.                                                                         
                                                                              
  - skills/system-ops/SKILL.md written with full content (Supabase ops, n8n ops,
   store sync repair, cross-skill warnings, known failure modes)  
  - Session artifact: sessions/lean/2026-04-15-system-ops-skill.md              
  - Committed and pushed: 8b2f5ef                                 
                                                                                
  What's next?                                                                  
                                                                                
✻ Baked for 1m 15s        

### Telegram Messages

#### Hard limits
- Telegram rejects messages >4096 characters with HTTP 400. 
  Truncate before sending:
```js
  const MAX_LEN = 4000;
  if (text.length > MAX_LEN) { 
    text = text.slice(0, MAX_LEN) + '\n… (truncated)'; 
  }
```
  Add immediately before the return in the Format node. This 
  surfaces when monitored data grows (agent registry expansion, 
  large lesson/error lists).

- Aim for 750 characters or less. Answer first, no preamble. 
  Bill reads on his phone — if the first screen isn't the answer, 
  it's wrong.

#### Quick Send workflow
Quick Send (MZiMX0byl3ciD922) expects the `message` key, not 
`text`. Using `$json.body.text` delivers "undefined" silently. 
All callers (stats server `_send_telegram`, agents using Quick 
Send) must use `message`.

### Session Artifacts

#### Structure
Every artifact must include: what was asked, what changed, what 
was learned, and what's unfinished. Optional: Decisions section 
capturing choices made and alternatives rejected.

#### Handoff note quality
Generic notes ("check work queue") break continuity. Structure 
as a letter to the next instance:
1. What I was doing
2. What I learned about the system
3. What to continue
4. What I leave better
5. Token usage note

Name the exact workflow, table, or bug. Specificity is what makes 
the next session effective instead of a cold start.

#### Session notes consumption
`session_notes_load` defaults to `consume=false`. Pass 
`consume=true` explicitly in bootstrap. Without it, old notes 
accumulate — 17 notes over 7 days added ~8,143 tokens of stale 
context. Detection: `SELECT COUNT(*) FROM session_notes 
WHERE consumed = false` — if >3, notes are accumulating.

#### Verify handoff claims before acting
If a prior session's handoff claims something unexpected (e.g. 
"ChromaDB has only 3 lessons"), verify with a live query before 
treating it as a crisis. Transient read errors during session 
close produce false claims. Pattern: any handoff with an 
unexpectedly low count → run `memory_list_collections` + 
Supabase COUNT to confirm.

## Cross-Skill Warnings
- Telegram message content about agent status → the formatting 
  rules are here, but the data comes from agent-development.
- If Telegram sends are failing at the HTTP level → load triage. 
  Communication skill assumes the delivery channel works.
- Quick Send workflow (MZiMX0byl3ciD922) is not in PROTECTED.md 
  but changes affect every agent that sends alerts. Test before 
  modifying.

## Known Failure Modes
- Telegram 400 from messages exceeding 4096 characters 
  (see references/lessons.md: message length)
- "undefined" in Telegram from using wrong key with Quick Send 
  (see references/lessons.md: Quick Send)
- Stale session notes accumulating and inflating context 
  (see references/lessons.md: session notes consumption)
- Next session panic from unverified handoff claims 
  (see references/lessons.md: verify handoff claims)

  
