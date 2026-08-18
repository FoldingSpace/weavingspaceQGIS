"""A mirrored design, halved by TYPING, comes back un-mirrored.

    python3 tools/hunt_probe.py --prepare --name clampmates
    python3 tools/hunt_probe.py --name clampmates --run \
        docs/process/hunt_clampmates_2026-08-17_repro.py

Drives the keyboard the way a user does -- `_skip_zero_scale` fires on
`valueChanged`, and the scale boxes keep Qt's default keyboardTracking,
so the handler treats the LEADING ZERO of "-0.5" as a landing on zero
and rewrites the box under the user's fingers. The answer is read off
the tile unit's own geometry, not off the spin box, so the two routes
are independent.

Confirmed at 7482c9e. Introduced by 20ae7fe (2026-08-15), the commit
that allowed negative scales and so put zero inside the range.
"""
import importlib.util
import os
import sys

REPO = os.getcwd()
sys.path.insert(0, REPO)
spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject           # noqa: E402
from qgis.PyQt.QtCore import Qt                            # noqa: E402
from qgis.PyQt.QtTest import QTest                         # noqa: E402

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()
T._no_modal_dialogs()


def keyed(box, target):
  """Type `target` over a selected-all spin box, with real key events."""
  box.setFocus()
  box.selectAll()
  QTest.keyClicks(box, target)
  QTest.keyClick(box, Qt.Key.Key_Return)
  return box.value()


def main():
  from weavingspace_qgis.dialog import WeavingSpaceDialog
  project = QgsProject.instance()
  assert not project.mapLayers(), "the project is not clean"
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.spacing_spin.setValue(1000)
  names = [dlg.family_combo.itemText(i)
           for i in range(dlg.family_combo.count())]
  dlg.family_combo.setCurrentText(
    next(n for n in names if "hex" in n and "slice" in n))
  T._tick(250)

  def elements():
    unit = dlg._build_unit()
    return {str(t): round(g.centroid.x, 1)
            for t, g in zip(unit.tiles.tile_id, unit.tiles.geometry)}

  base = elements()
  print(f"unscaled           centroid x: {base}")
  value = keyed(dlg.mod_scale_x, "-1")          # the user mirrors it
  T._tick(150)
  mirrored = elements()
  print(f"typed '-1'   box={value!r:<8} centroid x: {mirrored}")
  value = keyed(dlg.mod_scale_x, "-0.5")        # ...and halves it too
  T._tick(150)
  halved = elements()
  print(f"typed '-0.5' box={value!r:<8} centroid x: {halved}")

  tid = next(t for t in base if abs(base[t]) > 1)
  print(f"\nelement {tid!r}: unscaled {base[tid]}, mirrored "
        f"{mirrored[tid]}, after typing -0.5 {halved[tid]}")
  if (halved[tid] > 0) == (base[tid] > 0):
    print("  RESULT: the mirror is GONE and the box says 0.502, "
          "not -0.5. Every element is on the wrong side of the map.")
  else:
    print("  RESULT: the mirror survived; this has been fixed.")
  dlg.close()


main()
