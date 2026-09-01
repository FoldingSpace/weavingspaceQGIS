"""Does each way of editing the topology actually DO anything?

The maintainer's instruction of 2026-08-31: "a bunch of your edit UI
click and move and whatever don't even seem to move anything even when
you're doing them though visually on the left ... check each of the
interaction modalities to make sure they *work*".

So this drives them, one at a time, through the widget's own mouse
events rather than by calling handlers -- a control must act through
its OWN signal, which is this project's standing rule and the reason a
test that calls `_rebuild_unit()` itself proves nothing.

WHAT EACH ROW ASKS, and the three answers are deliberately separate
because this project's characteristic defect is one fact in two stores
disagreeing:

    chose     did the SELECTION move (what the panel thinks is held)
    drawn     did the DRAWING's own unit change (what you look at)
    design    did the EDITED unit change (what the map is built from)

A row that changes the design and not the drawing is the reported
fault. A row that changes nothing at all is a dead control.

IT IS RUN BEFORE ANY REPAIR, deliberately: the red list is the work
list, and a modality that is already dead needs to be named before
somebody "fixes" it by changing what it draws.

    cd <checkout> && PYTHONUNBUFFERED=1 QT_QPA_PLATFORM=offscreen \\
      "$QGIS_PY" does_every_topology_interaction_work.py
"""

import importlib.util
import os

ROOT = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject            # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
rt._no_modal_dialogs()

from qgis.PyQt.QtCore import Qt, QPoint                     # noqa: E402
from qgis.PyQt.QtTest import QTest                          # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog     # noqa: E402


def ground(unit):
  """Area and perimeter of a unit's tiles, or None."""
  if unit is None or getattr(unit, "tiles", None) is None:
    return None
  tiles = unit.tiles
  return (round(float(tiles.geometry.area.sum()), 4),
          round(float(tiles.geometry.length.sum()), 4))


def state(dlg):
  """The four stores this is about, read together.

  `preview` is the view's own transient -- what a drag paints instead
  of the held topology. The first draft of this probe left it out and
  duly reported "NOTHING MOVED" during every drag, which is a claim
  about the instrument rather than about the tab: the preview does not
  live in `panel._unit`. A harness whose failures are mostly its own
  is one nobody acts on.
  """
  panel = dlg.topology_panel
  view = panel.view
  preview = getattr(view, "_preview", None)
  return {
    "chose": (panel.class_combo.currentText(),
              panel.how_combo.currentText()),
    "preview": None if preview is None else id(preview),
    "drawn": ground(getattr(panel, "_unit", None)),
    "design": ground(getattr(dlg, "_unit", None)),
    "edits": len(panel.edits() or []),
  }


def report(name, before, after):
  """Say what moved, for one modality.

  Args:
    name: the modality being reported.
    before: the state before the act.
    after: the state after it.

  Returns:
    The list of keys that changed, and prints the same. A row that
    moves the design and not the drawing is the reported fault; a row
    that moves nothing at all is a dead control.
  """
  moved = [key for key in ("chose", "preview", "drawn", "design", "edits")
           if before[key] != after[key]]
  verdict = ", ".join(moved) if moved else "NOTHING MOVED"
  print(f"  {name:<34} {verdict}")
  return moved


def a_point_on(view, thing_kind):
  """A widget point sitting on a vertex, or on the middle of an edge.

  Args:
    view: the drawing widget.
    thing_kind: "vertex" or "edge".

  Returns:
    A QPoint over the thing NEAREST THE MIDDLE OF THE WIDGET, or None.

  WHY THE MIDDLE AND NOT THE FIRST. The topology holds the whole patch
  -- 72 points for a four-tile unit -- while the view's own bounds come
  from the core tiles, so `points.values()[0]` is very often drawn off
  the edge of the widget and a click there lands on nothing. The first
  run of this probe reported "click a vertex: NOTHING MOVED" for
  exactly that reason, which is the fixture-that-cannot-reach-its-own
  -case trap wearing a coordinate.

  Everything is resolved through the view's OWN `_to_screen` and the
  same accessors its hit test uses, so the probe cannot disagree with
  the widget about where anything is.
  """
  topology = view._drawn() if hasattr(view, "_drawn") else view._topology
  if topology is None:
    return None
  middle = (view.width() / 2, view.height() / 2)
  best, at = None, None

  def consider(x, y):
    point = view._to_screen(x, y)
    if not (0 <= point.x() <= view.width() and 0 <= point.y() <= view.height()):
      return None, None
    away = ((point.x() - middle[0]) ** 2 + (point.y() - middle[1]) ** 2) ** 0.5
    return away, QPoint(int(round(point.x())), int(round(point.y())))

  if thing_kind == "vertex":
    for vertex in topology.points.values():
      away, candidate = consider(vertex.point.x, vertex.point.y)
      if candidate is not None and (best is None or away < best):
        best, at = away, candidate
    return at
  # AN EDGE POINT MUST BE CLEAR OF EVERY VERTEX. A vertex wins ties
  # inside eight pixels, and on this design the edges run 31-43px on
  # screen, so a midpoint can sit inside a vertex's radius -- which is
  # how the first run of this probe held a VERTEX while reporting that
  # the edge verbs were not offered. The point taken is the one on the
  # edge furthest from any vertex, and its clearance is returned so the
  # caller can refuse a point nothing could aim at.
  vertices = [view._to_screen(v.point.x, v.point.y)
              for v in topology.points.values()]
  for edge in topology.edges.values():
    try:
      coords = list(edge.get_geometry().coords)
    except Exception:                                   # noqa: BLE001
      continue
    if len(coords) < 2:
      continue
    # SAMPLE ALONG THE SEGMENTS. A straight edge's coords are its two
    # endpoints and an endpoint IS a vertex, so taking coords alone
    # leaves every candidate at clearance zero and rejects every edge
    # -- the same fault as the clickability probe's, made twice.
    along = []
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
      for i in range(1, 10):
        t = i / 10.0
        along.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    for x, y in along:
      away, candidate = consider(x, y)
      if candidate is None:
        continue
      clear = min(((candidate.x() - v.x()) ** 2 +
                   (candidate.y() - v.y()) ** 2) ** 0.5
                  for v in vertices) if vertices else 99.0
      if clear <= 8.0:
        continue
      if best is None or away < best:
        best, at = away, candidate
  return at


def main():
  """Drive every modality once and print what each moved."""
  QgsProject.instance().clear()
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
        print("PREMISE FAILED: no topology built")
        return
      panel = dlg.topology_panel
      view = panel.view
      view.resize(600, 600)
      rt._tick(100)
      # PAINT IT, OR IT HAS NO TRANSFORM. `_fit` runs inside
      # `paintEvent`, so offscreen -- where nothing ever exposes a
      # widget -- `_bounds` stays at its default (0,0,1,1) and
      # `_scale` at 1.0. Every coordinate this probe computes then
      # means widget pixels, and a drag reports raw pixel deltas as
      # though they were fractions of the unit: measured here as an
      # edit recording dx=12.0 for a twelve-pixel drag. `grab()`
      # forces the paint and with it the transform.
      view.grab()
      rt._tick(50)

      print(f"\ntopology: {len(view._topology.points)} points, "
            f"{len(view._topology.edges)} edges; "
            f"view {view.width()}x{view.height()}")
      print("\n--- selection ---")

      for kind in ("vertex", "edge"):
        at = a_point_on(view, kind)
        if at is None:
          print(f"  click a {kind:<28} NO SUCH THING IN THE TOPOLOGY")
          continue
        before = state(dlg)
        QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, at)
        rt._tick(150)
        report(f"click a {kind}", before, state(dlg))

      print("\n--- dragging ---")
      for kind in ("vertex", "edge"):
        at = a_point_on(view, kind)
        if at is None:
          continue
        # Select it first, so a drag is aimed at something.
        QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, at)
        rt._tick(150)
        # AN EDGE IS DRAGGED BY A HANDLE, NOT BY ITSELF. `_handle_at`
        # is asked first and a press anywhere else is a selection, so
        # pressing on the edge's own line reports "nothing moved" about
        # a gesture the tab never claimed to offer. The handles are
        # where the thing actually moves -- the end that swings, the
        # end that stretches, the middle that bows out.
        if kind == "edge":
          spots = view.handles()
          if not spots:
            print("  drag an edge: NO HANDLES for the current selection")
            continue
          _key, where, _shape = spots[0]
          at = QPoint(int(round(where.x())), int(round(where.y())))
        before = state(dlg)
        # A NOTE LEFT FROM AN EARLIER STEP IS NOT THIS STEP'S ANSWER.
        # `report` only writes when a replay produces something, so a
        # stale sentence sits there and reads as a verdict about the
        # gesture just made -- which cost one wrong reading already.
        panel.note.setText("")
        # A MODEST DRAG. Since the vertex arguments became fractions of
        # the unit, 60px on a 600px view is a tenth of the design, and
        # laves 3.3.4.3.4 genuinely cannot be laid out after a move
        # that size -- the plugin says so and suggests a smaller value.
        # What is under test here is whether a drag works at all.
        far = QPoint(at.x() + 12, at.y() - 9)
        QTest.mousePress(view, Qt.MouseButton.LeftButton,
                         Qt.KeyboardModifier.NoModifier, at)
        rt._tick(30)
        # A move event has to be delivered while the button is held;
        # QTest.mouseMove posts it to the widget under the pointer.
        QTest.mouseMove(view, far)
        rt._tick(30)
        during = state(dlg)
        QTest.mouseRelease(view, Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier, far)
        rt._settle_topology(dlg, seconds=30)
        rt._settle(dlg)
        report(f"drag a {kind} (during)", before, during)
        report(f"drag a {kind} (after)", before, state(dlg))
        said = panel.note.text().strip()
        if said:
          print(f"      the plugin said: {said[:130]}")
        made = (panel.edits() or [])
        if made:
          print(f"      the drag recorded: {made[-1]}")

      print("\n--- the numeric path ---")
      for how in ("nudge_vertex", "push_vertex", "rotate_edge",
                  "scale_edge", "zigzag_edge"):
        # SELECT THE KIND THE VERB IS ABOUT, FIRST. The tab narrows the
        # verb list to what suits the selection -- select, then act --
        # so asking for `rotate_edge` while a vertex is held is asking
        # for something the panel is right not to offer, and reporting
        # that as "not offered" measures the probe's own last drag.
        wanted = "vertex" if "vertex" in how else "edge"
        at = a_point_on(view, wanted)
        if at is not None:
          QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier, at)
          rt._tick(150)
        # ASSERT THE PREMISE: that a thing of the right KIND is held.
        # A vertex wins ties inside its eight-pixel radius, and an
        # edge's midpoint can easily be within eight pixels of one --
        # so "the verb is not offered" may be a claim about what this
        # probe managed to select rather than about the chooser.
        held = panel.class_combo.currentData()
        kind = (held or ("", ""))[0]
        index = panel.how_combo.findData(how)
        if index < 0:
          offered = [panel.how_combo.itemData(i)
                     for i in range(panel.how_combo.count())]
          print(f"  {how:<34} not offered; holding a {kind or 'nothing'}"
                f", chooser has {offered}")
          continue
        panel.how_combo.setCurrentIndex(index)
        rt._tick(100)
        before = state(dlg)
        panel.apply_button.click()
        rt._settle_topology(dlg, seconds=30)
        rt._settle(dlg)
        report(f"Apply {how}", before, state(dlg))
        said = panel.note.text().strip()
        if said:
          print(f"      the plugin said: {said[:130]}")

      print("\n--- undo and clear ---")
      before = state(dlg)
      panel.undo_button.click()
      rt._settle_topology(dlg, seconds=30)
      rt._settle(dlg)
      report("Undo", before, state(dlg))
      before = state(dlg)
      panel.clear_button.click()
      rt._settle_topology(dlg, seconds=30)
      rt._settle(dlg)
      report("Clear", before, state(dlg))
    finally:
      dlg.close()
      dlg.deleteLater()
      rt._tick(50)


main()
