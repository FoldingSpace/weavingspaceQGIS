"""Plugin patch 6: does the interior/boundary split assign the same zone?

`get_tiled_map`'s default path clips every tile against every zone and
keeps the fragment with the largest area -- an argmax whose geometry is
then thrown away. A tile lying wholly inside ONE zone has a foregone
answer: the fragment is the tile and the winner is that zone. Patch 6
assigns those by a `within` join and clips only what is left.

WHAT IS COMPARED IS THE ZONE EACH TILE TAKES ITS DATA FROM, keyed by
the tile's own geometry, because that is the whole of what this path
decides -- and getting it wrong makes a map that looks entirely
plausible and reads the wrong numbers, which is this software's
characteristic failure.

THE ORACLE IS WRITTEN OUT HERE rather than called, so the two sides
share no code and a disagreement cannot be a fault they hold in common.
"""
import os
import sys

import geopandas as gpd
import shapely

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")
SPACINGS = (500.0, 250.0)
AREA = "my_ridiculous_area_name_42"
ID = "id"


def expected_zones(region, tiles):
  """Upstream's own answer: clip everything, keep the largest fragment.

  Args:
    region: the zones, carrying the `id` column.
    tiles: the tiling's tiles, one row per placed tile.

  Returns:
    A dict from the tile's geometry bytes to the zone id it should take
    its data from. Tiles that overlap no zone are absent, exactly as
    they are absent from the drawn map.
  """
  work = tiles[["geometry"]].copy()
  work["joinUID"] = range(len(work))
  overlaps = region.overlay(work, make_valid=False)
  overlaps[AREA] = overlaps.geometry.area
  best = overlaps.iloc[
    overlaps.groupby("joinUID")[AREA].agg("idxmax")][["joinUID", ID]]
  by_uid = dict(zip(best["joinUID"], best[ID], strict=True))
  return {shapely.to_wkb(g): by_uid[u]
          for g, u in zip(work.geometry, work["joinUID"], strict=True)
          if u in by_uid}


def main():
  """Drive the product and compare its zone assignment against the oracle."""
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  from weavingspace import Tiling
  from weavingspace_qgis import catalog

  region = gpd.read_file(REGION)
  assert ID in region.columns, f"PREMISE: the region has no {ID!r} column"
  crs = region.crs.to_epsg()
  designs = catalog.TILINGS_BY_N[4]
  names = sorted(designs)[: int(os.environ.get("WEAVINGSPACE_CASES", "6"))]

  print(f"{'design':<24} {'spacing':>7} {'tiles':>7} {'interior':>9} "
        f"{'compared':>9}  agree?")
  compared = disagreed = missing = 0
  shares = []
  for name in names:
    for spacing in SPACINGS:
      unit = catalog.make_unit(designs[name], spacing=spacing, crs=crs)
      tiling = Tiling(unit, region, rotations=(0.0,))
      want = expected_zones(region, tiling.tiles)
      drawn = tiling.get_tiled_map(rotation=0.0).map
      inside = tiling.tiles.sjoin(region, predicate="within", how="inner")
      shares.append(len(inside) / max(len(tiling.tiles), 1))

      here = bad = 0
      for row in drawn.itertuples():
        key = shapely.to_wkb(row.geometry)
        if key not in want:
          missing += 1
          continue
        here += 1
        if want[key] != getattr(row, ID):
          bad += 1
      compared += here
      disagreed += bad
      assert here > 100, \
        f"PREMISE: only {here} tiles compared for {name} at {spacing}"
      print(f"{name:<24} {spacing:>7.0f} {len(tiling.tiles):>7} "
            f"{len(inside):>9} {here:>9}  "
            f"{'identical' if bad == 0 else f'{bad} DIFFER'}")

  print(f"\n{compared} tile(s) compared, {disagreed} assigned differently, "
        f"{missing} drawn tiles the oracle did not place")
  print(f"interior share of all tiles: "
        f"{100 * sum(shares) / len(shares):.1f}% on average")
  assert compared, "nothing was compared, so this says nothing"
  assert disagreed == 0, f"{disagreed} tiles take their data from a different zone"
  print("\nPROBE COMPLETE: every drawn tile takes the zone the clip would give it.")


main()
