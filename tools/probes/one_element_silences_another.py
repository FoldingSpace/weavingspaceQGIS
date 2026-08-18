"""Control + independent route for the field-deduped notice.

  control  -- element a has NOTHING empty, so `said` never gains v3.
              If c then speaks, the dedup is the cause and nothing else.
  hand     -- count c's empty classes WITHOUT the plugin's own helper:
              read the renderer's ranges off the layer and walk the
              layer's features, so the number does not come from
              `_classes_nothing_wears` or `bridge.unworn_classes`.
"""
import importlib.util, os, sys

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO); sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
from qgis.core import QgsApplication, QgsProject                   # noqa
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True); _app.initQgis()
from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa

MODE = sys.argv[1] if len(sys.argv) > 1 else "control"

project = QgsProject.instance(); project.clear()
project.addMapLayer(T.make_region_layer(n=12))
dlg = WeavingSpaceDialog(iface=T._Iface())
dlg.live_check.setChecked(False)
dlg.n_combo.setCurrentText("4")
dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
dlg.spacing_spin.setValue(1200)
for row in (0, 2):
  dlg.table.cellWidget(row, 1).setCurrentText("v3")
T._tick(200)
T._generate_and_wait(dlg)
a, c = dlg.table.item(0, 0).text(), dlg.table.item(2, 0).text()

if MODE != "control":
  src = dlg._classification_values("v3")
  vals = sorted(float(v) for v in src.uniqueValues(src.fields().indexOf("v3")))
  dlg._pinned_bounds.setdefault(a, {})["v3"] = {"high": vals[-1] * 1.5}
dlg.table.cellWidget(2, 3).setValue(20)
T._tick(250)
del T.BAR_MESSAGES[:]
dlg._apply_style_change(); T._tick(300)
dlg._generate(); assert T._settle(dlg, seconds=90); T._tick(300)

print("1 a is pinned beyond the data:", MODE != "control")
print("1 said to the user           :",
      [m for _k, m in T.BAR_MESSAGES if "class" in m or "empty" in m])

# ---- counted by hand off the LAYER, not through the plugin's helper
for tid in (a, c):
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  r = out.renderer()
  held = r.ranges() if hasattr(r, "ranges") else []
  spans = [(x.lowerValue(), x.upperValue()) for x in held]
  idx = out.fields().indexOf("v3")
  worn = set()
  for feature in out.getFeatures():
    v = feature.attributes()[idx]
    if v is None:
      continue
    v = float(v)
    for i, (lo, hi) in enumerate(spans):
      if (lo <= v <= hi) if i == 0 else (lo < v <= hi):
        worn.add(i); break
  empty = [i for i in range(len(spans)) if i not in worn]
  print(f"2 {tid}: {len(spans)} classes drawn, "
        f"{out.featureCount()} tiles, EMPTY BY HAND = {empty}")
dlg.close(); QgsProject.instance().clear()
