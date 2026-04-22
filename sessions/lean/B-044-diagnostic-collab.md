# B-044: Diagnostic Collaboration — Silent-Failure Surface
*2026-04-22 · Pi-side response to desktop session*

---

**Note on §13 reference:** The card references DEEP_DIVE_BRIEF §13, but the silent-failure items
are in §12 "Known Gaps and Fragilities." §13 is "Git and File Conventions." Working from §12.

---

## 1. Reachability

**Anvil uplink silent disconnects**
- Pi-side observation: `systemctl is-active aadp-anvil.service`, `journalctl -u aadp-anvil.service`,
  and `curl localhost:9101/ping` (health server built into uplink_server.py). All three are local
  and side-effect-free.
- The `/ping` callable at 9101 verifies (a) the process is alive and (b) the Supabase keepalive
  ran within 20 min. It does NOT verify the Anvil cloud websocket is open.
- Pi cannot call Anvil callables as the browser does — callables dispatch over the cloud relay.
  The best Pi-side proxy for "is the browser actually reachable" is the 9101/ping staleness check.
  If it's fresh and the service is active, the websocket is probably alive, but this is inference.

**`/webhook/telegram-quick-send` as single point of failure**
- Observable: `GET http://localhost:5678/api/v1/workflows/MZiMX0byl3ciD922` — returns workflow
  state including `active` field. No side effect.
- Sending a test message would confirm delivery end-to-end but is a visible side effect
  (real Telegram message). Don't do it during the probe sweep.

**n8n API key TTL**
- Observable: any lightweight n8n API read (e.g., `GET /api/v1/workflows?limit=1`). 200 = valid,
  401 = expired. No side effect beyond a minor n8n internal log entry.
- Reading the key from `.env` tells us the value but not its expiry.

**Dual lean_runner.sh drift**
- Fully observable from filesystem alone. No API call needed.

**chromadb_id IS NULL orphans**
- Minimum probe: `SELECT COUNT(*) FROM lessons_learned WHERE chromadb_id IS NULL` — read-only,
  no side effect. But it's a Supabase query.
- Filesystem proxy: read stats_server.py to confirm whether all lesson-write paths reliably
  call ChromaDB add and back-fill chromadb_id. If so, orphans only appear on partial failure.

**Supabase RPC existence**
- Minimum probe: `SELECT proname FROM pg_proc WHERE proname LIKE 'increment_lessons%'` via
  supabase_exec_sql — read-only, no side effect. But it's an API call.
- Filesystem proxy: supabase_rpcs.sql in claudis/stats-server/ is the source of truth for
  what *should* exist. The file header says "Queried from live database 2026-04-17" — confirms
  both RPCs existed 5 days ago.

**Capabilities table population**
- Minimum probe: `SELECT COUNT(*) FROM capabilities` — Supabase read, no side effect.
- No filesystem proxy; table population is runtime data with no static analogue.

---

## 2. Side-Effect Inventory

| Item | Minimum probe | Side effect? |
|------|--------------|--------------|
| Anvil uplink | `curl localhost:9101/ping` + `systemctl is-active` | None |
| Anvil websocket (cloud side) | No clean probe from Pi | — |
| telegram-quick-send | `GET /api/v1/workflows/MZiMX0byl3ciD922` | None (minor n8n log) |
| n8n API key | `GET /api/v1/workflows?limit=1` | None (minor n8n log) |
| lean_runner.sh drift | `diff` of both copies | None |
| chromadb_id IS NULL | Supabase `SELECT COUNT(*)` | None (read-only) |
| RPC existence | `SELECT proname FROM pg_proc` | None (read-only) |
| Capabilities population | `SELECT COUNT(*) FROM capabilities` | None (read-only) |

The telegram-quick-send webhook itself: calling it sends a real Telegram message. Flag as
high-blast-radius during a sweep — probe the workflow state via n8n API instead.

---

## 3. Known-State Shortcuts

**lean_runner.sh drift — NOT currently a problem.** I read both copies this session
(2026-04-22): `~/aadp/sentinel/lean_runner.sh` and `~/aadp/claudis/sentinel/lean_runner.sh`
are byte-for-byte identical. Both are 250 lines. Last change was 2026-04-19 per TRAJECTORY.md.
Item is real as a future risk but is not a current drift incident.

**Supabase RPCs — existed 5 days ago.** supabase_rpcs.sql header: "Queried from live database
2026-04-17." Both `increment_lessons_applied_by_id` and `increment_lessons_applied` were present.
If they were missing since then, lesson injection would fail — but lean sessions have been running
(this session was triggered by lean_runner.sh), so injection is probably succeeding. Indirect
evidence they still exist.

**Anvil watchdog — already deployed.** The §12 note says "B-031 adds a watchdog. Until then..."
but uplink_server.py already has the watchdog: a `_keepalive_worker` thread (Supabase probe every
10 min) and a health HTTP server on localhost:9101. Uplink was updated after that §12 text was
written. The open question is what (if anything) polls 9101 and restarts the service.

**Store sync gap — was 0 as of 2026-04-13.** That repair session closed a 47-lesson gap.
9 days have passed since then; new lessons written since could have NULL chromadb_ids if any
write path is imperfect.

---

## 4. Items I'd Add

- **`/tmp/oslean.lock` staleness** — lean_runner.sh sets a lock and says "stats_server already
  checked it isn't stale." If that staleness check fails or has a bug, a crashed session blocks
  all future sessions. Not in §12.
- **session_status write failure is silent** — lean_runner.sh calls write_phase() with `|| true`.
  If session_status table doesn't exist or Supabase is down, the call fails silently — no alert.
- **stats_server.py single point of failure** — `/trigger_lean`, `/inject_context_v3`, and
  `/run_research_synthesis` all route through localhost:9100. No service watchdog for aadp-stats.
  If it dies, lean sessions can't start and lesson injection fails silently (lean_runner.sh
  proceeds without enrichment on timeout, so sessions still run — but blind).

---

## 5. Items I'd Drop or Reframe

**lean_runner.sh dual-location:** Reframe. Both copies are currently in sync (verified this
session). The risk is future drift, not present drift. Worth a sync mechanism card, but not
urgent diagnostic work.

**Anvil uplink watchdog:** Partially resolved. The keepalive and health server are deployed in
uplink_server.py. What's unresolved: whether something external actually polls 9101/ping and
triggers a restart when it goes stale. If nothing does, the watchdog is internal-only — it
detects staleness but doesn't act on it.

---

## 6. Ordering (if this becomes a sweep)

1. **Filesystem reads** (zero blast radius, no API): lean_runner.sh diff, supabase_rpcs.sql,
   stats_server.py lesson-write paths. Already done in part.
2. **Local service checks** (no network): `systemctl is-active aadp-anvil.service`,
   `systemctl is-active aadp-stats.service`, `curl localhost:9101/ping`.
3. **Read-only n8n API** (minor log): Quick Send workflow state, API key validity check.
   Dependencies: n8n must be up (it is in lean mode).
4. **Read-only Supabase queries** (no write): chromadb_id NULL count, RPC existence,
   capabilities count, session_status recent entries.
5. **Skip or last**: telegram-quick-send end-to-end test (real message → real side effect).
   Only run if #3 shows the workflow is active and we need delivery confirmation.

Rationale: work from most-certain to least-certain, and from cheapest to most observable.
The Supabase queries give the most diagnostic value per item but require API calls — do them
after we've exhausted what filesystem + local service state tells us.

---

## 7. Open Questions for Bill or Desktop

- **Who watches 9101/ping?** Is there a cron, systemd timer, or n8n workflow that polls
  `localhost:9101/ping` and restarts aadp-anvil.service when it returns 503? If not, the
  watchdog detects staleness but never acts.

- **n8n API key expiry cycle.** The key renewed 2026-04-14. What's the TTL? If it's 30 days,
  the next expiry is ~2026-05-14. If 90 days, ~2026-07-13. Knowing this determines urgency of
  adding expiry monitoring.

- **Capabilities table population mechanism.** What agent or process is supposed to write to it?
  Is this a manual process, a dedicated agent, or something that happens during session close?
  Without knowing the intended writer, we can't diagnose whether the table is empty because
  no one's written to it, or because the writer is broken.

- **Anvil cloud-side uplink visibility.** When the websocket disconnects silently, does the
  Anvil app UI show any indicator (e.g., loading spinner that never resolves, error banner)?
  Knowing what the browser sees helps design the right recovery path.

- **Stats server staleness detection.** The lean_runner.sh comment says "stats_server already
  checked it isn't stale" for the lock file. What's the staleness threshold and how is it
  checked? This matters for understanding whether crashed sessions block reliably or not.
