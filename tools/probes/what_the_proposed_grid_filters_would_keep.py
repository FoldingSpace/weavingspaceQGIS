"""The two proposed reductions, measured at spacing 250.

Neither is built, so this measures the FACTORS they would apply rather
than a plugin that applies them: how many grid placements each filter
keeps, and what the interior/boundary split does to the overlay. The
composition into a projected column is arithmetic and is labelled as
such where it is quoted.

It reuses the committed probe's own helpers by exec'ing its source with
the trailing main() call stripped -- the probe is a script, and copying
its unit construction here would be a second definition of the thing
under test, which is the fault this project keeps recording.
"""
import os, pathlib, sys, time
import geopandas as gpd
import numpy as np
import shapely

ROOT = pathlib.Path.cwd()
src = (ROOT / "tools" / "probes" / "what_the_tiled_map_costs.py").read_text()
assert src.rstrip().endswith("main()"), "probe no longer ends in main()"
ns = {"__name__": "not_main", "__file__": str(
  ROOT / "tools" / "probes" / "what_the_tiled_map_costs.py")}
exec(compile(src.rstrip()[: -len("main()")], "probe", "exec"), ns)

REGION = ns["REGION"]
region = gpd.read_file(REGION)
SPACING = 250.0
from weavingspace import Tiling                                   # noqa: E402

unit = ns["a_unit"](SPACING, region.crs.to_epsg())
tiling = Tiling(unit, region)

# ---- (a) HOW MANY PLACEMENTS EACH FILTER KEEPS.
# Today's grid is laid over a DISC whose radius is centre-to-corner of
# the oriented bounding rectangle, so it serves any rotation. The first
# proposal keeps that promise on a smaller radius: rotation about the
# centre PRESERVES distance from the centre, so only the radii the
# region actually occupies are needed. The second knows the rotation is
# zero and can ask the region's own shape.
grid = tiling.grid
pts = getattr(grid, "points", None)
centre = region.union_all().centroid
verts = shapely.get_coordinates(region.union_all())
d = np.hypot(verts[:, 0] - centre.x, verts[:, 1] - centre.y)
reach_now = None
try:
  reach_now = float(np.max(np.hypot(
    shapely.get_coordinates(grid.extent_in_grid_space)[:, 0] - centre.x,
    shapely.get_coordinates(grid.extent_in_grid_space)[:, 1] - centre.y)))
except Exception:
  pass
reach_region = float(d.max())

# the prototile's own reach, which a tile may extend beyond its cell by
proto = unit.prototile.geometry[0]
pc = proto.centroid
pv = shapely.get_coordinates(proto)
margin = float(np.max(np.hypot(pv[:, 0] - pc.x, pv[:, 1] - pc.y)))

cells = np.array([[p.x, p.y] for p in grid.points]) if pts is not None \
  else shapely.get_coordinates(shapely.union_all(
    [shapely.Point(c) for c in []]))
dist = np.hypot(cells[:, 0] - centre.x, cells[:, 1] - centre.y)
placements_now = len(cells)
placements_any_rotation = int(np.sum(dist <= reach_region + margin))
buffered = region.union_all().buffer(margin)
placements_known = int(np.sum(shapely.contains_xy(
  buffered, cells[:, 0], cells[:, 1])))

print(f"spacing {SPACING:.0f}, {len(region)} zones")
print(f"  placements today                 {placements_now:>7}   100.0%")
print(f"  ... radius the region reaches    {placements_any_rotation:>7}   "
      f"{100 * placements_any_rotation / placements_now:5.1f}%   "
      f"(any rotation, no API change)")
print(f"  ... the region's own shape       {placements_known:>7}   "
      f"{100 * placements_known / placements_now:5.1f}%   "
      f"(rotation known to be zero)")

# ---- (b) WHAT THE SPLIT DOES TO THE OVERLAY, and whether it is exact.
tiling.get_tiled_map(join_on_prototiles=False, retain_tileables=False,
                     ragged_edges=True)
split = ns["split_and_compare"](tiling)
print()
for key, value in split.items():
  print(f"  {key}: {value:.3f}" if isinstance(value, float)
        else f"  {key}: {value}")
print("\nPROBE COMPLETE: placements and the split both measured at 250.")
