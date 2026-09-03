"""Does a build that lands SUPERSEDED stop the tab saying it is working?

`_the_topology_tab_is_quiet` treats a non-empty `working` label as
"something is still coming", and the label is written by
`say_a_build_is_coming` the moment a build is QUEUED. Three of the four
landing branches end at `panel.set_unit(...)`, which clears it. TWO DO
NOT: the SUPERSEDED branch, where the design moved while the build was
being worked out, and the EDITS-MOVED branch beside it. Both dump a
line and return.

WHY THAT IS WORTH MEASURING RATHER THAN READING. If a superseded
landing always has another build behind it, the sentence is cleared a
moment later and nothing is wrong; if it does not, the tab tells
somebody it is working when nothing is coming, and every test that
waits for quiet waits out its whole ceiling. CI's 4.0.3 leg spent 91
seconds on one such premise on 2026-09-02 at `743e73b` -- 771 passed,
1 failed -- while the next topology test on the same runner passed in
4.3 seconds, so the tab itself was healthy and only that one dialog
never went quiet.

THE CONDITION IS STAGED, NOT RACED. A build is queued and the design
is moved under it before it lands, which is exactly what a slower
machine supplies by itself. The control queues a build and leaves the
design alone.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/what_a_superseded_build_leaves_up.py
"""
import time

import probe_kit


def the_four_terms(dlg):
  """What `_the_topology_tab_is_quiet` asks, read once.

  Args:
    dlg: the dialog whose Topology tab to read.

  Returns:
    A dict of the four things that mean "something is still coming",
    so a caller can say WHICH one is outstanding rather than only that
    one is -- which is what the suite's own premise cannot say today.
  """
  panel = dlg.topology_panel
  label = getattr(panel, "working", None)
  timer = getattr(dlg, "_preview_timer", None)
  return {
    "a build in flight": getattr(dlg, "_topology_task", None) is not None,
    "one queued behind it": bool(getattr(dlg, "_topology_wanted", False)),
    "the working sentence": bool(
      (label.text() if label is not None else "").strip()),
    "a rebuild pending": bool(timer is not None and timer.isActive()),
  }


def one_arm(probe, name, move_the_design_under_the_build):
  """Queue a build, optionally move the design, and read the tab.

  Args:
    probe: the `probe_kit.Probe` holding QGIS and the project.
    name: names the arm in the report.
    move_the_design_under_the_build: True to change the family while
      the build is in flight, which is what makes its landing
      SUPERSEDED.

  Returns:
    A dict with the four terms afterwards and how long the tab took to
    go quiet, bounded, so an arm that never goes quiet says so rather
    than hanging.
  """
  from qgis.core import QgsProject
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  suite = probe.suite
  probe.clear()

  layer = suite.make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=suite._Iface())
  try:
    dlg.live_check.setChecked(False)
    dlg.opt_experimental.setChecked(True)
    dlg.show()
    suite._tick(200)
    dlg.n_spin.setValue(4)
    suite._tick(200)
    suite._choose_family(dlg, "laves 3.3.4.3.4")
    suite._tick(300)
    assert suite._wait_for_the_topology(dlg), \
      "PREMISE: no topology was built at all, so nothing is staged"

    # ---- QUEUE ONE, and know it was queued: the sentence going up IS
    # `say_a_build_is_coming`, so a run where it never appears has
    # staged nothing.
    dlg._queue_topology(even_if_unasked=True)
    suite._tick(50)
    queued = the_four_terms(dlg)
    assert queued["the working sentence"] or queued["a build in flight"], \
      f"PREMISE: no build was queued at all: {queued}"

    if move_the_design_under_the_build:
      # THE DESIGN MOVES UNDER IT, which is what makes the landing
      # superseded -- the stamp the build carries no longer matches.
      suite._choose_family(dlg, "hex-slice 4")
      suite._tick(50)

    # ---- WAIT, BOUNDED, for the tab to go quiet, and report what was
    # still outstanding if it never did.
    deadline = time.monotonic() + 40
    quiet_after = None
    while time.monotonic() < deadline:
      terms = the_four_terms(dlg)
      if not any(terms.values()):
        quiet_after = round(40 - (deadline - time.monotonic()), 1)
        break
      suite._tick(100)
    return {"went quiet after": quiet_after,
            "still outstanding": [k for k, v in the_four_terms(dlg).items() if v],
            "the sentence": (dlg.topology_panel.working.text() or "")[:44]}
  finally:
    dlg.close()
    suite._tick(100)


def main():
  """Both arms in one run, control first."""
  probe = probe_kit.start()
  for name, moved in (("control: the design stays put", False),
                      ("treated: the design moves under the build", True)):
    row = one_arm(probe, name, moved)
    print(f"--- {name}")
    for key, value in row.items():
      print(f"      {key}: {value}")
  print()
  print("A tab that never goes quiet is one every waiting premise sits "
        "out to its ceiling, and a sentence saying the plugin is "
        "working when nothing is coming is what a person reads.")
  print("\nPROBE COMPLETE: both arms reported, teardown next.")


main()
