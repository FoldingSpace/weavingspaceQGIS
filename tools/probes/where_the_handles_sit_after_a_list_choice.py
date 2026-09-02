"""Do the drawing's handles follow a class chosen from the list?

`_chosen_thing` has ONE writer, in `mousePressEvent`. The panel's
`_selection` is the owner every other reader asks -- Apply, the drag
preview and the drop -- but the HANDLES are built from
`_chosen_thing`, so choosing a class in the combo or the tick list
leaves them where the last click put them.

  CLICKED   click edge a, read the handles.
  CHOSEN    then choose edge b from the combo, and read them again.

If the handles do not move, a person grabs a handle sitting on one
edge while the edit is recorded against another -- and the drag's
parameter is a polar coordinate about THAT edge's middle.
"""
import sys
import probe_kit
sys.path.insert(0, probe_kit._repo_root())
from probe_kit import start  # noqa: E402
from qgis.PyQt.QtCore import QPoint  # noqa: E402
from qgis.PyQt.QtCore import Qt as QtNamespace  # noqa: E402
from qgis.PyQt.QtTest import QTest  # noqa: E402

probe = start()
s = probe.suite
dlg, _layer, _tid = probe.dialog()
try:
  dlg.opt_experimental.setChecked(True)
  dlg.show(); s._tick(200)
  s._choose_family(dlg, "laves 3.3.4.3.4"); s._tick(300)
  assert s._the_topology_tab_is_quiet(dlg), "PREMISE: no topology built"
  s._tick(300)
  panel, view = dlg.topology_panel, dlg.topology_panel.view
  view.grab(); s._tick(50)

  # ---- CLICK AN EDGE, whichever the product agrees is reachable.
  topology = view._drawn()
  middle = (view.width() / 2, view.height() / 2)
  seats = []
  for edge in topology.edges.values():
    ends = [topology.points[edge.vertices[0]],
            topology.points[edge.vertices[-1]]]
    pts = [view._to_screen(e.point.x, e.point.y) for e in ends]
    mid = ((pts[0].x() + pts[1].x()) / 2, (pts[0].y() + pts[1].y()) / 2)
    if not (0 <= mid[0] <= view.width() and 0 <= mid[1] <= view.height()):
      continue
    away = ((mid[0] - middle[0]) ** 2 + (mid[1] - middle[1]) ** 2) ** 0.5
    seats.append((away, QPoint(int(mid[0]), int(mid[1]))))
  seats.sort(key=lambda pair: pair[0])
  clicked = None
  for _away, point in seats:
    QTest.mouseClick(view, QtNamespace.MouseButton.LeftButton,
                     QtNamespace.KeyboardModifier.NoModifier, point)
    s._tick(150)
    if view.handles() and panel._selection[0] == "edge":
      clicked = point
      break
  assert clicked is not None, "PREMISE: no edge click offered a handle"
  first_selection = panel._selection
  first_handles = [(h[0], round(h[1].x()), round(h[1].y()))
                   for h in view.handles()]
  print(f"  clicked : selection={first_selection} handles={first_handles}")

  # ---- NOW CHOOSE A DIFFERENT CLASS FROM THE COMBO.
  wanted = None
  for i in range(panel.class_combo.count()):
    text = panel.class_combo.itemText(i)
    if text.startswith("edge") and text != f"edge {first_selection[1][0]}":
      panel.class_combo.setCurrentIndex(i)
      panel.class_combo.activated.emit(i)
      s._tick(250)
      wanted = text
      break
  assert wanted, "PREMISE: the chooser offers no second edge class"
  second_selection = panel._selection
  second_handles = [(h[0], round(h[1].x()), round(h[1].y()))
                    for h in view.handles()]
  print(f"  chose {wanted!r}: selection={second_selection} "
        f"handles={second_handles}")
  print()
  print(f"  the selection moved : {first_selection != second_selection}")
  print(f"  the handles moved   : {first_handles != second_handles}")
finally:
  dlg.close()
print("REPORTED, teardown complete.")
