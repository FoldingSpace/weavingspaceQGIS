"""Second route: measure the PIXELS, never ask layer.opacity().

Clean project, a different geometry change (tile inset, not spacing),
a different opacity (25), and the answer read off a render rather
than off the layer object.
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

from qgis.core import (QgsApplication, QgsProject, QgsMapSettings,  # noqa: E402
                       QgsMapRendererParallelJob)
from qgis.PyQt.QtCore import QSize, QEventLoop  # noqa: E402
from qgis.PyQt.QtGui import QColor  # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
app = QgsApplication([], True)
app.initQgis()
rt._no_modal_dialogs()
QgsProject.instance().clear()          # CLEAN project, nothing ran first
rt.BAR_MESSAGES.clear()

from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402


def fill_counts(layer, size=400):
  """Render one layer on WHITE and tally the colours it paints.

  Args:
    layer: the element layer to render on its own.
    size: the square render in pixels; 400 is enough to separate a
      faded fill from a solid one without costing a second.

  Returns:
    Counter of "#rrggbb" -> pixels. Rendering over WHITE is what makes
    opacity readable without knowing any colour: a 30% fill blends
    toward the background and a full-strength one does not.
  """
  settings = QgsMapSettings()
  settings.setLayers([layer])
  settings.setBackgroundColor(QColor(255, 255, 255))
  settings.setExtent(layer.extent().buffered(layer.extent().width() * 0.02))
  settings.setOutputSize(QSize(size, size))
  settings.setDestinationCrs(layer.crs())
  job = QgsMapRendererParallelJob(settings)
  loop = QEventLoop()
  job.finished.connect(loop.quit)
  job.start()
  loop.exec()
  image = job.renderedImage()
  tally = {}
  for y in range(0, size, 3):
    for x in range(0, size, 3):
      rgb = QColor(image.pixel(x, y)).getRgb()[:3]
      tally[rgb] = tally.get(rgb, 0) + 1
  return sorted(tally.items(), key=lambda kv: -kv[1])[:4]


project = QgsProject.instance()
layer = rt.make_region_layer(n=10, cell=800)
project.addMapLayer(layer)
dlg = WeavingSpaceDialog(iface=rt._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer)
rt._tick(200)
tid = dlg.table.item(2, 0).text()
dlg.spacing_spin.setValue(900)
rt._generate_and_wait(dlg)

element = project.mapLayer(dlg._element_layer_ids[tid])
element.setRenderer(rt._rule_based_renderer("#00aa44"))
element.styleChanged.emit()
rt._tick(400)
rt._generate_and_wait(dlg)             # the restyle that records the mode
rt._tick(200)
print("row says:", dlg.table.cellWidget(2, 2).currentText())
print("solid render:", fill_counts(project.mapLayer(
  dlg._element_layer_ids[tid])))

# fade it in the plugin's own table -- the control is ENABLED while
# deferring (RENDERER_COLUMNS omits column 6), so this is offered
spin = dlg._row_opacity(2)
print("opacity control enabled while deferring:", spin.isEnabled())
spin.setValue(25)
rt._tick(300)

# a DIFFERENT geometry change from the first probe: a tile inset
dlg.mod_t_inset.setValue(4)
rt._tick(400)
rt._generate_and_wait(dlg)
rt._tick(300)
after = project.mapLayer(dlg._element_layer_ids[tid])
print("table says:", dlg._row_opacity(2).value(), "%")
print("expected at 25%: (191, 234, 208)  solid: (0, 170, 68)")
print("landed render:", fill_counts(after))

# and the same fade on a NEIGHBOUR the plugin still styles, as control
other = dlg.table.item(3, 0).text()
dlg._row_opacity(3).setValue(25)
rt._tick(300)
dlg.mod_t_inset.setValue(5)
rt._tick(400)
rt._generate_and_wait(dlg)
rt._tick(300)
print("control element render:",
      fill_counts(project.mapLayer(dlg._element_layer_ids[other])))
print("deferring element render after 2nd re-tile:",
      fill_counts(project.mapLayer(dlg._element_layer_ids[tid])))
dlg.close()
