"""An INVENTORY of what QGIS's symbology panel can do to an element.

The promise is "edit the symbology in QGIS and the plugin follows".
The guard that existed tested ONE change -- a pasted renderer with a
different field, class count AND ramp at once -- and passed, while a
tester retyping a single boundary found nothing followed. One big
change is not coverage of many small ones: a route that only ever
moves three things together can never show which of the three is
carrying the adoption.

So this walks the atomic edits a person can actually make and reports
EVERY failure rather than stopping at the first, because "some things
do not work" is not actionable and "these four routes do not work" is.

Each route says what it CHANGES and what should then FOLLOW, and the
two are deliberately different questions: a class count that follows
while its colours do not is a different defect from neither
following, and a single boolean cannot tell them apart.
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

from qgis.core import QgsApplication, QgsProject  # noqa: E402
from qgis.PyQt.QtGui import QColor  # noqa: E402
from weavingspace_qgis import bridge  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

from qgis.core import (QgsFeature, QgsGeometry, QgsPointXY,  # noqa: E402
                       QgsVectorLayer)
from weavingspace_qgis import compat  # noqa: E402


def region_from(values):
  """A square region whose one column holds exactly these values.

  Args:
    values: one value per area, None meaning a gap. The grid side is
      the ceiling of the square root, so the layer is always roughly
      square and the tiling has somewhere to go.

  Returns:
    A memory layer with a single float column, ``pct``.
  """
  import math
  n = int(math.ceil(math.sqrt(len(values))))
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "region", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("pct", float)])
  layer.updateFields()
  cell = 1000
  feats = []
  for k, value in enumerate(values):
    i, j = divmod(k, n)
    f = QgsFeature(layer.fields())
    ring = [QgsPointXY(i * cell, j * cell),
            QgsPointXY((i + 1) * cell, j * cell),
            QgsPointXY((i + 1) * cell, (j + 1) * cell),
            QgsPointXY(i * cell, (j + 1) * cell)]
    f.setGeometry(QgsGeometry.fromPolygonXY([ring]))
    if value is not None:
      f["pct"] = float(value)
    feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


# ---- THE SHAPES. Every one of these has broken this plugin before,
# which is why they are here rather than a spread of pretty numbers.
# A smooth column is the case that always worked.
def _even():
  return [3.1 + (79.1 - 3.1) * k / 99 for k in range(100)]


def _tied():
  # four values, each worn by twenty-five areas: quantiles and equal
  # intervals disagree hard, and k must reduce
  return [v for v in (10.0, 20.0, 30.0, 40.0) for _ in range(25)]


def _skewed():
  # most areas tiny, a few enormous: equal interval puts almost
  # everything in the first class
  return [1.0 + (k ** 3) / 400.0 for k in range(100)]


def _bimodal():
  # an empty band in the middle, so some class wears nothing
  return [2.0 + k / 25.0 for k in range(50)] + \
         [70.0 + k / 25.0 for k in range(50)]


def _with_gaps():
  # a quarter of the areas hold no value at all
  return [None if k % 4 == 0 else 3.1 + k * 0.75 for k in range(100)]


def _constant():
  # every area identical: k collapses to one, historically a crash
  return [7.0] * 100


def _two_values():
  # two distinct values against five classes: reduction territory
  return [5.0 if k % 2 else 95.0 for k in range(100)]


def _negatives():
  return [-40.0 + k * 0.8 for k in range(100)]


def _hairline():
  # values differing in the sixth decimal: precision and formatting
  return [1.0 + k * 1e-6 for k in range(100)]


def _huge():
  return [1.0e9 + k * 1.0e6 for k in range(100)]


DATASETS = [
  ("even", _even), ("tied", _tied), ("skewed", _skewed),
  ("bimodal", _bimodal), ("gaps", _with_gaps), ("constant", _constant),
  ("two values", _two_values), ("negatives", _negatives),
  ("hairline", _hairline), ("huge", _huge),
]


def _interior(classes):
  """The boundaries between classes, which is what a retype moves."""
  return [round(hi, 2) for _lo, hi, _c in classes[:-1]]


def _colours(classes):
  """Each class's colour, lowercased for comparison."""
  return [c.lower() for _lo, _hi, c in classes]


# ---- the routes. Each mutates a CLONE and says what must follow.
def retype_one(renderer):
  """Double-click one range and retype its top; QGIS moves the next."""
  # BOUND FIRST, every time: ranges() hands back a temporary whose
  # contents are freed, and subscripting one segfaults. This probe
  # crashed on exactly that before the binding was added, which is
  # the hazard bridge.py and dialog.py both carry warnings about.
  ranges = renderer.ranges()
  if len(ranges) < 2:
    return None
  # ROUNDED TO THE SAME PLACES THE READER USES. At 3 here against 2
  # in _interior, skewed and bimodal reported NOT FOLLOWED for
  # 88.374 against 88.37 -- the probe disagreeing with itself and
  # calling it a defect, which is the first way a hunt wastes a day.
  mid = round((ranges[0].upperValue() + ranges[1].upperValue()) / 2, 2)
  renderer.updateRangeUpperValue(0, mid)
  renderer.updateRangeLowerValue(1, mid)
  after = renderer.ranges()
  return ("interior", [mid] + [round(r.upperValue(), 2)
                               for r in after[1:-1]])


def retype_all(renderer):
  """Retype every boundary into a round ladder, as a tester would."""
  typed = [0.0, 10.0, 20.0, 30.0, 50.0, 80.0]
  ranges = renderer.ranges()
  if len(ranges) != len(typed) - 1:
    return None
  for i in range(len(typed) - 1):
    renderer.updateRangeLowerValue(i, typed[i])
    renderer.updateRangeUpperValue(i, typed[i + 1])
  return ("interior", typed[1:-1])


def recolour_one(renderer):
  """Change a single class's colour, leaving every boundary alone."""
  ranges = renderer.ranges()
  if len(ranges) < 2:
    return None
  symbol = ranges[1].symbol().clone()
  symbol.setColor(QColor("#123456"))
  renderer.updateRangeSymbol(1, symbol)
  return ("colour_at_1", "#123456")


def delete_a_class(renderer):
  """Remove a class, which is what the minus button does."""
  ranges = renderer.ranges()
  before = len(ranges)
  # GUARDED, because QGIS does not guard it: deleteClass(1) on a
  # one-class renderer SEGFAULTS rather than raising, which killed
  # this probe outright on the constant column. A constant column
  # draws exactly one class by design.
  if before < 2:
    return None
  renderer.deleteClass(1)
  return ("count", before - 1)


def relabel(renderer):
  """Retype a legend label, changing no number and no colour."""
  if not renderer.ranges():
    return None
  renderer.updateRangeLabel(0, "the lowest sort")
  return ("label_at_0", "the lowest sort")


ROUTES = [
  ("retype one boundary", retype_one),
  ("retype the whole ladder", retype_all),
  ("recolour one class", recolour_one),
  ("delete a class", delete_a_class),
  ("retype a legend label", relabel),
]


def run_route(name, mutate, values):
  """Stage one edit and report whether the plugin followed it.

  Args:
    name: the route's name, for the report.
    mutate: a callable taking a cloned renderer, mutating it in
      place, and returning (what_to_check, expected) or None when the
      fixture cannot stage it.

  Returns:
    (name, "ok"/"FOLLOWED NOTHING"/..., detail) for the inventory.
  """
  project = QgsProject.instance()
  project.clear()
  layer = region_from(values)
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

  renderer = element.renderer().clone()
  asked = mutate(renderer)
  if asked is None:
    dlg.close()
    return (name, "SKIPPED", "fixture could not stage it")
  what, expected = asked
  element.setRenderer(renderer)
  element.styleChanged.emit()
  element.triggerRepaint()
  rt._tick(400)

  assignment = [a for a in dlg._assignments() if a["id"] == tid][0]
  classes = dlg._current_graduated_classes(assignment)
  if what == "interior":
    got = _interior(classes)
  elif what == "count":
    got = len(classes)
  elif what == "colour_at_1":
    got = _colours(classes)[1] if len(classes) > 1 else None
  elif what == "label_at_0":
    live = element.renderer().ranges()
    got = [r.label() for r in live][0]
  dlg.close()
  ok = got == expected
  return (name, "ok" if ok else "NOT FOLLOWED",
          f"wanted {expected}, plugin has {got}")


def main():
  """Walk every route and print the inventory.

  Returns:
    0 always -- this reports what is true, and a red exit would make
    it a gate before anybody has decided which routes are promises.
  """
  app = QgsApplication([], False)
  app.initQgis()
  print("\nWHAT A QGIS SYMBOLOGY EDIT REACHES\n")
  failures = []
  width = max(len(n) for n, _ in ROUTES)
  for shape, build in DATASETS:
    values = build()
    print(f"  --- {shape} ---")
    for name, fn in ROUTES:
      try:
        _n, verdict, detail = run_route(name, fn, values)
      except Exception as exc:
        verdict, detail = "RAISED", f"{type(exc).__name__}: {exc}"
      print(f"    {name:{width}}  {verdict:14}  {detail}")
      if verdict in ("NOT FOLLOWED", "RAISED"):
        failures.append((shape, name, detail))
  print(f"\n  {len(failures)} failing cell(s) "
        f"of {len(DATASETS) * len(ROUTES)}")
  for shape, name, detail in failures:
    print(f"    {shape} / {name}: {detail}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
