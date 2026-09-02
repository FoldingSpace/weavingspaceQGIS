"""Report what a click on the Topology drawing can reach, on THIS leg.

WHY THIS EXISTS. `test_several_classes_can_be_moved_together` has
failed on one Linux leg of three CI rounds with the selection left
exactly where the plain click put it, and passed on this project's
development machine every time. Three candidate causes were measured
and ruled out there, in one probe with its arms in one run
(`tools/probes/what_the_aim_promised_and_the_click_met.py`): the aim
and the click agreed about all eight seats of the second class, the
font was swept to 18pt, and a topology build was STAGED to land
between the aim and the click. None of them reproduced it.

So the cause is a property of a machine nobody here can drive, and the
honest instrument is one that MEASURES ON THAT MACHINE rather than a
fifth guess made on this one. This project's own rule is that when a
reproduction will not reproduce, you measure the session that is
broken.

IT REPORTS AND DOES NOT GATE, deliberately, and exits 0 whatever it
finds. The suite's own test is the gate; a second thing failing about
the same journey would only make one red mean two things. What this
adds is the numbers beside that red: how large the drawing came out,
how many seats of each class a click could reach at all, and -- for
the seat the test itself would choose -- what the view's hit test said
at aim time against what the press actually met.

READING IT: the answer is in the disagreements. A seat the aim calls
clear and the press meets a handle on is a state changing between the
two; a class with ZERO reachable seats is a drawn layout this machine
never produces; a press that met the right class while the selection
did not move is the panel's own handling rather than the aiming.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
for where in (ROOT, TOOLS):
  if where not in sys.path:
    sys.path.insert(0, where)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import probe_kit                                        # noqa: E402


def seats_of(view, target, label):
  """Every drawn seat of one class, with what the view says of it.

  Args:
    view: the Topology tab's drawing widget.
    target: "vertex" or "edge".
    label: the class label to look for.

  Returns:
    A list of (point, handle over it, what `_nearest` names). Vertices
    only: an edge seat needs a walk along its segments, and the
    failure this reports on is about a vertex.
  """
  topology = view._drawn()
  if topology is None or target != "vertex":
    return []
  from qgis.PyQt.QtCore import QPoint
  found = []
  for vertex in topology.points.values():
    if getattr(vertex, "label", None) != label:
      continue
    where = view._to_screen(vertex.point.x, vertex.point.y)
    if not (0 <= where.x() <= view.width()
            and 0 <= where.y() <= view.height()):
      continue
    seat = QPoint(int(round(where.x())), int(round(where.y())))
    named = view._nearest(seat)
    found.append((seat, bool(view._handle_at(seat)),
                  (named[0], named[1])))
  return found


def main():
  """Measure the aim on this machine and print what it found.

  Returns:
    None. The exit status is always 0: this is an instrument rather
    than a gate, and a red here would only duplicate the suite's.
  """
  print("=== topology aim probe: what a click can reach here ===")
  # THE PROJECT'S OWN HARNESS RATHER THAN A FRESH ONE. `probe_kit`
  # starts QGIS, empties the project, installs the modal shim and
  # hands back a dialog -- the forty lines every probe here used to
  # re-type, and which eleven hand-written wrappers once got wrong in
  # the same way at once.
  probe = probe_kit.start()
  suite = probe.suite
  from qgis.PyQt.QtCore import Qt
  from qgis.PyQt.QtTest import QTest
  from qgis.PyQt.QtWidgets import QApplication

  app = QApplication.instance()
  if app is not None:
    print(f"    font: {app.font().family()!r} at "
          f"{app.font().pointSize()}pt")
  dlg, _layer, _tile_id = probe.dialog()
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show()
    suite._tick(200)
    dlg.n_spin.setValue(4)
    suite._choose_family(dlg, "laves 3.3.4.3.4")
    suite._tick(300)
    if not suite._the_topology_tab_is_quiet(dlg):
      print("    no topology was built, so there was nothing to aim at")
      return
    panel = dlg.topology_panel
    view = panel.view
    view.grab()
    suite._tick(50)
    print(f"    drawing: {view.width()}x{view.height()}")

    from weavingspace_qgis import topology_edits
    classes = topology_edits.classes(panel._topology).get("vertex", "")
    print(f"    vertex classes: {classes!r}")
    if len(classes) < 2:
      print("    fewer than two classes, so the journey does not arise")
      return
    first, second = classes[0], classes[1]

    for label in (first, second):
      found = seats_of(view, "vertex", label)
      reachable = [s for s in found
                   if not s[1] and s[2] == ("vertex", label)]
      print(f"    class {label!r}: {len(found)} drawn, "
            f"{len(reachable)} a click would reach")
      for seat, handled, named in found:
        print(f"        ({seat.x()},{seat.y()}) handle={handled} "
              f"nearest={named}")

    aim = [s for s in seats_of(view, "vertex", first)
           if not s[1] and s[2] == ("vertex", first)]
    if not aim:
      print(f"    NOTHING REACHES {first!r}: the plain click has no seat")
      return
    QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, aim[0][0])
    suite._tick(150)
    print(f"    after the plain click: {panel._selection}")

    later = seats_of(view, "vertex", second)
    aim2 = [s for s in later if not s[1] and s[2] == ("vertex", second)]
    print(f"    class {second!r} after the first click: {len(later)} "
          f"drawn, {len(aim2)} reachable")
    if not aim2:
      print(f"    NOTHING REACHES {second!r} ONCE {first!r} IS HELD, "
            f"which is the state the suite's aimer reports as a "
            f"fixture failure rather than a defect")
      return

    met = {}
    real_press = view.mousePressEvent

    def watched(event):
      """Record what the press finds, then let it run."""
      where = (event.position() if hasattr(event, "position")
               else event.pos())
      named = view._nearest(where)
      met.update({"handle": bool(view._handle_at(where)),
                  "nearest": (named[0], named[1]),
                  "modifiers": str(event.modifiers())})
      return real_press(event)

    view.mousePressEvent = watched
    try:
      QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.ShiftModifier, aim2[0][0])
      suite._tick(150)
    finally:
      view.mousePressEvent = real_press
    print(f"    aimed the shift-click at "
          f"({aim2[0][0].x()},{aim2[0][0].y()})")
    print(f"    the press met: {met or 'nothing -- it never ran'}")
    print(f"    selection at the end: {panel._selection}")
    held = panel._selection
    if held and held[0] == "vertex" and set(held[1]) == {first, second}:
      print("    -> both classes held here")
    else:
      print(f"    -> ONLY {held} held, which is the runner's own "
            f"failure, and the lines above are its context")
  except Exception as trouble:                          # noqa: BLE001
    # AN INSTRUMENT MUST NOT REPLACE THE VERDICT. Anything raised here
    # is reported as a finding about the probe rather than thrown,
    # since this runs before the suite and a traceback from it would
    # colour a job about something it does not measure.
    import traceback
    print(f"    the probe itself failed: {trouble!r}")
    traceback.print_exc()
  finally:
    try:
      dlg.close()
      probe.clear()
    except Exception:                                   # noqa: BLE001
      pass
  print("=== probe complete ===")


if __name__ == "__main__":
  main()
