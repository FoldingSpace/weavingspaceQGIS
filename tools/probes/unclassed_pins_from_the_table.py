"""(a) USER-GUIDE:141-142 -- "The map repaints at once, without
    re-tiling" when a colour is clicked in the editor.
(b) second, independent route onto the Unclassed finding: the RECORD
    and the two controls' identities, not just the renderer."""
from p_boot import rt, fresh
from qgis.core import QgsProject
from weavingspace_qgis.category_editor import CategoryColourDialog
from weavingspace_qgis.dialog import WeavingSpaceDialog
from weavingspace_qgis import bridge

def cat_colours(dlg, tid):
  """Each category value mapped to the colour the map paints it.

  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    {value: "#rrggbb"} read off the layer's own categorized renderer,
    or None when the element is not categorized.
  """
  L = QgsProject.instance().mapLayer(dlg._element_layer_ids.get(tid) or "")
  r = L.renderer() if L else None
  if not hasattr(r, "categories"): return None
  cs = r.categories()
  return {str(cs[i].value()): cs[i].symbol().color().name()
          for i in range(len(cs))}

fresh()
layer = rt.make_region_layer(n=8)
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(400)
dlg.table.cellWidget(0, 1).setCurrentText("landcover")
rt._tick(400)
tid = dlg.table.item(0, 0).text()
rt._generate_and_wait(dlg); rt._tick(200)
print("(a) before:", cat_colours(dlg, tid))
tiles_before = QgsProject.instance().mapLayer(
  dlg._element_layer_ids[tid]).featureCount()
opened = {}
def catch(self, *a, **k):
  """Stand in for the editor's modal exec so the probe can drive it.

  Args:
    *a: whatever exec was called with; unused.
    **k: likewise.

  Returns:
    0, the rejected code, so nothing blocks.

  Bound in place of `CategoryColourDialog.exec`, so it is handed the
  window itself as the receiver and keeps it in `opened` for the probe
  to drive directly. A real modal exec would stop a headless run,
  which is the whole reason this stands in for it.
  """
  opened["e"] = self; return 0
real = CategoryColourDialog.exec
CategoryColourDialog.exec = catch
try:
  dlg.table.cellWidget(0, 8).click()
finally:
  CategoryColourDialog.exec = real
e = opened["e"]
e._on_change("forest", "#123456")   # what a colour click ends in
rt._tick(300)
after = cat_colours(dlg, tid)
tiles_after = QgsProject.instance().mapLayer(
  dlg._element_layer_ids[tid]).featureCount()
print("(a) after :", after)
print("(a) repainted at once:", after.get("forest") == "#123456",
      "| re-tiled:", tiles_before != tiles_after,
      f"({tiles_before} -> {tiles_after})")
dlg.close(); fresh()

# (b) Unclassed, second route
layer = rt.make_region_layer(n=8)
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(400)
m = dlg.table.cellWidget(0, 2); i = m.findText("Quant: Unclassed")
m.setCurrentIndex(i); m.activated.emit(i); rt._tick(400)
tid = dlg.table.item(0, 0).text()
field = dlg._assignment_for(tid).get("var")
rt._generate_and_wait(dlg); rt._tick(200)
opened.clear()
CategoryColourDialog.exec = catch
try:
  dlg._edit_quant_colours(tid, field, dlg._assignment_for(tid))
finally:
  CategoryColourDialog.exec = real
e = opened["e"]
in_table = [p for p in e._pin_widgets["low"] if e.table.isAncestorOf(p[1])]
in_strip = [p for p in e._pin_widgets["low"] if not e.table.isAncestorOf(p[1])]
print("(b) rows:", e.table.rowCount(), "locked flag:", e._locked)
print("(b) low-end controls: table", len(in_table), "strip", len(in_strip),
      "distinct objects:", in_table[0][1] is not in_strip[0][1])
print("(b) record before:", dlg._pinned_bounds.get(tid, {}).get(field))
pin, box = in_table[0]
box.setValue(2.25); box.editingFinished.emit(); rt._tick(400)
print("(b) record after typing into the TABLE's box:",
      dlg._pinned_bounds.get(tid, {}).get(field))
print("(b) table pin down:", pin.isChecked(),
      "| strip pin followed:", in_strip[0][0].isChecked(),
      "| strip box now:", in_strip[0][1].value())
L = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
rr = L.renderer().ranges()
print("(b) layer's first range:", (rr[0].lowerValue(), rr[0].upperValue()))
print("(b) stamped on the layer:",
      L.customProperty("weavingspace_pinned_bounds"))
dlg.close(); fresh()
