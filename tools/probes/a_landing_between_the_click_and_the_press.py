"""Does a landing between CHOOSING a thing and GRABBING it wipe the choice?

The ruling of 2026-09-01 holds a landing that arrives MID-GESTURE until
the pointer comes up, because `show_topology` clears the drag preview
and the chosen thing. `gesture_in_progress()` is true between the press
and the release -- so the window between the CLICK that chooses and the
PRESS that grabs is NOT covered, and a landing there is applied at once:
the chosen thing goes, `_refresh_classes` resets the class chooser to
the first vertex class, and the press that follows finds no handle.

WHY IT IS WORTH MEASURING RATHER THAN READING. macOS CI failed `every
way of editing the topology moves the drawing` on 2026-09-02 at
`743e73b` -- 771 passed, 1 failed -- with BOTH complaints its vertex
cell can make: "dragging a vertex showed nothing while it moved" and
"dragging a vertex left ['chose'] rather than moving the design AND the
drawing". No preview, and the chooser moved. That is the signature this
probe stages. The same commit touched no shipped source, and the test
passes three times out of three here, so the frequency is not the
question -- the window is.

THE CONDITION IS STAGED, NOT RACED, which is this project's standing
answer to a case that depends on a window: the landing is delivered by
hand, through the same method the build's own callback uses, at the one
moment the hold does not cover. The control clicks and grabs with
nothing landing in between.

AND WHAT LANDS IS A REBUILD OF THE SAME DESIGN, because that is what
the journey produces -- a queued build finishing re-runs this design.
The classes carry the same labels over new objects, which is precisely
the case `show_topology` says it handles: "the CLASS survives a
rebuild; the object does not".

Each arm clears the project first: two arms sharing one QgsProject is
how a control gets contaminated.

    unset PYTHONHOME PROJ_LIB QGIS_PREFIX_PATH
    set -a; eval "$(bash tools/macos_qgis_env.sh)"; set +a
    QT_QPA_PLATFORM=offscreen PYTHONUNBUFFERED=1 \\
      PYTHONPATH="$PWD:$PWD/tools" "$QGIS_PY" -u \\
      tools/probes/a_landing_between_the_click_and_the_press.py
"""
import probe_kit


def a_vertex_to_aim_at(view):
  """A screen point on a drawn vertex, nearest the middle.

  Args:
    view: the topology view to read.

  Returns:
    A QPoint inside the widget, or None where nothing is drawn there.
  """
  from qgis.PyQt.QtCore import QPoint
  topology = view._drawn()
  if topology is None:
    return None
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
  return seats[0][1] if seats else None


def one_arm(probe, land_between_the_click_and_the_press):
  """Click a vertex, optionally land a build, then drag it.

  Args:
    probe: the `probe_kit.Probe` holding QGIS and the project.
    land_between_the_click_and_the_press: True to deliver a landing
      after the choice is made and BEFORE the pointer goes down, which
      is the window `gesture_in_progress()` does not cover.

  Returns:
    A dict saying what the choice was before and after, whether the
    press drew a preview, and whether the drag moved the design --
    which together are the two complaints CI's vertex cell makes.
  """
  from qgis.PyQt.QtCore import QPoint, Qt as QtNamespace
  from qgis.PyQt.QtTest import QTest
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
      "PREMISE: no topology was built, so there is nothing to choose"
    panel = dlg.topology_panel
    view = panel.view
    view.grab()
    suite._tick(50)

    at = a_vertex_to_aim_at(view)
    assert at is not None, "PREMISE: no vertex is drawn inside the widget"

    # ---- CHOOSE, exactly as a person does: one click on a vertex.
    QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                     QtNamespace.KeyboardModifier.NoModifier, at)
    suite._tick(150)
    chose = panel.class_combo.currentText()
    held = view._chosen_thing
    assert held is not None, \
      "PREMISE: the click chose nothing, so nothing is staged"

    # ---- THE STAGED CONDITION: a landing with the choice made and the
    # pointer still up, which is the one moment the hold cannot see.
    if land_between_the_click_and_the_press:
      # A REBUILD OF THE SAME DESIGN, which is what actually lands: a
      # queued build finishing re-runs THIS design, so the classes are
      # the same labels over NEW objects. Landing another family would
      # stage a louder condition than the journey ever produces, and a
      # fixture louder than the case measures something else.
      from weavingspace_qgis import topology_edits
      rebuilt, why = topology_edits.build(panel._unit)
      assert rebuilt is not None, \
        f"PREMISE: the same design would not rebuild ({why})"
      panel.set_unit(panel._unit, rebuilt, ghost=None)
      suite._tick(100)

    chose_after_the_landing = panel.class_combo.currentText()
    # THE OLD OBJECT IS *MEANT* TO GO -- a rebuild makes new ones, and
    # `show_topology` says so at the line. What matters is whether the
    # panel is still holding SOMETHING of the chosen class, and whether
    # a handle still sits where the person clicked, since the press
    # that follows asks `_handle_at` and nothing else.
    holding_now = view._chosen_thing
    label_now = getattr(holding_now, "label", None)
    handles = view.handles() or []
    nearest = None
    if handles:
      nearest = round(min(((h[1].x() - at.x()) ** 2
                           + (h[1].y() - at.y()) ** 2) ** 0.5
                          for h in handles), 1)

    # ---- GRAB AND DRAG, from the same point the click chose.
    far = QPoint(at.x() + 12, at.y() - 9)
    QTest.mousePress(view, QtNamespace.MouseButton.LeftButton,
                     QtNamespace.KeyboardModifier.NoModifier, at)
    suite._tick(30)
    QTest.mouseMove(view, far)
    suite._tick(30)
    drew_a_preview = view._preview is not None
    QTest.mouseRelease(view, QtNamespace.MouseButton.LeftButton,
                       QtNamespace.KeyboardModifier.NoModifier, far)
    suite._tick(250)
    return {
      "chose at the click": chose,
      "chose after the landing": chose_after_the_landing,
      "the chooser moved": chose_after_the_landing != chose,
      "holds a thing of that class": label_now,
      "it is the same object": holding_now is held,
      "handles drawn": len(handles),
      "nearest handle to the click": nearest,
      "the drag drew a preview": drew_a_preview,
      "edits recorded": len(panel.edits() or []),
    }
  finally:
    dlg.close()
    suite._tick(100)


def main():
  """Both arms in one run, control first."""
  probe = probe_kit.start()
  for name, staged in (("control: nothing lands between them", False),
                       ("treated: a build lands between them", True)):
    row = one_arm(probe, staged)
    print(f"--- {name}")
    for key, value in row.items():
      print(f"      {key}: {value}")
  print()
  print("A choice a person made and can no longer see is the harm the "
        "mid-gesture hold exists to prevent, one step earlier: the "
        "press that follows finds no handle and the drag does nothing.")
  print("\nPROBE COMPLETE: both arms reported, teardown next.")


main()
