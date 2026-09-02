"""Does the seat a test aims at still reach its class when clicked?

`test_several_classes_can_be_moved_together` has failed on one Linux
leg of three CI rounds with the selection left exactly where the plain
click put it -- "a shift-click left the selection at ('vertex', 'A')"
-- while this Mac passes it every time. The repair of 2026-09-01 made
its aimer ask THE VIEW'S OWN HIT TEST before clicking, and the leg
still fails, so the aim and the click are answering differently about
one point.

THIS ASKS BOTH, FOR THE SAME POINT, AT BOTH MOMENTS. For every
candidate seat of the second class it records what `_handle_at` and
`_nearest` say when the seat is CHOSEN, and what they say again at the
instant the click is DELIVERED -- with the click driven through
`QTest` exactly as the test drives it. A disagreement names the cause;
agreement says the fault is somewhere else entirely and that the
aimer is not the thing to repair.

AND IT SWEEPS THE FONT, because that is what the other machine has
more of. `QT_QPA_PLATFORM=offscreen` supplies Sans Serif at 9pt on
every runner and here; a wider font moves the drawn layout, and which
of a class's vertices is reachable is decided by that layout. Setting
the quantity directly is this project's own way of reaching a case
another machine has and this one does not.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QPoint, Qt  # noqa: E402
from qgis.PyQt.QtGui import QFont  # noqa: E402
from qgis.PyQt.QtTest import QTest  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication  # noqa: E402


def candidates(view, label):
  """Every drawn seat of one vertex class, with what the view says.

  Args:
    view: the drawing widget.
    label: the vertex class label wanted.

  Returns:
    A list of (QPoint, handle over it, what `_nearest` names). Every
    on-screen vertex of the class is offered, not only the first, so
    the sweep can say how many of them a click would actually reach.
  """
  topology = view._drawn()
  if topology is None:
    return []
  found = []
  for vertex in topology.points.values():
    if getattr(vertex, "label", None) != label:
      continue
    where = view._to_screen(vertex.point.x, vertex.point.y)
    if not (0 <= where.x() <= view.width()
            and 0 <= where.y() <= view.height()):
      continue
    seat = QPoint(int(round(where.x())), int(round(where.y())))
    target, found_label, _thing = view._nearest(seat)
    found.append((seat, bool(view._handle_at(seat)),
                  (target, found_label)))
  return found


def run_one_font(probe, points, land_a_build=False):
  """Drive the test's own journey at one font size.

  Args:
    probe: the probe kit's handle.
    points: the application font size to set, or None for whatever
      the platform supplies.
    land_a_build: True to let a topology build LAND between the aim
      and the click, which is the other candidate cause and the one a
      slower machine supplies for nothing. `_wait_for_the_topology`
      returns as soon as the panel holds an ANSWER -- an answer left
      over from the previous design is an answer -- and
      `show_topology` clears the chosen thing on its way past, which
      is the mechanism four other tests met a site at a time.

  Returns:
    A dict of what the aim saw, what the click met, and where the
    selection ended -- which is the assertion the runner fails.
  """
  probe.clear()
  was = QApplication.font()
  if points is not None:
    font = QFont(was)
    font.setPointSize(points)
    QApplication.setFont(font)
  try:
    dlg, _layer, _tile_id = probe.dialog()
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show()
    for _ in range(20):
      QApplication.processEvents()
    dlg.n_spin.setValue(4)
    probe.suite._choose_family(dlg, "laves 3.3.4.3.4")
    for _ in range(20):
      QApplication.processEvents()
    if not probe.suite._wait_for_the_topology(dlg):
      return {"note": "no topology was built"}
    panel = dlg.topology_panel
    view = panel.view
    view.grab()
    for _ in range(10):
      QApplication.processEvents()

    from weavingspace_qgis import topology_edits
    groups = topology_edits.classes(panel._topology)
    vertices = groups.get("vertex", "")
    if len(vertices) < 2:
      return {"note": f"only {len(vertices)} vertex class(es)"}
    first, second = vertices[0], vertices[1]

    # THE PLAIN CLICK, aimed the way the test aims it.
    for seat, handled, names in candidates(view, first):
      if not handled and names == ("vertex", first):
        QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, seat)
        break
    for _ in range(15):
      QApplication.processEvents()
    after_first = panel._selection

    # WHAT THE AIM SEES NOW, once the first class is in hand and its
    # handles are drawn on it.
    at_aim = candidates(view, second)
    chosen = None
    for seat, handled, names in at_aim:
      if not handled and names == ("vertex", second):
        chosen = seat
        break

    landed = None
    if land_a_build and chosen is not None:
      # A BUILD LANDS BETWEEN THE AIM AND THE CLICK, staged rather
      # than waited for: the runner has time this machine does not,
      # and measuring how often one lands there would measure the
      # machine.
      dlg._queue_topology(even_if_unasked=True)
      for _ in range(400):
        QApplication.processEvents()
        if not getattr(dlg, "_topology_wanted", False) \
           and getattr(dlg, "_topology_task", None) is None:
          break
      landed = panel._selection

    met = None
    if chosen is not None:
      # AND WHAT THE SAME POINT ANSWERS AT THE INSTANT OF THE CLICK,
      # read from inside the press itself rather than before it, so
      # nothing between the two moments can hide.
      real_press = view.mousePressEvent

      def watched(event):
        """Record what the press finds, then let it run."""
        where = (event.position() if hasattr(event, "position")
                 else event.pos())
        target, label, _thing = view._nearest(where)
        met_here = {
          "handle": bool(view._handle_at(where)),
          "nearest": (target, label),
          "modifiers": str(event.modifiers()),
        }
        met.clear()
        met.update(met_here)
        return real_press(event)

      met = {}
      view.mousePressEvent = watched
      QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.ShiftModifier, chosen)
      for _ in range(15):
        QApplication.processEvents()
      view.mousePressEvent = real_press

    return {
      "classes": f"{first},{second}",
      "after the plain click": after_first,
      "seats of the second class": [
        (h, n) for _s, h, n in at_aim],
      "aimed at": (chosen.x(), chosen.y()) if chosen else None,
      "selection after a build landed": landed,
      "met at the click": met,
      "selection at the end": panel._selection,
    }
  finally:
    QApplication.setFont(was)


def main():
  """Sweep the font and say whether the aim and the click agree.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()
  arms = [(None, False), (13, False),
          (None, True)]   # the third is the staged landing
  for points, land in arms:
    where = "the platform's own" if points is None else f"{points}pt"
    if land:
      where += ", with a build landing between the aim and the click"
    print(f"=== FONT: {where} ===")
    found = run_one_font(probe, points, land_a_build=land)
    for key, value in found.items():
      print(f"    {key}: {value}")
    held = found.get("selection at the end")
    if held and isinstance(held, tuple) and len(held) == 2:
      labels = set(held[1]) if held[1] else set()
      wanted = set(found.get("classes", "").split(","))
      if labels == wanted:
        print("    -> both classes held: the runner's failure is not "
              "reproduced at this font")
      else:
        print(f"    -> ONLY {sorted(labels)} held, which is the "
              f"runner's own failure")
  print("every font reported; teardown next")


if __name__ == "__main__":
  main()
