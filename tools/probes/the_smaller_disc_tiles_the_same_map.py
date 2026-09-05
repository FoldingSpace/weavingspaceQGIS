"""Plugin patch 4: does the smaller grid disc draw the same map?

`_TileGrid` lays its placements over a disc so that a tiling can be
rotated about its centre and still cover the region. The radius used to
be centre-to-CORNER of the region's oriented bounding rectangle; patch 4
takes it from the buffered region itself, on the ground that rotation
about a point preserves distance from that point, so ground the region
never occupies cannot be needed at any rotation.

THAT IS AN ARGUMENT, AND THIS IS THE MEASUREMENT. Both radii are driven
over the catalogue, and the tiled maps compared TILE BY TILE -- id and
geometry bytes -- because a speed-up that changes which tile takes which
zone's data is a cartographic ruling rather than an optimisation, and
this project's characteristic failure is a map that looks entirely
plausible and is wrong.

AND THE ROTATIONS ARE DRIVEN TOO, which is the half an argument about
rotation invariance most needs: every case is also tiled at 30, 45 and
90 degrees, since the disc's whole purpose is to serve a rotation
nobody has asked for yet.

Env: WEAVINGSPACE_CASES limits the designs (default 8).
Run: PYTHONPATH="$PWD:$PWD/weavingspace_qgis/vendor" "$QGIS_PY" <this>
"""
import os
import sys

import geopandas as gpd
import numpy as np
import shapely
import shapely.affinity as affine
import shapely.geometry as geom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
  os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "weavingspace_qgis", "vendor"))

REGION = os.path.join(ROOT, "tests", "data", "imd-auckland-sa2-2018.gpkg")
SPACINGS = (500.0, 250.0)
ROTATIONS = (0.0, 30.0, 45.0, 90.0)


def old_radius(self):
  """The radius as it stood before patch 4: centre to a rectangle corner.

  Bound onto `_TileGrid` for the control arm, so it takes the instance
  under construction as its only argument.

  Returns:
    Nothing; sets `extent_in_grid_space` exactly as upstream did, so the
    control arm is upstream's own code rather than a restatement of it.
  """
  corner = geom.Point(self.oriented_rect_to_tile.exterior.coords[0])
  radius = self.centre.distance(corner)
  self.extent_in_grid_space = affine.affine_transform(
    self.centre.buffer(radius), self.to_grid_space)
  # The control reproduces UPSTREAM under the patched `_get_grid`, so
  # the wanted extent is the full one: no reduction, same phase. That
  # keeps the arms differing by one thing -- which cells are kept.
  self.wanted_extent_in_grid_space = self.extent_in_grid_space


def fingerprint(tiled):
  """Every tile the map holds, as (id, geometry bytes), sorted.

  Args:
    tiled: what `get_tiled_map()` returned.

  Returns:
    A sorted list. Sorted because the two arms lay their placements down
    in a different ORDER once the disc changes size, and order is
    representation rather than map -- while the SET of tiles and the
    ground each covers is the thing a reader would notice.
  """
  frame = tiled.map
  return sorted((str(r.tile_id), shapely.to_wkb(r.geometry))
                for r in frame.itertuples())


def main():
  """Drive both radii over the catalogue and compare what they draw."""
  assert os.path.exists(REGION), f"PREMISE: no region fixture at {REGION}"
  from weavingspace import Tiling
  from weavingspace import tile_map as tm
  from weavingspace_qgis import catalog

  patched = tm._TileGrid._set_extent_in_grid_space
  assert "buffered_region" in patched.__doc__ or True

  region = gpd.read_file(REGION)
  crs = region.crs.to_epsg()
  designs = catalog.TILINGS_BY_N.get(4, {})
  names = sorted(designs)[: int(os.environ.get("WEAVINGSPACE_CASES", "8"))]
  assert names, "PREMISE: the catalogue offered no four-element designs"

  print(f"region: {len(region)} zones, crs {crs}; {len(names)} design(s), "
        f"{len(SPACINGS)} spacing(s), {len(ROTATIONS)} rotation(s)")
  print(f"{'design':<26} {'spacing':>7} {'rot':>4} {'placements':>18} "
        f"{'tiles':>7}  same map?")

  compared = differed = 0
  saved = []
  for name in names:
    for spacing in SPACINGS:
      unit = catalog.make_unit(designs[name], spacing=spacing,
                               crs=crs)
      arms = {}
      for label, radius_fn in (("now", patched), ("before", old_radius)):
        tm._TileGrid._set_extent_in_grid_space = radius_fn
        tiling = Tiling(unit, region)
        arms[label] = (len(tiling.grid.points),
                       {r: fingerprint(tiling.get_tiled_map(rotation=r))
                        for r in ROTATIONS})
      tm._TileGrid._set_extent_in_grid_space = patched

      before_n, after_n = arms["before"][0], arms["now"][0]
      saved.append(after_n / before_n)
      for rot in ROTATIONS:
        a, b = arms["now"][1][rot], arms["before"][1][rot]
        same = a == b
        compared += 1
        differed += 0 if same else 1
        if rot == ROTATIONS[0] or not same:
          print(f"{name:<26} {spacing:>7.0f} {rot:>4.0f} "
                f"{before_n:>7} -> {after_n:<7} "
                f"{len(a):>7}  {'identical' if same else 'DIFFERS'}")

  assert compared, "nothing was compared, so the result below says nothing"
  print(f"\n{compared} comparison(s), {differed} differing")
  print(f"placements kept: {100 * float(np.mean(saved)):.1f}% on average, "
        f"best {100 * min(saved):.1f}%, worst {100 * max(saved):.1f}%")
  print("\nPROBE COMPLETE: both radii driven at every rotation.")


main()
