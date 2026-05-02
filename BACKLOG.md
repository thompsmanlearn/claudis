B-077: Collapse thread action panel to redesign shape

## Goal

Finish the thread page legibility win. B-076 reorganized the display of entries; this card reorganizes the actions below them. The current panel exposes five flat controls (annotate, state, wire, gather, add analysis) with no signal about which to reach for when. The redesign calls for three primary actions — Gather, Export, Paste analysis — plus annotation as a secondary action, with state-change and wire controls moving into a collapsed drawer alongside the History drawer that already exists. After this card, opening a thread shows the partitioned content from B-076 above a clean action surface that matches the design spec.

## Context

Authoritative design: ~/aadp/claudis/anvil-redesign-principles-and-plan.md, "Thread page" section (the four-paragraph block describing top/middle/bottom/actions). The Actions paragraph is the spec.

Current state of _build_thread_actions in ~/aadp/claude-dashboard/client_code/Form1/__init__.py:
- It has a NOTE comment at the top (added in the prior cleanup pass) flagging it as pending its own card. That comment goes away when this card lands.
- It currently builds five controls in a flat layout: annotate, state-change, wire-agent, gather, add-analysis. All visible at once, no grouping.
- It does NOT currently have an Export action. Export is part of the redesign principles (principle 1: "Export. Take the current view's state to a desktop Claude session as a clean bundle.") but no thread-level export exists yet.

This card delivers the layout. Export-the-action wires up to a callable that doesn't exist yet — for this card, the Export button calls a placeholder that returns a stub bundle and shows a "not yet implemented" message in the feedback label. Wiring real export is a future card. Building the button now is correct because the layout it slots into is what we're shipping.

The redesign explicitly collapses state-change and wire-agent into a drawer. Both are still real operations the system needs to expose; they're just not primary. Treat them like the existing History drawer at the bottom of the entries list — a labeled toggle that reveals the controls when opened.

The History drawer pattern from B-076 (▶ History (N) / ▼ History (N), hist_panel.visible toggling) is the reference shape. Match its visual style and toggle behavior so the two drawers feel like one pattern.

## Done when

- _build_thread_actions in Form1/__init__.py renders three primary action buttons in this order: Gather, Export, Paste analysis. Each is a Button with role='filled-button' and its own feedback Label below it. The existing Gather and Add-analysis behaviors carry over unchanged into the new buttons (Gather → existing trigger_thread_gather; Paste analysis → existing add-analysis behavior with the embedded TextArea).
- An Annotation control renders below the three primary actions, visually secondary (role='outlined-button' or role='tonal-button', smaller). Existing annotate behavior carries over unchanged.
- A drawer labeled "▶ Thread settings (state, agent)" renders below the annotation control. Clicking it expands to reveal the existing state-change controls and wire-agent controls, unchanged in behavior. Clicking again collapses. Toggle text flips to "▼ Thread settings (state, agent)" when open. Match the History drawer's pattern from _load_thread_entries.
- An Export button is wired. On click it calls a new uplink callable `export_thread_bundle(thread_id)` that returns a dict with keys `{thread_id, exported_at, stub: True, message}`. The feedback label shows "Stub export — full bundle not yet implemented" and the call is logged. Add the callable to ~/aadp/claudis/anvil/uplink_server.py as a stub returning that dict. No real bundle assembly in this card.
- The NOTE comment at the top of _build_thread_actions is removed.
- The five-flat-controls layout is gone. No control appears twice (i.e., state-change appears in the drawer, not also at the top level).
- One commit on claude-dashboard master with the Form1 changes. One commit on claudis main with the uplink stub. Both pushed.
- Session artifact written.

## Scope

Touch:
- ~/aadp/claude-dashboard/client_code/Form1/__init__.py (only _build_thread_actions and any small helper added for the drawer if needed)
- ~/aadp/claudis/anvil/uplink_server.py (add export_thread_bundle stub)
- session artifact in ~/aadp/claudis/sessions/lean/

Do not touch:
- _load_thread_entries (B-076 work, do not modify)
- The History drawer in _load_thread_entries (reference its pattern, don't refactor it)
- Any other Form1 function
- Any database schema
- Any other uplink callable
- The thread page top section (header, summary handling) — that's a separate concern
- Any other file in either repo

If you find yourself wanting to assemble a real export bundle, write a new entry_type, or refactor anything in _load_thread_entries — stop. That's a future card. This card delivers the action layout and a stub export endpoint. Real export bundling is its own card after we've decided what goes in the bundle.
