"""Edge classes that stay on one strand family, and what they cost.

The library takes edge classes as orbits under the design's FULL
symmetry group G. A weave's geometry generally admits a mirror that
maps warps onto wefts, so a G-orbit holds edges of both directions:
`twill weave a|b` class `a` was measured at 81 vertical edges against
80 horizontal.

A CLOTH HAS NO SUCH SYMMETRY. Warp and weft differ physically even
where the drawing is symmetric under swapping them, so the swap is a
symmetry of the picture rather than of the weave -- which is the same
mistake this project's weave report is about, arriving in a new place
(the maintainer's question, 2026-09-11).

WHAT THE REFINEMENT IS. Every element of G either fixes the two strand
families or swaps them, which is a homomorphism onto a group of order
two; its kernel H is the DIRECTION-PRESERVING SUBGROUP, normal and of
index one or two. Orbits under H refine orbits under G, and a G-orbit
splits in two exactly where no swapping element lies in the stabiliser
of any of its edges.

WHAT IS MEASURED HERE IS A PROXY, and the docstring says so rather
than letting a reader assume otherwise: the refinement is taken by each
edge's own orientation, which agrees with the H-orbits while the index
is two and the only direction-mixing comes from the swap. Computing H
properly means reading `tile_matching_transforms`, keeping the
transforms that carry a direction to itself, and taking orbits under
those. The uniform doubling below is consistent with the proxy and is
not a proof of it.

Run it in the reference venv, under the watchdog:

    python3 tools/watchdog.py --stall 900 --timeout 3600 -- \
      ./.venv-reference/bin/python3 \
      tools/probes/classes_that_stay_on_one_strand_family.py

NO TIMINGS ARE TAKEN; every figure is structural.
"""
import collections
import faulthandler
import math
import os
import signal
import sys
import warnings

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

warnings.filterwarnings("ignore", category=RuntimeWarning)
faulthandler.register(signal.SIGUSR1)

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECTS = (0.9, 0.75, 0.5)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd")


def spec_for(name: str) -> dict:
  """The catalogue's own entry for a weave, looked up rather than typed.

  Args:
    name: the catalogue key.

  Returns:
    The spec dict `catalog.make_unit` takes.

  Raises:
    KeyError: where no entry of that name exists.
  """
  for entries in catalog.TILINGS_BY_N.values():
    if name in entries:
      return entries[name]
  raise KeyError(name)


def lattice_of(unit) -> list:
  """The two shortest non-parallel translations the unit repeats by.

  Args:
    unit: a Tileable.

  Returns:
    A list of two (dx, dy) pairs, or fewer where the vectors do not
    supply two independent ones.

  IT READS THE VECTORS' VALUES rather than looking them up by key,
  since a lookup by `(1, 0)` and `(0, 1)` misses every hex-keyed family.
  """
  found = []
  for value in unit.vectors.values():
    dx, dy = value[0], value[1]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
      continue
    found.append((dx, dy))
  found.sort(key=lambda v: v[0] ** 2 + v[1] ** 2)
  out = []
  for candidate in found:
    if not out:
      out.append(candidate)
      continue
    if abs(out[0][0] * candidate[1] - out[0][1] * candidate[0]) > 1e-6:
      out.append(candidate)
      break
  return out


def strandwise_marks(topology, glue) -> list:
  """Every edge's class refined by the direction the edge runs in.

  Args:
    topology: a built Topology.
    glue: the map a reading of the aspect gaps called for, or None.

  Returns:
    A list of `(mark, midpoint)`, the mark being the class label with
    a direction suffix.
  """
  out = []
  for edge in topology.edges.values():
    label = getattr(edge, "label", "")
    if not label:
      continue
    klass = glue["edges"].get(label, label) if glue else label
    line = edge.get_geometry()
    (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
    angle = math.degrees(math.atan2(abs(y1 - y0), abs(x1 - x0)))
    out.append((f"{klass}{'|' if angle > 45 else '-'}",
                line.interpolate(0.5, normalized=True)))
  return out


def read(name: str, reading: str, aspect: float) -> dict:
  """Count the library's classes beside the strandwise ones.

  Args:
    name: the catalogue key.
    reading: which reading of the aspect gaps to build under.
    aspect: the strand width, as a fraction of the spacing.

  Returns:
    A dict of readings, with `note` carrying any refusal.

  THE TRANSLATION CHECK IS THE CONTROL. Copies of one edge under the
  lattice are the same edge, so they must carry the same mark; a
  refinement where they disagree is describing the constructor's patch
  rather than the design.
  """
  topology, unit, kinds, glue, note = te.weave_topology(
    spec_for(name), SPACING, aspect, reading=reading)
  if topology is None:
    return {"note": note}
  library = te.class_labels(topology, glue)["edge"]
  marks = strandwise_marks(topology, glue)
  vectors = lattice_of(unit)
  if len(vectors) < 2:
    return {"note": "the unit does not give two lattice vectors"}
  (ax, ay), (bx, by) = vectors[0], vectors[1]
  determinant = ax * by - ay * bx
  by_place = collections.defaultdict(set)
  for mark, point in marks:
    first = ((point.x * by - point.y * bx) / determinant) % 1.0
    second = ((ax * point.y - ay * point.x) / determinant) % 1.0
    by_place[(round(first, 3), round(second, 3))].add(mark)
  return {
    "note": "",
    "library": len(library),
    "strandwise": len({mark for mark, _p in marks}),
    "disagree": sum(1 for marks_here in by_place.values()
                    if len(marks_here) > 1),
  }


def main() -> None:
  """Report the refinement for each weave, reading and strand width."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    for reading in te.ASPECT_READINGS:
      shapes = []
      for aspect in ASPECTS:
        row = read(name, reading, aspect)
        if row.get("note"):
          print(f"  {reading:14s} a={aspect}: {row['note'][:44]}")
          continue
        shapes.append((row["library"], row["strandwise"]))
        print(f"  {reading:14s} a={aspect}  library {row['library']:>3} "
              f"classes   strandwise {row['strandwise']:>3}   "
              f"places that disagree {row['disagree']}")
      if shapes:
        print(f"  {'':14s}          across widths: "
              f"{'INVARIANT' if len(set(shapes)) == 1 else 'MOVES'}")


if __name__ == "__main__":
  main()
