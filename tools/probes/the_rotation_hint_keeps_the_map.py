"""Plugin patch 5: does naming the rotations keep the same map?

`Tiling` can be told which rotations it will ever be asked for. Told
none, it lays its grid over every radius the region reaches, which is
patch 4. Told `(0,)`, it can ask the region's own SHAPE instead of a
disc, which is the larger reduction -- and the plugin can honestly say
`(0,)` because it rotates the UNIT through the Rotate modifier, before
the grid is laid, and never passes a rotation to `get_tiled_map`.

THE HINT IS A PROMISE THE CALLER CAN BREAK, so this drives the
negative control too: a tiling told `(0,)` and then asked for 30
degrees SHOULD come back short. A probe that only showed the happy arm
would be evidence that the hint is free rather than that it is sound.
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


def fingerprint(tiled):
  """Every tile the map holds, as (id, geometry bytes), sorted.

  Args:
    tiled: what `get_tiled_map()` returned.

  Returns:
    A sorted list, because the arms lay their placements down in a
    different order once the wanted ground changes shape, and order is
    representation rather than map.
  """
  return sorted((str(r.tile_id), shapely.to_wkb(r.geometry))
                for r in tiled.map.itertuples())


def main():
  """Drive the hint honestly, and then dishonestly."""
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  from weavingspace import Tiling
  from weavingspace_qgis import catalog

  region = gpd.read_file(REGION)
  crs = region.crs.to_epsg()
  designs = catalog.TILINGS_BY_N[4]
  names = sorted(designs)[: int(os.environ.get("WEAVINGSPACE_CASES", "6"))]

  print(f"region: {len(region)} zones; {len(names)} design(s)")
  print(f"{'design':<24} {'spacing':>7} {'placements':>20} {'tiles':>7}  "
        f"same map at 0?")
  compared = differed = 0
  kept = []
  for name in names:
    for spacing in SPACINGS:
      unit = catalog.make_unit(designs[name], spacing=spacing, crs=crs)
      loose = Tiling(unit, region)
      tight = Tiling(unit, region, rotations=(0.0,))
      a = fingerprint(loose.get_tiled_map(rotation=0.0))
      b = fingerprint(tight.get_tiled_map(rotation=0.0))
      same = a == b
      compared += 1
      differed += 0 if same else 1
      kept.append(len(tight.grid.points) / len(loose.grid.points))
      print(f"{name:<24} {spacing:>7.0f} "
            f"{len(loose.grid.points):>8} -> {len(tight.grid.points):<8} "
            f"{len(b):>7}  {'identical' if same else 'DIFFERS'}")

  assert compared, "nothing was compared"
  print(f"\n{compared} comparison(s) at rotation 0, {differed} differing")
  print(f"placements kept: {100 * sum(kept) / len(kept):.1f}% on average, "
        f"best {100 * min(kept):.1f}%")

  # THE NEGATIVE CONTROL. A hint that costs nothing when broken is a
  # hint nobody needs to keep, so this shows what breaking it costs.
  # THE CONTROL NEEDS A CASE THAT CAN SHOW IT. A small design at a
  # coarse spacing has few placements and a nearly round wanted area,
  # so breaking the promise costs nothing visible -- measured on
  # `basket weave ab|cd` at 500, where 30 degrees came back identical.
  # A finer spacing and a 45-degree turn is where the shortfall lives,
  # and the sweep says which cases bit rather than assuming one does.
  print("\nnegative control -- declaring only 0 and then asking for a turn:")
  bit = []
  for name in names:
    unit = catalog.make_unit(designs[name], spacing=250.0, crs=crs)
    honest = Tiling(unit, region)
    told_zero = Tiling(unit, region, rotations=(0.0,))
    for rot in (45.0, 90.0):
      a = fingerprint(honest.get_tiled_map(rotation=rot))
      b = fingerprint(told_zero.get_tiled_map(rotation=rot))
      if a != b:
        bit.append((name, rot, len(a), len(b)))
  for name, rot, n_honest, n_broken in bit[:4]:
    print(f"  {name} at {rot:.0f}deg: honest {n_honest} tiles, "
          f"told-zero {n_broken} -- SHORT, as documented")
  print(f"  {len(bit)} of {2 * len(names)} cases bit")
  assert bit, (
    "the negative control did not bite on any case: if declaring (0,) "
    "and then rotating costs nothing, the hint promises nothing and "
    "the happy arm above means nothing either")

  print("\nPROBE COMPLETE: the hint kept honestly and broken deliberately.")


main()
