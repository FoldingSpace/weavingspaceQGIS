"""What each of the three approaches COSTS TO RUN, in seconds.

A complexity bound is a shape, not a price. Both alternatives to what
we do are small enough to implement roughly and time, so this times
all three on the same designs on one machine:

  1. WHAT WE DO. `topology_edits.build`, the whole Topology.

  2. A WALLPAPER-STYLE DETECTION, written here. It works MODULO THE
     LATTICE, which removes the boundary problem that makes a finite
     patch awkward: reduce every vertex to the fundamental cell, and a
     candidate isometry is a symmetry exactly when the reduced point
     set maps onto itself. Candidate centres are the vertices, the
     edge midpoints and the tile centres; candidate orders are 2, 3,
     4 and 6, which is the whole of what a repeating pattern admits;
     candidate mirrors run through those centres along the lattice
     directions and their bisectors.

  3. THE COMBINATORIAL STRUCTURE a Delaney-Dress symbol is built on:
     four chambers per edge, with the two involutions that the
     incidence gives directly.

WHAT IS AND IS NOT TIMED, said plainly so the figures are not read for
more than they are. (2) tests the VERTEX SET only, so it would accept
a motion that moves an edge while fixing every vertex, which a full
implementation would catch by testing edges too; it also omits glide
reflections. (3) builds the chambers and the two involutions the
incidence answers directly, and stops short of the canonical form,
which is the O(D^2) step. Both are therefore LOWER BOUNDS on a real
implementation, and the document says so where it quotes them.

    cd <checkout> && PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 \\
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \\
      tools/probes/what_the_three_symmetry_approaches_cost.py

MEASURED 2026-09-01 over ten designs: ours 0.29 to 19.08 seconds, the
wallpaper enumeration 3.6 to 23.8 milliseconds, the chamber build 0.35
to 1.17 milliseconds. The ratio between the first two grows from 50 on
the smallest design to 803 on the largest, which is the complexity
difference arriving as wall clock.
"""
import math
import os
import sys
import time

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))

from tools import probe_kit                                # noqa: E402

probe = probe_kit.start()

import numpy as np                                         # noqa: E402
from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

DESIGNS = (("laves 3.3.4.3.4", 4), ("hex-slice", 3), ("hex-slice", 4),
           ("hex-slice", 6), ("archimedean 4.8.8", 2),
           ("archimedean 3.12.12", 3), ("archimedean 3.6.3.6", 3),
           ("square-colouring", 5), ("hex-colouring", 4),
           ("hex-colouring", 7))

TOLERANCE = 1e-6


def lattice_of(unit):
  """The two shortest independent translations of the repeat.

  Args:
    unit: a Tileable.

  Returns:
    A pair of (x, y) tuples, or None where the tileable states fewer
    than two independent vectors. Asked of the VALUES rather than the
    keys, since a hex tileable keys them by three-element coordinates
    and a square one by pairs.
  """
  vectors = getattr(unit, "vectors", None) or {}
  candidates = sorted((tuple(float(c) for c in v) for v in vectors.values()),
                      key=lambda v: v[0] * v[0] + v[1] * v[1])
  first = second = None
  for candidate in candidates:
    if abs(candidate[0]) < 1e-12 and abs(candidate[1]) < 1e-12:
      continue
    if first is None:
      first = candidate
      continue
    cross = first[0] * candidate[1] - first[1] * candidate[0]
    if abs(cross) > 1e-9:
      second = candidate
      break
  return None if second is None else (first, second)


def reducer(basis):
  """A function taking a point to its cell coordinates, rounded.

  Args:
    basis: the two lattice vectors.

  Returns:
    A callable mapping (x, y) to a hashable pair of integers, being
    the fractional position within the cell at the working tolerance.
    Working modulo the lattice is what lets a finite patch answer a
    question about an infinite tiling.
  """
  matrix = np.array([[basis[0][0], basis[1][0]],
                     [basis[0][1], basis[1][1]]], dtype=float)
  inverse = np.linalg.inv(matrix)
  places = 6

  def reduce(point):
    coordinates = inverse @ np.array([point[0], point[1]], dtype=float)
    fractional = coordinates - np.floor(coordinates)
    # a coordinate a hair under 1 is a coordinate at 0
    fractional = np.where(fractional > 1 - 1e-9, 0.0, fractional)
    return (round(float(fractional[0]), places),
            round(float(fractional[1]), places))

  return reduce


def wallpaper_symmetries(unit):
  """Find the symmetries by bounded enumeration, modulo the lattice.

  Args:
    unit: a Tileable.

  Returns:
    (count, tested) -- how many candidate isometries turned out to be
    symmetries of the vertex set, and how many were tried.
  """
  basis = lattice_of(unit)
  if basis is None:
    return 0, 0
  reduce = reducer(basis)
  points = []
  for geometry in unit.tiles.geometry:
    points.extend(list(geometry.exterior.coords)[:-1])
  reduced = {reduce(p) for p in points}

  centres = list(points)
  for geometry in unit.tiles.geometry:
    centres.append((geometry.centroid.x, geometry.centroid.y))
    ring = list(geometry.exterior.coords)
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
      centres.append(((ax + bx) / 2, (ay + by) / 2))

  def holds(matrix, offset):
    """Does this isometry carry the reduced point set onto itself?"""
    for point in points:
      x = matrix[0][0] * point[0] + matrix[0][1] * point[1] + offset[0]
      y = matrix[1][0] * point[0] + matrix[1][1] * point[1] + offset[1]
      if reduce((x, y)) not in reduced:
        return False
    return True

  found = tested = 0
  directions = [basis[0], basis[1],
                (basis[0][0] + basis[1][0], basis[0][1] + basis[1][1]),
                (basis[0][0] - basis[1][0], basis[0][1] - basis[1][1])]
  for centre in centres:
    for order in (2, 3, 4, 6):
      angle = 2 * math.pi / order
      cos, sin = math.cos(angle), math.sin(angle)
      matrix = ((cos, -sin), (sin, cos))
      offset = (centre[0] - cos * centre[0] + sin * centre[1],
                centre[1] - sin * centre[0] - cos * centre[1])
      tested += 1
      if holds(matrix, offset):
        found += 1
    for direction in directions:
      length = math.hypot(direction[0], direction[1])
      if length < 1e-12:
        continue
      ux, uy = direction[0] / length, direction[1] / length
      matrix = ((ux * ux - uy * uy, 2 * ux * uy),
                (2 * ux * uy, uy * uy - ux * ux))
      offset = (centre[0] - matrix[0][0] * centre[0] - matrix[0][1] * centre[1],
                centre[1] - matrix[1][0] * centre[0] - matrix[1][1] * centre[1])
      tested += 1
      if holds(matrix, offset):
        found += 1
  return found, tested


def chambers_of(topology):
  """Build the chambers and the two involutions the incidence gives.

  Args:
    topology: a built Topology.

  Returns:
    (chambers, swaps) -- how many chambers the barycentric
    subdivision has, and how many neighbour pairs were recorded.
    Four chambers per edge, one per (endpoint, side) pair; `s0` swaps
    the endpoint and `s2` swaps the tile, and both are table lookups
    over incidence this object already holds. The canonical form,
    which is the quadratic step, is NOT built here.
  """
  chambers = {}
  for key, edge in topology.edges.items():
    ends = list(getattr(edge, "vertices", []) or [])[:2]
    sides = [getattr(edge, "left_tile", None), getattr(edge, "right_tile", None)]
    for end in ends or [None]:
      for side in sides:
        chambers[(key, end, side)] = len(chambers)
  swaps = 0
  for (key, end, side) in chambers:
    edge = topology.edges[key]
    ends = list(getattr(edge, "vertices", []) or [])[:2]
    other_end = next((e for e in ends if e != end), end)
    if (key, other_end, side) in chambers:
      swaps += 1                                   # s0, the vertex swap
    sides = [getattr(edge, "left_tile", None), getattr(edge, "right_tile", None)]
    other_side = next((s for s in sides if s != side), side)
    if (key, end, other_side) in chambers:
      swaps += 1                                   # s2, the tile swap
  return len(chambers), swaps


print(f"{'design':24s} {'ours s':>8s} {'wallpaper s':>12s} {'chambers s':>11s} "
      f"{'ours/wall':>10s} {'syms':>6s} {'tried':>6s} {'chambers':>9s}")
for family, n in DESIGNS:
  named = [k for k in catalog.TILINGS_BY_N.get(n, {}) if k.startswith(family)]
  if not named:
    continue
  unit = catalog.make_unit(catalog.TILINGS_BY_N[n][named[0]],
                           spacing=500, crs=3857)
  started = time.monotonic()
  topology, why = te.build(unit)
  ours = time.monotonic() - started
  if topology is None:
    print(f"{family + ' ' + str(n):24s}  no topology ({why})")
    continue

  started = time.monotonic()
  found, tried = wallpaper_symmetries(unit)
  wallpaper = time.monotonic() - started

  started = time.monotonic()
  chambers, swaps = chambers_of(topology)
  combinatorial = time.monotonic() - started

  print(f"{family + ' ' + str(n):24s} {ours:8.2f} {wallpaper:12.4f} "
        f"{combinatorial:11.5f} {ours / max(wallpaper, 1e-9):10.0f} "
        f"{found:6d} {tried:6d} {chambers:9d}")
