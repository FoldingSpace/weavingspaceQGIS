"""How many tiles change side when the mapped variable changes?

The question decides whether a variable switch can be answered by
rewriting a column in place, or has to rebuild the layer: a tile that
crosses the no-data boundary MOVES between the element layer and its
twin, and moving is the expensive half.

ASKED OF THE PRODUCT'S OWN SPLIT, not of a reimplementation of it.
`bridge.split_out_the_no_data` is what decides this at run time, so a
second copy of the rule here would measure the copy.
"""
import os, sys
sys.path.insert(0, os.getcwd())
from qgis.core import QgsApplication, QgsVectorLayer

QgsApplication.setPrefixPath(os.environ.get("QGIS_PREFIX_PATH", ""), True)
app = QgsApplication([], False)
app.initQgis()

from weavingspace_qgis import deps
deps.add_paths()                      # vendor and libs, as the plugin does
from weavingspace_qgis import bridge, catalog

FIELDS = ["population", "imd", "employment", "income", "crime"]
path = os.path.join("tests", "data", "imd-auckland-sa2-2018.gpkg")
layer = QgsVectorLayer(path, "ak", "ogr")
assert layer.isValid(), "PREMISE: the packaged data will not open"
region = bridge.layer_to_gdf(layer, FIELDS)
print(f"region: {len(region)} areas, crs {region.crs.to_epsg()}")

for spacing in (500.0, 250.0):
  designs = catalog.TILINGS_BY_N[4]
  unit = catalog.make_unit(designs["crosses 4"], spacing=spacing,
                           crs=region.crs.to_epsg())
  from weavingspace import Tiling
  tiled = Tiling(unit, region).get_tiled_map(prioritise_tiles=True)
  frame = tiled.map
  print(f"\n=== spacing {spacing:.0f}: {len(frame)} tiles ===")

  absent_of = {}
  for field in FIELDS:
    drawable, absent = bridge.split_out_the_no_data(frame, field)
    absent_of[field] = set() if absent is None else set(absent.index)
    share = len(absent_of[field]) / len(frame) * 100
    print(f"  {field:<12} no-data tiles {len(absent_of[field]):>6}  "
          f"({share:.1f}%)")

  print("  crossings, as a share of all tiles:")
  worst = 0.0
  for one in FIELDS:
    for two in FIELDS:
      if one >= two:
        continue
      crossing = absent_of[one] ^ absent_of[two]
      share = len(crossing) / len(frame) * 100
      worst = max(worst, share)
      print(f"    {one:<11} -> {two:<11} {len(crossing):>6} "
            f"({share:.1f}%)")
  print(f"  WORST PAIR: {worst:.1f}% of tiles change side")


# A SECOND ARM, because the packaged data cannot exhibit the case: its
# nulls sit in the SAME areas for every variable, so every pair crosses
# zero tiles and the fixture proves only that it cannot tell a small
# number from none. Here each variable loses a DIFFERENT tenth of the
# areas, which is the shape a real multi-source dataset has -- a census
# table joined to a health table joined to a crime table, each with its
# own suppressed cells.
print("\n=== synthetic arm: each variable null in a different tenth ===")
import numpy as np
rng = np.random.default_rng(20260905)
spoiled = region.copy()
for index, field in enumerate(FIELDS):
  hurt = rng.choice(len(spoiled), size=max(1, len(spoiled) // 10),
                    replace=False)
  spoiled.loc[spoiled.index[hurt], field] = np.nan
unit = catalog.make_unit(catalog.TILINGS_BY_N[4]["crosses 4"],
                         spacing=250.0, crs=spoiled.crs.to_epsg())
tiled = Tiling(unit, spoiled).get_tiled_map(prioritise_tiles=True)
frame = tiled.map
absent_of = {}
for field in FIELDS:
  _drawable, absent = bridge.split_out_the_no_data(frame, field)
  absent_of[field] = set() if absent is None else set(absent.index)
  print(f"  {field:<12} no-data {len(absent_of[field]):>6} "
        f"({len(absent_of[field]) / len(frame) * 100:.1f}%)")
worst = 0.0
for one in FIELDS:
  for two in FIELDS:
    if one >= two:
      continue
    share = len(absent_of[one] ^ absent_of[two]) / len(frame) * 100
    worst = max(worst, share)
print(f"  of {len(frame)} tiles, WORST PAIR crosses {worst:.1f}%")
