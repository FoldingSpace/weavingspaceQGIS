"""SECOND ROUTE. Same state, but reached and read differently:
the pins are read back off the LAYER through a saved-and-reopened
project, and off the colour editor's own controls, rather than out of
`dialog._pinned_bounds`."""
import importlib.util, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT); sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ["QGIS_PREFIX_PATH"], True)
app = QgsApplication([], True); app.initQgis(); rt._no_modal_dialogs()

from weavingspace_qgis.category_editor import CategoryColourDialog
from weavingspace_qgis.dialog import WeavingSpaceDialog

work = tempfile.mkdtemp()
gpkg = os.path.join(work, "map.gpkg")
qgz = os.path.join(work, "probe.qgz")

layer = rt.make_region_layer(n=12)
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(300)
dlg.table.cellWidget(0, 1).setCurrentText("v3")
rt._tick(200)
tid = dlg.table.item(0, 0).text()
dlg.table.cellWidget(0, 3).setValue(2)
rt._tick(150)
dlg.spacing_spin.setValue(1200)
rt._generate_and_wait(dlg)
field = dlg._assignment_for(tid).get("var")

mode = dlg.table.cellWidget(0, 2)
i = mode.findText("Quant: Unclassed"); mode.setCurrentIndex(i); mode.activated.emit(i)
rt._tick(500)
opened = {}
real = CategoryColourDialog.exec
CategoryColourDialog.exec = lambda self, *a, **k: (opened.__setitem__("e", self), 0)[1]
try:
  dlg._edit_quant_colours(tid, field, dlg._assignment_for(tid))
finally:
  CategoryColourDialog.exec = real
ed = opened["e"]
lp, lb = [p for p in ed._pin_widgets["low"] if ed.table.isAncestorOf(p[1])][0]
hp, hb = [p for p in ed._pin_widgets["high"] if ed.table.isAncestorOf(p[1])][0]
lb.setValue(10.0); lp.setChecked(True); rt._tick(400)
hb.setValue(60.0); hp.setChecked(True); rt._tick(400)
ed.close(); dlg._open_editor = None; rt._tick(200)
mode = dlg.table.cellWidget(0, 2)
j = mode.findText("Quant: Quantiles"); mode.setCurrentIndex(j); mode.activated.emit(j)
rt._tick(600)
del rt.BAR_MESSAGES[:]
rt._generate_and_wait(dlg); rt._tick(300)

def ladder(d, t):
  """The (lower, upper) pairs an element's layer actually draws.

  Args:
    d: the dialog holding the element.
    t: the element's tile id.

  Returns:
    A list of bound pairs, empty when the renderer carries no ranges.
    Read off the RENDERER rather than the record, because a record
    claiming bounds the ladder lacks is the defect being looked for.
  """
  lyr = QgsProject.instance().mapLayer(d._element_layer_ids.get(t))
  r = lyr.renderer() if lyr is not None else None
  return ([(x.lowerValue(), x.upperValue()) for x in r.ranges()]
          if r is not None and hasattr(r, "ranges") else [])

print("=== IN SESSION ===")
print("map ladder :", ladder(dlg, tid))
print("told       :", [t for _k, t in rt.BAR_MESSAGES])

# --- ROUTE 2a: what the COLOUR EDITOR shows the user
opened.clear()
CategoryColourDialog.exec = lambda self, *a, **k: (opened.__setitem__("e", self), 0)[1]
try:
  dlg._edit_quant_colours(tid, field, dlg._assignment_for(tid))
finally:
  CategoryColourDialog.exec = real
ed2 = opened["e"]
lp2, lb2 = [p for p in ed2._pin_widgets["low"] if ed2.table.isAncestorOf(p[1])][0]
hp2, hb2 = [p for p in ed2._pin_widgets["high"] if ed2.table.isAncestorOf(p[1])][0]
print("editor: low pin down?", lp2.isChecked(), "box", lb2.value(),
      "| high pin down?", hp2.isChecked(), "box", hb2.value())
printed = []
off = 1 if ed2._pin_column else 0
for r in range(ed2.table.rowCount()):
  cells = []
  for c in (off, off + 1):
    w = ed2.table.cellWidget(r, c); it = ed2.table.item(r, c)
    cells.append(("%.6g" % w.value()) if (w is not None and hasattr(w, "value"))
                 else (it.text() if it is not None else None))
  printed.append(tuple(cells))
print("editor prints bounds:", printed)
ed2.close(); dlg._open_editor = None; rt._tick(200)

# --- ROUTE 2b: SAVE AND REOPEN, so the pins are read off the LAYER
QgsProject.instance().write(qgz)
dlg.close(); rt._tick(200)
QgsProject.instance().clear(); rt._tick(200)
QgsProject.instance().read(qgz); rt._tick(400)
dlg2 = WeavingSpaceDialog(iface=rt._Iface())
rt._tick(600)
del rt.BAR_MESSAGES[:]
print()
print("=== AFTER SAVE + REOPEN (pins read off the layer's stamp) ===")
lyr = None
for cand in QgsProject.instance().mapLayers().values():
  if cand.customProperty("weavingspace_tile_id") == tid:
    lyr = cand
print("layer stamp        :", lyr.customProperty("weavingspace_quant_style"))
r = lyr.renderer()
print("layer draws        :", [(x.lowerValue(), x.upperValue()) for x in r.ranges()])
print("reopened dialog record:", dlg2._pinned_bounds.get(tid, {}))
print("told on reopening  :", [t for _k, t in rt.BAR_MESSAGES])
