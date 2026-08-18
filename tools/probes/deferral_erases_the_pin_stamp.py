"""Controls for H5, and a second route to the same fact.

  CONTROL   an element that is NOT deferring keeps its stamp across the
            identical restyle and round trip.
  ROUTE 2   read the .qgz as BYTES with zipfile -- no QGIS, no dialog.
  PATH      does the run-landing path (`_add_output_layers`) destroy it
            too, or only `_restyle_only`?

Pass "control", "bytes" or "landing".
"""
import importlib.util, json, os, sys, zipfile

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO); sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
from qgis.core import QgsApplication, QgsProject                   # noqa
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True); _app.initQgis()
from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa

WHICH = sys.argv[1] if len(sys.argv) > 1 else "control"


def stamp(dlg, tid):
  """The whole quant-style record written onto an element's layer.

  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    The parsed `weavingspace_quant_style` property -- pinned bounds
    and hand-picked class colours together -- or None when the
    property is absent, which is the state this probe is about.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  raw = out.customProperty("weavingspace_quant_style")
  return json.loads(raw) if raw else None


def in_the_file(path):
  """Every quant-style property inside the saved .qgz, read as bytes."""
  with zipfile.ZipFile(path) as archive:
    name = [n for n in archive.namelist() if n.endswith(".qgs")][0]
    text = archive.read(name).decode("utf-8", "replace")
  return [p.split("value=")[1][:60] for p in text.split("<")
          if "weavingspace_quant_style" in p and "value=" in p]


project = QgsProject.instance(); project.clear()
project.addMapLayer(T.make_region_layer(n=12))
dlg = WeavingSpaceDialog(iface=T._Iface())
dlg.live_check.setChecked(False)
dlg.n_combo.setCurrentText("4")
dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
dlg.spacing_spin.setValue(1200)
dlg.table.cellWidget(0, 1).setCurrentText("v3")
dlg.table.cellWidget(1, 1).setCurrentText("v3")
T._tick(200)
T._generate_and_wait(dlg)
a, b = dlg.table.item(0, 0).text(), dlg.table.item(1, 0).text()

src = dlg._classification_values("v3")
values = sorted(float(v) for v in src.uniqueValues(src.fields().indexOf("v3")))
low, high = values[1], values[-2]
# BOTH elements pinned, so one of them is always the control
for tid in (a, b):
  dlg._pinned_bounds.setdefault(tid, {})["v3"] = {"low": low, "high": high}
  dlg._quant_colours.setdefault(tid, {})["v3"] = {"0": "#ff00ff"}
dlg._apply_style_change(); T._tick(400)
print("0 stamp a / b :", bool(stamp(dlg, a)), "/", bool(stamp(dlg, b)))

if WHICH != "control":
  el = QgsProject.instance().mapLayer(dlg._element_layer_ids[a])
  el.setRenderer(T._rule_based_renderer("#00aa44"))
  el.styleChanged.emit(); T._tick(400)
  print("1 a deferring :", dlg.table.cellWidget(0, 2).currentText())

if WHICH == "landing":
  # a GEOMETRY change: the full run path, not the restyle
  dlg.spacing_spin.setValue(1150); T._tick(250)
  before = dict(dlg._element_layer_ids)
  T._generate_and_wait(dlg)
  print("2 re-tiled (new layer ids)   :", before != dlg._element_layer_ids)
else:
  kb = dlg.table.cellWidget(dlg._row_for_element(b), 3)
  kb.setValue(7); T._tick(250)
  before = dict(dlg._element_layer_ids)
  dlg._generate(); assert T._settle(dlg, seconds=90); T._tick(300)
  print("2 restyled (same layer ids)  :", before == dlg._element_layer_ids)

print("2 stamp a / b :", bool(stamp(dlg, a)), "/", bool(stamp(dlg, b)))

with T._temp_dir() as folder:
  path = os.path.join(folder, "p.qgz")
  assert QgsProject.instance().write(path), "would not save"
  print("2 BYTES in the .qgz          :", in_the_file(path))
  T._project_round_trip(folder, "p2.qgz")
  again = WeavingSpaceDialog(iface=T._Iface())
  again.live_check.setChecked(False)
  keep = [l for l in QgsProject.instance().mapLayers().values()
          if not l.customProperty("weavingspace_output")]
  again.layer_combo.setLayer(keep[0]); T._tick(600)
  print("3 REOPENED pin a             :", again._pinned_bounds.get(a, {}).get("v3"))
  print("3 REOPENED pin b (control)   :", again._pinned_bounds.get(b, {}).get("v3"))
  print("3 REOPENED picks a           :", again._quant_colours.get(a, {}).get("v3"))
  print("3 REOPENED picks b (control) :", again._quant_colours.get(b, {}).get("v3"))
  again.close()
dlg.close(); QgsProject.instance().clear()
