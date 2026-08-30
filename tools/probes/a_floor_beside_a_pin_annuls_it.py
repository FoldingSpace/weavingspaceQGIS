"""A floor annuls a pin, and every control goes on claiming the pin.

`make_graduated_renderer` narrows `finite_values` to the floor and the
ceiling BEFORE asking `pin_problem` (bridge.py 2612-2649), so a limit can
make a pin undrawable and bridge drops it. Only the dialog ever tells the
user, through `_retire_an_undrawable_pin` -- and that site asks
`pin_problem` of the WHOLE column (dialog.py 4919), so it sees no problem,
says nothing, and leaves the record, the ramp cell's pinned box and the
layer stamp asserting a bound the map does not have.

Driven as a user reaches it: pin the last class's lower bound, watch it
reach the map, then set a floor BELOW that pin -- which is what
`_limit_problem` permits -- and watch the pin leave without a word.

    eval "$(bash tools/macos_qgis_env.sh | grep -E '^[A-Z_]+=' \
            | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen WEAVINGSPACE_REPO="$PWD"
    "$QGIS_PY" -u tools/probes/colourgates_a_floor_annuls_a_pin_in_silence.py
"""
import importlib.util
import json
import os
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
  """The (lower, upper) pairs the element's own layer is drawing.

  Args:
    dlg: the dialog whose output layers to read.
    tid: the element whose layer to ask.

  Returns:
    [(lower, upper), ...] rounded to two places, read off the LAYER
    rather than rebuilt from the record, since the whole question here
    is whether the two agree.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  rends = out.renderer()
  held = rends.ranges() if hasattr(rends, "ranges") else []
  return [(round(r.lowerValue(), 2), round(r.upperValue(), 2))
          for r in held]


def stamp(dlg, tid):
  """The pin record written onto the layer, which a reopen reads.

  Args:
    dlg: the dialog whose output layers to read.
    tid: the element whose layer to ask.

  Returns:
    The stamped `pinned` mapping, or None where nothing is stamped.
    This is what a reopened project has to go on, so it is read
    separately from the record the live dialog holds.
  """
  out = QgsProject.instance().mapLayer(dlg._element_layer_ids[tid])
  raw = out.customProperty("weavingspace_quant_style")
  return json.loads(raw).get("pinned") if raw else None


def in_the_file(path):
  """The pin text inside the saved .qgz, read as bytes -- no QGIS."""
  with zipfile.ZipFile(path) as archive:
    name = [n for n in archive.namelist() if n.endswith(".qgs")][0]
    text = archive.read(name).decode("utf-8", "replace")
  return ["".join(part.split("value=")[1:])[:110] for part in text.split("<")
          if "weavingspace_quant_style" in part]


project = QgsProject.instance()
project.clear()
project.addMapLayer(T.make_region_layer(n=12))
dlg = WeavingSpaceDialog(iface=T._Iface())
dlg.live_check.setChecked(False)
dlg.n_spin.setValue(2)
dlg.family_combo.setCurrentText("laves 3.3.4.3.4")
dlg.spacing_spin.setValue(1200)
dlg.table.cellWidget(0, 1).setCurrentText("v3")
T._tick(200)
T._generate_and_wait(dlg)
a = dlg.table.item(0, 0).text()

source = dlg._classification_values("v3")
values = sorted(float(v) for v in
                source.uniqueValues(source.fields().indexOf("v3")))
print("v3 distinct:", [int(v) for v in values])

# A FLOOR and a HIGH PIN with a GAP between them: nothing in the column
# lies in [floor, pin), so the pool the floor leaves holds no sample for
# the middle classes, while the whole column holds plenty.
floor = pin = None
for i in range(len(values) - 1):
  lower, upper = values[i], values[i + 1]
  if upper - lower < 4:
    continue                      # want a real hole, not two neighbours
  # the pin sits on the value above the hole; the floor sits INSIDE the
  # hole, so nothing at all lies in [floor, pin)
  if len([v for v in values if v > upper]) >= 2:
    floor, pin = lower + (upper - lower) / 2.0, upper
    break
assert floor is not None, "no gap in the fixture column"
print(f"\nfloor {floor:g}, last class begins at {pin:g}; "
      f"values in [{floor:g}, {pin:g}): "
      f"{[int(v) for v in values if floor <= v < pin]}")

assignment = dlg._assignment_for(a)
k = int(assignment.get("k", 5))

# ---- 1. the pin alone, which is the control
dlg._pinned_bounds.setdefault(a, {})["v3"] = {"high": pin}
dlg._apply_style_change()
T._tick(400)
print("\n1 pin alone -> ladder :", ladder(dlg, a))
print("1 last class begins at:", ladder(dlg, a)[-1][0],
      "  (the pin is on the map)")

# ---- 2. the floor, through the two guards the control applies
wanted = {"high": pin, "floor": floor}
whole = source.uniqueValues(source.fields().indexOf("v3"))
print("\n2 what `pin_changed` asks before accepting the floor:")
print("   bridge.pin_problem(low, high, WHOLE column, k) :",
      bridge.pin_problem(wanted.get("low"), wanted.get("high"), whole, k))
print("   dlg._limit_problem(wanted, assignment)         :",
      dlg._limit_problem(wanted, assignment))
print("   -> both accept, so the control keeps the floor")

del T.BAR_MESSAGES[:]
dlg._pinned_bounds[a]["v3"] = dict(wanted)
dlg._apply_style_change()
T._tick(300)
# a limit is a geometry change, so the restyle declines and says to press
# Generate; press it, exactly as the notice asks
dlg._generate()
assert T._settle(dlg, seconds=120), "the run never settled"
T._tick(400)
print("\n3 the map with the floor:", ladder(dlg, a))
drawn = ladder(dlg, a)
kept = bool(drawn) and abs(drawn[-1][0] - float(pin)) < 1e-9
print(f"3 last class begins at {pin:g}: {kept}")

# ---- 4. what every other store still says
print("\n4 dialog record        :", dlg._pinned_bounds.get(a, {}).get("v3"))
print("4 layer stamp          :", stamp(dlg, a))
print("4 said to the user     :")
for _lvl, m in T.BAR_MESSAGES:
  print("     -", m[:150])
print("4 retirement verdict   :",
      dlg._retire_an_undrawable_pin("v3", dlg._assignment_for(a)))

# ---- 5. the second route: the saved project, read as bytes
folder = tempfile.mkdtemp()
path = os.path.join(folder, "saved.qgz")
assert project.write(path), "the project would not save"
print("\n5 inside the saved .qgz:", in_the_file(path))

dlg.close()
project.clear()
T._tick(200)
assert project.read(path), "the project would not reopen"
T._tick(400)
again = WeavingSpaceDialog(iface=T._Iface())
again.live_check.setChecked(False)
T._tick(600)
print("5 reopened, row's record:", again._pinned_bounds.get(a, {}).get("v3"))
print("5 the map it sits over  :", ladder(again, a))
again.close()
