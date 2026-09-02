"""Does dragging the push rail record anything, or only preview it?

A hunt reported on 2026-09-02 that `TopologyPanel._drag_moved` has a
branch for each of `nudge_vertex`, `zigzag_edge`, `rotate_edge` and
`scale_edge` and none for `push_vertex`, so `_commit_the_drag` returns
before `_record` and the gesture is thrown away -- while
`_on_dragging` has a whole push branch that draws the preview. The
push rail was added on 2026-08-31 with the handles that make every
manipulation reachable on the drawing; `_drag_moved` was written the
day before, when a vertex carried one handle.

THIS TAKES A DIFFERENT ROUTE FROM THE HUNT'S. It drives the widget's
own mouse events with QTest rather than calling the panel's handlers,
and it reads the GROUND the map would be drawn from as well as the
record -- so a disagreement is about what a person meets rather than
about one store.

TWO ARMS, one process, on `archimedean 4.8.8`: the push handle, and
the nudge handle beside it as the control. The design matters and is
asserted: on `laves 3.3.4.3.4` the incident unit vectors cancel, the
push has nowhere to go, and no rail is drawn at all -- so that design
would report a clean answer about a control it does not offer.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtCore import QPoint, Qt  # noqa: E402
from qgis.PyQt.QtTest import QTest  # noqa: E402
from qgis.PyQt.QtWidgets import QApplication  # noqa: E402


def tick(ms):
  """Pump the event loop for roughly ms milliseconds.

  Args:
    ms: how long to pump, in milliseconds.

  Returns:
    None.
  """
  import time
  end = time.monotonic() + ms / 1000.0
  while time.monotonic() < end:
    QApplication.processEvents()
    time.sleep(0.005)


def settle_the_tab(dlg, seconds=90.0):
  """Wait until no topology build is outstanding.

  Args:
    dlg: the dialog whose tab to settle.
    seconds: a hang-catcher rather than a budget.

  Returns:
    True where the tab went quiet. Waiting on an ANSWER instead would
    return while the previous design's topology was still in hand,
    which is a fault this project has now met at five sites.
  """
  import time
  deadline = time.monotonic() + seconds
  while time.monotonic() < deadline:
    building = getattr(dlg, "_topology_task", None) is not None
    queued = bool(getattr(dlg, "_topology_wanted", False))
    panel = getattr(dlg, "topology_panel", None)
    holds = panel is not None and panel._topology is not None
    if holds and not building and not queued:
      return True
    tick(200)
  return False


def unit_area(unit):
  """The ground a unit's own tiles cover.

  Args:
    unit: a Tileable, or None.

  Returns:
    The total area of its tiles, or None. Area rather than a vertex
    list deliberately: the library re-grids what it hands back and
    restarts every ring, so a coordinate comparison reports a change
    that nobody can see.
  """
  if unit is None:
    return None
  return float(sum(unit.tiles.geometry.area))


def drag_one_handle(dlg, panel, view, wanted):
  """Click a vertex, drag the named handle, and say what happened.

  Args:
    dlg: the dialog, for settling.
    panel: the topology panel.
    view: its drawing.
    wanted: the manipulation whose handle to drag.

  Returns:
    A dict carrying the premise readings and what the gesture left
    behind: whether a preview was drawn, how many edits the record
    holds afterwards, and the unit's own area before and after.
  """
  view.resize(600, 600)
  tick(100)
  # PAINT IT, OR IT HAS NO TRANSFORM: `_fit` runs inside `paintEvent`,
  # so a widget nothing has exposed reports unit coordinates as pixels.
  view.grab()
  tick(50)

  topology = view._drawn()
  middle = (view.width() / 2, view.height() / 2)
  seat = None
  for vertex in topology.points.values():
    point = view._to_screen(vertex.point.x, vertex.point.y)
    if not (0 <= point.x() <= view.width()
            and 0 <= point.y() <= view.height()):
      continue
    away = ((point.x() - middle[0]) ** 2
            + (point.y() - middle[1]) ** 2) ** 0.5
    if seat is None or away < seat[0]:
      seat = (away, QPoint(int(round(point.x())), int(round(point.y()))))
  if seat is None:
    return {"premise": "no vertex is drawn inside the widget"}

  assert settle_the_tab(dlg), "PREMISE: the tab never went quiet"
  QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                   Qt.KeyboardModifier.NoModifier, seat[1])
  tick(150)

  handles = view.handles()
  grab_at = None
  for handle in handles:
    key, point = handle[0], handle[1]
    if key == wanted:
      grab_at = QPoint(int(round(point.x())), int(round(point.y())))
      break
  if grab_at is None:
    return {"premise": f"this design offers no {wanted} handle "
                       f"(it offers {[h[0] for h in handles]})"}

  before = unit_area(getattr(dlg, "_unit", None))
  edits_before = len(panel._edits)

  # AIMED AT THE PARAMETER IT MOVES, radially and tangentially at once
  # about the thing's own seat: a scale reads the handle's DISTANCE
  # from the middle and a rotation its ANGLE, so a drag across one of
  # them asks for nothing and is discarded correctly.
  span = (grab_at.x() - seat[1].x(), grab_at.y() - seat[1].y())
  length = (span[0] ** 2 + span[1] ** 2) ** 0.5
  if length < 1.0:
    out, along = (1.0, 0.0), (0.0, 1.0)
  else:
    out = (span[0] / length, span[1] / length)
    along = (-out[1], out[0])
  travel = QPoint(int(round(60 * out[0] + 60 * along[0])),
                  int(round(60 * out[1] + 60 * along[1])))
  QTest.mousePress(view, Qt.MouseButton.LeftButton,
                   Qt.KeyboardModifier.NoModifier, grab_at)
  tick(50)
  QTest.mouseMove(view, grab_at + travel)
  tick(200)
  previewed = getattr(view, "_preview", None) is not None
  asked_for = dict(panel._drag_from or {})
  QTest.mouseRelease(view, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier,
                     grab_at + travel)
  tick(300)
  settle_the_tab(dlg)
  tick(200)

  return {
    "premise": None,
    "previewed_during_the_drag": previewed,
    "asked_for": asked_for,
    "edits_before": edits_before,
    "edits_after": len(panel._edits),
    "area_before": before,
    "area_after": unit_area(getattr(dlg, "_unit", None)),
  }


def main():
  """Drive both arms and say whether a push drag is kept.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.opt_experimental.setChecked(True)
  dlg.live_check.setChecked(False)
  dlg.show()
  tick(200)
  dlg.n_spin.setValue(2)
  tick(200)
  probe.suite._choose_family(dlg, "archimedean 4.8.8")
  tick(300)
  assert settle_the_tab(dlg), "PREMISE: no topology was ever built"
  panel = dlg.topology_panel
  view = panel.view

  for wanted in ("push_vertex", "nudge_vertex", "scale_edge",
                 "rotate_edge", "zigzag_edge"):
    panel._edits.clear()
    panel._refresh_list()
    tick(50)
    found = drag_one_handle(dlg, panel, view, wanted)
    print(f"=== dragging the {wanted} handle ===")
    if found.get("premise"):
      print(f"    PREMISE UNMET: {found['premise']}")
      continue
    print(f"    preview drawn during the drag  "
          f"{found['previewed_during_the_drag']}")
    print(f"    what the gesture asked for     {found['asked_for']}")
    print(f"    edits recorded                 "
          f"{found['edits_before']} -> {found['edits_after']}")
    print(f"    the unit's own area            "
          f"{found['area_before']} -> {found['area_after']}")
    kept = found["edits_after"] > found["edits_before"]
    print(f"    THE GESTURE WAS {'KEPT' if kept else 'THROWN AWAY'}")

  probe.clear()
  print("both arms reported; teardown next")


if __name__ == "__main__":
  main()
