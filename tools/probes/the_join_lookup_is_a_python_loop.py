"""Three checks before treating the one-word tiling speed-up as real.

Measured 2026-08-31: `get_tiled_map` spends over half its time in
`_aggregate_series_pure_python`, because `tile_map.py` passes the
FUNCTION `pd.Series.idxmax` to `.agg()`, which defeats pandas' cython
path and walks every group in Python.

  1. does the saving hold across region sizes, or is it one fixture?
  2. do the two forms break TIES the same way -- two tiles covering a
     zone equally is not exotic on a regular tiling over a rectangle;
  3. and is `overlay` itself doing something avoidable, since it is the
     other half of the cost?
"""
import os, sys, time
ROOT = os.getcwd(); sys.path.insert(0, ROOT)
from weavingspace_qgis import deps; deps.add_paths()
from weavingspace_qgis import catalog
import geopandas as gpd, pandas as pd, numpy as np
from weavingspace import Tiling

d = gpd.read_file("tests/data/imd-auckland-sa2-2018.gpkg")

print("=== 1. across sizes ===")
for spacing in (400.0, 250.0, 150.0, 100.0):
  unit = catalog.make_unit(catalog.TILINGS_BY_N[4]["laves 3.3.4.3.4"],
                           spacing=spacing, crs=d.crs)
  tiling = Tiling(unit, d)
  tiles = tiling.tiles.copy()
  tiles["joinUID"] = np.arange(len(tiles))
  overlaps = d.overlay(tiles, make_valid=False)
  overlaps["area"] = overlaps.geometry.area
  t0 = time.perf_counter()
  slow = overlaps.groupby("joinUID")["area"].agg(pd.Series.idxmax)
  t1 = time.perf_counter()
  fast = overlaps.groupby("joinUID")["area"].idxmax()
  t2 = time.perf_counter()
  assert slow.equals(fast), "the two forms disagreed on real data"
  print(f"  spacing {spacing:5.0f}  {len(tiles):7d} tiles  "
        f"{len(overlaps):7d} overlaps  {overlaps['joinUID'].nunique():7d} groups"
        f"   slow {t1-t0:6.3f}s  fast {t2-t1:6.3f}s  "
        f"{(t1-t0)/max(t2-t1,1e-9):5.0f}x")

print("\n=== 2. ties ===")
# EXACT TIES, STAGED RATHER THAN HOPED FOR. Real areas rarely tie to
# the last bit, so a run over real data says nothing about this: the
# case is built.
frame = pd.DataFrame({
  "joinUID": [1, 1, 1, 2, 2, 3, 3, 3],
  "area":    [5.0, 9.0, 9.0, 4.0, 4.0, 1.0, 7.0, 7.0],
  "id_var":  list("abcdefgh")})
slow = frame.groupby("joinUID")["area"].agg(pd.Series.idxmax)
fast = frame.groupby("joinUID")["area"].idxmax()
named = frame.groupby("joinUID")["area"].agg("idxmax")
print(f"  callable : {list(slow)}")
print(f"  method   : {list(fast)}   same: {slow.equals(fast)}")
print(f"  string   : {list(named)}   same: {slow.equals(named)}")
print("  (each index is the row the join would take for that group)")

print("\n=== 3. what overlay costs, and whether it is avoidable ===")
unit = catalog.make_unit(catalog.TILINGS_BY_N[4]["laves 3.3.4.3.4"],
                         spacing=100.0, crs=d.crs)
tiling = Tiling(unit, d)
tiles = tiling.tiles.copy()
tiles["joinUID"] = np.arange(len(tiles))
t0 = time.perf_counter(); overlaps = d.overlay(tiles, make_valid=False)
t1 = time.perf_counter()
print(f"  overlay              {t1-t0:6.2f}s  -> {len(overlaps)} rows")
# The cheaper question a lookup actually needs: which zone contains
# each tile's REPRESENTATIVE POINT. It cannot answer "largest share"
# for a tile straddling two zones, so it is a different rule rather
# than a faster one -- measured here to say what the difference costs
# and how often it would decide differently.
t2 = time.perf_counter()
pts = tiles.copy()
pts["geometry"] = tiles.geometry.representative_point()
by_point = gpd.sjoin(pts, d, predicate="within", how="left")
t3 = time.perf_counter()
print(f"  sjoin on centroids   {t3-t2:6.2f}s  -> {len(by_point)} rows")
straddlers = len(overlaps) - overlaps["joinUID"].nunique()
print(f"  tiles straddling a zone boundary: {straddlers} of "
      f"{len(tiles)} ({straddlers / max(len(tiles),1) * 100:.1f}%), "
      f"so that is how often the two rules could disagree")
