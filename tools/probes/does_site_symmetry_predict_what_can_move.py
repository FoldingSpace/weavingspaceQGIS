"""Does a crystallographic reading predict what we measured empirically?

Three questions, all measured rather than argued:

  1. WHAT GROUP DO WE ACTUALLY FIND? The library assembles candidate
     symmetries -- the lattice translations, the prototile's own
     symmetries, each tile's, and shape matches between tiles -- and
     keeps the ones that map the tiling to itself. So it already
     computes a symmetry group; it just never names it. Print its
     size and the multiset of transform kinds, which is what a
     wallpaper group IS up to naming.

  2. DO THE ROTATION ORDERS OBEY THE CRYSTALLOGRAPHIC RESTRICTION?
     A periodic pattern admits rotations of order 2, 3, 4 and 6 only.
     If the found transforms respect that, the search space a
     wallpaper approach would enumerate is exactly the one already
     being searched blind.

  3. DOES SITE SYMMETRY PREDICT WHICH VERTEX CLASSES CAN MOVE? This
     is the one that matters. `push_vertex` was measured to move
     NOTHING on laves 3.3.4.3.4 and hex-slice 3 and 0.414 units on
     archimedean 4.8.8, and the reason recorded was "the incident
     unit vectors cancel". The crystallographic statement is
     stronger and needs no arithmetic about neighbours: a vertex
     whose STABILISER contains a rotation of order >= 2 has {0} as
     its only invariant displacement, so no equivariant manipulation
     can move it at all. If the stabiliser computed from the found
     transforms agrees with the measured displacement, the prediction
     works.

COUNTING STABILISER ELEMENTS WAS THE WRONG TEST and is recorded here
because it read exactly like a finding: it predicted that archimedean
4.8.8 cannot move, and the measurement in the same run showed it
moving by a tenth of the unit's area. What forbids a move is not that
something fixes the point but what its LINEAR PART does to a
direction, so the question became the rank of the stacked `L - I`.

    cd <checkout> && PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 \\
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \\
      tools/probes/does_site_symmetry_predict_what_can_move.py
"""
import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))

from tools import probe_kit                                # noqa: E402

probe = probe_kit.start()

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402
from weavingspace_qgis.vendor.weavingspace.symmetry import (  # noqa: E402
  Symmetries)

DESIGNS = (("laves 3.3.4.3.4", 4), ("hex-slice", 3),
           ("archimedean 4.8.8", 2), ("archimedean 3.12.12", 3), ("hex-slice", 6))


def unit_for(family, n):
  """Build a design through the door the dialog uses.

  Args:
    family: the family's name as the catalogue spells it, matched by
      prefix so a catalogue key carrying its own count still answers.
    n: the element count to look it up under.

  Returns:
    A Tileable, or None where the catalogue offers no such family at
    that count. It goes through `catalog.make_unit` rather than the
    library's own constructor because the PRODUCT is where the
    arguments are parsed and the defaults chosen -- an aspect of 0.75
    among them, which decides whether a topology can be built at all.
  """
  named = [k for k in catalog.TILINGS_BY_N.get(n, {}) if k.startswith(family)]
  if not named:
    return None
  return catalog.make_unit(catalog.TILINGS_BY_N[n][named[0]],
                           spacing=500, crs=3857)


def order_of(transform):
  """The rotation order a transform stands for, or None.

  Args:
    transform: one of the library's `Transform` objects.

  Returns:
    360 divided by the angle, or None for anything that is not a
    rotation. It is deliberately RAW: a 240 degree entry answers 1.5
    rather than 3, because these are group ELEMENTS and the powers of
    a 3-fold rotation are in the list beside it. Reduce before
    quoting an order.
  """
  if transform.transform_type != "rotation":
    return None
  angle = abs(float(transform.angle)) % 360.0
  if angle < 1e-9:
    return None
  return round(360.0 / angle, 3)


def fixed_space(topology, vertex, transforms):
  """How many directions a vertex may move in, under its site symmetry.

  Args:
    topology: the built Topology.
    vertex: one of its `points` values.
    transforms: the tile-matching transforms the library found.

  Returns:
    (dimension, description). The dimension is the rank of the space
    of displacements u with L u = u for every LINEAR part L of a
    transform that holds this vertex still. Counting stabiliser
    ELEMENTS is the wrong test and was tried first: what forbids a
    move is not that something fixes the point but what its linear
    part does to a direction. A rotation of order >= 2 leaves only
    the zero vector; a single mirror leaves the line along its axis;
    nothing leaves the plane.
  """
  import numpy as np
  import shapely.affinity as affinity
  rows = []
  kinds = []
  for transform in transforms.values():
    if transform.transform_type in ("identity", "translation"):
      continue
    moved = affinity.affine_transform(vertex.point, transform.transform)
    if moved.distance(vertex.point) > 1e-6:
      continue
    a, b, d, e = (transform.transform[0], transform.transform[1],
                  transform.transform[2], transform.transform[3])
    linear = np.array([[a, b], [d, e]], dtype=float)
    if np.allclose(linear, np.eye(2), atol=1e-9):
      continue                      # a 360 degree turn is the identity
    kinds.append(f"{transform.transform_type}"
                 f"{'' if transform.transform_type != 'rotation' else ' ' + str(round(float(transform.angle), 1)) + 'deg'}")
    rows.append(linear - np.eye(2))
  if not rows:
    return 2, "trivial"
  stacked = np.vstack(rows)
  rank = np.linalg.matrix_rank(stacked, tol=1e-9)
  return 2 - rank, ", ".join(sorted(set(kinds)))


for family, n in DESIGNS:
  unit = unit_for(family, n)
  if unit is None:
    print(f"\n{family} {n}: not in the catalogue at this n")
    continue
  topology, why = te.build(unit)
  if topology is None:
    print(f"\n{family} {n}: no topology ({why})")
    continue

  transforms = topology.tile_matching_transforms
  kinds = Counter(t.transform_type for t in transforms.values())
  orders = sorted({order_of(t) for t in transforms.values()} - {None})
  classes = te.classes(topology)
  print(f"\n{family} {n}")
  print(f"  the group it FOUND: {len(transforms)} transforms, {dict(kinds)}")
  print(f"  rotation orders present: {orders}")
  print(f"  prototile's own point group: "
        f"{Symmetries(topology.tileable.prototile.loc[0, 'geometry']).get_symmetry_group_code()}")
  print(f"  classes: tiles {len(topology.tile_transitivity_classes)}, "
        f"vertices {classes.get('vertex')!r}, edges {classes.get('edge')!r}")

  # ---- the prediction, per vertex class
  seen = {}
  for vertex in topology.points.values():
    if not getattr(vertex, "is_tiling_vertex", False):
      continue
    label = getattr(vertex, "label", None)
    if label is None or label in seen:
      continue
    seen[label] = fixed_space(topology, vertex, transforms)
  for label in sorted(seen):
    dimension, kinds = seen[label]
    predicted = {0: "cannot move at all",
                 1: "may move along one line",
                 2: "may move freely"}[dimension]
    print(f"    vertex class {label}: site symmetry [{kinds}], "
          f"fixed space {dimension}D -> {predicted}")

  # ---- what push_vertex ACTUALLY does to this design
  vertex_classes = classes.get("vertex") or ""
  if vertex_classes:
    from shapely.ops import unary_union
    before = unary_union(list(unit.tiles.geometry))
    tileable, refusals, _state = te.apply(
      topology, [{"classes": vertex_classes, "how": "push_vertex",
                  "args": {"push_d": 0.1}}])
    after = unary_union(list(tileable.tiles.geometry))
    moved = before.symmetric_difference(after).area / before.area
    print(f"  push_vertex on {vertex_classes!r} moves "
          f"{moved:.3e} of the unit's area"
          + (f"  (refused: {refusals})" if refusals else ""))
