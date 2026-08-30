"""Two questions about the tail of `_restyle_only`, both about ORDER.

Measured at 0299c77. Both confirmed.

A. `_restyle_only` STAMPS the layer (dialog.py:8070) and only THEN
   retires an undrawable pin (8113). Its twin `_add_output_layers`
   retires FIRST (9612) and stamps afterwards (9908), and says at that
   line why: the stamp is the last moment before a dead number is
   written where a reopen reads it straight back. So the restyle path
   tells the user the bound has been recalculated, clears the row's
   record, and saves the retired number into the .qgz -- where
   reopening restores a pin the map does not honour.

B. The `field in said` dedup at 8108 stands in front of the pin
   retirement as well as in front of the legend notice, and `said`
   is filled by whether an EARLIER element raised a legend notice
   about the same column. So a second element carrying that column
   may never be asked at all. Part C is the control: the identical
   act on element b, with element a merely asking for a class count
   its column can fill, retires and announces b's pin normally.

Driven as a user reaches it. Both ends pinned, then Classes moved to
2: `pin_problem` refuses two pins on a ladder with one boundary, and
the count is symbology, so Generate answers it with a restyle and the
run-landing twin never sees it. With live update off the table and
the map disagree until Generate, which is what lets TWO elements move
before one restyle -- the state part B needs.

    python3 tools/hunt_probe.py --prepare --name order-asymmetry
    python3 tools/hunt_probe.py --name order-asymmetry \
        --run tools/probes/restyle_stamps_the_pin_it_retires.py ABC

Pass A, B, C or any combination as the argument; each part clears the
project and builds its own fixture, so any one of them runs alone.
"""

import importlib.util
import json
import os
import shutil
import sys
import tempfile
import zipfile

REPO = os.environ.get("WEAVINGSPACE_REPO") or os.getcwd()
os.chdir(REPO)
sys.path.insert(0, REPO)

spec = importlib.util.spec_from_file_location(
  "run_tests", os.path.join(REPO, "tests", "run_tests.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)

from qgis.core import QgsApplication, QgsProject                   # noqa

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", "/usr"), True)
_app = QgsApplication([], True)
_app.initQgis()

from weavingspace_qgis import bridge                               # noqa
from weavingspace_qgis.dialog import WeavingSpaceDialog            # noqa


def ladder(dlg, tid):
  """The classes the element's own layer actually draws.
  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    The (lower, upper) pairs the element's own layer is drawing, or
    [] when it has no ranged renderer.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  rends = out.renderer()
  held = rends.ranges() if hasattr(rends, "ranges") else []
  return [(round(r.lowerValue(), 2), round(r.upperValue(), 2))
          for r in held]


def stamp(dlg, tid):
  """The pin record written onto the layer, which a reopen reads.
  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.

  Returns:
    The pin record stamped on the element's layer, or None.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  raw = out.customProperty("weavingspace_quant_style")
  return json.loads(raw).get("pinned") if raw else None


def in_the_file(path):
  """The pin text inside the saved .qgz, read as bytes -- no QGIS."""
  with zipfile.ZipFile(path) as archive:
    name = [n for n in archive.namelist() if n.endswith(".qgs")][0]
    text = archive.read(name).decode("utf-8", "replace")
  return ["".join(part.split("value=")[1:])[:70] for part in text.split("<")
          if "weavingspace_quant_style" in part]


def build():
  """Two elements on one column, tiled, dialog left open."""
  project = QgsProject.instance()
  project.clear()
  project.addMapLayer(T.make_region_layer(n=12))
  dlg = WeavingSpaceDialog(iface=T._Iface())
  dlg.live_check.setChecked(False)
  dlg.n_spin.setValue(4)
  dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
  dlg.spacing_spin.setValue(1200)
  dlg.table.cellWidget(0, 1).setCurrentText("v3")
  dlg.table.cellWidget(1, 1).setCurrentText("v3")
  T._tick(200)
  T._generate_and_wait(dlg)
  return dlg


def press_generate(dlg):
  """What the button does, and whether it re-tiled or restyled."""
  before = dict(dlg._element_layer_ids)
  dlg._generate()
  assert T._settle(dlg, seconds=90), "the run never settled"
  T._tick(300)
  return before == dlg._element_layer_ids


def k_to(dlg, tid, count):
  """Move one row's Classes spinner, as a user does.
  Args:
    dlg: the dialog holding the element.
    tid: the element's tile id.
    count: the class count to move the spinner to.

  Returns:
    None; the row's Classes spinner is moved and the debounce run.
  """
  spin = dlg.table.cellWidget(dlg._row_for_element(tid), 3)
  assert spin is not None and spin.isEnabled(), f"{tid}: no Classes cell"
  spin.setValue(count)
  T._tick(250)


def bounds(dlg):
  """A low and a high that ARE drawable at k=5, from the data itself."""
  source = dlg._classification_values("v3")
  values = sorted(float(v) for v in
                  source.uniqueValues(source.fields().indexOf("v3")))
  return values, values[1], values[-2]


ONLY = sys.argv[1] if len(sys.argv) > 1 else "AB"
folder = tempfile.mkdtemp()
try:
 # ----------------------------------------------------------------- A
 if "A" in ONLY:
  dlg = build()
  a, b = dlg.table.item(0, 0).text(), dlg.table.item(1, 0).text()
  values, low, high = bounds(dlg)
  print(f"v3: {len(values)} distinct, {values[0]}..{values[-1]}; "
        f"pinning {low} and {high} on element {a}")

  dlg._pinned_bounds.setdefault(a, {})["v3"] = {"low": low, "high": high}
  dlg._apply_style_change()
  T._tick(400)
  print("A0 drawable at k=5, ladder    :", ladder(dlg, a))
  print("A0 dialog record / layer stamp:",
        dlg._pinned_bounds[a]["v3"], "/", stamp(dlg, a))

  del T.BAR_MESSAGES[:]
  k_to(dlg, a, 2)
  restyled = press_generate(dlg)
  print("A1 restyled rather than tiled :", restyled)
  print("A1 said to the user           :",
        [m for _k, m in T.BAR_MESSAGES if "bound" in m])
  print("A1 dialog record AFTER        :",
        dlg._pinned_bounds.get(a, {}).get("v3"))
  print("A1 layer stamp AFTER          :", stamp(dlg, a))
  print("A1 the ladder the map draws   :", ladder(dlg, a))

  path = os.path.join(folder, "saved.qgz")
  assert QgsProject.instance().write(path), "the project would not save"
  print("A2 inside the saved .qgz      :", in_the_file(path))
  dlg.close()
  QgsProject.instance().clear()
  T._tick(200)
  assert QgsProject.instance().read(path), "the project would not reopen"
  T._tick(400)
  again = WeavingSpaceDialog(iface=T._Iface())
  again.live_check.setChecked(False)
  T._tick(600)
  print("A2 reopened, the row's pin    :",
        again._pinned_bounds.get(a, {}).get("v3"))
  print("A2 the map it sits over       :", ladder(again, a))
  again.close()

 # ----------------------------------------------------------------- B
 if "B" in ONLY:
  QgsProject.instance().clear()
  T._tick(200)
  dlg = build()
  a, b = dlg.table.item(0, 0).text(), dlg.table.item(1, 0).text()
  values, low, high = bounds(dlg)
  dlg._pinned_bounds.setdefault(b, {})["v3"] = {"low": low, "high": high}
  dlg._apply_style_change()
  T._tick(400)
  print("B0 b pinned and drawn         :", ladder(dlg, b))

  # live update is off, so BOTH rows move before anything repaints
  k_to(dlg, a, 20)
  k_to(dlg, b, 2)
  del T.BAR_MESSAGES[:]
  asked = []
  original = dlg._retire_an_undrawable_pin
  dlg._retire_an_undrawable_pin = lambda f, x: (
    asked.append(x.get("id")) or original(f, x))
  restyled = press_generate(dlg)
  print("B1 restyled rather than tiled :", restyled)
  print("B1 elements asked to retire   :", asked, "of", [a, b])
  print("B1 said to the user           :",
        [m for _k, m in T.BAR_MESSAGES if "bound" in m or "class" in m])
  print("B1 b's record AFTER           :",
        dlg._pinned_bounds.get(b, {}).get("v3"))
  print("B1 b's layer stamp AFTER      :", stamp(dlg, b))
  print("B1 b's ladder                 :", ladder(dlg, b))
  print("B1 pin_problem on b says      :",
        bridge.pin_problem(low, high, values, 2, None))
  dlg.close()

 # ----- C: the CONTROL. Identical act on b; element a merely asks for
 # a count its column can fill, so a's legend notice stays silent and
 # `said` never gains the field.
 if "C" in ONLY:
  QgsProject.instance().clear()
  T._tick(200)
  dlg = build()
  a, b = dlg.table.item(0, 0).text(), dlg.table.item(1, 0).text()
  values, low, high = bounds(dlg)
  dlg._pinned_bounds.setdefault(b, {})["v3"] = {"low": low, "high": high}
  dlg._apply_style_change()
  T._tick(400)
  k_to(dlg, a, 6)
  k_to(dlg, b, 2)
  del T.BAR_MESSAGES[:]
  asked = []
  original = dlg._retire_an_undrawable_pin
  dlg._retire_an_undrawable_pin = lambda f, x: (
    asked.append(x.get("id")) or original(f, x))
  print("C1 restyled rather than tiled :", press_generate(dlg))
  print("C1 elements asked to retire   :", asked, "of", [a, b])
  print("C1 said to the user           :",
        [m for _k, m in T.BAR_MESSAGES if "bound" in m or "class" in m])
  print("C1 b's record AFTER           :",
        dlg._pinned_bounds.get(b, {}).get("v3"))
  print("C1 b's layer stamp AFTER      :", stamp(dlg, b))
  dlg.close()
finally:
  QgsProject.instance().clear()
  shutil.rmtree(folder, ignore_errors=True)
