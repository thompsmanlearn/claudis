# Session: 2026-04-16 — Feedback Agent

## Directive
B-020: Build Feedback Agent — Parse Telegram Replies (Phase 2, Card 3 of Capability Amplifier).

## What Changed

**n8n workflow created and activated:**
- Name: "Feedback Agent — Telegram Replies"
- ID: `izJKH5YqPIE9lES2`
- Webhook: POST `/webhook/feedback-agent` — receives `{chat_id, text}`

**Workflow structure (10 nodes):**
1. Webhook → Parse Intent (Code) → Get Active Thread → Get Recent Resources → Build Payloads (Code)
2. From Build Payloads: Insert Feedback Log + Write Audit (parallel)
3. Insert Feedback Log → Route (Code, re-surfaces payload) → IF Refinement (string comparison on `is_refinement_str`)
4. IF true → Insert Refinement → Confirm via Telegram
5. IF false → Confirm via Telegram

**Parse patterns (v1):**
- "more like item N", "item N more/yes/good" → thumbs_up + resource_id lookup (Nth by scouted_at DESC)
- "less like item N", "item N less/no/bad" → thumbs_down + resource_id lookup
- 👍/👎 + item number → reaction with resource match
- All other text → refinement (writes to both feedback_log and refinements)

**Supabase rows confirmed written:**
- `feedback_log`: all test inputs written with correct feedback_type and resource_id
- `refinements`: source='telegram' row written for refinement inputs
- `audit_log`: parallel write per execution

**Agent registry:** `feedback_agent` registered as type=router, status=active, workflow_id=izJKH5YqPIE9lES2

## What Was Learned

**n8n 2.6.4 bugs discovered:**
1. `responseFormat: text` on a POST node with `Prefer: return=minimal` causes "Converting circular structure to JSON" (TLSSocket) — remove `responseFormat: text` from all POST insert nodes.
2. IF node boolean conditions (`type: boolean, operation: equal/true`) fail silently or raise type errors even with `typeValidation: loose`. Workaround: use a Code "Route" node to convert `is_refinement` to a string (`'true'`/`'false'`), then compare with `type: string, operation: equals`.
3. `$('NodeName').item.json` cross-node references do not resolve correctly in IF node condition expressions when the current item is `{}` (empty 204 response). Add a Route Code node to re-surface upstream data as `$json.*` before any IF.

**Architecture constraint:**
Telegram only supports one webhook URL per bot. The TCA (`kddIKvA37UDw4x6e`) owns the bot's webhook via `telegramTrigger`. The Feedback Agent cannot independently receive Telegram messages — it requires TCA to detect non-command messages and forward them via HTTP POST to `/webhook/feedback-agent`.

**Pending TCA modification (needs Bill's approval per PROTECTED.md):**
Add a routing rule in TCA's Route Command switch to detect digest reply patterns and POST `{chat_id, text}` to `http://localhost:5678/webhook/feedback-agent`. Without this, the Feedback Agent must be triggered manually or via other means.

## Unfinished
- TCA routing: TCA modification to forward non-command Telegram messages to the Feedback Agent webhook. Requires Bill's explicit approval. Exact change: one new case in TCA's Route Command switch for `cmd_group = "feedback"` (or a fallback for non-command text that looks like feedback), POSTing to the Feedback Agent webhook.
