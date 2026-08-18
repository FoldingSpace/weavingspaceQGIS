"""Retype a class break in QGIS's Symbology panel; does the plugin see it?

Reported against rc8 on 2026-08-18 with two screenshots: QGIS holding
0-10, 10-20, 20-30, 30-50, 50-80 on Percent_White while the plugin's
colour editor showed 3.1-18.3, 18.3-33.5, 33.5-48.7, 48.7-63.9,
63.9-79.1 -- its own equal-interval breaks. "regardless of HOW I do
it, changes to the Q symbology are not reflected in the plugin".

The colours in both panels MATCHED, which is the clue this probe is
built around. `_graduated_layer_edited` decides whether to adopt by
comparing `[r.symbol().color().name() for r in ranges]` against what
the plugin would draw, and returns early when they agree. Retyping a
BOUNDARY moves no colour, so the comparison sees nothing.

Two arms, so a pass cannot be mistaken for coverage:
  BOUNDS_ONLY  -- the user's action: same field, count, ramp, colours;
                  only the numbers move. Expected to expose the defect.
  CONTROL      -- the same edit with one colour ALSO changed, which is
                  the route the existing guard drives. If this arm
                  fails too the diagnosis is wrong and the fault is
                  elsewhere.
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


def _bounds_of(renderer):
  """Every class boundary a renderer holds, rounded for printing.

  Args:
    renderer: a graduated renderer, from a layer or freshly built.

  Returns:
    [(lower, upper), ...] in class order.
  """
  return [(round(r.lowerValue(), 3), round(r.upperValue(), 3))
          for r in renderer.ranges()]


def arm(label, also_change_a_colour):
  """One route from a dock edit to what the plugin then believes.

  Args:
    label: what to print this arm as.
    also_change_a_colour: when true, move one class colour as well as
      the two boundaries. That is the CONTROL: the existing guard
      covers a change that moves colours, so if this arm fails too the
      fault is not the colour comparison.

  Returns:
    True when the plugin's view matches what QGIS now holds, False
    when it does not, or None when the fixture could not be staged.
  """
  project = QgsProject.instance()
  project.clear()
  layer = rt.make_region_layer()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  rt._tick(200)
  dlg.table.cellWidget(0, 1).setCurrentText("v1")
  dlg.table.cellWidget(0, 2).setCurrentText("Quant: Equal interval")
  dlg._update_dynamic_columns()
  rt._tick(150)
  tid = dlg.table.item(0, 0).text()
  dlg.spacing_spin.setValue(500)
  rt._generate_and_wait(dlg)
  rt._tick(200)

  element = project.mapLayer(dlg._element_layer_ids[tid])
  before = _bounds_of(element.renderer())

  # WHAT THE USER DID: double-click a range, retype its top, and QGIS
  # moves the bottom of the next one to match. Same renderer, same
  # symbols, same ramp -- only two numbers move.
  renderer = element.renderer().clone()
  ranges = renderer.ranges()
  if len(ranges) < 2:
    print(f"  {label}: only {len(ranges)} class(es); nothing to retype")
    return None
  moved = round((ranges[0].upperValue() + ranges[1].upperValue()) / 2.0, 3)
  renderer.updateRangeUpperValue(0, moved)
  renderer.updateRangeLowerValue(1, moved)
  if also_change_a_colour:
    from qgis.PyQt.QtGui import QColor
    symbol = ranges[0].symbol().clone()
    symbol.setColor(QColor("#010203"))
    renderer.updateRangeSymbol(0, symbol)
  element.setRenderer(renderer)
  element.styleChanged.emit()
  element.triggerRepaint()
  rt._tick(400)

  in_qgis = _bounds_of(element.renderer())
  # what the PLUGIN believes, by the same route its editor reads
  assignment = [a for a in dlg._assignments()
                if a["id"] == tid][0]
  plugin_view = dlg._current_graduated_classes(assignment)
  plugin_bounds = ([(round(lo, 3), round(hi, 3))
                    for lo, hi, _c in plugin_view] if plugin_view else None)

  print(f"  {label}")
  print(f"    before the edit   : {before[:3]} ...")
  print(f"    QGIS now holds    : {in_qgis[:3]} ...")
  print(f"    plugin reports    : "
        f"{plugin_bounds[:3] if plugin_bounds else None} ...")
  agrees = plugin_bounds == in_qgis
  # THE SECOND REPORT: is the plugin's lowest bound the data's minimum?
  index = layer.fields().indexOf("v1")
  raw = [f["v1"] for f in layer.getFeatures()
         if f["v1"] is not None]
  if plugin_bounds and raw:
    print(f"    data v1 min/max   : {min(raw):.3f} / {max(raw):.3f}")
    print(f"    plugin low/high   : {plugin_bounds[0][0]:.3f} / "
          f"{plugin_bounds[-1][1]:.3f}")
    print(f"    LOWEST BOUND IS THE MINIMUM: "
          f"{abs(plugin_bounds[0][0] - min(raw)) < 1e-6}")
  print(f"    AGREES WITH QGIS  : {agrees}")
  dlg.close()
  return agrees


def main():
  """Run both arms and say what the pair means.

  Returns:
    0 always: this reports a measurement rather than gating anything.
  """
  app = QgsApplication([], False)
  app.initQgis()
  print("\nRETYPED BREAKS IN THE DOCK -- does the plugin follow?\n")
  bounds_only = arm("BOUNDS_ONLY (the user's action)", False)
  control = arm("CONTROL (a colour moves too)", True)
  print("\nVERDICT")
  if bounds_only is False and control is True:
    print("  CONFIRMED: the plugin follows a dock edit only when a "
          "COLOUR changes.\n  Retyping a boundary alone is invisible "
          "to it, which is the report.")
  elif bounds_only and control:
    print("  NOT REPRODUCED on this route: both arms agree with QGIS.")
  else:
    print(f"  INCONCLUSIVE: bounds_only={bounds_only} control={control}. "
          f"If the control also fails the diagnosis is wrong.")
  return 0


if __name__ == "__main__":
  sys.exit(main())
