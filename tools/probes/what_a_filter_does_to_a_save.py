"""What does a Save write when an element layer carries a filter?

A hunt reported on 2026-09-02 that setting a filter on an element
layer in QGIS makes the next Save delete every tile the filter hides
from the saved GeoPackage, permanently, while the plugin says "Saved".

TWO SETTLED RULES MEET AT ONE PRESS. A layer already reading from the
destination table is SKIPPED as saved already (`dialog.py`, the
`already` list), and identity is `same_source`, which compares the
WHOLE tail of a source string. A filter puts `|subset=...` in that
tail, so the skip cannot match, and the layer goes down the WRITE path
instead -- into the table it is reading from, through
`getFeatures()`, which honours the filter.

AND THE PLUGIN'S OWN WORDS SAY WHICH OF THE TWO A FILTER IS. Where a
re-tile carries a person's filter onto the new layer, the comment at
that line calls a subset something that "says which features to
DRAW". A view, then, rather than a fact about which tiles the map has
-- which is what makes writing the filtered set a loss rather than an
interpretation.

THREE ARMS, one process, each on its own file, and the third is the
one the hunt did not drive:
  CONTROL   two saves with no filter -- the counts must not move, or
            the arms below measure a save that never worked;
  SECOND    a filter set between two saves, which is the claim;
  RE-TILED  a filter set, then the design changed so every element
            gets a NEW memory layer carrying that filter forward, then
            saved. No skip can fire there, so it asks whether the harm
            needs the skip at all.

READ THROUGH OGR, released at once, because the writer is what is
under test and a reader that goes through the plugin would share it.
"""
import sys

import probe_kit

sys.path.insert(0, probe_kit._repo_root())

from qgis.PyQt.QtWidgets import QApplication  # noqa: E402
from osgeo import ogr  # noqa: E402


def counts(path):
  """How many features each element table holds.

  Args:
    path: the GeoPackage to read.

  Returns:
    {table name: feature count} over the `tiles_` tables, empty where
    the file will not open. The data source is released at once, since
    a held handle changes what the next reading sees.
  """
  source = ogr.Open(path)
  if source is None:
    return {}
  found = {}
  for index in range(source.GetLayerCount()):
    layer = source.GetLayerByIndex(index)
    name = layer.GetName()
    if name.startswith("tiles_"):
      found[name] = layer.GetFeatureCount()
  source = None
  return found


def run_one_arm(probe, name, how):
  """Save, filter, save again, and report what the file holds.

  Args:
    probe: the probe kit's handle.
    name: the arm's name, which is also its file's name.
    how: "none" for the control, "second" to filter between two saves,
      "retiled" to filter and then change the design before saving.

  Returns:
    A dict of the counts before and after, the filter used, and where
    the filtered layer was reading from at the moment of the second
    press -- which is what the skip compares.
  """
  probe.clear()
  dlg, _layer, _tile_id = probe.dialog()
  dlg.live_check.setChecked(False)
  dlg.show()
  probe.generate(dlg, spacing=700.0)
  path = probe.path(f"{name}.gpkg")
  assert probe.save(dlg, path), f"PREMISE: {name}'s first save wrote nothing"
  before = counts(path)
  assert before, f"PREMISE: {name} holds no element tables to lose"

  from qgis.core import QgsProject
  target = None
  reading = None
  if how != "none":
    # THE FILTER IS SET THE WAY QGIS SETS ONE, on the layer itself,
    # which is what the Query Builder in Layer Properties does.
    for layer_id in dlg._element_layer_ids.values():
      found = QgsProject.instance().mapLayer(layer_id)
      if found is None:
        continue
      target = found
      break
    assert target is not None, "PREMISE: no element layer to filter"
    target.setSubsetString('"weavingspace_fid" <= 3')
    for _ in range(20):
      QApplication.processEvents()

  if how == "retiled":
    # A RE-TILE GIVES EVERY ELEMENT A NEW MEMORY LAYER, and the plugin
    # carries the person's filter onto it deliberately. No layer then
    # reads from the file, so the skip cannot fire and this arm asks
    # whether the loss needs it.
    dlg.spacing_spin.setValue(dlg.spacing_spin.value() * 0.9)
    for _ in range(20):
      QApplication.processEvents()
    dlg._generate()
    probe.suite._settle(dlg)

  if target is not None:
    still = QgsProject.instance().mapLayer(
      list(dlg._element_layer_ids.values())[0])
    reading = still.source() if still is not None else None

  probe.save(dlg, path, overwrite=True)
  for _ in range(40):
    QApplication.processEvents()
  after = counts(path)
  return {
    "before": before,
    "after": after,
    "reading at the second press": reading,
    "lost": {k: (before.get(k), after.get(k))
             for k in before
             if after.get(k, 0) < before.get(k, 0)},
  }


def main():
  """Drive the three arms and say whether the claim reproduces.

  Returns:
    None; everything is printed, and the last line is a sentinel.
  """
  probe = probe_kit.start()

  control = run_one_arm(probe, "control", "none")
  print("=== CONTROL: two saves, no filter ===")
  for key, value in control.items():
    print(f"    {key}: {value}")
  assert not control["lost"], (
    "PREMISE: an ordinary second save already lost features, so this "
    "probe cannot say anything about filters")

  second = run_one_arm(probe, "second", "second")
  print("=== SECOND: a filter set between two saves ===")
  for key, value in second.items():
    print(f"    {key}: {value}")

  retiled = run_one_arm(probe, "retiled", "retiled")
  print("=== RE-TILED: filtered, then the design changed ===")
  for key, value in retiled.items():
    print(f"    {key}: {value}")

  print()
  if second["lost"] or retiled["lost"]:
    print(f"CLAIM REPRODUCES: the second-save arm lost "
          f"{len(second['lost'])} table(s) and the re-tiled arm "
          f"{len(retiled['lost'])}, so a filter is being written into "
          f"the file as though it were the map")
  else:
    print("A FILTER IS A VIEW: no table lost features on either arm")
  print("every arm reported; teardown next")


if __name__ == "__main__":
  main()
