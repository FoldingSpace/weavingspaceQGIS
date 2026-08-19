"""Read back what QGIS's Symbology panel actually shows after a retype.

The tester's report of 2026-08-19, against rc9. He retypes the first
class's lower bound to 0 in QGIS's Symbology panel, over a column
whose minimum is 3.1, and reports that the two columns of that panel
then DISAGREE WITH EACH OTHER: `Values` keeps `0.000000 - 10.000000`
while `Legend` reads `3.1 - 10`. He also reports the LAST interval's
top value being overwritten -- 80 typed, 79.1 shown -- which is the
opposite treatment at the other end.

WHY A NEW PROBE RATHER THAN THE EXISTING ONE.
`retyped_ladder_is_adopted.py` proved the fix by reading the PLUGIN's
side, through `_current_graduated_classes`, and it deliberately
compares only the INTERIOR boundaries -- its own comment says
comparing the ends would demand a promise the model never made. So it
is structurally unable to see this: both of the tester's symptoms are
at the ENDS, and one of them is a LABEL, which nothing in that probe
reads at all. A probe that cannot see the report is not evidence
about it.

WHAT THIS ONE READS, and it reads all three because the report is
that they disagree:

  * every range's lowerValue and upperValue, which is QGIS's `Values`;
  * every range's label, which is QGIS's `Legend`;
  * the plugin's own ladder, which is what its editor draws.

It asserts nothing and fixes nothing. It prints the three side by
side so the disagreement can be seen, or shown not to exist.

Run it under QGIS's own Python:

    eval "$(bash tools/macos_qgis_env.sh 2>/dev/null \
            | grep -E '^[A-Z_]+=' | sed 's/^/export /')"
    export QT_QPA_PLATFORM=offscreen
    "$QGIS_PY" -u tools/probes/the_legend_disagrees_with_the_values.py
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
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa: E402

# The tester's own ladder, from the rc8 screenshots and repeated in
# the rc9 report: 0-10, 10-20, 20-30, 30-50, 50-80 over a column
# running 3.1 to 79.1. BOTH ends deliberately sit outside the data,
# which is the whole point -- 0 is below the minimum and 80 above the
# maximum, so each end can be watched independently.
TYPED = [0.0, 10.0, 20.0, 30.0, 50.0, 80.0]

# Reuse the fixture that reproduced the earlier report to the decimal
# rather than inventing a second one; two fixtures for one report is
# two things to keep in step.


def _region():
  """The tester-shaped column, built by the probe that already has one.

  Returns:
    A memory layer of a hundred areas whose `pct` runs 3.1 to 79.1.

  Loaded by path rather than imported as a package, because
  `tools/probes` is not one and adding an `__init__.py` for a probe
  would be a change to the tree for the sake of a throwaway.
  """
  path = os.path.join(ROOT, "tools", "probes", "retyped_ladder_is_adopted.py")
  spec_ = importlib.util.spec_from_file_location("_retyped", path)
  mod = importlib.util.module_from_spec(spec_)
  spec_.loader.exec_module(mod)
  return mod.continuous_region()


def _read_ranges(layer):
  """Everything QGIS's Symbology panel shows about each class.

  Args:
    layer: the element output layer, carrying a graduated renderer.

  Returns:
    A list of ``(lower, upper, label)`` in class order, or None when
    the layer's renderer is not graduated.

  The ranges list is BOUND TO A NAME before it is indexed: a
  temporary list from a QGIS getter frees its contents, which has
  segfaulted this project once and returned a plausible wrong colour
  another time.
  """
  renderer = layer.renderer()
  if not hasattr(renderer, "ranges"):
    return None
  ranges = renderer.ranges()
  return [(r.lowerValue(), r.upperValue(), r.label()) for r in ranges]


def main():
  """Retype the tester's ladder, let it settle, print all three views.

  Returns:
    0 always. This probe reports; it does not judge.
  """
  app = QgsApplication([], False)
  app.initQgis()

  project = QgsProject.instance()
  project.clear()
  layer = _region()
  project.addMapLayer(layer)

  dlg = WeavingSpaceDialog(iface=rt._Iface())
  # LIVE UPDATE IS LEFT AT ITS DEFAULT, WHICH IS ON, and that is the
  # whole difference between this probe and the first draft of it.
  # Switched off, the retype simply stays where it was put and the
  # report cannot reproduce -- the plugin never gets an occasion to
  # write anything back. The tester has it on, because it is the
  # default; a probe that quietly turns off the mechanism the report
  # travels through is measuring a plugin nobody runs.
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

  print("\nWHAT QGIS HOLDS BEFORE THE RETYPE")
  for i, (lo, hi, lab) in enumerate(_read_ranges(element)):
    print(f"  {i}  values {lo:>12.6f} - {hi:<12.6f}  legend {lab!r}")

  # THE TESTER'S EDIT, made the way the panel makes it: each range's
  # own two numbers retyped, which is what double-clicking the Values
  # cell does. QGIS moves no neighbour for you, so the ladder is
  # written from consecutive pairs.
  renderer = element.renderer().clone()
  ranges = renderer.ranges()
  if len(ranges) != len(TYPED) - 1:
    print(f"  fixture unusable: {len(ranges)} classes, not {len(TYPED) - 1}")
    return 0
  for index in range(len(TYPED) - 1):
    renderer.updateRangeLowerValue(index, TYPED[index])
    renderer.updateRangeUpperValue(index, TYPED[index + 1])
    renderer.updateRangeLabel(
      index, f"{TYPED[index]:g} - {TYPED[index + 1]:g}")
  element.setRenderer(renderer)
  element.styleChanged.emit()
  element.triggerRepaint()

  print("\nWHAT QGIS HOLDS THE INSTANT AFTER THE RETYPE")
  for i, (lo, hi, lab) in enumerate(_read_ranges(element)):
    print(f"  {i}  values {lo:>12.6f} - {hi:<12.6f}  legend {lab!r}")

  # LET THE PLUGIN ANSWER. The tester's words are that his edit
  # "sticks in QGIS for a bit, but then gets changed", so the moment
  # this probe exists to reach is AFTER the debounces have run, not
  # the instant above.
  rt._tick(1200)

  after = _read_ranges(element)
  print("\nWHAT QGIS HOLDS ONCE THE PLUGIN HAS SETTLED")
  disagree = []
  for i, (lo, hi, lab) in enumerate(after):
    own = f"{lo:g} - {hi:g}"
    flag = ""
    if lab.replace(" ", "") != own.replace(" ", ""):
      flag = "   <-- LEGEND DISAGREES WITH VALUES"
      disagree.append(i)
    print(f"  {i}  values {lo:>12.6f} - {hi:<12.6f}  legend {lab!r}{flag}")

  assignment = [a for a in dlg._assignments() if a["id"] == tid][0]
  print("\nWHAT THE PLUGIN'S OWN EDITOR WOULD DRAW")
  for i, (lo, hi, _c) in enumerate(dlg._current_graduated_classes(assignment)):
    print(f"  {i}  {lo:g} - {hi:g}")

  print("\nWHAT WAS TYPED")
  print(f"  {[f'{TYPED[i]:g} - {TYPED[i + 1]:g}' for i in range(len(TYPED) - 1)]}")

  # WAS THE USER TOLD? Two numbers a person typed have just been
  # discarded, and this project's standing rule is that a control
  # never silently changes what somebody entered. `BAR_MESSAGES` is
  # the harness's record of everything raised on the message bar --
  # the stub collects rather than swallows, precisely so a question
  # like this one can be asked at all.
  print("\nWHAT THE USER WAS TOLD")
  said = list(rt.BAR_MESSAGES)
  if said:
    for entry in said:
      print(f"  {entry!r}")
  else:
    print("  NOTHING. The typed ends were discarded in silence.")

  print("\nREADING")
  print(f"  ranges whose legend contradicts their own values: "
        f"{disagree if disagree else 'none'}")
  first_low = after[0][0]
  last_high = after[-1][1]
  print(f"  first class's lower value: {first_low:g}  "
        f"(typed {TYPED[0]:g}, column minimum 3.1)")
  print(f"  last class's upper value : {last_high:g}  "
        f"(typed {TYPED[-1]:g}, column maximum 79.1)")
  if first_low != last_high:
    ends = ("BOTH ENDS TREATED ALIKE"
            if (first_low == TYPED[0]) == (last_high == TYPED[-1])
            else "THE TWO ENDS ARE TREATED DIFFERENTLY")
    print(f"  {ends}")

  dlg.close()
  return 0


if __name__ == "__main__":
  sys.exit(main())
