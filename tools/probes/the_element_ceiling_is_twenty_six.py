"""Second route on the ceiling: don't read the combo, BUILD a design at
21 and at 26 and count the elements the table offers."""
from p_boot import rt, fresh
from qgis.core import QgsProject
from weavingspace_qgis.dialog import WeavingSpaceDialog

fresh()
layer = rt.make_region_layer(n=8)
QgsProject.instance().addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(400)
for n in (20, 21, 26):
  i = dlg.n_combo.findText(str(n))
  if i < 0:
    print(f"n={n}: NOT OFFERED"); continue
  dlg.n_combo.setCurrentIndex(i); dlg.n_combo.activated.emit(i)
  rt._tick(600)
  ids = [dlg.table.item(r, 0).text() for r in range(dlg.table.rowCount())]
  print(f"n={n}: family={dlg.family_combo.currentText()!r} "
        f"table rows={len(ids)} ids={''.join(ids)} "
        f"unit tiles={len(dlg._unit.tiles) if dlg._unit is not None else None}")
dlg.close(); fresh()
