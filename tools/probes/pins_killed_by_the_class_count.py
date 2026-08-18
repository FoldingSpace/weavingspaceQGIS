"""Does a CLASS COUNT destroy pinned bounds, and blame the data?

A. Pin both ends legally at k=5, then move the Classes spinner to 2 --
   the spinner's own floor. `pin_problem` refuses two pins on a ladder
   with one boundary, so `_retire_an_undrawable_pin` pops the WHOLE
   record and reports "cannot be drawn from the values it holds now".
   The values did not move; the user's own spinner did. Put the
   spinner back to 5 and see whether the pins come home.

B. The CONTROL, and it is the settled twin: a COPIED ladder met by the
   same act keeps its pins ("a copy degrades to its pins", CLAUDE.md).

C. A constant column met on the RESTYLE route: the run route says
   "every area has the same value"; does this one?
"""

import importlib.util
import json
import os
import sys

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer,   # noqa
                       QgsFeature, QgsGeometry, QgsPointXY)

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import bridge, compat                          # noqa
from weavingspace_qgis.dialog import WeavingSpaceDialog               # noqa


def ladder(dlg, tid):
  """The (lower, upper) pairs the element's own layer actually draws.

  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    Rounded bounds, or [] when the renderer carries no ranges.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  rends = out.renderer()
  held = rends.ranges() if hasattr(rends, "ranges") else []
  return [(round(r.lowerValue(), 3), round(r.upperValue(), 3))
          for r in held]


def stamp(dlg, tid):
  """The pin record written onto the layer, which a reopen reads.

  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    The stamped pin record, or None when nothing is stamped.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  raw = out.customProperty("weavingspace_quant_style")
  return json.loads(raw).get("pinned") if raw else None


def k_to(dlg, tid, count):
  """Move one row's Classes spinner, as a user does.

  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.
    count: the class count to move the spinner to.

  Returns:
    None; the spinner is moved and the debounce run.
  """
  spin = dlg.table.cellWidget(dlg._row_for_element(tid), 3)
  assert spin is not None and spin.isEnabled(), f"{tid}: no Classes cell"
  spin.setValue(count)
  T._tick(250)


def press_generate(dlg):
  """What the Generate button does, and how it was answered.

  Args:
    dlg: the dialog to press Generate on.

  Returns:
    True when the same layers survived, i.e. it restyled in place.
  """
  before = dict(dlg._element_layer_ids)
  dlg._generate()
  assert T._settle(dlg, seconds=90), "the run never settled"
  T._tick(300)
  return before == dlg._element_layer_ids     # True == restyled in place


def build(layer=None, var="v3"):
  """A clean project, two elements on one column, tiled once.

  Args:
    layer: the region layer to use, or None for the standard fixture.
    var: the column both elements carry.

  Returns:
    The dialog, left open with its first map drawn.
  """
  project = QgsProject.instance()
  project.clear()
  T._tick(100)
  project.addMapLayer(layer if layer is not None
                      else T.make_region_layer(n=12))
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.n_combo.setCurrentText("4")
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(1200)
  dlg.table.cellWidget(0, 1).setCurrentText(var)
  dlg.table.cellWidget(1, 1).setCurrentText(var)
  T._tick(200)
  T._generate_and_wait(dlg)
  return dlg


def values_of(dlg, field):
  """The column's distinct values as the classifier reads them.

  Args:
    dlg: the dialog whose region layer is asked.
    field: the column name.

  Returns:
    A sorted list of floats.
  """
  source = dlg._classification_values(field)
  return sorted(float(v) for v in
                source.uniqueValues(source.fields().indexOf(field)))


ONLY = sys.argv[1] if len(sys.argv) > 1 else "ABC"

# ------------------------------------------------------------------ A
if "A" in ONLY:
  dlg = build()
  a = dlg.table.item(0, 0).text()
  vals = values_of(dlg, "v3")
  low, high = vals[1], vals[-2]
  print("A0 pin_problem at k=5        :",
        bridge.pin_problem(low, high, vals, 5, None))
  dlg._pinned_bounds.setdefault(a, {})["v3"] = {"low": low, "high": high}
  dlg._apply_style_change()
  T._tick(400)
  print(f"A0 pinned {low} / {high}; the map draws:", ladder(dlg, a))
  print("A0 stamp                     :", stamp(dlg, a))

  del T.BAR_MESSAGES[:]
  k_to(dlg, a, 2)
  print("A1 restyled rather than tiled:", press_generate(dlg))
  print("A1 said to the user          :", [m for _k, m in T.BAR_MESSAGES])
  print("A1 record AFTER              :",
        dlg._pinned_bounds.get(a, {}).get("v3"))
  print("A1 stamp AFTER               :", stamp(dlg, a))
  print("A1 pin_problem at k=2 said   :",
        bridge.pin_problem(low, high, vals, 2, None))
  print("A1 values NOW                :", len(values_of(dlg, "v3")),
        "distinct,", values_of(dlg, "v3")[0], "..",
        values_of(dlg, "v3")[-1])

  del T.BAR_MESSAGES[:]
  k_to(dlg, a, 5)
  print("A2 spinner back to 5, restyled:", press_generate(dlg))
  print("A2 record                    :",
        dlg._pinned_bounds.get(a, {}).get("v3"))
  print("A2 the map draws             :", ladder(dlg, a))
  print("A2 said                      :", [m for _k, m in T.BAR_MESSAGES])
  dlg.close()

# ------------------------------------------------------------------ B
if "B" in ONLY:
  dlg = build()
  a = dlg.table.item(0, 0).text()
  vals = values_of(dlg, "v3")
  low, high = vals[1], vals[-2]
  # a COPIED ladder plus the same two pins, which is the settled twin
  dlg._pinned_bounds.setdefault(a, {})["v3"] = {
    "low": low, "high": high,
    "breaks": [low, vals[len(vals) // 3], vals[2 * len(vals) // 3], high]}
  del T.BAR_MESSAGES[:]
  k_to(dlg, a, 2)
  print("B1 record after the SAME act :",
        dlg._pinned_bounds.get(a, {}).get("v3"))
  print("B1 said                      :", [m for _k, m in T.BAR_MESSAGES])
  dlg.close()

# ------------------------------------------------------------------ C
if "C" in ONLY:
  flat = QgsVectorLayer("Polygon?crs=EPSG:3857", "constant", "memory")
  flat.dataProvider().addAttributes([compat.make_field("v3", float),
                                     compat.make_field("v9", float)])
  flat.updateFields()
  feats = []
  for k in range(36):
    i, j = k % 6, k // 6
    x, y = i * 1000.0, j * 1000.0
    ring = [QgsPointXY(x, y), QgsPointXY(x + 1000, y),
            QgsPointXY(x + 1000, y + 1000), QgsPointXY(x, y + 1000)]
    f = QgsFeature(flat.fields())
    f.setGeometry(QgsGeometry.fromPolygonXY([ring]))
    f["v3"] = 7.0
    f["v9"] = float(k)
    feats.append(f)
  flat.dataProvider().addFeatures(feats)
  flat.updateExtents()
  del T.BAR_MESSAGES[:]
  dlg = build(layer=flat, var="v3")
  a = dlg.table.item(0, 0).text()
  print("C0 the RUN route said        :",
        [m for _k, m in T.BAR_MESSAGES if "same value" in m])
  print("C0 classes drawn             :", len(ladder(dlg, a)))
  del T.BAR_MESSAGES[:]
  k_to(dlg, a, 8)
  print("C1 restyled rather than tiled:", press_generate(dlg))
  print("C1 spinner says 8, map draws :", len(ladder(dlg, a)), "class(es)")
  print("C1 said to the user          :", [m for _k, m in T.BAR_MESSAGES])
  dlg.close()

QgsProject.instance().clear()
