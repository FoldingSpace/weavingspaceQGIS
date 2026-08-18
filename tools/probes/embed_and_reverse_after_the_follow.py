"""Two things a QGIS-side edit does not carry into the exported file.

Run it with the hunt harness, which supplies QGIS's own Python, the
environment and a frozen copy of the tree:

    python3 tools/hunt_probe.py --prepare --name reverse
    python3 tools/hunt_probe.py --name reverse \
        --run tools/probes/embed_and_reverse_after_the_follow.py

A. A CATEGORIZED element restyled in QGIS in a way that leaves every
   FILL colour alone -- layer opacity, an outline, a legend label --
   reaches the project and never the GeoPackage. `_on_layer_style_
   edited`'s categorized colour guard returns without embedding, where
   its graduated twin in `_graduated_layer_edited` embeds on the way
   out. Pressing Generate does not heal it, because `_restyle_only`
   continues past an element whose row never moved.

B. A graduated row with REVERSE on, handed the FORWARD ramp of the
   same name in QGIS's dock. `_graduated_layer_edited` builds its trial
   renderer without the row's `reverse`, so the forward ramp matches a
   reversed row: the plugin announces that it now follows the ramp
   chosen in QGIS while the Reverse switch stays on, and the next
   unrelated edit redraws the map the other way round.

Both are read back by opening the GeoPackage COLD -- a fresh layer on
the file with `loadDefaultStyle()`, which is what a colleague's QGIS
does -- and, for opacity, out of `layer_styles.styleQML` with sqlite as
well, so neither claim rests on the live session's own objects.
"""
import importlib.util
import os
import re
import shutil
import sqlite3
import sys
import tempfile

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsProject,                 # noqa
                       QgsVectorLayer)
from qgis.PyQt.QtGui import QColor                                 # noqa

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import bridge                               # noqa
from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa


def cold(path, table):
  """What a colleague's QGIS makes of one table in the file.

  Args:
    path: the GeoPackage the run wrote.
    table: the layer name inside it, e.g. "tiles_a".

  Returns:
    (opacity, [class or category fill colours], the stored styleQML).
    The layer is built fresh on the file and never added to the
    project, so nothing here reads the live session's own renderers.
    Lists off QGIS getters are bound before subscripting: a temporary
    frees its contents.
  """
  layer = QgsVectorLayer(f"{path}|layername={table}", table, "ogr")
  layer.loadDefaultStyle()
  renderer = layer.renderer()
  if hasattr(renderer, "ranges"):
    parts = renderer.ranges()
  elif hasattr(renderer, "categories"):
    parts = renderer.categories()
  else:
    parts = []
  colours = [p.symbol().color().name() for p in parts]
  con = sqlite3.connect(path)
  stored = dict(con.execute(
    "select f_table_name, styleQML from layer_styles").fetchall())
  con.close()
  return layer.opacity(), colours, stored.get(table, "")


folder = tempfile.mkdtemp()
try:
  project = QgsProject.instance()
  project.clear()                     # the singleton is shared
  region = T.make_region_layer()
  project.addMapLayer(region)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(region)
  T._tick(200)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles")
  dlg.table.cellWidget(1, 1).setCurrentText("landcover")
  dlg.table.cellWidget(1, 2).setCurrentText("Categorized")
  dlg._update_dynamic_columns()
  T._tick(200)
  grad, cat = dlg.table.item(0, 0).text(), dlg.table.item(1, 0).text()

  # the ramp is chosen the way a CLICK chooses it, then reversed
  combo = dlg.table.cellWidget(0, 4)
  index = combo.findText("Reds")
  assert index >= 0, "no Reds ramp in this profile's style library"
  combo.setCurrentIndex(index)
  combo.activated.emit(index)
  T._tick(200)
  dlg._row_reverse(0).setChecked(True)
  T._tick(200)

  path = os.path.join(folder, "map.gpkg")
  dlg.gpkg_widget.setFilePath(path)
  dlg.spacing_spin.setValue(500)
  T._generate_and_wait(dlg)
  print(f"the plugin drew tiles_{grad} as", cold(path, f"tiles_{grad}")[1])

  # ---- A: opacity, an outline and a label, none of them a fill
  clayer = project.mapLayer(dlg._element_layer_ids[cat])
  fills_before = [c.symbol().color().name()
                  for c in clayer.renderer().categories()]
  renderer = clayer.renderer().clone()
  held = renderer.categories()
  symbol = held[0].symbol().clone()
  symbol.symbolLayer(0).setStrokeColor(QColor("#ff0000"))
  symbol.symbolLayer(0).setStrokeWidth(1.2)
  renderer.updateCategorySymbol(0, symbol)
  renderer.updateCategoryLabel(0, "Forest cover")
  clayer.setRenderer(renderer)
  clayer.setOpacity(0.25)
  clayer.styleChanged.emit()
  T._tick(500)
  fills_after = [c.symbol().color().name()
                 for c in clayer.renderer().categories()]
  assert fills_before == fills_after, \
    "the fixture changed a fill, so the guard under test never runs"

  # ---- B: the forward ramp of the name the row already holds
  glayer = project.mapLayer(dlg._element_layer_ids[grad])
  glayer.setRenderer(bridge.make_graduated_renderer(
    glayer, "v1", "Reds", "Quantiles", 5, False,
    classify_from=dlg._classification_values("v1")))
  glayer.styleChanged.emit()
  T._tick(500)
  row = dlg._row_for_element(grad)
  print("B  QGIS now holds :",
        [r.symbol().color().name()
         for r in project.mapLayer(
           dlg._element_layer_ids[grad]).renderer().ranges()])
  print("B  the row claims :",
        [c for _lo, _hi, c in dlg._current_graduated_classes(
          dlg._assignment_for(grad))])
  print("B  ramp cell", dlg.table.cellWidget(row, 4).currentText(),
        "| Reverse switch", dlg._row_reverse(row).isChecked())

  # ...and a Generate that says nothing about either
  dlg.table.cellWidget(row, 3).setValue(6)
  T._tick(250)
  dlg._generate()
  assert T._settle(dlg, seconds=90), "the second run never settled"
  T._tick(400)

  opacity, _c, qml = cold(path, f"tiles_{cat}")
  print(f"A  FILE tiles_{cat}: opacity {opacity}",
        "| red outline", "255,0,0" in qml,
        "| 'Forest cover'", "Forest cover" in qml,
        "| sqlite layerOpacity",
        re.findall(r"<layerOpacity>([0-9.]+)</layerOpacity>", qml))
  print(f"A  PROJECT tiles_{cat}: opacity",
        project.mapLayer(dlg._element_layer_ids[cat]).opacity())
  print(f"B  FILE tiles_{grad} after that Generate:",
        cold(path, f"tiles_{grad}")[1])
  dlg.close()
finally:
  QgsProject.instance().clear()
  shutil.rmtree(folder, ignore_errors=True)
