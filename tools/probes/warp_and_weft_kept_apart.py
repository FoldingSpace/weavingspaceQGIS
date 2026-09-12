"""What splitting warp from weft costs, read from the symmetries.

The library takes its classes as orbits under the design's FULL
symmetry group. A weave's drawing generally admits a mirror carrying
warps onto wefts, so one class holds edges of both directions. A CLOTH
HAS NO SUCH SYMMETRY: warp and weft differ physically whatever the
picture does, so that mirror is a symmetry of the picture rather than
of the weave (the maintainer's question, 2026-09-11; C-353).

THIS IS THE CONSTRUCTION RATHER THAN THE PROXY.
`classes_that_stay_on_one_strand_family.py` refined the classes by each
edge's own orientation and said in its own docstring that it was a
proxy. This one takes orbits under the direction-preserving transforms
themselves, which is what that docstring said the real thing would be,
and it reports three things the proxy could not:

  THE CONTROL. Orbits under the WHOLE pool of transforms must
  reproduce the library's own classes exactly, or the pool is not
  describing this design's symmetry and nothing taken from it is a
  refinement of what somebody is looking at. `topology_edits` refuses
  the refinement where that fails; this prints it either way.

  THE COST. How many classes each reading gives, against the library's
  own count, and whether that holds still across strand widths.

  THE STRANDWISE CHECK. No refined class may hold edges of two
  directions -- which is the PROXY's own claim, now asked of the real
  construction as an independent reading of it rather than as its
  definition.

Run it in the reference venv, unbuffered, under the watchdog:

    PYTHONUNBUFFERED=1 python3 tools/watchdog.py --stall 900 \
      --timeout 5400 -- ./.venv-reference/bin/python3 \
      tools/probes/warp_and_weft_kept_apart.py

NO TIMINGS DECIDE ANYTHING HERE; every figure is structural. The
elapsed seconds are printed only because a `twill weave a|b` build
takes about forty of them and a silent probe looks like a stuck one.
"""
import collections
import faulthandler
import math
import os
import signal
import sys
import time
import warnings

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "weavingspace_qgis", "vendor"))

warnings.filterwarnings("ignore", category=RuntimeWarning)
faulthandler.register(signal.SIGUSR1)

from weavingspace_qgis import catalog, topology_edits as te  # noqa: E402

SPACING = 1000.0
ASPECTS = (0.9, 0.75, 0.5)
WEAVES = ("plain weave a|b", "twill weave a|b", "basket weave ab|cd",
          "twill weave a|b-")


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


def directions_in_each_class(topology, glue) -> dict:
  """How many distinct directions each class's edges run in.

  Args:
    topology: a built Topology.
    glue: the label map a reading of the aspect gaps called for, or
      None.

  Returns:
    A dict of class label to the number of distinct edge directions it
    holds. One everywhere is what "kept apart" claims.

  IT ASKS THE GEOMETRY, NOT THE CONSTRUCTION. The refinement is taken
  from the transforms; this reads the drawn edges and is therefore a
  second description of the same thing, which is the only kind of
  agreement worth having.
  """
  found = collections.defaultdict(list)
  for edge in topology.edges.values():
    label = getattr(edge, "label", "")
    if not label:
      continue
    klass = glue["edges"].get(label, label) if glue else label
    line = edge.get_geometry()
    (x0, y0), (x1, y1) = line.coords[0], line.coords[-1]
    angle = te._as_direction(x1 - x0, y1 - y0)
    if not any(te._same_direction(angle, other) for other in found[klass]):
      found[klass].append(angle)
  return {klass: len(angles) for klass, angles in found.items()}


def control_holds(topology, kinds) -> bool:
  """Whether the transform pool reproduces the library's own classes.

  Args:
    topology: a built Topology, before any refinement.
    kinds: the map `scaffolded_weave` returned, or None.

  Returns:
    True where orbits under the whole pool partition the base elements
    exactly as the library's labels do.
  """
  edges = [edge for edge in topology.edges.values()
           if getattr(edge, "label", None)]
  points = [point for point in topology.points.values()
            if getattr(point, "label", None)]
  edge_places, vertex_places = {}, {}
  for edge in edges:
    edge_places.setdefault(edge.base_ID, edge.get_geometry().centroid)
  for point in points:
    vertex_places.setdefault(point.base_ID, point.point)
  pool = te._transform_pool(topology)
  return (te._partition_of(te._orbits(edge_places, pool))
          == te._partition_of({e.base_ID: e.label for e in edges})
          and te._partition_of(te._orbits(vertex_places, pool))
          == te._partition_of({v.base_ID: v.label for v in points}))


def read(name: str, aspect: float, reading: str, families: str) -> dict:
  """Build one weave one way and count what came back.

  Args:
    name: the catalogue key.
    aspect: the strand width, as a fraction of the spacing.
    reading: which reading of the aspect gaps to build under.
    families: whether warp and weft share their classes.

  Returns:
    A dict of readings, with `note` carrying any refusal.
  """
  started = time.monotonic()
  topology, unit, kinds, glue, note = te.weave_topology(
    spec_for(name), SPACING, aspect, reading=reading, families=families)
  if topology is None:
    return {"note": note}
  seen = te.class_labels(topology, glue)
  mixed = [klass for klass, count
           in directions_in_each_class(topology, glue).items() if count > 1]
  return {"note": "", "edge": len(seen["edge"]), "vertex": len(seen["vertex"]),
          "mixed": len(mixed), "seconds": time.monotonic() - started}


def main() -> None:
  """Report the cost of the refinement for each weave and width."""
  for name in WEAVES:
    print(f"\n=== {name} ===")
    for aspect in ASPECTS:
      # THE CONTROL IS PINNED TO G. It asks whether the transform pool
      # reproduces the LIBRARY's own classes, and a topology built under
      # H would compare the pool against labels already refined.
      topology, _unit, kinds, _glue, note = te.weave_topology(
        spec_for(name), SPACING, aspect,
        families=te.WARP_AND_WEFT_TOGETHER)
      if topology is None:
        print(f"  a={aspect}: REFUSED -- {note}")
        continue
      print(f"  a={aspect}: the pool reproduces the library's classes: "
            f"{control_holds(topology, kinds)}")
      for reading in te.ASPECT_READINGS:
        row = []
        for families in te.STRAND_FAMILIES:
          answer = read(name, aspect, reading, families)
          if answer["note"]:
            row.append(f"{families}: {answer['note'][:40]}")
            continue
          row.append(f"{families:9s} {answer['edge']:>4}e {answer['vertex']:>4}v "
                     f"mixed {answer['mixed']:>2} ({answer['seconds']:.0f}s)")
        print(f"    {reading:14s} " + " | ".join(row))


if __name__ == "__main__":
  main()
