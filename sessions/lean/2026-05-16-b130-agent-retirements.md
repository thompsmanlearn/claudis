# B-130: Retire Two Superseded Agents, Wire agent_health_monitor Schedule

**Date:** 2026-05-16
**Card:** B-130
**Status:** Complete — Path A chosen for agent_health_monitor

---

## Caller Search Findings

**lesson_injector (/webhook/inject-context):**
Caller found: `sentinel/scheduler.sh` lines 68–112. Expected, documented caller. Fail-graceful (`|| echo ""`). Sentinel is suspended — caller is dormant. No unexpected callers. Safe to retire.

**session_health_reporter (/webhook/session-health-report):**
Caller found: `sentinel/scheduler.sh` lines 147–151. Expected, documented caller. Fail-graceful (`|| log "WARNING: ... (non-fatal)"`). Sentinel is suspended — caller is dormant. Note: when Sentinel is restarted, scheduler.sh will attempt this webhook — it will 404 gracefully. scheduler.sh does not need modification; the non-fatal guard handles it.

---

## Actions Taken

1. `agent_registry.status = 'retired'`, `workflow_id = NULL` for `lesson_injector` and `session_health_reporter`
2. n8n workflow `MFmk28ijs1wMig7h` (lesson_injector) deleted
3. n8n workflow `5x6G8gFlCxX0YKdM` (session_health_reporter) deleted
4. `experiments/sessions/` GitHub directory left as-is (historical artifact)
5. `agent_health_monitor` (Path A): Schedule Trigger node added (cron `0 */6 * * *`), connecting to `Get Active Agents` — same as Webhook trigger. Workflow remains active.
6. `agent_registry.schedule` updated to `'every 6h (0 */6 * * *)'` for `agent_health_monitor`
7. `agent_registry.description` updated to reflect scheduled operation

---

## Scoped Change (card adjustment)

Card assumed a `consecutive_errors` column in agent_registry for the Path A test. No such column exists. The workflow determines error counts from n8n execution API history (last 5 executions per workflow). Test adjusted: manual webhook trigger confirms workflow runs; Telegram notification path verified through Sandbox Notify (which already sends Telegram — this was not obvious from the agent description).

**Discovery:** `Sandbox Notify` (workflow `Ls0znhBx9W5Cr6sV`) is not an orphan sink. It rate-limits to 3 Telegram messages per agent per 24h, logs to `experimental_outputs`, and sends via Life OS Telegram Bot. `agent_health_monitor` was already wired to Telegram — the only missing piece was a scheduled trigger.

---

## Capability Delta

**Before:** 3 agents listed as active with no callers. `lesson_injector` and `session_health_reporter` dormant (Sentinel suspended); `session_health_reporter` additionally broken (reads retired `session_notes` table). `agent_health_monitor` scanned for errors but ran only on manual webhook call.

**After:** `lesson_injector` and `session_health_reporter` retired and removed from n8n. `agent_health_monitor` now runs every 6h automatically, alerting Bill via Telegram (through Sandbox Notify) when any agent has 3+ consecutive execution failures. Active fleet: 7 agents (was 9).

**Reader of this change:** Bill — via Telegram when agent errors are detected. Fleet count visible in dashboard Home status strip.

---

## Sanity Check

Active agents before: 9. After: 7. Drop of 2 (lesson_injector + session_health_reporter retired; agent_health_monitor retained on Path A). Confirmed via `agent_registry WHERE status = 'active'` count.
