"""What every number box in the dialog now shows, before and after.

Printed rather than asserted, because the point is for a person to
look at the list and say whether each reads sensibly -- three
significant figures is a rule about what a reader wants, and no
assertion can tell me that spacing in whole metres is right.
"""
import importlib.util
import os
import sys

REPO = os.environ["WEAVINGSPACE_REPO"]
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject            # noqa: E402
from qgis.PyQt.QtWidgets import QDoubleSpinBox              # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()


def main():
  """Print every number box with its value, step and decimals."""
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  layer = T.make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  T._tick(400)

  named = {}
  for attr in dir(dlg):
    if attr.startswith("__"):
      continue
    try:
      value = getattr(dlg, attr)
    except Exception:
      continue
    if isinstance(value, QDoubleSpinBox):
      named[id(value)] = attr

  print(f"{'control':<26} {'value':>14} {'step':>8} {'dp':>3}  shown")
  worst = []
  for box in dlg.findChildren(QDoubleSpinBox):
    name = named.get(id(box), "(unnamed)")
    shown = box.textFromValue(box.value())
    figures = len(shown.lstrip("-0.").replace(".", "").rstrip())
    print(f"{name:<26} {box.value():>14.6g} {box.singleStep():>8.4g} "
          f"{box.decimals():>3}  {shown!r}")
    if box.decimals() > 3:
      worst.append((name, box.decimals()))
  print(f"\nboxes still showing more than three decimals: "
        f"{worst or 'none'}")
  dlg.close()


main()
