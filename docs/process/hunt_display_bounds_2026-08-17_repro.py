"""Smallest reproduction: the Ramp Display Range eats a typed digit.

    python3 tools/hunt_probe.py --name display-bounds --prepare
    python3 tools/hunt_probe.py --name display-bounds --run \
        "$PWD/docs/process/hunt_display_bounds_2026-08-17_repro.py"

The absolute path matters: the harness runs the probe inside a frozen
copy of HEAD, and an untracked file is not in it.
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

from qgis.core import QgsApplication                            # noqa: E402
from qgis.PyQt.QtTest import QTest                              # noqa: E402
from qgis.PyQt.QtCore import Qt                                 # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()

from weavingspace_qgis.category_editor import CategoryColourDialog  # noqa

bounds = [(0.0, 10.0), (10.0, 20.0), (20.0, 30.0), (30.0, 40.0)]
order = [str(i) for i in range(len(bounds))]
sent = []
editor = CategoryColourDialog(
  "a", "v3", order, {k: "#cccccc" for k in order}, lambda *a: None,
  bounds=bounds, range_bounds=(0, 100), ramp_name="Reds",
  range_changed=lambda lo, hi: sent.append((lo, hi)) or [])

for box, text in ((editor.upper_spin, "40"),      # look at the bottom
                  (editor.lower_spin, "60"),      # then ask for the top
                  (editor.upper_spin, "100")):
  box.setFocus()
  box.selectAll()
  QTest.keyClick(box, Qt.Key.Key_Delete)
  QTest.keyClicks(box, text)
  QTest.keyClick(box, Qt.Key.Key_Return)
  T._tick(80)

print("asked for (60, 100); the dialog was told", sent[-1])
assert sent[-1] == (60, 100), sent
editor.close()
