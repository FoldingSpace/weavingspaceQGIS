"""Do the common names we show match the geometry the library builds?

A label is a claim about mathematics made in the software's own voice,
and these twelve were written from standard usage rather than checked
against a source. Each name PREDICTS something measurable: an
Archimedean tiling's vertex configuration says which regular polygons
meet at a vertex, and a Laves tiling is the dual of the Archimedean
with the same symbol, so its tiles are all of one kind with a
predictable number of corners.

This builds each entry through `catalog.make_unit` -- the door the
dialog uses -- and prints what it actually holds: the corner counts of
its tiles, whether those tiles are regular, and how many distinct
shapes there are. The reader can then compare that against the name.
"""
import math
import os
import sys

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))
from tools import probe_kit                                # noqa: E402

probe = probe_kit.start()

from weavingspace_qgis import catalog                      # noqa: E402

NAMED = {
  "archimedean 3.12.12": ("truncated hexagonal", "triangles and 12-gons"),
  "archimedean 3.3.3.3.6": ("snub hexagonal", "triangles and hexagons"),
  "archimedean 3.3.3.4.4": ("elongated triangular", "triangles and squares"),
  "archimedean 3.3.4.3.4": ("snub square", "triangles and squares"),
  "archimedean 3.4.6.4": ("rhombitrihexagonal",
                          "triangles, squares and hexagons"),
  "archimedean 3.6.3.6": ("trihexagonal", "triangles and hexagons"),
  "archimedean 4.6.12": ("truncated trihexagonal",
                         "squares, hexagons and 12-gons"),
  "archimedean 4.8.8": ("truncated square", "squares and octagons"),
  "laves 3.12.12": ("triakis triangular", "triangles only"),
  "laves 3.3.3.3.6": ("floret pentagonal", "pentagons only"),
  "laves 3.3.3.4.4": ("prismatic pentagonal", "pentagons only"),
  "laves 3.3.4.3.4": ("cairo", "pentagons only"),
}


def corners(polygon):
  """How many corners a tile has, ignoring the repeated last point."""
  return len(polygon.exterior.coords) - 1


def regular(polygon) -> bool:
  """Is this tile a regular polygon, to a tenth of a percent?"""
  ring = list(polygon.exterior.coords)[:-1]
  sides = [math.dist(ring[i], ring[(i + 1) % len(ring)])
           for i in range(len(ring))]
  return max(sides) - min(sides) < 0.001 * max(sides)


print(f"{'catalogue key':24s} {'name shown':24s} {'corners found':22s} "
      f"{'regular':8s} {'name predicts'}")
for key, (common, predicts) in NAMED.items():
  found = None
  for n, entries in catalog.TILINGS_BY_N.items():
    if key in entries:
      found = (n, entries[key])
      break
  if found is None:
    print(f"{key:24s} NOT IN THE CATALOGUE")
    continue
  unit = catalog.make_unit(found[1], spacing=500, crs=3857)
  counts = sorted(corners(g) for g in unit.tiles.geometry)
  every = all(regular(g) for g in unit.tiles.geometry)
  print(f"{key:24s} {common:24s} {str(counts):22s} "
        f"{'yes' if every else 'no ':8s} {predicts}")
