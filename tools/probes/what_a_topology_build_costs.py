"""What drives the cost of building a Topology, measured against the bound.

The derivation says the work is dominated by the ORBIT SEARCH: for
every candidate transform, every core vertex and edge is matched by a
LINEAR SCAN over the others, so the term is |S| x (V^2 + E^2) with |S|
the number of candidate transforms. Candidate generation is itself
quadratic in the core tile count and linear in corners, and the
duplicate filter is quadratic in |S|.

This measures the quantities that bound says matter -- tiles, corners,
vertices, edges, |S| -- beside the wall-clock, so the claim can be
checked rather than believed. It is a RATIO test: if the bound is the
right shape, time/(|S|(V^2+E^2)) is roughly constant across designs,
while time/n is not.

    cd <checkout> && PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 \\
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \\
      tools/probes/what_a_topology_build_costs.py

MEASURED 2026-09-01 over ten designs: per element the cost varies by a
factor of 36 and per |S|(V^2+E^2) by 3.4, so the bound is the right
shape and the residual is the tile term this ratio leaves out. It also
found a design nobody had timed -- `hex-colouring 7` at 19.8 seconds,
against the 0.75-4.4s the documents record.
"""
import os
import sys
import time

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))

from tools import probe_kit                                # noqa: E402

probe = probe_kit.start()

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

DESIGNS = (("laves 3.3.4.3.4", 4), ("hex-slice", 3), ("hex-slice", 4),
           ("hex-slice", 6), ("archimedean 4.8.8", 2),
           ("archimedean 3.12.12", 3), ("archimedean 3.6.3.6", 3),
           ("square-colouring", 5), ("hex-colouring", 4),
           ("hex-colouring", 7))


def corners_of(unit):
  """How many corners the core tiles carry between them.

  Args:
    unit: a Tileable.

  Returns:
    The total number of exterior coordinates over the unit's own
    tiles, which is the `c` the candidate generation is linear in.
  """
  total = 0
  for geometry in unit.tiles.geometry:
    total += len(geometry.exterior.coords) - 1
  return total


print(f"{'design':26s} {'n':>3s} {'c':>4s} {'|S|':>4s} {'V':>4s} {'E':>4s} "
      f"{'build s':>8s} {'s/n':>9s} {'s/|S|(V^2+E^2)':>16s}")
for family, n in DESIGNS:
  named = [k for k in catalog.TILINGS_BY_N.get(n, {}) if k.startswith(family)]
  if not named:
    print(f"{family + ' ' + str(n):26s}  not in the catalogue at this n")
    continue
  unit = catalog.make_unit(catalog.TILINGS_BY_N[n][named[0]],
                           spacing=500, crs=3857)
  started = time.monotonic()
  topology, why = te.build(unit)
  spent = time.monotonic() - started
  if topology is None:
    print(f"{family + ' ' + str(n):26s}  no topology ({why})")
    continue
  transforms = len(topology.tile_matching_transforms)
  vertices = len([v for v in topology.points.values()
                  if getattr(v, "is_tiling_vertex", False)])
  edges = len(topology.edges)
  work = transforms * (vertices ** 2 + edges ** 2)
  print(f"{family + ' ' + str(n):26s} {topology.n_tiles:3d} "
        f"{corners_of(unit):4d} {transforms:4d} {vertices:4d} {edges:4d} "
        f"{spent:8.2f} {spent / max(topology.n_tiles, 1):9.4f} "
        f"{spent / max(work, 1) * 1e6:16.4f}")
