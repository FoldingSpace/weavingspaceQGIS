"""Red and green for the topology-landing test's repair.

CI failed `a topology landing does not strand a live tick` on the
macOS runner and again under the coverage recorder, with the same
assertion: at the second call to `_generate`, `_live_pending` was
still True. The repair stops the live timer once the condition is
staged, on the reading that the competing caller is
`_maybe_live_generate`, which ends in `self._generate(live=True)` and
does NOT clear the flag -- `_finish_run` does, afterwards.

THAT READING IS A HYPOTHESIS UNTIL BOTH ARMS ARE DRIVEN. This project's
own rule: before saying a case cannot be reproduced here, ask what the
other machine has more of and set that quantity directly. What the
runners have is a live tick landing BEFORE the topology build; so this
stages exactly that, by firing the live timer immediately instead of
waiting for a slower machine to do it for us.

ARM A: the timer left running and fired at once -- the CI condition.
        Expect `seen[1]` to be `_maybe_live_generate` with the flag
        True, which is the failure CI reported.
ARM B: the timer stopped, which is the repair. Expect the landing's
        own re-press, with the flag False.

Both arms run in ONE process, each from an empty project, because two
arms sharing a QgsProject is how a control gets contaminated -- which
cost this project two wrong readings earlier the same day.

    cd <checkout> && PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" tools/probes/a_live_tick_racing_the_topology_landing.py
"""

import importlib.util
import os
import traceback

ROOT = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject      # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
rt._no_modal_dialogs()

from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402


def drive(stop_the_timer: bool):
  """Run the test's journey once and report every `_generate` call.

  Args:
    stop_the_timer: True to apply the repair (stop the live timer once
      the condition is staged); False to leave it running and fire it
      at once, which is what a slower machine does by itself.

  Returns:
    The list of (live_pending, caller) pairs, in call order.
  """
  QgsProject.instance().clear()          # each arm from an empty project
  rt.BAR_MESSAGES.clear()
  layer = rt.make_region_layer()
  QgsProject.instance().addMapLayer(layer)

  with rt._temp_dir():
    dlg = WeavingSpaceDialog(iface=rt._Iface())
    try:
      dlg.opt_experimental.setChecked(True)
      dlg.live_check.setChecked(False)
      dlg.show()
      rt._tick(200)
      dlg.n_spin.setValue(4)
      rt._tick(200)
      dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
      rt._tick(300)
      if not rt._wait_for_the_topology(dlg):
        return [("PREMISE FAILED: no topology", "")]
      rt._generate_and_wait(dlg)

      panel = dlg.topology_panel
      wanted = next(
        i for i in range(panel.class_combo.count())
        if (panel.class_combo.itemData(i) or ("", ""))[0] == "vertex")
      panel.class_combo.setCurrentIndex(wanted)
      rt._tick(150)
      panel.how_combo.setCurrentIndex(
        panel.how_combo.findData("nudge_vertex"))
      rt._tick(150)
      panel.apply_button.click()

      dlg.live_check.setChecked(True)
      dlg._live_pending = True

      if stop_the_timer:
        dlg._live_timer.stop()
      else:
        # SET THE QUANTITY THE OTHER MACHINE HAS MORE OF. A runner is
        # slow enough that the live tick lands before the topology
        # build; here the timer is simply told to fire now.
        dlg._live_timer.start(0)

      seen = []
      real_generate = dlg._generate

      def watched(*a, **kw):
        who = "?"
        for frame in reversed(traceback.extract_stack()[:-1]):
          if frame.name != "watched":
            who = frame.name
            break
        seen.append((bool(getattr(dlg, "_live_pending", False)), who))
        return real_generate(*a, **kw)

      dlg._generate = watched
      try:
        dlg._generate()
        rt._settle_topology(dlg, seconds=30)
        rt._settle(dlg)
        for _ in range(10):
          rt._tick(200)
      finally:
        dlg._generate = real_generate
      return seen
    finally:
      dlg.close()
      dlg.deleteLater()
      rt._tick(50)


def verdict(name, seen):
  """Print one arm's calls and what the test's assertion would say.

  Args:
    name: how to label this arm in the output, e.g. which of the two
      conditions it staged.
    seen: the list of (live_pending, caller) pairs `drive` returned,
      in call order. A list shorter than two means the journey never
      reached a second call, which is the test's own premise failing
      rather than its assertion.

  Returns:
    None. Everything is printed, because the point of the probe is a
    reading a person compares between the two arms.
  """
  print(f"\n--- {name} ---")
  for index, (live, who) in enumerate(seen):
    print(f"  [{index}] live_pending={live!s:5}  <- {who}")
  if len(seen) < 2:
    print("  fewer than two calls: the test's own PREMISE would fail")
    return
  live, who = seen[1]
  print(f"  the old assertion reads seen[1]: live_pending={live}, from {who}")
  print("  old test would: " + ("FAIL" if live else "pass"))
  print("  new test would: " + (
    "refuse to judge (premise names the live timer)"
    if who == "_maybe_live_generate" else
    ("FAIL" if live else "pass")))


# ARM A first is deliberate: if the contaminated-control fault were
# present, running the repair first would hide it.
verdict("ARM A: live timer left running and fired at once (the CI condition)",
        drive(stop_the_timer=False))
verdict("ARM B: live timer stopped (the repair)",
        drive(stop_the_timer=True))
