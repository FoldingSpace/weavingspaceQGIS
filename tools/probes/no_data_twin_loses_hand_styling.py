"""H7/H9: a deferring element's NO-DATA layer, hand-styled in QGIS.

The landing path carries the paired layer's renderer through
`kept_by_hand`, which is TRUE while an element is deferring
(dialog.py:10111, 10171). `_restyle_no_data_layer` (7797) has no such
gate and calls setRenderer unconditionally (7826), and `_restyle_only`
calls it for a deferring element (8258) even though the arm just above
deliberately leaves that element's OWN renderer alone.

  landing  -- change the SPACING (a re-tile)
  restyle  -- move the element's OPACITY spinner, which CLAUDE.md
              names as the one control that stays live while deferring
"""
import importlib.util, os, sys

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO); sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
from qgis.core import (QgsApplication, QgsProject, QgsFillSymbol,     # noqa
                       QgsSingleSymbolRenderer, QgsRuleBasedRenderer,
                       QgsRenderContext)
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True); _app.initQgis()
from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa

WHICH = sys.argv[1] if len(sys.argv) > 1 else "restyle"

project = QgsProject.instance(); project.clear()
layer = T.make_region_layer(n=12)
index = layer.fields().indexOf("v1")
layer.startEditing()
for offset, feature in enumerate(layer.getFeatures()):
  if offset % 3 == 0:
    layer.changeAttributeValue(feature.id(), index, None)
assert layer.commitChanges()
project.addMapLayer(layer)

dlg = WeavingSpaceDialog(iface=T._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(layer); T._tick(200)
dlg.table.cellWidget(0, 1).setCurrentText("v1")
dlg.table.cellWidget(0, 2).setCurrentText("Quant: Quantiles"); T._tick(150)
tid = dlg.table.item(0, 0).text()
dlg.spacing_spin.setValue(1200)
T._generate_and_wait(dlg)

el = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
el.setRenderer(QgsRuleBasedRenderer(QgsRuleBasedRenderer.Rule(None)))
el.styleChanged.emit(); T._tick(400)
T._generate_and_wait(dlg)
print("0 row says                   :", dlg.table.cellWidget(0, 2).currentText())
twin_id = dlg._no_data_layer_ids.get(tid)
assert twin_id, "no paired layer, so the case cannot arise"
twin = QgsProject.instance().mapLayer(twin_id)

# the user styles the NO DATA layer by hand in QGIS
twin.setRenderer(QgsSingleSymbolRenderer(
  QgsFillSymbol.createSimple({"color": "#123456"})))
twin.styleChanged.emit(); T._tick(300)


def twin_now():
  """What the element's paired No Data layer is wearing right now.

  Returns:
    (renderer class name, its fill colours, its opacity), or a
    sentence when the paired layer has gone. Read fresh each time
    because the layer object is replaced by a re-tile and kept by a
    restyle, which is the difference this probe measures.
  """
  lyr = QgsProject.instance().mapLayer(dlg._no_data_layer_ids.get(tid, ""))
  if lyr is None:
    return "the paired layer is gone"
  r = lyr.renderer()
  ctx = QgsRenderContext()
  syms = r.symbols(ctx) if hasattr(r, "symbols") else []
  names = [s.color().name() for s in syms]
  return (type(r).__name__, names[:3], round(lyr.opacity(), 2))


print("1 hand-styled twin           :", twin_now())
if WHICH == "landing":
  dlg.spacing_spin.setValue(1150); T._tick(250)
  before = dict(dlg._element_layer_ids)
  T._generate_and_wait(dlg)
  print("2 re-tiled                   :", before != dlg._element_layer_ids)
else:
  spin = dlg.table.cellWidget(0, 6)
  print("2 opacity cell enabled       :", spin is not None and spin.isEnabled())
  spin.setValue(40); T._tick(250)
  before = dict(dlg._element_layer_ids)
  dlg._generate(); assert T._settle(dlg, seconds=90); T._tick(300)
  print("2 restyled (ids unmoved)     :", before == dlg._element_layer_ids)
print("3 twin AFTER                 :", twin_now())
dlg.close(); QgsProject.instance().clear()
