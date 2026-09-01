"""Does an edit that moves geometry leave the COMBINATORICS alone?

This is the claim that decides whether a Delaney-Dress style approach
would be worth building. Our transitivity classes are derived from
GEOMETRY -- shapes matched under affine transforms -- so an edit that
lowers the symmetry re-derives them, and docs/TOPOLOGY.md records one
vertex nudge taking laves 3.3.4.3.4 from `a, b` to ten edge classes.
That relabelling under the person is the thing chaining works around.

A D-symbol is COMBINATORIAL: chambers of the barycentric subdivision,
three involutions between them, and two integer functions. It knows
nothing about coordinates. So the prediction is that a manipulation
which moves vertices WITHOUT changing incidence leaves it identical,
and therefore leaves the labels alone -- while the same edit changes
our class counts.

WHAT IS MEASURED, on the same unit before and after one nudge:

  the class counts, which are geometry's answer;
  the combinatorial fingerprint -- how many tiles, how many corners
  each has, each vertex's degree, and the multiset of (left, right)
  tile-corner-counts per edge, which is the incidence a D-symbol is
  built from;
  the flag count, 4 per edge, which bounds the D-symbol's size.

If the fingerprint is identical while the class counts move, the
combinatorial route gives stable labels where ours cannot.

    cd <checkout> && PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 \\
      QT_QPA_PLATFORM=offscreen "$QGIS_PY" \\
      tools/probes/is_the_combinatorics_stable_under_an_edit.py

MEASURED 2026-09-01: on laves 3.3.4.3.4 a nudge of ONE class moves a
tenth of the unit and takes the classes from 1 tile, AB, ab to 2
tiles, ABC, abcde, while the fingerprint is identical -- same corner
counts, same degrees, same incidence, same 428 flags.

AND THE FIRST VERSION MEASURED NOTHING, which is why the premise is
asserted: nudging EVERY vertex class by one vector is a pure
TRANSLATION of the design, so it preserves every symmetry and both
answers came back unchanged. This project had already recorded that
trap once, in a hunt's own report.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.environ.get("WS_ROOT", os.getcwd()))

from tools import probe_kit                                # noqa: E402

probe = probe_kit.start()

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402


def fingerprint(topology):
  """The combinatorics, with every coordinate thrown away.

  Args:
    topology: a built Topology.

  Returns:
    A dict of counts that a D-symbol is a canonical form of: the
    corner counts of the core tiles, the degrees of the tiling
    vertices, and the incidence multiset of the edges. Nothing here
    reads a coordinate, which is the whole point.
  """
  tiles = topology.tiles[:topology.n_tiles]
  corners = Counter(len(t.shape.exterior.coords) - 1 for t in tiles)
  degrees = Counter()
  for vertex in topology.points.values():
    if getattr(vertex, "is_tiling_vertex", False):
      degrees[len(getattr(vertex, "tiles", []) or [])] += 1
  incidence = Counter()
  for edge in topology.edges.values():
    ends = len(getattr(edge, "vertices", []) or [])
    faces = len([t for t in (getattr(edge, "left_tile", None),
                             getattr(edge, "right_tile", None))
                 if t is not None])
    incidence[(ends, faces)] += 1
  return {"tile corner counts": dict(sorted(corners.items())),
          "vertex degrees": dict(sorted(degrees.items())),
          "edge incidence": dict(sorted(incidence.items())),
          "flags (4 per edge)": 4 * len(topology.edges)}


def classes_of(topology):
  """Geometry's answer: how many transitivity classes of each kind."""
  groups = te.classes(topology)
  return {"tiles": len(topology.tile_transitivity_classes),
          "vertices": groups.get("vertex"),
          "edges": groups.get("edge")}


for family, n in (("laves 3.3.4.3.4", 4), ("archimedean 4.8.8", 2)):
  named = [k for k in catalog.TILINGS_BY_N.get(n, {}) if k.startswith(family)]
  if not named:
    print(f"{family} {n}: absent")
    continue
  unit = catalog.make_unit(catalog.TILINGS_BY_N[n][named[0]],
                           spacing=500, crs=3857)
  before, why = te.build(unit)
  if before is None:
    print(f"{family} {n}: no topology ({why})")
    continue
  print(f"\n{family} {n}")
  print(f"  before  classes {classes_of(before)}")
  print(f"          combinatorics {fingerprint(before)}")

  # ONE NUDGE, through the model's own apply, then REBUILT from the
  # edited unit -- which is what makes the classes move, and is
  # exactly the step chaining avoids.
  groups = te.classes(before)
  # ONE CLASS ONLY. Nudging EVERY vertex class by one vector is a pure
  # TRANSLATION of the design -- this project has already recorded
  # that trap once -- so it preserves every symmetry and measures
  # nothing. The premise below is what caught it here.
  one = groups["vertex"][0]
  from shapely.ops import unary_union
  ground_before = unary_union(list(unit.tiles.geometry))
  edited, refusals, _state = te.apply(
    before, [{"classes": one, "how": "nudge_vertex",
              "args": {"dx": 0.05, "dy": 0.05}}])
  if refusals:
    print(f"  the edit was refused: {refusals}")
    continue
  ground_after = unary_union(list(edited.tiles.geometry))
  moved = (ground_before.symmetric_difference(ground_after).area
           / ground_before.area)
  print(f"  the edit on class {one!r} moved {moved:.3e} of the unit")
  if moved < 1e-6:
    print("  PREMISE FAILED: the edit moved nothing, so nothing below "
          "is about an edited design")
    continue
  after, why = te.build(edited)
  if after is None:
    print(f"  after the edit the design carries no topology ({why})")
    continue
  print(f"  after   classes {classes_of(after)}")
  print(f"          combinatorics {fingerprint(after)}")
  same = fingerprint(before) == fingerprint(after)
  moved = classes_of(before) != classes_of(after)
  print(f"  --> combinatorics identical: {same}; classes moved: {moved}")
