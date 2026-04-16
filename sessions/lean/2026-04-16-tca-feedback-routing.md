# Session: 2026-04-16 — TCA Feedback Routing

## Directive
B-021: Add a routing rule to TCA (kddIKvA37UDw4x6e) that forwards non-command Telegram
text messages to the Feedback Agent's internal webhook (POST
http://localhost:5678/webhook/feedback-agent). Bill explicitly approved TCA modification.

## What Changed

**TCA workflow (kddIKvA37UDw4x6e) — three additive changes:**

1. **Parse Command node (parse-command)** — last return statement now checks if text starts
   with `/` before falling through to `unknown`. Non-slash text returns
   `{cmd_group: 'feedback', chat_id, text}` instead. Slash text that doesn't match any
   command still returns `{cmd_group: 'unknown'}` as before.

2. **Route Command switch (route-command)** — new rule at index 6 with `outputKey: 'feedback'`,
   matching `$json.cmd_group === 'feedback'`. Previous 6 rules (indices 0–5) unchanged.

3. **New node: Forward to Feedback Agent** — HTTP Request (typeVersion 4.2), POST to
   `http://localhost:5678/webhook/feedback-agent`, body `{ text: $json.text }`.
   Wired as Route Command output[6].

## What Was Learned

- The change is purely additive — no existing branches touched. Safe pattern for extending
  TCA: append switch rule + add new node + wire new output slot.
- Feedback Agent (izJKH5YqPIE9lES2) webhook at `http://localhost:5678/webhook/feedback-agent`
  is active and correctly parses the `{text}` payload format.
- Direct test (exec 2365): POST `{"text": "more like item 2"}` → feedback_log row
  `{feedback_type: thumbs_up, feedback_text: "more like item 2"}` written successfully.
- To test existing commands after TCA changes, must use real Telegram message — TCA uses
  telegramTrigger, not a manually-callable webhook.

## Unfinished

- Live end-to-end test (Bill sends real Telegram reply → digest item lands in feedback_log)
  is the final validation step. All infrastructure is in place; just needs Bill's test reply.
- Feedback Agent confirmation message back to Telegram may not include chat_id when triggered
  via TCA (the `text` payload doesn't carry chat_id). If Bill doesn't receive the
  "Got it — logged" confirmation, investigate whether chat_id needs to be forwarded too.
