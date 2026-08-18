"""Does an opacity set on a DEFERRING element survive a re-tile?

The restyle fast path (dialog.py:8151) sets a deferring element's
opacity from the dialog, saying so at 8132 ("the one control that
stays live while deferring"). The run-landing path (dialog.py:10019)
folds `carried_while_deferring` into `kept_by_hand` and then takes
the OLD LAYER'S opacity instead. Two paths, one rule, one of them.
"""
import importlib.util
import os
import sys

# The repository root, which is two levels up now this probe lives
# under tools/probes/ rather than in a hunt's own worktree. Taken from
# the environment first so it can be pointed at a frozen copy.
ROOT = os.environ.get("WEAVINGSPACE_REPO") or os.path.dirname(
  os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import QgsApplication, QgsProject  # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._no_modal_dialogs()
QgsProject.instance().clear()
rt.BAR_MESSAGES.clear()

from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

project = QgsProject.instance()
layer = rt.make_region_layer(n=12)
project.addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(200)
tile_id = dlg.table.item(1, 0).text()
dlg.spacing_spin.setValue(1200)
rt._generate_and_wait(dlg)

element = project.mapLayer(dlg._element_layer_ids[tile_id])
element.setRenderer(rt._rule_based_renderer("#00aa44"))
element.styleChanged.emit()
rt._tick(400)
print("row style now:", dlg.table.cellWidget(1, 2).currentText())

# the first Generate after deferral goes down the RESTYLE path and
# records the moved signature; anything after it is "unchanged"
rt._generate_and_wait(dlg)
rt._tick(200)

# now the user fades the element in the plugin's own table
spin = dlg._row_opacity(1)
spin.setValue(30)
rt._tick(300)
print("table says:", spin.value(), "%")
print("assignment says:", next(a["opacity"] for a in dlg._assignments()
                               if a["id"] == tile_id))
prev = dlg._table_id_colours()[tile_id]
print("preview colour:", prev, "alpha", int(str(prev)[1:3], 16))

# ROUTE 1 -- the restyle path (no geometry change)
rt._generate_and_wait(dlg)
rt._tick(200)
after_restyle = project.mapLayer(dlg._element_layer_ids[tile_id])
print("RESTYLE  layer opacity:", after_restyle.opacity(),
      "renderer:", type(after_restyle.renderer()).__name__)

# put it back to solid through the same control, then re-tile
spin = dlg._row_opacity(1)
spin.setValue(100)
rt._tick(300)
rt._generate_and_wait(dlg)
rt._tick(200)
print("reset  layer opacity:", project.mapLayer(
  dlg._element_layer_ids[tile_id]).opacity())

# ROUTE 2 -- fade, then a GEOMETRY change, so the run lands
spin = dlg._row_opacity(1)
spin.setValue(30)
rt._tick(300)
dlg.spacing_spin.setValue(1100)
rt._tick(300)
rt._generate_and_wait(dlg)
rt._tick(300)
landed = project.mapLayer(dlg._element_layer_ids[tile_id])
print("LANDING  layer opacity:", landed.opacity(),
      "renderer:", type(landed.renderer()).__name__)
print("table still says:", dlg._row_opacity(1).value(), "%")
prev = dlg._table_id_colours()[tile_id]
print("preview colour:", prev, "alpha", int(str(prev)[1:3], 16))

# a control for the same journey on a NON-deferring element
other = dlg.table.item(0, 0).text()
dlg._row_opacity(0).setValue(30)
rt._tick(300)
dlg.spacing_spin.setValue(1050)
rt._tick(300)
rt._generate_and_wait(dlg)
rt._tick(300)
print("CONTROL (not deferring) layer opacity:",
      project.mapLayer(dlg._element_layer_ids[other]).opacity())
print("bar:", [m for m in rt.BAR_MESSAGES][-4:])
dlg.close()
