"""Render the tab's drawing with an edge and a vertex selected.

The maintainer's test is whether the handles are PERCEIVABLE and read
as what they do. That is a visual question, so this drives the product
and writes the pixels out to be looked at rather than asserted about.
"""
import importlib.util, os, sys
ROOT = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True); _app.initQgis(); rt._no_modal_dialogs()
from qgis.PyQt.QtCore import Qt, QPoint
from qgis.PyQt.QtTest import QTest
from weavingspace_qgis.dialog import WeavingSpaceDialog

OUT = sys.argv[1]
QgsProject.instance().clear()
QgsProject.instance().addMapLayer(rt.make_region_layer())
with rt._temp_dir():
  dlg = WeavingSpaceDialog(iface=rt._Iface())
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show(); rt._tick(200)
    dlg.n_spin.setValue(2); rt._tick(200)
    dlg.family_combo.setCurrentText("archimedean 4.8.8"); rt._tick(300)
    assert rt._wait_for_the_topology(dlg), "PREMISE: no topology"
    view = dlg.topology_panel.view
    view.resize(760, 700); rt._tick(80); view.grab(); rt._tick(50)

    def point_on(kind):
      topo = view._drawn()
      mid = (view.width() / 2, view.height() / 2)
      best = at = None
      if kind == "vertex":
        for v in topo.points.values():
          p = view._to_screen(v.point.x, v.point.y)
          if not (0 <= p.x() <= view.width() and 0 <= p.y() <= view.height()):
            continue
          d = ((p.x()-mid[0])**2 + (p.y()-mid[1])**2) ** 0.5
          if best is None or d < best:
            best, at = d, QPoint(int(p.x()), int(p.y()))
        return at
      vs = [view._to_screen(v.point.x, v.point.y) for v in topo.points.values()]
      for e in topo.edges.values():
        try: cs = list(e.get_geometry().coords)
        except Exception: continue
        for (ax, ay), (bx, by) in zip(cs, cs[1:]):
          for i in range(1, 10):
            t = i / 10.0
            p = view._to_screen(ax + (bx-ax)*t, ay + (by-ay)*t)
            if not (0 <= p.x() <= view.width() and 0 <= p.y() <= view.height()):
              continue
            clear = min(((p.x()-v.x())**2 + (p.y()-v.y())**2) ** 0.5 for v in vs)
            if clear <= 10: continue
            d = ((p.x()-mid[0])**2 + (p.y()-mid[1])**2) ** 0.5
            if best is None or d < best:
              best, at = d, QPoint(int(p.x()), int(p.y()))
      return at

    for kind, name in (("vertex", "vertex"), ("edge", "edge")):
      at = point_on(kind)
      assert at is not None, f"PREMISE: found no {kind} to click"
      QTest.mouseClick(view, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.NoModifier, at)
      rt._tick(200)
      held = dlg.topology_panel.class_combo.currentData()
      pix = view.grab()
      path = os.path.join(OUT, f"handles-488-{name}.png")
      pix.save(path)
      print(f"  {name}: holding {held}, {len(view.handles())} handle(s) -> {path}")
  finally:
    dlg.close(); dlg.deleteLater(); rt._tick(50)
