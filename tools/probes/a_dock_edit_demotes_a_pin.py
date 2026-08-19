"""A pinned bound, an unrelated QGIS edit, and the pin is gone.

Two arms differing in ONE act: whether a boundary the user did not pin
is retyped in QGIS's Symbology panel before the plugin's own Classes
spinner is moved. Read twice -- off the dialog's record, and off the
MAP the next Generate draws, which knows nothing about the record.
"""
import importlib.util
import math
import os
import sys

# THE REPOSITORY THIS FILE LIVES IN, derived rather than written
# down. It arrived from a hunt's worktree with that worktree's path
# hard-coded, so running it from here measured the HUNT'S frozen tree
# and reported on code this checkout had already moved past -- which
# is exactly the trap of a probe that quietly answers a different
# question. Every other probe here derives its root the same way.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
spec = importlib.util.spec_from_file_location(
    "run_tests", os.path.join(ROOT, "tests", "run_tests.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

from qgis.core import (QgsApplication, QgsFeature, QgsGeometry,  # noqa
                       QgsGraduatedSymbolRenderer, QgsPointXY, QgsProject,
                       QgsVectorLayer)
from weavingspace_qgis import compat  # noqa
from weavingspace_qgis.dialog import WeavingSpaceDialog  # noqa

STYLE = "Quant: Equal intervals"
PIN = 25.0


def region():
  """The tester's own column, 3.1 to 79.1 across a small grid.

  Returns:
    A memory layer whose values run far enough for a pin at 25 to
    sit well inside the data, which is what these arms need.
  """
  vals = [3.1 + (79.1 - 3.1) * k / 99 for k in range(100)]
  n = int(math.ceil(math.sqrt(len(vals))))
  layer = QgsVectorLayer("MultiPolygon?crs=EPSG:3857", "region", "memory")
  prov = layer.dataProvider()
  prov.addAttributes([compat.make_field("pct", float)])
  layer.updateFields()
  feats = []
  for k, v in enumerate(vals):
    i, j = divmod(k, n)
    f = QgsFeature(layer.fields())
    c = 1000
    f.setGeometry(QgsGeometry.fromPolygonXY([[
      QgsPointXY(i * c, j * c), QgsPointXY((i + 1) * c, j * c),
      QgsPointXY((i + 1) * c, (j + 1) * c), QgsPointXY(i * c, (j + 1) * c)]]))
    f["pct"] = float(v)
    feats.append(f)
  prov.addFeatures(feats)
  layer.updateExtents()
  return layer


def ladder(layer):
  """The (lower, upper) pairs an element's layer is drawing.

  Args:
    layer: the element layer to read.

  Returns:
    Pairs read off the LAYER, so the map is compared with the
    record rather than with itself.
  """
  rs = layer.renderer().ranges()          # bind: temporaries dangle
  return [(round(r.lowerValue(), 2), round(r.upperValue(), 2)) for r in rs]


def arm(edit_in_qgis, pins, k_to, do_generate=True):
  """Run one arm on a cleared project and print what it leaves.

  Args:
    See the call sites: each arm differs by one act.

  Returns:
    None; a probe reports rather than judges.
  """
  project = QgsProject.instance()
  project.clear()                          # a CLEAN project, every arm
  del rt.BAR_MESSAGES[:]
  layer = region()
  project.addMapLayer(layer)
  dlg = WeavingSpaceDialog(iface=rt._Iface())
  dlg.live_check.setChecked(False)
  dlg.layer_combo.setLayer(layer)
  rt._tick(200)
  dlg.table.cellWidget(0, 1).setCurrentText("pct")
  rt._tick(100)
  mode = dlg.table.cellWidget(0, 2)
  i = mode.findText(STYLE)
  mode.setCurrentIndex(i)
  mode.activated.emit(i)
  rt._tick(120)
  dlg._update_dynamic_columns()
  rt._tick(150)
  tid = dlg.table.item(0, 0).text()
  assert dlg.table.cellWidget(0, 2).currentText() == STYLE
  dlg.spacing_spin.setValue(500)
  rt._generate_and_wait(dlg)
  rt._tick(200)

  # THE PIN, written exactly as the suite's own pin tests write it
  dlg._pinned_bounds.setdefault(tid, {})["pct"] = dict(pins)
  dlg._apply_style_change()
  rt._tick(250)
  element = project.mapLayer(dlg._element_layer_ids[tid])
  assert dlg._pins_in_force(tid, "pct") == len(pins), "PREMISE: no pin"
  first = ladder(element)
  assert abs(first[0][1] - pins["low"]) < 1e-6, \
      f"PREMISE: the pin is not on the map: {first}"

  if edit_in_qgis is not None:
    clone = element.renderer().clone()
    edit_in_qgis(clone, element)
    element.setRenderer(clone)
    element.styleChanged.emit()
    element.triggerRepaint()
    rt._tick(500)
    element = project.mapLayer(dlg._element_layer_ids[tid])

  mid_ladder = ladder(element)
  mid_record = dict(dlg._pinned_bounds.get(tid, {}).get("pct") or {})
  mid_pins = dlg._pins_in_force(tid, "pct")

  said_from = len(rt.BAR_MESSAGES)
  if k_to is not None:
    spin = dlg.table.cellWidget(0, 3)
    spin.setValue(k_to)
    rt._tick(300)
  msgs = list(rt.BAR_MESSAGES[said_from:])

  out = dict(mid_ladder=mid_ladder, mid_record=mid_record,
             mid_pins=mid_pins, msgs=msgs,
             spin=dlg.table.cellWidget(0, 3).value(),
             krec=dlg._class_counts.get(tid),
             record=dict(dlg._pinned_bounds.get(tid, {}).get("pct") or {}),
             pins=dlg._pins_in_force(tid, "pct"))
  if do_generate:
    rt._generate_and_wait(dlg)
    rt._tick(300)
    element = project.mapLayer(dlg._element_layer_ids[tid])
    out["map"] = ladder(element) if element else None
  dlg.close()
  rt._tick(50)
  return out


def retype_the_third(r, layer):
  """Double-click range 3 in QGIS and type 60. The PIN IS NOT TOUCHED.

  Args:
    r: the renderer whose third boundary to move.
    layer: the element layer it belongs to, kept for the caller's
      convenience rather than read here.

  Returns:
    None; the renderer is mutated in place and the caller sets it
    back onto the layer.
  """
  r.updateRangeUpperValue(2, 60.0)
  r.updateRangeLowerValue(3, 60.0)


def show(title, o):
  """Print one labelled reading.

  Args:
    See the call sites; the first item is the label.

  Returns:
    None.
  """
  print(f"  {title}")
  print(f"     ladder before the spinner : {o['mid_ladder']}")
  print(f"     record before the spinner : {o['mid_record']}  "
        f"pins_in_force={o['mid_pins']}")
  print(f"     record after  the spinner : {o['record']}  "
        f"pins_in_force={o['pins']}")
  for kind, text in o["msgs"]:
    print(f"     TOLD: {text}")
  print(f"     THE MAP the next Generate draws: {o.get('map')}")


def main():
  """Run every arm and print what each leaves behind.

  Returns:
    0 always: the arms are read against each other.
  """
  app = QgsApplication([], False)
  app.initQgis()
  print("\nPIN low=25.0, Equal intervals, k=5 -> the Classes spinner to 6\n")
  show("ARM 1  no QGIS edit at all",
       arm(None, {"low": PIN}, 6))
  show("ARM 2  one OTHER boundary retyped in QGIS first",
       arm(retype_the_third, {"low": PIN}, 6))

  print("\nTWO PINS (25.0, 60.0) MEET A CLASS COUNT OF 2\n")

  def two(r, layer):
    r.updateClasses(layer, QgsGraduatedSymbolRenderer.Mode.EqualInterval, 2)
  o = arm(None, {"low": 25.0, "high": 60.0}, 2)
  show("ARM 3  by the plugin's own spinner", o)
  o = arm(two, {"low": 25.0, "high": 60.0}, None)
  print("  ARM 4  by QGIS")
  print(f"     layer QGIS left        : {o['mid_ladder']}")
  print(f"     spinner reads {o['spin']}, _class_counts says {o['krec']}, "
        f"record {o['mid_record']}")
  for kind, text in o["msgs"] + list(rt.BAR_MESSAGES[-4:]):
    print(f"     TOLD: {text}")
  print(f"     THE MAP the next Generate draws: {o.get('map')}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
