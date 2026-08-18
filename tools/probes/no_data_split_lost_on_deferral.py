"""Deferring an element destroys its No Data layer, and the gaps
come back as holes.

WHAT A USER LOSES. They map a column with gaps, so the plugin splits
the unplaceable tiles onto the element's paired "no data" layer and
draws them grey. They then refine that element in QGIS's Symbology
panel -- picking Standard Deviation, say, which QGIS offers and this
plugin does not name -- and the plugin correctly says the element is
now styled in QGIS. The very next Generate deletes the paired layer
and folds those tiles back onto the element, where a graduated
renderer has no class for them: they are drawn as NOTHING. The areas
that were honestly marked "not known" become holes that read as
"nothing is here", which is the exact harm the No Data layer was
built to remove, and nothing is said about it.

WHY. `_assignments` resolves a deferring element's mode to
"Deferring to QGIS", which is not "Graduated". Two readers ask about
the mode and both then answer as though the column had no gaps:
`_needs_a_no_data_split` (dialog.py:7354), which is in the GEOMETRY
signature -- so beginning to defer moves that signature all by itself
and the next Generate is a full re-tile rather than a restyle -- and
`field_here` at the landing (dialog.py:9578), which is what
`split_out_the_no_data` is given. Deferral is about who chooses the
COLOURS; the split is about which rows a renderer can place at all,
and it is geometry, as the signature comment beside it says.

Present since the split landed in dd112bf (2026-08-15); deferral
(e01896b) was already there.

Two arms on one fixture, each in a cleared project, so the dock edit
is the only difference between them. Run it the way the suite runs:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \\
      | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/no_data_split_lost_on_deferral.py
"""
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.dirname(
  os.path.dirname(os.path.abspath(__file__))))
os.chdir(REPO)
sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsMapRendererParallelJob,  # noqa: E402
                       QgsMapSettings, QgsProject)
from qgis.PyQt.QtCore import QEventLoop, QSize                     # noqa: E402
from qgis.PyQt.QtGui import QColor                                 # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import bridge                      # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog   # noqa: E402

KEY = "#ff00ff"


def region():
  """The stock synthetic region with gaps punched into one column.

  Returns:
    A memory layer where `v1` is NULL on every square whose v1 was 0,
    so an element mapped on v1 gets a paired no-data layer and an
    element mapped on anything else does not.
  """
  layer = T.make_region_layer(n=4, cell=1000)
  layer.startEditing()
  index = layer.fields().indexOf("v1")
  for feature in layer.getFeatures():
    if feature["v1"] == 0.0:
      layer.changeAttributeValue(feature.id(), index, None)
  layer.commitChanges()
  return layer


def unpainted(layers, extent):
  """How many pixels of a fixed view nothing paints.

  Args:
    layers: the output layers, the first drawn on top, as QGIS orders
      them.
    extent: the view, fixed across both arms so the two counts can be
      compared with each other.

  Returns:
    (unpainted pixels, total pixels). Magenta is the chroma key the
    visual suite uses, because no ramp here produces it, so
    "unpainted" is an exact test rather than a near-white guess.
  """
  settings = QgsMapSettings()
  settings.setLayers(layers)
  settings.setBackgroundColor(QColor(KEY))
  settings.setExtent(extent)
  settings.setOutputSize(QSize(700, 700))
  settings.setDestinationCrs(layers[0].crs())
  job = QgsMapRendererParallelJob(settings)
  loop = QEventLoop()
  job.finished.connect(loop.quit)
  job.start()
  loop.exec()
  image = job.renderedImage()
  key = QColor(KEY).rgb()
  found = sum(1 for y in range(image.height())
              for x in range(image.width())
              if image.pixel(x, y) == key)
  return found, image.width() * image.height()


def arm(defer):
  """Tile, optionally style the element in QGIS, tile again, measure.

  Args:
    defer: when True, install a graduated renderer on QGIS's Standard
      Deviation method between the two runs -- an ordinary Symbology
      panel action, and a method this plugin does not offer, so the
      element begins deferring.

  Returns:
    A dict of what the second run left: whether the paired layer
    survives, how many unplaceable rows ended up on the element
    layer, and how many pixels nothing paints.
  """
  project = QgsProject.instance()
  project.removeAllMapLayers()
  source = region()
  project.addMapLayer(source)
  extent = source.extent().buffered(source.extent().width() * 0.02)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(source)
  T._tick(200)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg._update_dynamic_columns()
  T._tick(150)
  tid = dlg.table.item(0, 0).text()
  dlg.spacing_spin.setValue(500)
  T._generate_and_wait(dlg)
  had_twin = bool(dlg._no_data_layer_ids.get(tid))

  if defer:
    from qgis.core import QgsClassificationStandardDeviation
    element = project.mapLayer(dlg._element_layer_ids[tid])
    dock = bridge.make_graduated_renderer(
      element, "v1", "Blues", "Quantiles", 5, False,
      classify_from=dlg._classification_values("v1"))
    dock.setClassificationMethod(QgsClassificationStandardDeviation())
    dock.updateClasses(element, 5)
    element.setRenderer(dock)
    element.styleChanged.emit()
    T._tick(400)
  dlg.live_note.setText("")

  # NOTHING ELSE IS TOUCHED. Just Generate.
  T._generate_and_wait(dlg)
  element = project.mapLayer(dlg._element_layer_ids[tid])
  ids = list(dlg._element_layer_ids.values()) \
      + list(dlg._no_data_layer_ids.values())
  layers = [project.mapLayer(i) for i in ids if project.mapLayer(i)]
  layers.reverse()          # the paired layer sits above its element
  holes, total = unpainted(layers, extent)
  answer = {
    "paired layer after run 1": had_twin,
    "paired layer after run 2": bool(dlg._no_data_layer_ids.get(tid)),
    "row reads": dlg.table.cellWidget(
      dlg._row_for_element(tid), 2).currentText(),
    "element tiles": element.featureCount(),
    "unplaceable rows on the element layer": sum(
      1 for f in element.getFeatures()
      if f["v1"] is None or str(f["v1"]) == "NULL"),
    "renderer": type(element.renderer()).__name__,
    "unpainted pixels": f"{holes} of {total}",
    "what the user was told": dlg.live_note.text() or "(nothing)",
  }
  dlg.close()
  T._tick(100)
  return answer


def main():
  """Print the two arms side by side, and the difference."""
  control = arm(False)
  deferred = arm(True)
  print("\n=== CONTROL: no dock edit ===")
  for key, value in control.items():
    print(f"  {key}: {value}")
  print("\n=== DEFERRED: Standard Deviation set in QGIS ===")
  for key, value in deferred.items():
    print(f"  {key}: {value}")


main()
os._exit(0)
