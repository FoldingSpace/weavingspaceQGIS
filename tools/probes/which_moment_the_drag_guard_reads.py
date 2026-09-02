"""Whose fault is "the panel adopted a new topology mid-gesture"?

CI's coverage leg failed `a build that lands mid drag does not wipe the
gesture` on 2026-09-02 at `6e40574`, on its MAIN assertion rather than
on a premise: 256 passed and 1 failed on one shard of three, each shard
naming the same total of 772. The same test passed in that candidate's
own local suite at 4.8s and failed on the runner at 11.7s.

TWO READINGS AND THEY NEED OPPOSITE REPAIRS. Either the hold has a hole
-- a landing adopted while a gesture really is in progress, which is
the product defect the guard exists for -- or the test READ ITS SUBJECT
AT THE WRONG MOMENT: it captures `aimed_at = panel._topology` BEFORE
the aiming clicks, and those clicks tick the event loop, and this test
deliberately does not drain the queued build first. A landing arriving
in that window is adopted CORRECTLY, since no gesture is in progress
yet, and the stale `aimed_at` then reports correct behaviour as the
defect -- in a sentence that says "mid-gesture" about a landing that
happened before the gesture.

SO THE CONDITION IS STAGED RATHER THAN RACED, which is this project's
standing answer to a case that depends on a window. Arm A delivers a
landing BEFORE the press, through the same method the task's callback
uses; arm B is the control with nothing landing there. Both then take
the two readings side by side -- the one the test makes today, and the
one taken at the press -- so a single run says which of them is about
the product.

Each arm clears the project first: two arms sharing one QgsProject is
how a control gets contaminated, which cost this project two wrong
readings on 2026-08-31.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/which_moment_the_drag_guard_reads.py
"""
import probe_kit


def a_second_design():
  """A unit and topology from another family, to land mid-run.

  Returns:
    (unit, topology) built from the first hex-slice at n=3, which is a
    design the fixture is not on, so an adoption of it is unmistakable.
  """
  from weavingspace_qgis import catalog, topology_edits
  named = [k for k in catalog.TILINGS_BY_N.get(3, {})
           if k.startswith("hex-slice")]
  assert named, "PREMISE: the catalogue offers no hex-slice at n=3"
  unit = catalog.make_unit(catalog.TILINGS_BY_N[3][named[0]],
                           spacing=500, crs=3857)
  topology, why = topology_edits.build(unit)
  assert topology is not None, \
    f"PREMISE: the second design built no topology to land ({why})"
  return unit, topology


def one_arm(probe, name, land_before_the_press):
  """Drive the guard's own journey and take BOTH readings.

  Args:
    probe: the `probe_kit.Probe` holding QGIS and the project.
    name: names the arm in the report.
    land_before_the_press: True to deliver a landing after the subject
      is captured and BEFORE the pointer goes down, which is the window
      the aiming clicks open and the test does not close.

  Returns:
    A dict saying whether each reading held, and what the panel was
    holding at each moment.
  """
  from qgis.PyQt.QtCore import QPoint, Qt as QtNamespace
  from qgis.PyQt.QtTest import QTest
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  from qgis.core import QgsProject
  suite = probe.suite
  probe.clear()

  layer = suite.make_region_layer()
  QgsProject.instance().addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=suite._Iface())
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show()
    suite._tick(200)
    dlg.n_spin.setValue(4)
    suite._tick(200)
    suite._choose_family(dlg, "laves 3.3.4.3.4")
    suite._tick(300)
    assert suite._wait_for_the_topology(dlg), \
      "PREMISE: no topology was built, so there is nothing to drag"
    panel = dlg.topology_panel
    view = panel.view
    view.grab()
    suite._tick(50)
    other_unit, other_topology = a_second_design()

    # ---- THE READING THE TEST MAKES TODAY, taken before any clicking.
    before_the_clicks = panel._topology

    # ---- THE STAGED CONDITION: a landing with NO gesture in progress,
    # which the product is right to adopt at once.
    if land_before_the_press:
      pre_unit, pre_topology = a_second_design()
      panel.set_unit(pre_unit, pre_topology, ghost=None)
      suite._tick(100)

    # ---- AIM, exactly as the guard does: click candidate seats until
    # the product agrees one offers a handle.
    topology = view._drawn()
    middle = (view.width() / 2, view.height() / 2)
    seats = []
    for vertex in topology.points.values():
      point = view._to_screen(vertex.point.x, vertex.point.y)
      if not (0 <= point.x() <= view.width()
              and 0 <= point.y() <= view.height()):
        continue
      away = ((point.x() - middle[0]) ** 2
              + (point.y() - middle[1]) ** 2) ** 0.5
      seats.append((away, QPoint(int(round(point.x())),
                                 int(round(point.y())))))
    seats.sort(key=lambda pair: pair[0])
    handles = []
    for _away, candidate in seats:
      QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                       QtNamespace.KeyboardModifier.NoModifier, candidate)
      suite._tick(150)
      handles = view.handles()
      if handles:
        break
    assert handles, "PREMISE: no drawn vertex offers a handle to drag"

    grab_at = QPoint(int(round(handles[0][1].x())),
                     int(round(handles[0][1].y())))
    QTest.mousePress(view, QtNamespace.MouseButton.LeftButton,
                     QtNamespace.KeyboardModifier.NoModifier, grab_at)
    suite._tick(50)

    # ---- THE READING TAKEN AT THE PRESS, which is what the claim is
    # actually about: what the panel holds once the gesture has begun.
    at_the_press = panel._topology

    moved_to = grab_at + QPoint(60, 0)
    QTest.mouseMove(view, moved_to)
    suite._tick(150)
    drew_a_preview = view._preview is not None

    # ---- THE LANDING THE GUARD IS ABOUT: mid-gesture, by hand.
    panel.set_unit(other_unit, other_topology, ghost=None)
    suite._tick(50)
    after = panel._topology

    QTest.mouseRelease(view, QtNamespace.MouseButton.LeftButton,
                       QtNamespace.KeyboardModifier.NoModifier, moved_to)
    suite._tick(200)
    return {
      "preview": drew_a_preview,
      "old reading (captured before the clicks)": after is before_the_clicks,
      "new reading (captured at the press)": after is at_the_press,
      "the panel moved before the press": at_the_press is not before_the_clicks,
      "the mid-gesture landing was adopted": after is other_topology,
    }
  finally:
    dlg.close()
    suite._tick(100)


def main():
  """Both arms in one run, control first."""
  probe = probe_kit.start()
  for name, staged in (("control", False), ("landed pre-press", True)):
    row = one_arm(probe, name, staged)
    print(f"--- {name}")
    for key, value in row.items():
      print(f"      {key}: {value}")
  print()
  print("A landing the product adopted BEFORE the pointer went down is "
        "correct behaviour; where the old reading fails and the new one "
        "holds, the guard is blaming the product for it.")
  print("\nPROBE COMPLETE: both arms reported, teardown next.")


main()
