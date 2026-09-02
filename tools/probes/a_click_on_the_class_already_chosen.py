"""Does clicking a vertex of the class already selected move anything?

macOS CI reported "clicking a vertex selected nothing" on 2026-09-01
against a test this machine passes every time. The premise held -- a
vertex WAS drawn inside the widget and the click was delivered -- so
what was in question is the claim that the SELECTION store must move.

THE HYPOTHESIS, recorded before the verdict so it is falsifiable:
`_refresh_classes` puts the chooser on the FIRST vertex class after a
landing, so a click on a vertex of THAT class correctly changes
nothing. Which vertex sits nearest the middle of the drawing decides
whether the test can see anything, and that is a fact about the drawn
layout -- so about the fonts and the panel's width, which is what
differs between this Mac and a runner.

WHAT IT DRIVES: the same setup the test uses, then a click on the
nearest vertex TWICE. The second click is the runner's condition,
staged rather than waited for: by then that class is already chosen.
If the selection stands still there and a later candidate moves it,
the hypothesis holds and aiming at the nearest vertex alone is what
made the verdict a fact about the machine.

    PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" tools/probes/a_click_on_the_class_already_chosen.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
  os.path.dirname(os.path.abspath(__file__)))))

from tools import probe_kit                              # noqa: E402


def main() -> int:
  """Drive the click twice and report what the selection did.

  Returns:
    0 always; this probe reports rather than judges, since what it
    measures is a fact about a drawing rather than a rule anybody
    settled.
  """
  from qgis.PyQt.QtCore import QPoint, Qt
  from qgis.PyQt.QtTest import QTest

  probe = probe_kit.start()
  # THE KIT HANDS BACK A TRIPLE, not a dialog: (dialog, layer, tile
  # id). Unpacking it wrongly costs a probe that dies on an
  # AttributeError, which reads as the product refusing to build.
  dlg, _layer, _tile_id = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  dlg.show()
  probe.suite._tick(200)
  dlg.n_spin.setValue(4)
  probe.suite._tick(200)
  probe.suite._choose_family(dlg, "laves 3.3.4.3.4")
  probe.suite._tick(300)
  if not probe.suite._wait_for_the_topology(dlg):
    print("PREMISE FAILED: no topology was built")
    return 0

  panel = dlg.topology_panel
  view = panel.view
  topology = view._drawn()
  middle = (view.width() / 2, view.height() / 2)
  print(f"view {view.width()}x{view.height()}")

  seats = []
  for vertex in topology.points.values():
    point = view._to_screen(vertex.point.x, vertex.point.y)
    if 0 <= point.x() <= view.width() and 0 <= point.y() <= view.height():
      away = ((point.x() - middle[0]) ** 2
              + (point.y() - middle[1]) ** 2) ** 0.5
      seats.append((away, QPoint(int(round(point.x())),
                                 int(round(point.y())))))
  seats.sort(key=lambda pair: pair[0])
  print(f"{len(seats)} vertex(es) drawn inside the widget")
  if not seats:
    return 0

  def click(at):
    """Click the drawing where a person would, and report the choice.

    Args:
      at: the widget point to click.

    Returns:
      The panel's selection afterwards, as a comparable tuple.
    """
    QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, at)
    probe.suite._tick(150)
    target, labels = panel._selection
    return (target, tuple(sorted(labels or ())))

  start = panel._selection
  print(f"selection before anything: {start}")
  first = click(seats[0][1])
  print(f"after clicking the nearest vertex:  {first}")
  again = click(seats[0][1])
  print(f"after clicking the SAME one again:  {again}")
  print(f"  -> the second click moved the selection: {again != first}")

  moved_by = None
  for away, at in seats[1:]:
    now = click(at)
    if now != again:
      moved_by = (round(away, 1), now)
      break
  print(f"  -> a later candidate moved it: {moved_by}")
  print("READING: aiming at the nearest vertex ALONE makes the "
        "verdict a fact about which vertex is drawn nearest the "
        "middle; trying every candidate does not.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
