# Session Artifact: Click-to-Expand Recent Errors Panel

**Date:** 2026-06-28  
**Node:** d990001a-7b2c-4314-878a-3f1014a646ce  
**Project:** Home Tab Error Log Indicator  
**Code commit:** claude-dashboard 6aecc7d (branch: attempt/error-panel-expand)

---

## Directive

Implement click-to-expand recent errors panel. Add click handler and expandable panel listing 3 recent errors. Print full file contents/diff of the handler and panel markup.

---

## What was done

Added click-to-expand behavior to the Home tab error indicator (`_home_error_lbl`) in `~/aadp/claude-dashboard/client_code/Form1/__init__.py`.

**Three changes made:**

1. `__init__`: Added `self._home_recent_errors = []` instance variable alongside `_home_error_count`.

2. `_build_home_layout`: After adding the strip to `_home_panel`, inserted a hidden `ColumnPanel` (`_home_error_panel`) and wired a click handler to `_home_error_lbl`. The handler toggles panel visibility and, on expand, clears and repopulates it with the stored `_home_recent_errors` — showing timestamp, workflow/node name (bold), and message text (truncated to 300 chars) for each error.

3. `_load_error_status`: Now captures `data.get('recent', [])` into `_home_recent_errors` (and resets to `[]` on exception). The `get_error_log_status` callable already returns `recent` (up to 3 unresolved errors, ordered timestamp desc) — this was unused before.

---

## Full diff

```diff
diff --git a/client_code/Form1/__init__.py b/client_code/Form1/__init__.py
index 0414b04..35814fe 100644
--- a/client_code/Form1/__init__.py
+++ b/client_code/Form1/__init__.py
@@ -90,6 +90,7 @@ class Form1(Form1Template):
         self._home_queue_pending = 0
         self._home_inbox_count = 0
         self._home_error_count = 0
+        self._home_recent_errors = []
         self._lean_poll_timer = None
         self._research_briefing_full = ''
         self._build_layout()
@@ -223,6 +224,34 @@ class Form1(Form1Template):
         strip.add_component(self._home_error_lbl)
         self._home_panel.add_component(strip)
 
+        # Collapsible error panel — toggled by clicking the error indicator
+        self._home_error_panel = ColumnPanel()
+        self._home_error_panel.visible = False
+        self._home_panel.add_component(self._home_error_panel)
+
+        def _toggle_error_panel(**kw):
+            self._home_error_panel.visible = not self._home_error_panel.visible
+            if self._home_error_panel.visible:
+                self._home_error_panel.clear()
+                if not self._home_recent_errors:
+                    self._home_error_panel.add_component(
+                        Label(text='No recent unresolved errors.', role='body', font_size=16)
+                    )
+                else:
+                    for err in self._home_recent_errors:
+                        ts = (err.get('timestamp') or '')[:19].replace('T', ' ')
+                        wf = err.get('workflow_name') or '—'
+                        node = err.get('node_name') or '—'
+                        msg = (err.get('error_message') or '—')[:300]
+                        self._home_error_panel.add_component(
+                            Label(text=f'{ts}  {wf} / {node}', bold=True, role='body', font_size=14)
+                        )
+                        self._home_error_panel.add_component(
+                            Label(text=msg, role='body', font_size=13)
+                        )
+
+        self._home_error_lbl.set_event_handler('click', _toggle_error_panel)
+
         # 2. Bill input panel
         self._home_panel.add_component(Label(text='Session Input', bold=True, role='body', font_size=16))
         self._bill_input_mode = ['Question']
@@ -1174,8 +1203,10 @@ class Form1(Form1Template):
             with anvil.server.no_loading_indicator:
                 data = anvil.server.call('get_error_log_status')
             self._home_error_count = data.get('unresolved_count', 0)
+            self._home_recent_errors = data.get('recent', [])
         except Exception:
             self._home_error_count = 0
+            self._home_recent_errors = []
         self._update_home_status_strip()
```

---

## Capability Delta

**Before:** Error count badge shows `🔴 N` or `✅` — no interaction, no detail.  
**After:** Clicking the badge toggles a panel below the strip listing up to 3 recent unresolved errors with timestamp, workflow/node, and message.  
**Reader:** Bill on the Anvil Home tab — one tap reveals the current errors without leaving the home view.

---

## Pending feedback (surfaced, not acted on)

- Grader FAIL on node 5939bc2b (×2): agent skipped work, no spec doc in artifact
- Grader FAIL on node 3c1d70dd: missing diff/file contents for badge conditional rendering

These are on earlier nodes in the same project. Not acting autonomously — surfacing for Bill.
