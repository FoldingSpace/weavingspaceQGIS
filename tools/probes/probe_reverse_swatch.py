"""THE HARM. A graduated element with Reverse on. Press Generate, and
the row's ramp cell goes back to drawing the ramp FORWARD while the
switch stays on and the map stays reversed -- so the swatch a user
picks their next ramp by is the mirror image of what they will get.

`_refresh_ramp_icons` (dialog.py) has ONE caller, the Reverse toggle;
`_make_ramp_combo` draws every item with `_ramp_icon(name)`, forward.
Every Generate re-emits layerChanged, which rebuilds the table.

    python3 tools/hunt_probe.py --prepare --name reverse-flag
    python3 tools/hunt_probe.py --name reverse-flag --run <this file>
"""
import importlib.util
import os
import sys

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject                   # noqa
from qgis.PyQt.QtGui import QColor                                 # noqa

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import dialog as D                          # noqa


def ends(icon):
  """The swatch's two extreme stripes, which is what says direction."""
  image = icon.pixmap(D.RAMP_SWATCH).toImage()
  step = D.RAMP_SWATCH.width() / D.SWATCH_STRIPES
  mid = D.RAMP_SWATCH.height() // 2
  return (QColor(image.pixel(2, mid)).name(),
          QColor(image.pixel(int(7 * step) + 2, mid)).name())


project = QgsProject.instance()
project.clear()                    # RULE 4: nothing has run first
dlg, layer, tid = T._quant_dialog(k=5, ramp="Reds", row=1)
dlg._row_reverse(1).setChecked(True)
T._tick(300)
T._generate_and_wait(dlg)
T._tick(400)

combo = dlg.table.cellWidget(1, 4)
assert not combo.showing_custom() and combo._pinned_icon is None, \
  "the cell is showing a Custom/pinned swatch, so the item icon " \
  "below is not what the closed combo paints"
low, high = ends(combo.itemIcon(combo.findText("Reds")))
out = project.mapLayer(dlg._element_layer_ids[tid])
bound = out.renderer().ranges()
drawn = [r.symbol().color().name() for r in bound]

print(f"Reverse switch:  {dlg._row_reverse(1).isChecked()}")
print(f"ramp cell says:  lowest class {low} -> highest class {high}")
print(f"the map draws:   lowest class {drawn[0]} -> highest {drawn[-1]}")
print(f"CONTRADICTION:   {low != drawn[0]}")

# ...and the dropdown a user picks their NEXT ramp from
print()
for name in ("Blues", "Greens"):
  index = combo.findText(name)
  print(f"popup item {name:<7} shows {ends(combo.itemIcon(index))}")
combo.setCurrentText("Blues")
T._tick(300)
T._generate_and_wait(dlg)          # the restyle fast path repaints it
T._tick(400)
after = project.mapLayer(dlg._element_layer_ids[tid]).renderer().ranges()
print(f"picking Blues draws {[r.symbol().color().name() for r in after]}"
      f"  (the mirror of the picture it was picked by)")
dlg.close()
project.clear()
os._exit(0)
