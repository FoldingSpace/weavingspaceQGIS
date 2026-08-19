"""Does a floor or ceiling inside the data exclude, and is it DRAWN?

The maintainer's design of 2026-08-19: limits may sit inside the data
and put values out of bounds, and the areas they exclude become a
fourth kind of absence -- drawn, in a colour of their own, with a
legend line -- rather than holes.

Three things have to be true together, and each has failed on its own
in this project's history, so each is read separately here:

  * the LADDER starts at the floor and stops at the ceiling, rather
    than at whichever value happened to survive the narrowing, since
    two columns given one pair of limits must draw the same ladder;
  * the excluded areas LEAVE the element layer, so no tile is drawn
    from a value outside the limits;
  * and they ARRIVE on the paired layer carrying OUTSIDE_RANGE, so
    they are painted and named instead of leaving a hole. A hole is
    what this whole absence machinery exists to abolish, and it is
    indistinguishable from a tiling gap and from a missing value.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/a_limit_inside_the_data_excludes.py
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
from weavingspace_qgis import bridge  # noqa: E402
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

# Deliberately well inside a column running 3.1 to 79.1, so BOTH ends
# exclude real areas. A limit outside the data would prove only that
# nothing broke.
FLOOR, CEILING = 20.0, 60.0


def _region():
  """The tester-shaped column, from the probe that already builds one."""
  path = os.path.join(ROOT, "tools", "probes", "retyped_ladder_is_adopted.py")
  spec_ = importlib.util.spec_from_file_location("_retyped", path)
  mod = importlib.util.module_from_spec(spec_)
  spec_.loader.exec_module(mod)
  return mod.continuous_region()


def main():
  """Set limits inside the data, generate, and read all three claims.

  Returns:
    0 when every claim holds, 1 otherwise, so this can gate a loop.
  """
  app = QgsApplication([], False)
  app.initQgis()
  project = QgsProject.instance()
  project.clear()
  layer = _region()
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

  # Written straight into the record rather than typed into a box,
  # because the boxes do not exist yet -- this probe is about the
  # ARITHMETIC and the split, and staging through the control would
  # be testing two unbuilt things at once.
  dlg._pinned_bounds.setdefault(tid, {})["pct"] = {
    "floor": FLOOR, "ceiling": CEILING}
  dlg.spacing_spin.setValue(500)
  rt._generate_and_wait(dlg)
  rt._tick(300)

  failures = []

  element = project.mapLayer(dlg._element_layer_ids[tid])
  ranges = element.renderer().ranges()
  bounds = [(r.lowerValue(), r.upperValue()) for r in ranges]
  print(f"\nTHE LADDER, with floor {FLOOR:g} and ceiling {CEILING:g}")
  for i, (lo, hi) in enumerate(bounds):
    print(f"  {i}  {lo:g} - {hi:g}")
  if not bounds:
    failures.append("the element drew no classes at all")
  else:
    if abs(bounds[0][0] - FLOOR) > 1e-9:
      failures.append(
        f"the ladder starts at {bounds[0][0]:g}, not at the floor {FLOOR:g}")
    if abs(bounds[-1][1] - CEILING) > 1e-9:
      failures.append(
        f"the ladder stops at {bounds[-1][1]:g}, not at the ceiling "
        f"{CEILING:g}")

  # NO TILE MAY BE DRAWN FROM AN EXCLUDED VALUE. Asked of the layer's
  # own features rather than of the renderer, since the question is
  # which rows are there at all.
  index = element.fields().indexOf("pct")
  drawn = [f[index] for f in element.getFeatures()]
  outside = [v for v in drawn
             if v is not None and (v < FLOOR - 1e-9 or v > CEILING + 1e-9)]
  print(f"\nTHE ELEMENT LAYER holds {len(drawn)} tiles, "
        f"{len(outside)} of them outside the limits")
  if outside:
    failures.append(
      f"{len(outside)} tiles were drawn from values outside the limits, "
      f"e.g. {sorted(outside)[:3]}")

  # ...AND THEY MUST BE ON THE PAIRED LAYER, NAMED.
  paired_id = dlg._no_data_layer_ids.get(tid)
  print(f"\nTHE PAIRED LAYER: {'present' if paired_id else 'ABSENT'}")
  if not paired_id:
    failures.append(
      "no paired layer was built, so the excluded areas are holes -- "
      "which is the fault this kind exists to prevent")
  else:
    paired = project.mapLayer(paired_id)
    kind_index = paired.fields().indexOf(bridge.ABSENCE_FIELD)
    kinds = {}
    for feature in paired.getFeatures():
      kinds[str(feature[kind_index])] = kinds.get(
        str(feature[kind_index]), 0) + 1
    print(f"  tiles by kind: {kinds}")
    wanted = bridge.ABSENCE_VALUE[bridge.OUTSIDE_RANGE_KEY]
    if wanted not in kinds:
      failures.append(
        f"the paired layer carries {sorted(kinds)} and not {wanted!r}, "
        f"so the excluded areas are not named as excluded")
    renderer = paired.renderer()
    labels = [c.label() for c in renderer.categories()] \
        if hasattr(renderer, "categories") else []
    print(f"  legend lines: {labels}")
    if not any("outside" in str(text).lower() for text in labels):
      failures.append(
        f"no legend line names the excluded areas: {labels!r}")

  print("\nVERDICT")
  if failures:
    for line in failures:
      print(f"  FAILED: {line}")
    return 1
  print("  All three hold: the ladder is the limits, no tile is drawn\n"
        "  from an excluded value, and the excluded areas are painted\n"
        "  and named on the paired layer.")
  dlg.close()
  return 0


if __name__ == "__main__":
  sys.exit(main())
