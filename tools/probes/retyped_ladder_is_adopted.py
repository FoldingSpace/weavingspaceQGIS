"""Prove that a ladder retyped in QGIS reaches the plugin, or does not.

Row 1 of docs/process/defects-2026-08-18.md. The first probe for this
could not settle it: `make_region_layer` gives `v1` four distinct
values against five classes, so the classifier reduces and
`fitted_breaks` collapses back to the same ladder whatever is adopted.
A fixture that cannot move cannot show a fix.

So this builds a CONTINUOUS column shaped like the tester's own -- one
hundred areas spread across 3.1 to 79.1, the range of the
`Percent_White` in the report -- and then retypes the tester's exact
ladder: 0-10, 10-20, 20-30, 30-50, 50-80.

SELF-PROVING, which is the point. It runs the same fixture and the
same actions TWICE: once with the adoption path in place, once with
`_adopt_dock_bounds` patched to a no-op. Nothing else differs between
the arms, so the difference between them is the fix and cannot be
anything else. Reverting code between runs would leave the comparison
resting on my having reverted exactly one thing.
"""
import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import (QgsApplication, QgsFeature, QgsGeometry,  # noqa: E402
                       QgsPointXY, QgsProject, QgsVectorLayer)
from weavingspace_qgis import compat  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

TYPED = [0.0, 10.0, 20.0, 30.0, 50.0, 80.0]


def continuous_region(n=10, cell=1000, low=3.1, high=79.1):
  """A region whose column is continuous enough to reclassify.

  Args:
    n: grid side, so the layer holds n*n areas.
    cell: each square's side, in EPSG:3857 map units.
    low, high: the extremes the column should span, chosen to match
      the reported data rather than invented.

  Returns:
    A memory layer with one float column, ``pct``, holding n*n
    distinct values evenly spread from low to high. Distinct, so no
    reduction to distinct-value count can hide a ladder that failed
    to move.
  """
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "region", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("pct", float)])
  layer.updateFields()
  count = n * n
  feats = []
  for i in range(n):
    for j in range(n):
      k = i * n + j
      f = QgsFeature(layer.fields())
      ring = [QgsPointXY(i * cell, j * cell),
              QgsPointXY((i + 1) * cell, j * cell),
              QgsPointXY((i + 1) * cell, (j + 1) * cell),
              QgsPointXY(i * cell, (j + 1) * cell)]
      f.setGeometry(QgsGeometry.fromPolygonXY([ring]))
      f["pct"] = low + (high - low) * k / (count - 1)
      feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


def arm(label, adopt):
  """Retype the tester's ladder in QGIS and read back what the plugin says.

  Args:
    label: what to print this arm as.
    adopt: when False, `_adopt_dock_bounds` is replaced by a no-op for
      the life of this arm, which is the plugin as rc8 shipped it.

  Returns:
    True when the plugin's ladder matches what QGIS holds, else False.
  """
  saved = WeavingSpaceDialog._adopt_dock_bounds
  if not adopt:
    WeavingSpaceDialog._adopt_dock_bounds = lambda *a, **k: None
  try:
    project = QgsProject.instance()
    project.clear()
    layer = continuous_region()
    project.addMapLayer(layer)
    dlg = WeavingSpaceDialog(iface=rt._Iface())
    dlg.live_check.setChecked(False)
    dlg.layer_combo.setLayer(layer)
    rt._tick(200)
    dlg.table.cellWidget(0, 1).setCurrentText("pct")
    dlg.table.cellWidget(0, 2).setCurrentText("Quant: Equal interval")
    dlg._update_dynamic_columns()
    rt._tick(150)
    tid = dlg.table.item(0, 0).text()
    dlg.spacing_spin.setValue(500)
    rt._generate_and_wait(dlg)
    rt._tick(200)

    element = project.mapLayer(dlg._element_layer_ids[tid])
    assignment = [a for a in dlg._assignments() if a["id"] == tid][0]
    mine = [(round(lo, 2), round(hi, 2))
            for lo, hi, _c in dlg._current_graduated_classes(assignment)]

    # THE TESTER'S OWN EDIT: double-click each range, retype its
    # numbers. QGIS moves the next range's bottom to match, which is
    # what building the ladder from consecutive pairs reproduces.
    renderer = element.renderer().clone()
    if len(renderer.ranges()) != len(TYPED) - 1:
      print(f"  {label}: the element drew {len(renderer.ranges())} "
            f"classes, not {len(TYPED) - 1}; fixture unusable")
      return None
    for index in range(len(TYPED) - 1):
      renderer.updateRangeLowerValue(index, TYPED[index])
      renderer.updateRangeUpperValue(index, TYPED[index + 1])
    element.setRenderer(renderer)
    element.styleChanged.emit()
    element.triggerRepaint()
    rt._tick(400)

    assignment = [a for a in dlg._assignments() if a["id"] == tid][0]
    after = [(round(lo, 2), round(hi, 2))
             for lo, hi, _c in dlg._current_graduated_classes(assignment)]
    wanted = [(TYPED[i], TYPED[i + 1]) for i in range(len(TYPED) - 1)]
    print(f"  {label}")
    print(f"    plugin drew        : {mine}")
    print(f"    retyped in QGIS    : {wanted}")
    print(f"    plugin NOW reports : {after}")
    agrees = after == wanted
    print(f"    FOLLOWS QGIS       : {agrees}")
    dlg.close()
    return agrees
  finally:
    WeavingSpaceDialog._adopt_dock_bounds = saved


def main():
  """Run both arms and say whether the fix is what separates them.

  Returns:
    0 when the pair proves the fix, 1 when it does not.
  """
  app = QgsApplication([], False)
  app.initQgis()
  print("\nA LADDER RETYPED IN QGIS -- does the plugin follow?\n")
  without = arm("WITHOUT the fix (rc8 as shipped)", adopt=False)
  with_fix = arm("WITH the fix", adopt=True)
  print("\nVERDICT")
  if without is False and with_fix is True:
    print("  PROVED. Same fixture, same edit; the only difference is\n"
          "  whether _adopt_dock_bounds runs. Without it the plugin\n"
          "  keeps its own ladder, which is the defect as reported.")
    return 0
  if without is True:
    print("  NOT PROVED: rc8's own code already follows this edit, so\n"
          "  this fixture does not reproduce the report.")
    return 1
  print(f"  NOT PROVED: without={without} with={with_fix}")
  return 1


if __name__ == "__main__":
  sys.exit(main())
