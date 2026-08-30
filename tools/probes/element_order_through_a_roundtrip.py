"""Do y, z, aa, ab read in that order in the dock and after a resume?

Three orders and they are three different questions. The DOCK is the
group's child order, which the plugin controls on both paths. The FILE
lists its tables in whatever order OGR reports, which nobody controls.
And the RESUMED dock is what the plugin makes of the file's order,
which is where a table name like `tiles_aa_v1` sorting before
`tiles_b_v1` would show.
"""
import importlib.util
import os
import sys
import tempfile

REPO = os.environ.get("WS_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)
_spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject          # noqa: E402
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()

from weavingspace_qgis.dialog import WeavingSpaceDialog   # noqa: E402


def dock_order(dlg, project):
  """The layer NAMES in the order the layers panel shows them.

  Args:
    dlg: the dialog whose output group is wanted; its own layers are
      what identifies that group, since a name is never a key here.
    project: the QgsProject holding it.

  Returns:
    A list of layer names in panel order, empty when this dialog has
    no group in the project.
  """
  group = dlg._group_of_our_layers(project.layerTreeRoot())
  if group is None:
    return []
  out = []
  for child in group.children():
    layer = child.layer() if hasattr(child, "layer") else None
    if layer is not None:
      out.append(layer.name())
  return out


def around_the_seam(names):
  """The entries either side of where the alphabet runs out.

  Args:
    names: layer names, each beginning with its element's id.

  Returns:
    Only the entries for x, y, z, aa, ab and ac, which is where a
    plain string sort would put the twenty-seventh element in the
    wrong place and everywhere else looks identical either way.
  """
  return [n for n in names
          if n.split(" ")[0] in ("x", "y", "z", "aa", "ab", "ac")]


project = QgsProject.instance()
project.clear()
folder = tempfile.mkdtemp(prefix="ws_order_")
out = os.path.join(folder, "thirty.gpkg")
region = T.make_region_layer(n=4, cell=1000)
region.setName("wards")
project.addMapLayer(region)

dlg = WeavingSpaceDialog(iface=T._Iface())
dlg.live_check.setChecked(False)
dlg.layer_combo.setLayer(region)
T._tick(400)
where = 30 if dlg.n_spin.maximum() >= 30 else -1
dlg.n_spin.setValue(where)
T._tick(600)
dlg.gpkg_widget.setFilePath(out)
dlg.spacing_spin.setValue(700)
T._generate_and_wait(dlg)
T._tick(400)
T._settle(dlg, seconds=180)

made = dock_order(dlg, project)
print("  dock, generated:", around_the_seam(made))
print("  table rows:     ",
      [dlg.table.item(r, 0).text() for r in range(dlg.table.rowCount())][23:29])
dlg.close()

from osgeo import ogr                                     # noqa: E402
data = ogr.Open(out, 0)
tables = [data.GetLayer(i).GetName() for i in range(data.GetLayerCount())]
data = None
seam = [t for t in tables if t.startswith(("tiles_x", "tiles_y", "tiles_z",
                                           "tiles_aa", "tiles_ab"))]
print("  file, as OGR lists it:", seam)
print("  file, sorted as text: ", sorted(seam))

project.clear()
T._tick(400)
fresh = WeavingSpaceDialog(iface=T._Iface())
fresh.live_check.setChecked(False)
T._tick(300)
ok = fresh._resume_from_gpkg(out)
T._tick(800)
T._settle(fresh, seconds=180)
print("  resumed?", ok)
print("  dock, resumed:  ", around_the_seam(dock_order(fresh, project)))
fresh.close()
project.clear()
os._exit(0)
