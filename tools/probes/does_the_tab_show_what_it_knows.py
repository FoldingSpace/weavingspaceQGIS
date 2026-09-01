"""Are the ghost, the gap marks and the change-list annotations real?

Three things were added on 2026-08-31 and nothing had looked at any of
them. Each is a claim the drawing makes, so each is asked of the widget
rather than of the code that sets it.
"""
import importlib.util, os
ROOT = os.getcwd()
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
from qgis.core import QgsApplication, QgsProject
QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True); _app.initQgis(); rt._no_modal_dialogs()
from weavingspace_qgis.dialog import WeavingSpaceDialog

QgsProject.instance().clear()
QgsProject.instance().addMapLayer(rt.make_region_layer())
with rt._temp_dir():
  dlg = WeavingSpaceDialog(iface=rt._Iface())
  try:
    dlg.opt_experimental.setChecked(True)
    dlg.live_check.setChecked(False)
    dlg.show(); rt._tick(200)
    dlg.n_spin.setValue(4); rt._tick(200)
    dlg.family_combo.setCurrentText("laves 3.3.4.3.4"); rt._tick(300)
    assert rt._wait_for_the_topology(dlg), "PREMISE: no topology"
    panel, view = dlg.topology_panel, dlg.topology_panel.view

    def look(when):
      print(f"  {when}")
      print(f"    ghost held      : {view._ghost is not None}")
      print(f"    gaps held       : {view._gaps is not None}")
      print(f"    marks           : {panel._marks}")
      print(f"    change list     : "
            f"{[panel.edit_list.item(i).text() for i in range(panel.edit_list.count())]}")

    look("before any edit")

    # A GENTLE EDIT, which should leave the tiles meeting.
    panel._record({"classes": "A", "how": "nudge_vertex",
                   "args": {"dx": 0.02, "dy": 0.02}})
    rt._settle_topology(dlg, seconds=40); rt._settle(dlg); rt._tick(200)
    look("after a small nudge")

    # AND ONE THAT OPENS GAPS: a rotation does, routinely.
    panel._record({"classes": "a", "how": "rotate_edge",
                   "args": {"angle": 15.0}})
    rt._settle_topology(dlg, seconds=40); rt._settle(dlg); rt._tick(200)
    look("after a rotate that opens gaps")
  finally:
    dlg.close(); dlg.deleteLater(); rt._tick(50)
